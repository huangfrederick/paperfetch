"""Tests for the paperfetch command line. Search and download are faked."""

from pathlib import Path

import pytest
import requests

# import cli as module so tests can patch cli.search_works / cli.download_pdf.
from paperfetch import cli
from paperfetch.models import Paper  # builds fake search results for testing.


def make_paper(work_id, title, year=2024):
    """Builds paper object for only CLI used parts vary. Everything else gets a dummy value."""
    return Paper(
        openalex_id=f"https://openalex.org/{work_id}",
        title=title,
        doi=None,
        year=year,
        authors=(),
        is_oa=True,
        pdf_url=None,
        landing_page_url=None,
        has_cached_pdf=False,
    )


# fake search results.
PAPERS = [make_paper("W1", "Has a PDF"), make_paper("W2", "No PDF", year=None)]


@pytest.fixture
def fake_backend(monkeypatch, tmp_path):
    """Fake search and download inside cli, and run the test in an empty folder."""
    monkeypatch.chdir(tmp_path)  # run inside an empty folder.
    searches = []  # create lists to record data in.
    downloads = []

    def fake_search(query, limit, **options):
        """Record query and limit, returning PAPERS."""
        searches.append({"query": query, "limit": limit, **options})
        return PAPERS

    def fake_download(paper, folder):
        """Record which paper and which folder was asked about.

        Returns path for W1 (saved), or W2 (None).
        Does not write any files."""
        downloads.append({"work_id": paper.work_id, "folder": folder})
        return folder / f"{paper.work_id}.pdf" if paper.work_id == "W1" else None

    # swap real search with fakes.
    monkeypatch.setattr(cli, "search_works", fake_search)
    monkeypatch.setattr(cli, "download_pdf", fake_download)
    # tests unpack this as: searches, downloads = fake_backend
    return searches, downloads


def test_searches_downloads_and_reports(fake_backend, capsys):
    """Test for when options are parsed, every paper is downloaded, and output and exit code are right."""
    searches, downloads = fake_backend

    exit_code = cli.main(["citation advantage", "--limit", "2", "--out", "pdfs"])

    # return everything printed in stdout so far as 1 string.
    out = capsys.readouterr().out
    assert exit_code == 0
    assert searches[0]["query"] == "citation advantage"
    assert searches[0]["limit"] == 2
    assert downloads == [
        {"work_id": "W1", "folder": Path("pdfs")},
        {"work_id": "W2", "folder": Path("pdfs")},
    ]
    assert "[saved]   2024  Has a PDF" in out
    assert "[no PDF]  ----  No PDF" in out
    assert "Saved 1 of 2 PDFs to pdfs/" in out


def test_default_options(fake_backend):
    """Pin defaults if no options are provided."""
    searches, downloads = fake_backend

    cli.main(["numpy"])

    assert searches[0]["limit"] == 10
    assert downloads[0]["folder"] == Path("papers")


def test_no_download_only_lists(fake_backend, capsys):
    """List results only, never call the downloader,  and no summary line."""
    _searches, downloads = fake_backend

    exit_code = cli.main(["numpy", "--no-download"])

    out = capsys.readouterr().out
    assert exit_code == 0
    assert downloads == []
    assert "2024  Has a PDF" in out
    assert "Saved" not in out


def test_search_error_exits_with_1(fake_backend, monkeypatch, capsys):
    """Replace fake search with one that raises the same ValueError as the real one with a limit of 500."""

    def failing_search(query, limit, **options):
        raise ValueError("limit must be between 1 and 100, got 500")

    monkeypatch.setattr(cli, "search_works", failing_search)

    assert cli.main(["numpy", "--limit", "500"]) == 1
    captured = capsys.readouterr()
    assert "Search failed: limit must be between 1 and 100" in captured.err
    assert captured.out == ""


def test_refused_download_stops_with_1(fake_backend, monkeypatch, capsys):
    """Simulate OpenAlex refusing a download, e.g. when budget is spent.

    If refused, stop and exit with code 1.
    """

    def refusing_download(paper, folder):
        raise requests.HTTPError("429 error")

    monkeypatch.setattr(cli, "download_pdf", refusing_download)

    assert cli.main(["numpy"]) == 1
    assert "Stopping, OpenAlex refused a download" in capsys.readouterr().err


def test_non_number_limit_is_rejected_by_argparse(capsys):
    """Test if non-numeric limit is rejected by argparse.

    Exit with code 2.
    """
    with pytest.raises(SystemExit) as exit_info:
        cli.main(["numpy", "--limit", "abc"])

    assert exit_info.value.code == 2
    assert "invalid int value: 'abc'" in capsys.readouterr().err


def test_default_search_options(fake_backend):
    """Pins CLI defaults to title+abstract, PDF only, relevance, and no extra filters.

    This is what user gets without typing any options.
    """
    searches, _downloads = fake_backend

    cli.main(["dental composite"])

    options = searches[0]
    assert options["search_in"] == "title_and_abstract"
    assert options["pdf_only"] is True
    assert options["sort"] == "relevance"
    assert options["from_year"] is None
    assert options["extra_filter"] is None


def test_search_options_are_passed_through(fake_backend):
    """Sets every flag and compares to whole recorded call.

    Proves each flag reaches right parameters ("2010" becoming 2010, etc.).
    """
    searches, _downloads = fake_backend

    cli.main(
        [
            '"dental composite" AND experimental',
            "--search-in",
            "title",
            "--from-year",
            "2010",
            "--to-year",
            "2020",
            "--exclude-reviews",
            "--english-only",
            "--include-no-pdf",
            "--sort",
            "newest",
            "--filter",
            "cited_by_count:>10",
        ]
    )

    assert searches[0] == {
        "query": '"dental composite" AND experimental',
        "limit": 10,
        "search_in": "title",
        "from_year": 2010,
        "to_year": 2020,
        "exclude_reviews": True,
        "english_only": True,
        "pdf_only": False,
        "extra_filter": "cited_by_count:>10",
        "sort": "newest",
    }


@pytest.mark.parametrize("bad_args", [["--sort", "oldest"], ["--search-in", "titles"]])
def test_unknown_choices_are_rejected_by_argparse(bad_args, capsys):
    """Checks choices= works for both options.

    Ensures that invalid choices for --sort and --search-in are rejected by argparse.
    """
    with pytest.raises(SystemExit) as exit_info:
        cli.main(["x", *bad_args])

    assert exit_info.value.code == 2
    assert "invalid choice" in capsys.readouterr().err
