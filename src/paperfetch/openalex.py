"""Helpers for talking to the OpenAlex API (https://openalex.org)."""

import os

import requests

BASE_URL = "https://api.openalex.org"


def get_work(doi: str, api_key: str | None = None, timeout: float = 30) -> dict:
    """Fetch one work (paper) from OpenAlex by its DOI, e.g. "10.7717/peerj.4375".

    API key is optional. If not given, it is read from the environment variable.
    Without any key, the request still works, but with lower rate limits.
    Raises requests.HTTPError if openalex returns an error such as 404."""
    api_key = api_key or os.environ.get("OPENALEX_API_KEY")
    headers = {"Authorization": f"Bearer {api_key}"} if api_key else {}

    response = requests.get(
        f"{BASE_URL}/works/doi:{doi}", headers=headers, timeout=timeout
    )
    response.raise_for_status()
    return response.json()


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
