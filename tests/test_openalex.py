"""Tests for paperfetch.openalex. These never touch the network.

This file contains four parts: imports, 5 tests for find_pdf_url, a fake response class, and 3 tests for get_work.
Formatting of imports follows standard libraries, third-party packages, and custom packages for ruff."""

from dataclasses import FrozenInstanceError  # Python's standard library

# tests for third-party packages
import pytest  # only needed for pytest.raises
import requests  # only needed for fake_get to raise the same error as real requests

# tests for paperfetch's own packages
from paperfetch import openalex  # module to test
from paperfetch.models import Paper
from paperfetch.openalex import find_pdf_url, get_work, parse_work  # functions to test

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


class FakeResponse:
    """Stands in for requests.Response."""

    def __init__(self, data, status_code=200):
        """Runs when FakeResponse is written and gives fake HTTP code 200."""
        self.data = data
        self.status_code = status_code

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
    )


def test_paper_is_read_only():
    """Tests and locks in frozen=True for any Paper."""
    paper = parse_work({"id": "https://openalex.org/W1"})  # arrange: create a paper

    with pytest.raises(FrozenInstanceError):  # act and asser together
        paper.title = "Changed"
