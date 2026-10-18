# paperfetch

[![CI](https://github.com/huangfrederick/paperfetch/actions/workflows/ci.yml/badge.svg)](https://github.com/huangfrederick/paperfetch/actions/workflows/ci.yml) [![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.23459102.svg)](https://doi.org/10.5281/zenodo.23459102)


Search for scholarly papers and download legal open-access PDFs, using the
[OpenAlex](https://openalex.org) API. 

> **For Users New to GitHub/IDEs:** Follow the [step-by-step getting started guide](docs/GETTING_STARTED.md).
> It walks you through installing and using paperfetch
> in a notebook on Mac or Windows.

```console
$ paperfetch "open access citation advantage" --limit 5 --out papers
[saved]   2010  The Open Access citation advantage: Studies and results to date
[saved]   2021  Is the open access citation advantage real? A systematic review of the citation of open access and subscription-based articles
[saved]   2022  The influence of funding on the Open Access citation advantage
[saved]   2018  The Open Access Citation Advantage: Does It Exist and What Does It Mean for Libraries?
[saved]   2019  Revisiting the Open Access Citation Advantage for Legal Scholarship

Saved 4 of 5 PDFs to papers/
```

## Why

Programmatic access to subscription-based publication databases largely depends on your university/institution's contracts with academic publishers. Elsevier's
Scopus API, for example, is governed by text/data mining agreements that do not always provide permissions to scrape data using their services. Finding the free, legal copy of a paper by hand
often means clicking through publisher pages, repositories and preprint servers.

OpenAlex already indexes where open-access copies live, and it's free for anyone.
paperfetch turns that into a single command, and it only downloads copies that
OpenAlex marks as open access.

## Features

- **Open-access-only search** over 250M+ works in OpenAlex, best matches first
- **Two-step download:** tries the free publisher or repository link first, then
  falls back to OpenAlex's cached copy
- **Verified files:** saves a file only if it really is a PDF and will discard any HTML/login/error pages
- **Re-runs are free:** already-downloaded papers are skipped
- **Usable via three ways:** a beginner-friendly Jupyter notebook, the terminal, or from Python
- **Scopus-style searching:** title/abstracts, year ranges, exlude reviews, English only, sorting, and any extra OpenAlex filters

## Installation

Requires Python 3.12+.

```bash
pip install git+https://github.com/huangfrederick/paperfetch.git
```

### API key (free, recommended)

Get a free key at <https://openalex.org/settings/api>, then either set it in your
shell or put it in a `.env` file in the folder you run paperfetch from:

```bash
OPENALEX_API_KEY=your-key-here
```

Search works without a key, but you share a small daily budget with everyone on your
network. **A key is needed for OpenAlex's cached PDFs**, which paperfetch uses only when
a publisher's PDF link fails.

## Usage

### Notebook

```bash
pixi run notebook
```

Opens `notebooks/quickstart.ipynb` in JupyterLab (viewable in browser): edit one
cell with your search, run the cells, and get a results table, the PDFs and an
index.csv listing which file is which paper.

### Command line

```bash
paperfetch "open access citation advantage"           # search titles + abstracts, download 10 PDFs into ./papers
paperfetch "numpy" --limit 25 --out data/pdfs         # more results, custom folder
paperfetch "scikit-learn" --no-download                      # only list the results
paperfetch '"dental composite" AND ("in vitro" OR experimental)' \
    --from-year 2010 --exclude-reviews --english-only # a Scopus-style query
paperfetch '"dental composite"' --filter 'cited_by_count:>50' --sort most_cited
paperfetch --help                                     # all options
```

Exit code is `0` on success and `1` if the search or OpenAlex fails, so it works in scripts.

### Python

```python
from paperfetch.download import download_pdf
from paperfetch.openalex import search_works

for paper in search_works("open access citation advantage", limit=5):
    path = download_pdf(paper, "papers")
    print(paper.year, paper.title, "->", path)
```

Each result is a `Paper` with `title`, `doi`, `year`, `authors`, `pdf_url`,
`landing_page_url` and more. See [`models.py`](src/paperfetch/models.py).

## Search options

By default paperfetch searches **titles and abstracts**, returns only **open-access,
non-retracted papers that have a PDF link**, and sorts by relevance.

| Command line | Python / notebook | What it does |
|---|---|---|
| `--search-in title\|abstract\|title_and_abstract\|all` | `search_in=` / `SEARCH_IN` | Where to match the query. `all` also searches full text (broader, noisier). |
| `--from-year 2010`, `--to-year 2020` | `from_year=`, `to_year=` | Publication year range; either end can be left open. |
| `--exclude-reviews` | `exclude_reviews=True` | Leave out review articles. |
| `--english-only` | `english_only=True` | Only papers in English. |
| `--include-no-pdf` | `pdf_only=False` | Also list open-access papers that can only be read online. |
| `--sort relevance\|newest\|most_cited` | `sort=` / `SORT_BY` | Result order. |
| `--filter '...'` | `extra_filter=` / `EXTRA_FILTERS` | Any extra [OpenAlex filter](https://docs.openalex.org/api/filtering), e.g. `cited_by_count:>10` or `institutions.country_code:us`. |

**Query syntax:** use `"double quotes"` for exact phrases, **AND / OR / NOT** in
capitals, and brackets for grouping. Don't use commas: OpenAlex uses them to
separate filters, so paperfetch rejects them with an error.

**Coming from Scopus?**

| Scopus | paperfetch |
|---|---|
| `TITLE-ABS-KEY("dental composite")` | `'"dental composite"'` (the default `--search-in`) |
| `TITLE(...)` / `ABS(...)` | `--search-in title` / `--search-in abstract` |
| `PUBYEAR > 2009` | `--from-year 2010` |
| `AND NOT DOCTYPE(re)` | `--exclude-reviews` |
| `LANGUAGE(english)` | `--english-only` |

In Python:

```python
papers = search_works(
    '"dental composite" AND ("in vitro" OR experimental)',
    limit=50,
    from_year=2010,
    exclude_reviews=True,
    english_only=True,
)
```

## How it works

1. **Search:** one request to the OpenAlex `/works` API. Your query and options become
   a single filter (e.g. `title_and_abstract.search:...,publication_year:2010-,
   has_pdf_url:true`), and only the fields paperfetch uses are requested.
2. **Parse:** each raw record becomes a small, read-only `Paper` dataclass.
3. **Download**, for each paper:
   1. Skip it if `papers/<OpenAlex ID>.pdf` already exists.
   2. Try the publisher or repository `pdf_url` (free).
   3. If that fails and OpenAlex has a cached copy, download it from the
      OpenAlex content API (uses your key's budget).
   4. Keep the file only if it starts with `%PDF`.

## Limitations

- **Not every open-access paper has a PDF link.** By default paperfetch only returns
  papers that do; `--include-no-pdf` also lists papers you can only read online. A
  listed PDF link can still fail (some websites block downloads); those show as
  `[no PDF]`.
- **No study-design filter.** Neither OpenAlex nor Scopus labels papers as
  "experimental" or "clinical trial". Add design terms to your query (e.g.
  `"in vitro"`, `experimental`) and screen the results yourself.
- **Review detection is approximate.** OpenAlex labels some reviews as articles, so
  `--exclude-reviews` also drops papers with "review" in the title, including the
  occasional non-review such as a study about peer review.
- **Daily budget:** a free OpenAlex key includes $1/day of usage. Searches cost
  a fraction of a cent, cached PDFs cost $0.01 each (about 100 per day).
  Publisher links don't count against it.
- **Duplicates:** a preprint and its published version can appear as two results.
- **Copyright:** downloaded PDFs keep their original license. Check
  `best_oa_location.license` in OpenAlex before redistributing them.

## Uninstalling

- **Installed with pip:** `pip uninstall paperfetch`
- **Downloaded or cloned folder (pixi):** delete the folder; its environment lives in
  `.pixi/` inside it. To also free pixi's shared download cache, run
  `pixi clean cache` *before* removing pixi itself
  ([pixi uninstall docs](https://pixi.sh/latest/installation/)).
- **Your data:** downloaded PDFs are in `papers/` (or your `--out` folder), so move them
  out before deleting the folder. A saved API key is in `.env`.

Step-by-step instructions for Mac and Windows are in the
[getting started guide](docs/GETTING_STARTED.md#uninstalling-paperfetch).

## Development

The project uses [pixi](https://pixi.sh) for a reproducible environment
(Python, ruff, pytest). See `pixi.lock` and `pixi.toml`.

```bash
git clone https://github.com/huangfrederick/paperfetch.git
cd paperfetch
pixi install
cp .env.example .env      # then add your key

pixi run test             # pytest, no network needed
pixi run lint             # ruff check
pixi run format           # ruff format
pixi run notebook         # JupyterLab with quickstart notebook (if not using an existing IDE)
```

All tests replace the network with dummies, so they run offline in well under a
second. GitHub Actions runs lint, a format check, the tests and a CLI smoke test
on every push.

```
src/paperfetch/
├── openalex.py   # OpenAlex API: get_work, search_works, parse_work
├── download.py   # download_pdf: publisher link, then OpenAlex fallback
├── models.py     # Paper dataclass
└── cli.py        # the paperfetch command
tests/            # one test file per module
notebooks/        # quickstart.ipynb (a notebook integrating the entire process)
docs/             # GETTING_STARTED.md, new github/IDE user guide.
```

## Acknowledgments

Paper data comes from [OpenAlex](https://openalex.org), a fully open index of
scholarly works (Priem, Piwowar & Orr, 2022,
[arXiv:2205.01833](https://arxiv.org/abs/2205.01833)).

## Citing
If paperfetch helps your research, please kindly cite it either as shown below or through GitHub's **Cite this repository** button on the right-hand sidebar.

> Huang F. (2026). paperfetch (version 0.1.0). DOI: 10.5281/zenodo.23459102 URL: https://github.com/huangfrederick/paperfetch

## Contact

Questions, bugs or ideas: [open an issue](https://github.com/huangfrederick/paperfetch/issues).

## License

[MIT](LICENSE)
