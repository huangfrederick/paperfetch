"""Download open-access PDFs for papers."""

# import standard libraries
import os
from pathlib import Path

# import third-party libraries
import requests

# import custom modules
from paperfetch.models import Paper

CONTENT_URL = "https://content.openalex.org/works"
# Identify ourselves honestly; some sites block the default "python-requests" agent.
USER_AGENT = "paperfetch/0.1.0 (https://github.com/huangfrederick/paperfetch)"


def download_pdf(
    paper: Paper, folder: str | Path, api_key: str | None = None, timeout: float = 60
) -> Path | None:
    """Save a PDF of `paper` in `folder` and return its path, or None if none found.

    Tries the free publisher/repository link (paper.pdf_url) first, then OpenAlex's
    cached copy, which needs an API key and costs $0.01 of your daily budget
    (about 100 PDFs per day on a free key). Skips papers already downloaded.
    Raises requests.HTTPError if OpenAlex refuses, e.g. 429 when the budget is used up.
    """
    path = Path(folder) / f"{paper.work_id}.pdf"
    if path.exists():
        return path

    content = None
    if paper.pdf_url:
        content = _fetch_publisher_pdf(paper.pdf_url, timeout)
    if content is None and paper.has_cached_pdf:
        content = _fetch_cached_pdf(paper.work_id, api_key, timeout)
    if content is None:
        return None

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)
    return path


def _is_pdf(content: bytes) -> bool:
    """Real PDF files always start with "%PDF"; error and login pages don't."""
    return content.startswith(b"%PDF")


def _fetch_publisher_pdf(url: str, timeout: float) -> bytes | None:
    """Download from a publisher or repository. Any failure just means "no PDF here"."""
    try:
        response = requests.get(
            url, headers={"User-Agent": USER_AGENT}, timeout=timeout
        )
        response.raise_for_status()
    except requests.RequestException:
        return None
    return response.content if _is_pdf(response.content) else None


def _fetch_cached_pdf(
    work_id: str, api_key: str | None, timeout: float
) -> bytes | None:
    """Download OpenAlex's cached copy. Requires an API key."""
    api_key = api_key or os.environ.get("OPENALEX_API_KEY")
    if not api_key:
        return None

    response = requests.get(
        f"{CONTENT_URL}/{work_id}.pdf",
        params={"api_key": api_key},
        headers={"User-Agent": USER_AGENT},
        timeout=timeout,
    )
    response.raise_for_status()
    return response.content if _is_pdf(response.content) else None
