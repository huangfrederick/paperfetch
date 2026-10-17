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
    has_cached_pdf: bool  # check whether openalex's content api has a copy

    @property  # make work_id look like a field, computed from openalex_id every time.
    def work_id(self) -> str:
        """The short OpenAlex ID, e.g. "W3082255212"."""
        # split once from the right and keep the last piece of the ID.
        return self.openalex_id.rsplit("/", 1)[-1]
