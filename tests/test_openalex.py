"""Tests for paperfetch.openalex. These never touch the network.

Sections: find_pdf_url, get_work, parse_work, search_works, build_filter.
"""

from dataclasses import FrozenInstanceError  # Python's standard library

# tests for third-party packages
import pytest  # only needed for pytest.raises
import requests  # only needed for fake_get to raise the same error as real requests

# tests for paperfetch's own packages
from paperfetch import openalex  # module to test
from paperfetch.models import Paper
from paperfetch.openalex import (  # functions to test
    build_filter,
    find_pdf_url,
    get_work,
    parse_work,
    search_works,
)

# --- find_pdf_url: fake work records shaped like real OpenAlex data ---


def test_find_pdf_url_uses_best_oa_location():
    # Shaped like the NumPy paper, 10.1038/s41586-020-2649-2
    work = {
        "best_oa_location": {
            "is_oa": True,
            "pdf_url": "https://www.nature.com/articles/s41586-020-2649-2.pdf",
        },
        "locations": [],
    }  # arrange: build the input for testing where best has a pdf
    assert (
        find_pdf_url(work) == "https://www.nature.com/articles/s41586-020-2649-2.pdf"
    )  # act and assert: call code and check output


def test_find_pdf_url_falls_back_to_other_locations():
    work = {
        "best_oa_location": {"is_oa": True, "pdf_url": None},
        "locations": [
            {"is_oa": True, "pdf_url": None},
            {"is_oa": True, "pdf_url": "https://arxiv.org/pdf/1706.03762"},
        ],
    }  # arrange: build input for testing where best has none, but 2nd location has one pdf
    assert (
        find_pdf_url(work) == "https://arxiv.org/pdf/1706.03762"
    )  # call code and check output


def test_find_pdf_url_skips_closed_locations():
    work = {
        "best_oa_location": None,
        "locations": [
            {"is_oa": False, "pdf_url": "https://paywalled.example/paper.pdf"}
        ],
    }  # input for testing where only closed-access PDF exists, checking if is_oa is False
    assert find_pdf_url(work) is None


def test_find_pdf_url_returns_none_when_no_pdf_anywhere():
    # Shaped like 10.7717/peerj.4375: open access, but no direct PDF link
    work = {
        "best_oa_location": {"is_oa": True, "pdf_url": None},
        "locations": [{"is_oa": True, "pdf_url": None}],
    }  # input for testing where no PDF exists anywhere as open access and fails if indicate closed access
    assert find_pdf_url(work) is None


def test_find_pdf_url_handles_missing_fields():
    assert find_pdf_url({}) is None


# --- get_work: replace requests.get with a fake so no real request is sent ---


# general rule for fakes: should exactly need the attributes the code actually uses
class FakeResponse:
    """Stands in for requests.Response."""

    def __init__(self, data, status_code=200):
        """Runs when FakeResponse is written and gives fake HTTP code 200."""
        self.data = data
        self.status_code = status_code
        self.text = str(data)

    def raise_for_status(self):
        """Raise HTTPError for codes >= 400."""
        if self.status_code >= 400:
            raise requests.HTTPError(f"{self.status_code} error")

    def json(self):
        """Return the faked JSON data."""
        return self.data


def test_get_work_sends_doi_and_key(monkeypatch):
    """Monkeypatch reverts every change made during tests even if test fails.

    Empty list is created to act as notebook for recording requests.
    fake_get is defined inside the test to append to calls."""
    calls = []

    def fake_get(url, headers, timeout):
        """Parameters must match how get_work calls requests.get.

        Raises TypeError if parameters don't match."""
        calls.append({"url": url, "headers": headers, "timeout": timeout})
        return FakeResponse({"title": "Array programming with NumPy"})

    monkeypatch.setattr(
        openalex.requests, "get", fake_get
    )  # swaps real function for fake.

    work = get_work(
        "10.1038/s41586-020-2649-2", api_key="test-key"
    )  # test using made up key

    assert work == {
        "title": "Array programming with NumPy"
    }  # check if get_work returned what server sent
    assert calls == [
        {
            "url": "https://api.openalex.org/works/doi:10.1038/s41586-020-2649-2",
            "headers": {"Authorization": "Bearer test-key"},
            "timeout": 30,
        }
    ]  # check if request was built with correct URL, headers, and timeout


