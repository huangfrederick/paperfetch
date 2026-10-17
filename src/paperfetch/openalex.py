"""Helpers for talking to the OpenAlex API (https://openalex.org)."""

import os

import requests

from paperfetch.models import Paper

BASE_URL = "https://api.openalex.org"
WORK_FIELDS = (
    "id,title,doi,publication_year,authorships,open_access,best_oa_location,locations"
)


def _auth_headers(api_key: str | None) -> dict:
    """Help build the OpenAlex auth header, falling back to the OPENALEX_API_KEY env var."""
    api_key = api_key or os.environ.get("OPENALEX_API_KEY")
    return {"Authorization": f"Bearer {api_key}"} if api_key else {}


def get_work(doi: str, api_key: str | None = None, timeout: float = 30) -> dict:
    """Fetch one work (paper) from OpenAlex by its shortform DOI, e.g. "10.7717/peerj.4375".

    API key is optional. If not given, it is read from the environment variable.
    Without any key, the request still works, but with lower rate limits.
    Raises requests.HTTPError if openalex returns an error such as 404."""

    response = requests.get(
        f"{BASE_URL}/works/doi:{doi}", headers=_auth_headers(api_key), timeout=timeout
    )
    response.raise_for_status()
    return response.json()


def search_works(
    query: str, limit: int = 25, api_key: str | None = None, timeout: float = 30
) -> list[Paper]:
    """Search OpenAlex for open-access works matching `query`, best matches first.

    Returns at most `limit` papers (1-100). Raises requests.HTTPError if
    OpenAlex returns an error.
    Calls parse_work defined later in this file.
    """
    if not 1 <= limit <= 100:
        raise ValueError(f"limit must be between 1 and 100, got {limit}")

    params = {  # builds part of the URL and handles encoding
        "search": query,
        "filter": "is_oa:true",  # keep only open access works
        "per_page": limit,  # check inputs are kept to 100 results per page. raises ValueError up front.
        "select": WORK_FIELDS,
    }
    response = requests.get(
        f"{BASE_URL}/works",
        params=params,
        headers=_auth_headers(api_key),
        timeout=timeout,
    )
    response.raise_for_status()
    return [
        parse_work(work) for work in response.json()["results"]
    ]  # list comprehension to turn each raw result into a Paper object.


def find_pdf_url(work: dict) -> str | None:
    """Return a link to a free, legal PDF of the work, or None if there isn't one."""
    # check and retrieve best open-access location first
    best = work.get("best_oa_location") or {}
    if best.get("pdf_url"):
        return best["pdf_url"]

    for location in work.get("locations") or []:
        if location.get("is_oa") and location.get("pdf_url"):
            return location["pdf_url"]

    return None


def parse_work(work: dict) -> Paper:
    """Convert a raw OpenAlex work record into a Paper."""
    doi = work.get("doi")
    best = work.get("best_oa_location") or {}
    open_access = work.get("open_access") or {}

    return Paper(
        openalex_id=work["id"],
        title=work.get("title"),
        doi=doi.removeprefix("https://doi.org/") if doi else None,
        year=work.get("publication_year"),
        authors=tuple(
            a["author"]["display_name"] for a in work.get("authorships") or []
        ),  # for each authorship, take author's name for collecting into tuple
        is_oa=bool(open_access.get("is_oa")),
        pdf_url=find_pdf_url(work),
        landing_page_url=best.get("landing_page_url"),
    )
