"""Command-line interface: search OpenAlex and download open-access PDFs."""

# import standard libraries
import argparse
import sys
from pathlib import Path

# import third-party libraries
import requests
from dotenv import find_dotenv, load_dotenv

# import custom modules
from paperfetch.download import download_pdf
from paperfetch.openalex import search_works


def build_parser() -> argparse.ArgumentParser:
    """Describe the command's arguments; argparse also builds --help from this."""
    parser = argparse.ArgumentParser(
        prog="paperfetch",
        description="Search OpenAlex and download legal open-access PDFs.",
    )
    parser.add_argument(  # positional argument for query
        "query", help='what to search for, e.g. "open access citation advantage"'
    )
    parser.add_argument(  # sets number of articles to query
        "-n",
        "--limit",
        type=int,
        default=10,
        help="number of results, 1-100 (default: 10)",
    )
    parser.add_argument(  # set output folder for pdfs
        "-o",
        "--out",
        type=Path,
        default=Path("papers"),
        help="folder to save PDFs in (default: ./papers)",
    )
    parser.add_argument(  # flag for skipping pdf download
        "--no-download",
        action="store_true",
        help="only list the results, don't download anything",
    )
    return parser


def main(argv: list[str] | None = None) -> int:  # when argv is None, argparse reads CLI
    """Run the command. Returns the exit code: 0 for success, 1 for failure."""
    args = build_parser().parse_args(argv)
    # Read OPENALEX_API_KEY from a .env file in the folder you run the command from.
    load_dotenv(find_dotenv(usecwd=True))

    try:
        papers = search_works(args.query, limit=args.limit)
    except (ValueError, requests.RequestException) as error:
        print(f"Search failed: {error}", file=sys.stderr)
        return 1  # expect 0 for success

    saved = 0
    for paper in papers:
        line = f"{paper.year or '----'}  {paper.title or '(untitled)'}"
        if args.no_download:
            print(line)
            continue

        try:
            path = download_pdf(paper, args.out)
        except requests.RequestException as error:
            print(f"Stopping, OpenAlex refused a download: {error}", file=sys.stderr)
            return 1

        if path:
            saved += 1
            print(f"[saved]   {line}")
        else:
            print(f"[no PDF]  {line}")

    if not args.no_download:
        print(f"\nSaved {saved} of {len(papers)} PDFs to {args.out}/")
    return 0
