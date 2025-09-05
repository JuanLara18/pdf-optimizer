# PDF Optimizer

Smart PDF compression tool with multiple strategies to reduce file size while preserving quality.

## Features

- **Simple compression**: Structural optimization (preserves text selectability)
- **Raster compression**: Page-to-image conversion (aggressive compression)
- **Auto mode**: Intelligent strategy selection based on file size and compression results
- **Web interface**: Easy-to-use Streamlit app
- **CLI support**: Command-line interface for automation

## Quick Start

### Installation

```bash
git clone https://github.com/JuanLara18/pdf-optimizer.git
cd pdf-optimizer
poetry install
```

### Web Interface

```bash
poetry run streamlit run streamlit_app.py
```

### Command Line

```bash
# Basic usage
poetry run python pdf_compressor.py input.pdf

# Advanced usage
poetry run python pdf_compressor.py input.pdf --method raster --quality 75 --aggressive
```

## Compression Methods

| Method | Description | Best For |
|--------|-------------|----------|
| `simple` | Structural optimization only | Text-heavy PDFs |
| `raster` | Convert pages to images | Scanned documents, image-heavy PDFs |
| `auto` | Smart selection (default) | General use |

## CLI Options

```bash
python pdf_compressor.py input.pdf [OPTIONS]

Options:
  --method {auto,simple,raster}  Compression strategy (default: auto)
  --quality INTEGER              JPEG quality 1-100 (default: 85)
  --aggressive                   Stricter compression requirements
  --keep-text                    Never rasterize, preserve selectable text
  --target-reduction FLOAT       Target compression percentage
  --verbose                      Detailed logging
```

## Examples

```bash
# Quick compression
poetry run python pdf_compressor.py document.pdf

# High quality raster compression
poetry run python pdf_compressor.py scan.pdf --method raster --quality 95

# Aggressive auto mode targeting 50% reduction
poetry run python pdf_compressor.py large_file.pdf --aggressive --target-reduction 50
```

## License

MIT