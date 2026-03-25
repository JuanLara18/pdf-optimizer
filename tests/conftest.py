import fitz
import pytest
from pathlib import Path


@pytest.fixture
def sample_pdf(tmp_path: Path) -> Path:
    """Create a minimal single-page PDF for testing."""
    path = tmp_path / "sample.pdf"
    doc = fitz.open()
    page = doc.new_page(width=612, height=792)
    page.insert_text((72, 72), "Hello, PDF Optimizer!", fontsize=14)
    doc.save(str(path))
    doc.close()
    return path


@pytest.fixture
def large_text_pdf(tmp_path: Path) -> Path:
    """Create a multi-page PDF with enough content to compress meaningfully."""
    path = tmp_path / "large.pdf"
    doc = fitz.open()
    for i in range(20):
        page = doc.new_page(width=612, height=792)
        for y in range(72, 750, 16):
            page.insert_text(
                (72, y), f"Page {i + 1} — line of filler text for compression testing.", fontsize=10
            )
    doc.save(str(path))
    doc.close()
    return path
