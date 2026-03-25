# User Guide

PDF Optimizer reduces PDF file size using two complementary strategies. This guide explains when and how to use each one.

## Compression modes

### Simple (structural)

Removes unused objects, compresses internal streams, and runs garbage collection on the PDF structure. Text, vectors, and images stay untouched — the file remains fully searchable and selectable.

**Best for:** text-heavy documents, reports, and slides.

### Raster (page-to-image)

Renders every page as a JPEG image at a configurable DPI. This is destructive — selectable text is lost — but it can shrink image-heavy or scanned PDFs dramatically.

**Best for:** scanned documents, image-heavy PDFs, or cases where text selectability is not needed.

### Auto (default)

Tries simple compression first. If the reduction is below the acceptance threshold and the file is large enough, it falls back to raster automatically. When `--keep-text` is set, auto never rasterizes.

## Trade-offs at a glance

| Concern | Simple | Raster |
|---------|--------|--------|
| Text selectability | Preserved | Lost |
| Typical reduction | 5–30 % | 30–80 % |
| Speed | Fast | Slower (renders every page) |
| Visual fidelity | Identical | Depends on DPI and JPEG quality |

## Tips

- Start with the default `auto` mode — it handles most cases well.
- Use `--keep-text` if the PDF will be searched or copy-pasted later.
- For scanned documents, `--method raster --quality 80` is a good starting point.
- If the output is still too large, try `--target-reduction 50` to enable multi-pass rasterization at progressively lower DPI.
- The original file is never modified. The compressed copy is saved with a `_compressed` suffix by default.

## Web UI

Launch the Streamlit app:

```bash
poetry run streamlit run streamlit_app.py
```

1. Upload a PDF.
2. Choose **Quick Compress** (auto mode) or switch to **Advanced Options** for full control.
3. Click **Compress PDF** and download the result.

All processing runs locally in a temporary directory; uploaded files are deleted after compression.
