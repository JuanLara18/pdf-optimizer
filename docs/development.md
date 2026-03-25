# Development

## Prerequisites

- Python 3.9+
- [Poetry](https://python-poetry.org/) for dependency management

## Setup

```bash
git clone https://github.com/JuanLara18/pdf-optimizer.git
cd pdf-optimizer
poetry install
```

## Repository structure

```
pdf-optimizer/
├── pdf_compressor.py      # Core compression logic + CLI entry point
├── streamlit_app.py       # Streamlit web UI
├── pyproject.toml         # Project metadata, dependencies, tool config
├── poetry.lock            # Locked dependency versions
├── LICENSE
├── README.md
├── CHANGELOG.md
├── CONTRIBUTING.md
├── docs/
│   ├── user-guide.md      # Compression modes, trade-offs, tips
│   ├── cli.md             # Full CLI option reference
│   ├── development.md     # This file
│   └── assets/            # Screenshots and diagrams
└── .github/
    └── workflows/
        └── ci.yml         # Lint + test pipeline
```

## Running linters

```bash
poetry run black --check .
poetry run flake8
```

To auto-format:

```bash
poetry run black .
```

## Running tests

```bash
poetry run pytest
```

Tests live in the `tests/` directory and use `pytest`. CI runs them on every push and pull request.

## Releasing

1. Update `version` in `pyproject.toml`.
2. Add an entry in `CHANGELOG.md`.
3. Commit, tag (`git tag v0.1.0`), and push (`git push --tags`).
