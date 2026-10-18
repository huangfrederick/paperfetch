# paperfetch

[![CI](https://github.com/huangfrederick/paperfetch/actions/workflows/ci.yml/badge.svg)](https://github.com/huangfrederick/paperfetch/actions/workflows/ci.yml)

Search for scholarly papers and download legal open-access PDFs, using the
[OpenAlex](https://openalex.org) API. 

> **New Users to GitHub/IDEs:** Follow the [step-by-step getting started guide](docs/GETTING_STARTED.md).
> It walks you through installing and using paperfetch
> in a notebook on Mac or Windows.

```console
$ paperfetch "open access citation advantage" --limit 5 --out papers
[saved]   2010  The Open Access citation advantage: Studies and results to date
[no PDF]  2010  Open Access Citation Advantage: An Annotated Bibliography.
[saved]   2021  Is the open access citation advantage real? A systematic review ...
[saved]   2018  The Open Access Citation Advantage: Does It Exist and What Does It Mean for Libraries?
[saved]   2022  The influence of funding on the Open Access citation advantage

Saved 4 of 5 PDFs to papers/
```

## Why

Programmatic access to subscription databases depends on your institution: Elsevier's
Scopus API, for example, are governed by text/data mining agreements,
negotiated with each institution. Finding the free, legal copy of a paper by hand
often means clicking through publisher pages, repositories and preprint servers.

OpenAlex already indexes where open-access copies live, and it's free for anyone.
paperfetch turns that into a single command, and it only downloads copies that
OpenAlex marks as open access.

## Features

- **Open-access-only search** over 250M+ works in OpenAlex, best matches first
- **Two-step download:** tries the free publisher or repository link first, then
  falls back to OpenAlex's cached copy
- **Verified files:** saves a file only if it really is a PDF, never a login or
  error page
- **Re-runs are free:** already-downloaded papers are skipped
- **Usable via three ways:** a beginner-friendly Jupyter notebook, the terminal, or from Python

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

Searching should work without a key, but you share a small daily budget with
everyone on your network. **Cached PDFs/downloading from what is indexed by OpenAlex requires a key.** This is only in case a publisher link fails.

## Usage

### Notebook

```bash
pixi run notebook
```

Opens `notebooks/quickstart.ipynb` in JupyterLab: edit one
cell with your search, run the cells, and get a results table, the PDFs and an
index.csv listing which file is which paper.

### Command line

```bash
paperfetch "open access citation advantage"           # search + download 10 papers into ./papers
paperfetch "numpy" --limit 25 --out data/pdfs         # more results, custom folder
paperfetch "numpy" --no-download                      # only list the results
paperfetch --help
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

## How it works

1. **Search:** `GET /works?search=...&filter=is_oa:true` on the OpenAlex API,
   requesting only the fields paperfetch uses.
2. **Parse:** each raw record becomes a small, read-only `Paper` dataclass.
3. **Download**, for each paper:
   1. Skip it if `papers/<OpenAlex ID>.pdf` already exists.
   2. Try the publisher or repository `pdf_url` (free).
   3. If that fails and OpenAlex has a cached copy, download it from the
      OpenAlex content API (uses your key's budget).
   4. Keep the file only if it starts with `%PDF`.

## Limitations

- **Not every open-access paper has a PDF link.** Some are only available as a
  web page. paperfetch reports these as `[no PDF]`; the paper's
  `landing_page_url` still points to the free version.
- **Daily budget:** a free OpenAlex key includes $1/day of usage. Searches cost
  a fraction of a cent, cached PDFs cost $0.01 each (about 100 per day).
  Publisher links don't count against it.
- **Duplicates:** a preprint and its published version can appear as two results.
- **Copyright:** downloaded PDFs keep their original license. Check
  `best_oa_location.license` in OpenAlex before redistributing them.

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
pixi run format           # ruff 
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

If paperfetch helps your research, please cite it. GitHub's **Cite this repository**
button (right-hand sidebar) gives APA and BibTeX, generated from
[`CITATION.cff`](CITATION.cff). Please cite OpenAlex as well (see Acknowledgments).

## Contact

Please file issues on the repository.

## License

[MIT](LICENSE)