def test_get_work_without_key_sends_no_auth_header(monkeypatch):
    """Makes sure no real API key is leaked into tests."""
    monkeypatch.delenv("OPENALEX_API_KEY", raising=False)
    calls = []

    def fake_get(url, headers, timeout):
        calls.append(headers)
        return FakeResponse({})

    monkeypatch.setattr(
        openalex.requests, "get", fake_get
    )  # while this test runs, requests.get is fake_get.

    get_work("10.1038/s41586-020-2649-2")

    assert calls == [{}]


def test_get_work_raises_on_http_error(monkeypatch):
    monkeypatch.setattr(
        openalex.requests, "get", lambda url, headers, timeout: FakeResponse({}, 404)
    )

    with pytest.raises(requests.HTTPError):  # check that an error does happen.
        get_work("10.0000/does-not-exist")


# --- parse_work: raw OpenAlex dict -> Paper ---


def test_parse_work_full_record():
    """Test using a realistic input, comparing entire Paper with ==.

    Check that DOI prefix gets stripped and every field within Paper is correctly populated."""
    work = {  # build input for testing.
        "id": "https://openalex.org/W123",
        "title": "Array programming with NumPy",
        "doi": "https://doi.org/10.1038/s41586-020-2649-2",  # give full URL to check stripping
        "publication_year": 2020,
        "authorships": [
            {"author": {"display_name": "Charles R. Harris"}},
            {"author": {"display_name": "K. Jarrod Millman"}},
        ],
        "open_access": {"is_oa": True},
        "best_oa_location": {
            "is_oa": True,
            "pdf_url": "https://www.nature.com/articles/s41586-020-2649-2.pdf",  # is what find_pdf_url should pick up
            "landing_page_url": "https://doi.org/10.1038/s41586-020-2649-2",
        },
        "locations": [],  # leave empty since this is testing an ideal location
        "has_content": {"pdf": True},  # indicate that OpenAlex has a cached PDF
    }

    assert parse_work(
        work
    ) == Paper(  # act and run comparison between actual and theoretical results.
        openalex_id="https://openalex.org/W123",
        title="Array programming with NumPy",
        doi="10.1038/s41586-020-2649-2",
        year=2020,
        authors=("Charles R. Harris", "K. Jarrod Millman"),
        is_oa=True,
        pdf_url="https://www.nature.com/articles/s41586-020-2649-2.pdf",
        landing_page_url="https://doi.org/10.1038/s41586-020-2649-2",
        has_cached_pdf=True,
    )


def test_parse_work_minimal_record():
    """Test worst case scenario where only id is present.

    Only "id" is guaranteed; everything else should fall back safely"""
    assert parse_work({"id": "https://openalex.org/W1"}) == Paper(
        openalex_id="https://openalex.org/W1",
        title=None,
        doi=None,
        year=None,
        authors=(),
        is_oa=False,
        pdf_url=None,
        landing_page_url=None,
        has_cached_pdf=False,
    )


def test_paper_is_read_only():
    """Tests and locks in frozen=True for any Paper."""
    paper = parse_work({"id": "https://openalex.org/W1"})  # arrange: create a paper

    with pytest.raises(FrozenInstanceError):  # act and asser together
        paper.title = "Changed"


def test_paper_work_id_is_short_id():
    paper = parse_work({"id": "https://openalex.org/W3082255212"})
    assert paper.work_id == "W3082255212"


# --- search_works ---


