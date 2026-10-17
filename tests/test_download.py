"""Tests for paperfetch.download. These never touch the network or real files."""

# standard libraries
import pytest
import requests

# custom modules
from paperfetch import download
from paperfetch.download import download_pdf
from paperfetch.models import Paper

PUBLISHER_URL = "https://example.org/paper.pdf"
OPENALEX_URL = "https://content.openalex.org/works/W123.pdf"
PDF_BYTES = b"%PDF-1.7 pretend this is a paper"
HTML_BYTES = b"<html>Please log in</html>"


def make_paper(pdf_url=None, has_cached_pdf=False):
    """Build a Paper with only the fields the downloader cares about filled in.-"""
    return Paper(
        openalex_id="https://openalex.org/W123",
        title="A paper",
        doi=None,
        year=2024,
        authors=(),
        is_oa=True,
        pdf_url=pdf_url,
        landing_page_url=None,
        has_cached_pdf=has_cached_pdf,
    )


class FakeResponse:
    """Stands in for requests.Response, with raw bytes instead of JSON."""

    def __init__(self, content, status_code=200):
        self.content = content
        self.status_code = status_code

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError(f"{self.status_code} error")


def fake_server(monkeypatch, responses):
    """Make requests.get answer from `responses` (url -> response) and record calls.

    A response can also be an exception, which is raised to simulate a network error.
    A URL missing from `responses` fails the test, so unexpected requests are caught.
    """
    calls = []

    def fake_get(url, params=None, headers=None, timeout=None):
        calls.append({"url": url, "params": params})
        result = responses[url]
        if isinstance(result, Exception):
            raise result
        return result

    monkeypatch.setattr(download.requests, "get", fake_get)
    return calls


def test_downloads_from_publisher(monkeypatch, tmp_path):
    """Test downloader fetches PDFs and saves them to a temporary folder.

    tmp_path is another test fixture like monkeypatch."""
    calls = fake_server(monkeypatch, {PUBLISHER_URL: FakeResponse(PDF_BYTES)})

    path = download_pdf(make_paper(pdf_url=PUBLISHER_URL), tmp_path)

    assert path == tmp_path / "W123.pdf"
    assert path.read_bytes() == PDF_BYTES
    assert len(calls) == 1


def test_falls_back_to_openalex_when_publisher_sends_html(monkeypatch, tmp_path):
    calls = fake_server(
        monkeypatch,
        {
            PUBLISHER_URL: FakeResponse(HTML_BYTES),
            OPENALEX_URL: FakeResponse(PDF_BYTES),
        },
    )
    paper = make_paper(pdf_url=PUBLISHER_URL, has_cached_pdf=True)

    path = download_pdf(paper, tmp_path, api_key="test-key")

    assert path.read_bytes() == PDF_BYTES
    #   check the second request, the fall back, and confirms it sent api key to right url.
    assert calls[1] == {"url": OPENALEX_URL, "params": {"api_key": "test-key"}}


def test_publisher_network_error_is_not_fatal(monkeypatch, tmp_path):
    fake_server(monkeypatch, {PUBLISHER_URL: requests.ConnectionError("offline")})

    assert download_pdf(make_paper(pdf_url=PUBLISHER_URL), tmp_path) is None
    assert not (tmp_path / "W123.pdf").exists()


def test_no_sources_makes_no_requests(monkeypatch, tmp_path):
    calls = fake_server(monkeypatch, {})

    assert download_pdf(make_paper(), tmp_path) is None
    assert calls == []


def test_skips_cached_copy_without_api_key(monkeypatch, tmp_path):
    monkeypatch.delenv("OPENALEX_API_KEY", raising=False)
    calls = fake_server(monkeypatch, {})

    assert download_pdf(make_paper(has_cached_pdf=True), tmp_path) is None
    assert calls == []


def test_existing_file_is_not_downloaded_again(monkeypatch, tmp_path):
    existing = tmp_path / "W123.pdf"
    existing.write_bytes(b"%PDF already here")
    calls = fake_server(monkeypatch, {})

    assert download_pdf(make_paper(pdf_url=PUBLISHER_URL), tmp_path) == existing
    assert calls == []


def test_openalex_errors_are_raised(monkeypatch, tmp_path):
    fake_server(monkeypatch, {OPENALEX_URL: FakeResponse(b"", status_code=429)})

    with pytest.raises(requests.HTTPError):
        download_pdf(make_paper(has_cached_pdf=True), tmp_path, api_key="test-key")
