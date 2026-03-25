#!/usr/bin/env python3
"""
PDF Compression Utility

A professional utility to compress PDF files while preserving content quality.
Supports multiple compression strategies optimized for different use cases.

COMPRESSION METHODS:
- simple: Structural optimization only (removes unused objects, compresses streams)
          Preserves all text, vectors, and image quality. Best for text-heavy PDFs.
- raster: Converts pages to optimized images (loses text selectability)
          Aggressive compression for scanned documents or image-heavy PDFs.
- auto:   Intelligent selection - tries simple first, falls back to raster for large files
          with insufficient compression (configurable thresholds).

BASIC USAGE:
    python pdf_compressor.py input.pdf
    python pdf_compressor.py input.pdf --method simple
    python pdf_compressor.py input.pdf --method raster --quality 75

ADVANCED USAGE:
    # Aggressive auto mode with higher compression requirements
    python pdf_compressor.py input.pdf --aggressive --target-reduction 40

    # Multi-pass raster compression targeting specific reduction
    python pdf_compressor.py input.pdf --method raster --target-reduction 50 --min-raster-dpi 80

    # Preserve text while being more aggressive about simple compression
    python pdf_compressor.py input.pdf --keep-text --aggressive --min-reduction 15

KEY PARAMETERS:
    --quality: JPEG quality for raster method (1-100, default: 85)
    --target-reduction: Target compression percentage for multi-pass optimization
    --aggressive: Require higher reduction to accept simple compression (50% stricter)
    --keep-text: Never rasterize, preserving searchable/selectable text
    --min-reduction: Minimum acceptable reduction percentage (default: 8.0%)
    --raster-dpi: Resolution for rasterization (50-300, default: 110)

OUTPUT:
    Creates a new file with '_compressed' suffix in the same directory.
    Original file is never modified.
"""

import argparse
import logging
import sys
import tempfile
from pathlib import Path
from typing import Optional, Literal

import fitz  # PyMuPDF
from tqdm import tqdm

# ===========================
# DEFAULT CONFIGURATION
# ===========================

# COMPRESSION SETTINGS
DEFAULT_JPEG_QUALITY = 85  # Range: 1-100 (higher = better quality, larger size)
DEFAULT_MIN_REDUCTION = 8.0  # Range: 0-100 (minimum % reduction to accept simple compression)
DEFAULT_RASTER_DPI = 110  # Range: 50-300 (DPI for rasterization, higher = better quality)
DEFAULT_LARGE_THRESHOLD_MB = 5  # Range: 1-1000 (MB threshold to consider PDF "large")

# MULTI-PASS RASTER SETTINGS
DEFAULT_MIN_RASTER_DPI = 72  # Range: 50-300 (minimum DPI floor for multi-pass)
DEFAULT_DPI_STEP = 10  # Range: 5-50 (DPI decrement per pass)
DEFAULT_TARGET_REDUCTION = None  # Range: 0-95 or None (target % reduction for multi-pass)

# BEHAVIOR FLAGS
DEFAULT_KEEP_TEXT = False  # Options: True/False (preserve text vs allow rasterization)
DEFAULT_AGGRESSIVE = False  # Options: True/False (stricter acceptance criteria)
DEFAULT_SIMPLE_PROGRESS = False  # Options: True/False (show progress bar for simple compression)
DEFAULT_METHOD = "auto"  # Options: "auto", "simple", "raster"

# COMPRESSION ALGORITHM SETTINGS
GARBAGE_COLLECTION_LEVEL = 4  # Range: 0-4 (PyMuPDF garbage collection intensity)
DEFLATE_COMPRESSION = True  # Options: True/False (enable stream compression)
CLEAN_UNUSED_OBJECTS = True  # Options: True/False (remove unused PDF objects)

# PROGRESS AND LOGGING
PROGRESS_LEAVE_BARS = False  # Options: True/False (keep progress bars after completion)
LOG_LEVEL_INFO = logging.INFO  # Options: DEBUG, INFO, WARNING, ERROR
LOG_FORMAT = "%(asctime)s - %(levelname)s - %(message)s"

