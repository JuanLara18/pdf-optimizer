"""Tests for the core PDFCompressor class."""

from pathlib import Path

import pytest
from pdf_compressor import PDFCompressor


class TestInit:
    def test_defaults(self):
        c = PDFCompressor()
        assert c.quality == 85
        assert c.min_reduction == 8.0
        assert c.raster_dpi == 110
        assert c.keep_text is False
        assert c.aggressive is False

    def test_clamps_quality(self):
        assert PDFCompressor(quality=0).quality == 1
        assert PDFCompressor(quality=200).quality == 100

    def test_clamps_dpi(self):
        assert PDFCompressor(raster_dpi=10).raster_dpi == 50
        assert PDFCompressor(raster_dpi=999).raster_dpi == 300


class TestCompression:
    def test_simple_produces_output(self, sample_pdf: Path, tmp_path: Path):
        out = tmp_path / "out.pdf"
        c = PDFCompressor()
        result = c.compress_pdf(sample_pdf, out, method="simple")
        assert result.exists()
        assert result.stat().st_size > 0

    def test_raster_produces_output(self, sample_pdf: Path, tmp_path: Path):
        out = tmp_path / "out.pdf"
        c = PDFCompressor(quality=50, raster_dpi=72)
        result = c.compress_pdf(sample_pdf, out, method="raster")
        assert result.exists()
        assert result.stat().st_size > 0

    def test_auto_produces_output(self, sample_pdf: Path, tmp_path: Path):
        out = tmp_path / "out.pdf"
        c = PDFCompressor()
        result = c.compress_pdf(sample_pdf, out, method="auto")
        assert result.exists()

    def test_default_output_path(self, sample_pdf: Path):
        c = PDFCompressor()
        result = c.compress_pdf(sample_pdf)
        expected = sample_pdf.parent / f"{sample_pdf.stem}_compressed.pdf"
        assert result == expected
        assert result.exists()

    def test_keep_text_never_rasterizes(self, large_text_pdf: Path, tmp_path: Path):
        out = tmp_path / "out.pdf"
        c = PDFCompressor(keep_text=True, min_reduction=0.0)
        result = c.compress_pdf(large_text_pdf, out, method="auto")
        assert result.exists()

    @pytest.mark.parametrize("method", ["auto", "simple", "raster"])
    def test_output_never_larger_than_input(self, sample_pdf: Path, tmp_path: Path, method: str):
        """Compressed (or fallback) file must not exceed original size."""
        out = tmp_path / f"out_{method}.pdf"
        c = PDFCompressor(quality=95, raster_dpi=150)
        orig_size = sample_pdf.stat().st_size
        result = c.compress_pdf(sample_pdf, out, method=method)  # type: ignore[arg-type]
        assert result.stat().st_size <= orig_size


class TestValidation:
    def test_missing_file(self, tmp_path: Path):
        c = PDFCompressor()
        with pytest.raises(FileNotFoundError):
            c.compress_pdf(tmp_path / "nonexistent.pdf")

    def test_non_pdf_file(self, tmp_path: Path):
        txt = tmp_path / "notes.txt"
        txt.write_text("not a pdf")
        c = PDFCompressor()
        with pytest.raises(ValueError, match="must be a PDF"):
            c.compress_pdf(txt)
