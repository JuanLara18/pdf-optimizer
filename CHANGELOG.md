# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/), and this project adheres to [Semantic Versioning](https://semver.org/).

## [0.1.0] - 2025-06-15

### Added

- Core PDF compression with simple (structural) and raster (page-to-image) strategies.
- Auto mode that picks the best strategy based on file size and reduction ratio.
- Multi-pass raster compression with configurable DPI floor and target reduction.
- `--keep-text` flag to prevent rasterization.
- `--aggressive` mode with stricter acceptance thresholds.
- Streamlit web UI with quick-compress and advanced-options modes.
- CLI with full control over quality, DPI, method, and output path.