# AGGRESSIVE MODE MULTIPLIER
AGGRESSIVE_THRESHOLD_MULTIPLIER = (
    1.5  # Range: 1.0-3.0 (multiplier for min_reduction in aggressive mode)
)

# VALIDATION LIMITS
MIN_QUALITY = 1  # Minimum JPEG quality allowed
MAX_QUALITY = 100  # Maximum JPEG quality allowed
MIN_DPI = 50  # Minimum DPI allowed
MAX_DPI = 300  # Maximum DPI allowed
MIN_REDUCTION_PERCENT = 0.0  # Minimum reduction percentage
MAX_REDUCTION_PERCENT = 100.0  # Maximum reduction percentage
MAX_TARGET_REDUCTION = 95.0  # Maximum target reduction percentage
MIN_DPI_STEP = 5  # Minimum DPI step allowed
MAX_DPI_STEP = 50  # Maximum DPI step allowed

# CONVERSION CONSTANTS
BYTES_PER_MB = 1024 * 1024  # Bytes to MB conversion factor
PDF_POINTS_PER_INCH = 72  # PDF coordinate system baseline DPI

# Configure logging
logging.basicConfig(level=LOG_LEVEL_INFO, format=LOG_FORMAT)
logger = logging.getLogger(__name__)


class PDFCompressor:
    """PDF compression utility using PyMuPDF.

    Supported strategies:
    - simple: structural optimization only (garbage collection, deflate).
      Preserves text and vectors.
    - raster: converts each page to an image (loses selectable text).
      Useful for heavy scanned/image PDFs.
    - auto (default): tries simple first; if reduction is below threshold
      and original size is large, may rasterize (unless keep_text is set).
    """

    def __init__(
        self,
        quality: int = DEFAULT_JPEG_QUALITY,
        min_reduction: float = DEFAULT_MIN_REDUCTION,
        raster_dpi: int = DEFAULT_RASTER_DPI,
        large_pdf_threshold_mb: int = DEFAULT_LARGE_THRESHOLD_MB,
        keep_text: bool = DEFAULT_KEEP_TEXT,
        target_reduction: Optional[float] = DEFAULT_TARGET_REDUCTION,
        min_raster_dpi: int = DEFAULT_MIN_RASTER_DPI,
        dpi_step: int = DEFAULT_DPI_STEP,
        aggressive: bool = DEFAULT_AGGRESSIVE,
        simple_progress: bool = DEFAULT_SIMPLE_PROGRESS,
    ):
        """Init.

        Args:
            quality: JPEG quality (1-100)
            min_reduction: Minimum % reduction required to accept simple compression in auto mode
            raster_dpi: Starting DPI used when rasterizing pages (raster method)
            large_pdf_threshold_mb: Size threshold (MB) to consider a PDF as "large" in auto mode
            keep_text: If True, never rasterize (preserve selectable/searchable text)
            target_reduction: Desired % reduction; multi-pass attempts down to this
            min_raster_dpi: Minimum DPI floor for multi-pass raster logic
            dpi_step: DPI decrement per additional raster pass
            aggressive: If True, raise threshold for accepting simple compression
            simple_progress: Show simulated progress during simple compression
        """
        self.quality = max(MIN_QUALITY, min(MAX_QUALITY, quality))
        self.min_reduction = max(
            MIN_REDUCTION_PERCENT, min(MAX_REDUCTION_PERCENT, float(min_reduction))
        )
        self.raster_dpi = max(MIN_DPI, min(MAX_DPI, raster_dpi))
        self.large_pdf_threshold = large_pdf_threshold_mb * BYTES_PER_MB
        self.keep_text = keep_text
        self.target_reduction = (
            None
            if target_reduction is None
            else max(MIN_REDUCTION_PERCENT, min(MAX_TARGET_REDUCTION, target_reduction))
        )
        self.min_raster_dpi = max(MIN_DPI, min(MAX_DPI, min_raster_dpi))
        self.dpi_step = max(MIN_DPI_STEP, min(MAX_DPI_STEP, dpi_step))
        self.aggressive = aggressive
        self.simple_progress = simple_progress

    def compress_pdf(
        self,
        input_path: Path,
        output_path: Optional[Path] = None,
        method: Literal["auto", "simple", "raster"] = "auto",
    ) -> Path:
        """Compress PDF.

        Args:
            input_path: Source PDF path
            output_path: Destination PDF path (auto-generated if None)
            method: Strategy: auto | simple | raster
        Returns:
            Path to compressed PDF
        """
        if not input_path.exists():
            raise FileNotFoundError(f"Input file not found: {input_path}")
        if input_path.suffix.lower() != ".pdf":
            raise ValueError(f"Input file must be a PDF: {input_path}")

        if output_path is None:
            output_path = input_path.parent / f"{input_path.stem}_compressed.pdf"

        logger.info("PDF Compression Start")
        logger.info(f"Input: {input_path}")
        logger.info(f"Output: {output_path}")
        logger.info(f"Method: {method}")

        original_size = input_path.stat().st_size
        logger.info(f"Original size: {self._format_size(original_size)}")

        # Fast path for raster-only request
        if method == "raster":
            return self._compress_with_images(input_path, output_path, original_size)

        # SIMPLE compression attempt (always executed in auto/simple)
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_simple = Path(tmpdir) / "simple.pdf"
            logger.info("Attempting simple structural compression ...")
            simple_ok = self._try_simple_compression(input_path, tmp_simple) is not None
            if not simple_ok or not tmp_simple.exists():
                logger.warning("Simple compression failed; fallback decision ...")
                if method == "simple" or self.keep_text:
                    raise RuntimeError(
                        "Simple compression failed and rasterization disabled / not requested"
                    )
                logger.info("Falling back to raster compression")
                return self._compress_with_images(input_path, output_path, original_size)

            simple_size = tmp_simple.stat().st_size
            reduction = (1 - simple_size / original_size) * 100
            logger.info(
                "Simple compression result: %s (%.1f%% reduction)",
                self._format_size(simple_size),
                reduction,
            )

            # If user explicitly wants simple, finalize
            if method == "simple":
                logger.info("Method 'simple' requested; saving result")
                self._finalize_output(tmp_simple, output_path)
                return output_path

            # AUTO strategy decision
            effective_min = self.min_reduction * (
                AGGRESSIVE_THRESHOLD_MULTIPLIER if self.aggressive else 1.0
            )
            if reduction >= effective_min:
                logger.info(
                    f"Reduction >= threshold ({effective_min:.1f}%). Using simple result."
                    + (" (aggressive mode)" if self.aggressive else "")
                )
                self._finalize_output(tmp_simple, output_path)
                return output_path

            if self.keep_text:
                logger.info("keep_text=True prevents rasterization. Using simple result.")
                self._finalize_output(tmp_simple, output_path)
                return output_path

            if original_size < self.large_pdf_threshold:
                logger.info(
                    "File below large threshold; skipping rasterization. Using simple result."
                )
                self._finalize_output(tmp_simple, output_path)
                return output_path

            logger.info("Simple compression insufficient for large PDF. Trying raster ...")
            last_simple_reduction = reduction

        # Outside tempdir scope now – perform raster
        return self._multi_pass_raster(
            input_path,
            output_path,
            original_size,
            baseline_simple_reduction=locals().get("last_simple_reduction", 0.0),
        )

    def _try_simple_compression(self, input_path: Path, output_path: Path) -> Optional[Path]:
        """Try simple PDF compression without re-rendering."""
        try:
            doc = fitz.open(str(input_path))
            if self.simple_progress:
                pages = len(doc)
                pbar = tqdm(total=pages, desc="Simple optimize", leave=False)
                for _ in range(pages):
                    pbar.update(1)
                pbar.close()
            doc.save(
                str(output_path),
                garbage=GARBAGE_COLLECTION_LEVEL,
                deflate=DEFLATE_COMPRESSION,
                clean=CLEAN_UNUSED_OBJECTS,
            )
            doc.close()
            return output_path
        except Exception as e:
            logger.debug(f"Simple compression failed: {e}")
            return None

    def _compress_with_images(
        self,
        input_path: Path,
        output_path: Path,
        original_size: int,
        dpi: Optional[int] = None,
        pass_num: int = 1,
    ) -> Path:
        """Compress PDF by rasterizing each page (destructive: loses selectable/searchable text).

        Uses configured DPI (raster_dpi). Higher DPI => better quality & larger size.
        """
        doc = fitz.open(str(input_path))
        compressed_doc = fitz.open()
        chosen_dpi = dpi or self.raster_dpi
        # Scale factor = dpi / 72 (PDF points baseline)
        scale = chosen_dpi / PDF_POINTS_PER_INCH
        mat = fitz.Matrix(scale, scale)
        desc = (
            f"Rasterizing (pass {pass_num}, {chosen_dpi} DPI)"
            if pass_num > 1
            else f"Rasterizing pages ({chosen_dpi} DPI)"
        )
        for page_num in tqdm(range(len(doc)), desc=desc):
            page = doc[page_num]
            pix = page.get_pixmap(matrix=mat)  # type: ignore[attr-defined]
            new_page = compressed_doc.new_page(  # type: ignore[attr-defined]
                width=page.rect.width, height=page.rect.height
            )
            img_data = pix.tobytes("jpeg", jpg_quality=self.quality)
            new_page.insert_image(  # type: ignore[attr-defined]
                page.rect, stream=img_data, keep_proportion=True
            )
            pix = None

        compressed_doc.save(
            str(output_path),
            garbage=GARBAGE_COLLECTION_LEVEL,
            deflate=DEFLATE_COMPRESSION,
            clean=CLEAN_UNUSED_OBJECTS,
        )
        doc.close()
        compressed_doc.close()
        compressed_size = output_path.stat().st_size
        compression_ratio = (1 - compressed_size / original_size) * 100
        logger.info(f"Raster result size: {self._format_size(compressed_size)}")
        logger.info(f"Raster reduction: {compression_ratio:.1f}%")
        if compression_ratio < 0:
            logger.warning("Rasterization increased size (document likely already optimized).")
        return output_path

    def _multi_pass_raster(
        self,
        input_path: Path,
        output_path: Path,
        original_size: int,
        baseline_simple_reduction: float = 0.0,
    ) -> Path:
        """Perform single or multi-pass rasterization until target reduction or DPI floor."""
        current_path = self._compress_with_images(
            input_path, output_path, original_size, dpi=self.raster_dpi, pass_num=1
        )
        current_size = current_path.stat().st_size
        current_reduction = (1 - current_size / original_size) * 100
        if current_reduction < baseline_simple_reduction:
            logger.warning("Raster pass smaller than simple; reverting.")
            self._try_simple_compression(input_path, output_path)
            return output_path
        if not self.target_reduction or current_reduction >= self.target_reduction:
            logger.info("Raster target satisfied (or no target set).")
            return current_path
        dpi = self.raster_dpi
        pass_num = 1
        while (
            current_reduction < self.target_reduction and dpi - self.dpi_step >= self.min_raster_dpi
        ):
            dpi -= self.dpi_step
            pass_num += 1
            logger.info(
                "Raster pass %d at %d DPI (target %.1f%%, current %.1f%%)",
                pass_num,
                dpi,
                self.target_reduction,
                current_reduction,
            )
            self._compress_with_images(
                input_path, output_path, original_size, dpi=dpi, pass_num=pass_num
            )
            current_size = output_path.stat().st_size
            current_reduction = (1 - current_size / original_size) * 100
            logger.info(f"New reduction after pass {pass_num}: {current_reduction:.1f}%")
        if current_reduction < self.target_reduction:
            logger.info(
                "Stopped at DPI %d. Final %.1f%% (target %.1f%%)",
                dpi,
                current_reduction,
                self.target_reduction,
            )
        else:
            logger.info(
                "Achieved %.1f%% reduction (target %.1f%%) at %d DPI",
                current_reduction,
                self.target_reduction,
                dpi,
            )
        return output_path

    @staticmethod
    def _finalize_output(temp_file: Path, destination: Path):
        """Move / copy temp result to final destination (overwrite if exists)."""
        if destination.exists():
            destination.unlink()
        temp_file.replace(destination)

    _format_size = staticmethod(lambda b: format_size(b))


