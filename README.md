# PDF Optimizer

[![CI](https://github.com/JuanLara18/pdf-optimizer/actions/workflows/ci.yml/badge.svg)](https://github.com/JuanLara18/pdf-optimizer/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.9+](https://img.shields.io/badge/python-3.9%2B-blue.svg)](https://www.python.org/downloads/)

Smart PDF compression via CLI and web UI — structural optimization or aggressive raster compression, powered by [PyMuPDF](https://pymupdf.readthedocs.io/).

## Features

- **Simple mode** — structural optimization that preserves text selectability.
- **Raster mode** — page-to-image conversion for aggressive size reduction.
- **Auto mode** (default) — picks the best strategy based on file size and compression results.
- **Streamlit web UI** — drag-and-drop interface with live progress and download.
- **CLI** — scriptable, with fine-grained control over quality, DPI, and multi-pass compression.

> All processing happens locally — your files are never uploaded to external services.

## Quick start

### Install

```bash
git clone https://github.com/JuanLara18/pdf-optimizer.git
cd pdf-optimizer
poetry install
```

### Web UI

```bash
poetry run streamlit run streamlit_app.py
```

### CLI

```bash
# Default auto mode
poetry run python pdf_compressor.py document.pdf

# Raster mode, custom quality
poetry run python pdf_compressor.py scan.pdf --method raster --quality 75

# Aggressive auto with target reduction
poetry run python pdf_compressor.py large.pdf --aggressive --target-reduction 50
```

Run `poetry run python pdf_compressor.py --help` for the full option list, or see the [CLI reference](docs/cli.md).

## Documentation

| Document | Description |
|----------|-------------|
| [User guide](docs/user-guide.md) | Compression modes, trade-offs, and tips |
| [CLI reference](docs/cli.md) | Every flag and option explained |
| [Development](docs/development.md) | Repo structure, running tests and linters, releasing |
| [Changelog](CHANGELOG.md) | Version history |
| [Contributing](CONTRIBUTING.md) | How to report bugs and submit patches |

## License

[MIT](LICENSE) — Copyright (c) 2025 Juan Lara
