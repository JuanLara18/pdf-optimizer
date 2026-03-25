# CLI Reference

```
pdf_compressor.py INPUT [OPTIONS]
```

`INPUT` is the path to a PDF file (positional). Alternatively pass `--input`/`-i`.

## Options

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `--output`, `-o` | path | `<input>_compressed.pdf` | Output file path |
| `--method`, `-m` | `auto` \| `simple` \| `raster` | `auto` | Compression strategy |
| `--quality`, `-q` | int (1–100) | `85` | JPEG quality for raster mode |
| `--min-reduction` | float (0–100) | `8.0` | Minimum % reduction to accept simple compression in auto mode |
| `--raster-dpi` | int (50–300) | `110` | Starting DPI for rasterization |
| `--large-threshold-mb` | int | `5` | File size (MB) above which auto may try raster |
| `--keep-text` | flag | off | Never rasterize; always preserve selectable text |
| `--target-reduction` | float (0–95) | none | Enable multi-pass raster to reach this % reduction |
| `--min-raster-dpi` | int (50–300) | `72` | DPI floor for multi-pass raster |
| `--dpi-step` | int (5–50) | `10` | DPI decrement per additional raster pass |
| `--aggressive` | flag | off | Require 50 % higher reduction to accept simple compression |
| `--simple-progress` | flag | off | Show a progress bar during simple compression |
| `--verbose`, `-v` | flag | off | Enable debug logging |

## Examples

```bash
# Simple structural compression only
poetry run python pdf_compressor.py report.pdf --method simple

# Raster at high quality
poetry run python pdf_compressor.py scan.pdf --method raster --quality 95

# Aggressive auto targeting 50 % reduction
poetry run python pdf_compressor.py big.pdf --aggressive --target-reduction 50

# Preserve text, verbose output
poetry run python pdf_compressor.py paper.pdf --keep-text --verbose
```

## Output

The compressed file is written next to the original with a `_compressed` suffix unless `--output` is specified. The original is never modified.

If every strategy would produce a file **larger** than the input (common with already-optimized or tiny PDFs), the output is replaced with a **byte-for-byte copy** of the original so the saved file never exceeds the source size.

## Exit codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | Compression failed (see stderr for details) |
