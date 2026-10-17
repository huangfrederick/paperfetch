"""Data models used across paperfetch."""

from dataclasses import dataclass


@dataclass(frozen=True)
# Generates __init__ for the following fields, a readable print output, and a == comparison.
# frozen=True makes a Paper read only after creation.
class Paper:
    """One scholarly work, with just the fields paperfetch needs."""

    openalex_id: str
    title: str | None
    doi: str | None
    year: int | None
    authors: tuple[str, ...]
    is_oa: bool
    pdf_url: str | None
    landing_page_url: str | None