def format_size(size_bytes: int) -> str:
    """Format file size in human-readable format."""
    size = float(size_bytes)
    for unit in ["B", "KB", "MB", "GB"]:
        if size < 1024.0:
            return f"{size:.1f} {unit}"
        size /= 1024.0
    return f"{size:.1f} TB"


def main():
    """Main entry point for the PDF compressor."""
    parser = argparse.ArgumentParser(description="Compress PDF files while preserving quality")

    parser.add_argument("input", nargs="?", type=Path, help="Input PDF file path")

    parser.add_argument(
        "--input",
        "-i",
        type=Path,
        dest="input_file",
        help="Input PDF file path (alternative to positional argument)",
    )

    parser.add_argument(
        "--output",
        "-o",
        type=Path,
        help="Output PDF file path (optional, defaults to input_file_compressed.pdf)",
    )

    parser.add_argument(
        "--quality",
        "-q",
        type=int,
        default=DEFAULT_JPEG_QUALITY,
        help="JPEG quality for image compression (1-100, default: 85)",
    )
    parser.add_argument(
        "--method",
        "-m",
        choices=["auto", "simple", "raster"],
        default=DEFAULT_METHOD,
        help="Compression method: auto (default), simple, raster",
    )
    parser.add_argument(
        "--min-reduction",
        type=float,
        default=DEFAULT_MIN_REDUCTION,
        help="Minimum reduction percentage to accept simple compression in auto (default: 8.0)",
    )
    parser.add_argument(
        "--raster-dpi",
        type=int,
        default=DEFAULT_RASTER_DPI,
        help="DPI used when rasterizing pages (50-300, default: 110)",
    )
    parser.add_argument(
        "--large-threshold-mb",
        type=int,
        default=DEFAULT_LARGE_THRESHOLD_MB,
        help="File size (MB) threshold to consider rasterization in auto (default: 5)",
    )
    parser.add_argument(
        "--keep-text",
        action="store_true",
        help="Never rasterize (preserve selectable text even if compression is low)",
    )
    parser.add_argument(
        "--target-reduction",
        type=float,
        default=DEFAULT_TARGET_REDUCTION,
        help="Target reduction percentage; enables multi-pass raster down to this goal",
    )
    parser.add_argument(
        "--min-raster-dpi",
        type=int,
        default=DEFAULT_MIN_RASTER_DPI,
        help="Minimum DPI floor for multi-pass raster (default: 72)",
    )
    parser.add_argument(
        "--dpi-step",
        type=int,
        default=DEFAULT_DPI_STEP,
        help="DPI decrement per additional raster pass (5-50, default: 10)",
    )
    parser.add_argument(
        "--aggressive",
        action="store_true",
        help="Aggressive mode: require 50 percent higher reduction to accept simple compression",
    )
    parser.add_argument(
        "--simple-progress",
        action="store_true",
        help="Show simulated progress bar during simple compression",
    )

    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose logging")

    args = parser.parse_args()

    # Set logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Determine input file
    input_file = args.input or args.input_file
    if not input_file:
        parser.error("Input PDF file is required")

    try:
        # Create compressor and compress the PDF
        compressor = PDFCompressor(
            quality=args.quality,
            min_reduction=args.min_reduction,
            raster_dpi=args.raster_dpi,
            large_pdf_threshold_mb=args.large_threshold_mb,
            keep_text=args.keep_text,
            target_reduction=args.target_reduction,
            min_raster_dpi=args.min_raster_dpi,
            dpi_step=args.dpi_step,
            aggressive=args.aggressive,
            simple_progress=args.simple_progress,
        )
        output_file = compressor.compress_pdf(input_file, args.output, method=args.method)

        print("\nCompression completed successfully!")
        print(f"Output file: {output_file}")

    except Exception as e:
        logger.error(f"Compression failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
