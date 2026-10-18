"""Helpers for talking to the OpenAlex API (https://openalex.org)."""

import os

import requests

from paperfetch.models import Paper

BASE_URL = "https://api.openalex.org"
WORK_FIELDS = "id,title,doi,publication_year,authorships,open_access,best_oa_location,locations,has_content"

# Where in each paper the query is matched. "all" also searches the full text.
# Maps friendly names users type to OpenAlex's own names.
SEARCH_FIELDS = {
    "title": "title.search",
    "abstract": "abstract.search",
    "title_and_abstract": "title_and_abstract.search",
    "all": None,
}
SORT_ORDERS = {
    "relevance": "relevance_score:desc",
    "newest": "publication_date:desc",
    "most_cited": "cited_by_count:desc",
}


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


def build_filter(
    query: str,
    *,
    search_in: str = "title_and_abstract",
    from_year: int | None = None,
    to_year: int | None = None,
    exclude_reviews: bool = False,
    english_only: bool = False,
    pdf_only: bool = True,
    extra_filter: str | None = None,
) -> str:
    """Turn search options into an OpenAlex filter string, e.g. "is_oa:true,language:en".

    Raises ValueError for options OpenAlex would reject or silently misread.
    "*" indicates everything aftewards should be passed by name to prevent mix ups like swapping to and from_year.
    """
    if search_in not in SEARCH_FIELDS:
        # checks bad input before building anything, e.g., titles
        choices = ", ".join(SEARCH_FIELDS)
        raise ValueError(f"search_in must be one of {choices}, got {search_in!r}")
    if from_year and to_year and from_year > to_year:
        # checks for an actual, real year range
        raise ValueError(f"from_year ({from_year}) is after to_year ({to_year})")

    # always on filters to ensure nonretracted/open access: collects filter pieces and joins with commas.
    parts = ["is_oa:true", "is_retracted:false"]

    # e.g. "title_and_abstract.search", or None for "all"
    field = SEARCH_FIELDS[search_in]
    if field:
        # Commas separate filters, so a comma in the query would silently split it.
        if "," in query:
            raise ValueError(
                "Remove commas from the search text; use AND / OR instead."
            )
        parts.append(f"{field}:{query}")  # splits on commas

    # optional pieces only when they're specified
    if from_year or to_year:
        parts.append(f"publication_year:{from_year or ''}-{to_year or ''}")
    if exclude_reviews:
        # OpenAlex labels some reviews as articles, so also drop titles containing "review".
        parts += ["type:!review", "title.search:NOT review"]
    if english_only:
        parts.append("language:en")
    if pdf_only:
        parts.append("has_pdf_url:true")
    if extra_filter:
        parts.append(extra_filter)

    return ",".join(parts)


def search_works(
    query: str,
    limit: int = 25,
    *,
    search_in: str = "title_and_abstract",
    from_year: int | None = None,
    to_year: int | None = None,
    exclude_reviews: bool = False,
    english_only: bool = False,
    pdf_only: bool = True,
    extra_filter: str | None = None,
    sort: str = "relevance",
    api_key: str | None = None,
    timeout: float = 30,
) -> list[Paper]:
    """Search OpenAlex for open-access works matching `query`.

    By default the query is matched against titles and abstracts, and only papers
    with a PDF link are returned. Returns at most `limit` papers (1-100). Raises
    ValueError for invalid options, including filters OpenAlex rejects, and
    requests.HTTPError for other OpenAlex errors.
    """
    # check search limits and sort options
    if not 1 <= limit <= 100:
        raise ValueError(f"limit must be between 1 and 100, got {limit}")
    if sort not in SORT_ORDERS:
        raise ValueError(f"sort must be one of {', '.join(SORT_ORDERS)}, got {sort!r}")

    params = {  # all the criteria of the search
        "filter": build_filter(
            query,
            search_in=search_in,
            from_year=from_year,
            to_year=to_year,
            exclude_reviews=exclude_reviews,
            english_only=english_only,
            pdf_only=pdf_only,
            extra_filter=extra_filter,
        ),
        "sort": SORT_ORDERS[sort],
        "per_page": limit,
        "select": WORK_FIELDS,
    }
    if search_in == "all":
        params["search"] = query  # the one case outside of the filter

    # sending and error handling for the request
    response = requests.get(
        f"{BASE_URL}/works",
        params=params,
        headers=_auth_headers(api_key),
        timeout=timeout,
    )
    if response.status_code == 400:
        # Usually a typo in extra_filter; OpenAlex's reply says what's wrong.
        try:
            message = response.json().get("message", response.text)
        except ValueError:
            message = response.text
        raise ValueError(f"OpenAlex rejected the search: {message[:300]}")
    response.raise_for_status()
    return [parse_work(work) for work in response.json()["results"]]


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
        has_cached_pdf=bool((work.get("has_content") or {}).get("pdf")),
    )