def test_search_works_sends_query_and_parses_results(monkeypatch):
    """Check the search part of requests.

    Ensures every result comes back as a Paper object."""
    calls = []

    def fake_get(url, params, headers, timeout):
        """Takes params from search_works for testing."""
        calls.append({"url": url, "params": params})
        results = [
            {"id": "https://openalex.org/W1", "title": "First"},
            {"id": "https://openalex.org/W2", "title": "Second"},
        ]
        return FakeResponse({"results": results})

    monkeypatch.setattr(openalex.requests, "get", fake_get)

    papers = search_works("open access citation advantage", limit=2, api_key="k")

    assert [paper.title for paper in papers] == ["First", "Second"]
    assert calls[0]["url"] == "https://api.openalex.org/works"
    # checks default search covers title + abstract, excludes retracted papers, and has a pdf
    assert calls[0]["params"]["filter"] == (
        "is_oa:true,is_retracted:false,"
        "title_and_abstract.search:open access citation advantage,has_pdf_url:true"
    )
    # test to see that best matches are first by default
    assert calls[0]["params"]["sort"] == "relevance_score:desc"
    # checks default does not back to full-text search
    assert "search" not in calls[0]["params"]
    assert calls[0]["params"]["per_page"] == 2


@pytest.mark.parametrize("limit", [0, 101])  # boundary testing for search result limits
def test_search_works_rejects_bad_limit(limit):
    with pytest.raises(ValueError):
        search_works("anything", limit=limit)


# --- build_filter: search options -> OpenAlex filter string ---


def test_build_filter_defaults():
    """Pins exact default filter. Fails if default is changed by accident."""
    assert build_filter("dental composite") == (
        "is_oa:true,is_retracted:false,"
        "title_and_abstract.search:dental composite,has_pdf_url:true"
    )


def test_build_filter_all_options():
    """Turns every option on and compares results as a list.

    Checks each piece is present/written, order of pieces, and pdf_url is absent.
    """
    result = build_filter(
        '"dental composite" AND experimental',
        search_in="title",
        from_year=2010,
        to_year=2020,
        exclude_reviews=True,
        english_only=True,
        pdf_only=False,
        extra_filter="cited_by_count:>10",
    )
    # compares a list of parameters instead of 1 long string, and failures shows diff
    assert result.split(",") == [
        "is_oa:true",
        "is_retracted:false",
        'title.search:"dental composite" AND experimental',
        "publication_year:2010-2020",
        "type:!review",
        "title.search:NOT review",
        "language:en",
        "cited_by_count:>10",
    ]


@pytest.mark.parametrize(
    ("from_year", "to_year", "expected"),
    [(2010, None, "publication_year:2010-"), (None, 2015, "publication_year:-2015")],
)
def test_build_filter_open_ended_years(from_year, to_year, expected):
    assert expected in build_filter("x", from_year=from_year, to_year=to_year)


def test_build_filter_all_leaves_query_out_of_filter():
    """Ensures filter contains no search term with "all" search_in.

    Query goes in search= parameter and protects if field:/None logic.
    """
    assert "search" not in build_filter("dental composite", search_in="all")


@pytest.mark.parametrize(
    "options",
    [
        {"query": "resin, composite"},
        {"query": "x", "search_in": "titles"},
        {"query": "x", "from_year": 2020, "to_year": 2010},
    ],
)
def test_build_filter_rejects_bad_options(options):
    """Unpacks a dict in keyword arguments."""
    with pytest.raises(ValueError):
        build_filter(**options)


def test_search_works_all_uses_search_param(monkeypatch):
    calls = []

    def fake_get(url, params, headers, timeout):
        calls.append(params)
        return FakeResponse({"results": []})

    monkeypatch.setattr(openalex.requests, "get", fake_get)

    search_works("dental composite", search_in="all", sort="newest")

    assert calls[0]["search"] == "dental composite"
    assert calls[0]["sort"] == "publication_date:desc"


def test_search_works_rejects_unknown_sort():
    with pytest.raises(ValueError):
        search_works("x", sort="oldest")


def test_search_works_turns_bad_filter_into_value_error(monkeypatch):
    reply = {"message": "made_up_filter is not a valid field"}
    monkeypatch.setattr(
        openalex.requests,
        "get",
        lambda url, params, headers, timeout: FakeResponse(reply, 400),
    )

    # checks error message contains text instead of some random ValueError.
    # ensures openalex explanation reaches user.
    with pytest.raises(ValueError, match="made_up_filter is not a valid field"):
        search_works("x", extra_filter="made_up_filter:true")
