import streamlit as st
import tempfile
import os
from pathlib import Path
import time
from typing import Literal, Optional
from pdf_compressor import PDFCompressor, format_size

# Page config
st.set_page_config(page_title="PDF Optimizer", page_icon="📄", layout="centered")


def main():
    st.title("📄 PDF Optimizer")
    st.write("Compress PDF files while preserving quality")

    # File upload
    uploaded_file = st.file_uploader(
        "Choose a PDF file", type="pdf", help="Upload a PDF file to compress"
    )

    if uploaded_file is not None:
        # Display file info
        file_size = len(uploaded_file.getvalue())
        st.info(f"📁 **{uploaded_file.name}** ({format_size(file_size)})")

        # Mode selection
        mode = st.radio(
            "Select mode:", ["🚀 Quick Compress", "⚙️ Advanced Options"], horizontal=True
        )

        if mode == "🚀 Quick Compress":
            # Simple mode
            st.divider()

            if st.button("Compress PDF", type="primary", use_container_width=True):
                compress_pdf(uploaded_file, method="auto")  # type: ignore

        else:
            # Advanced mode
            st.divider()

            col1, col2 = st.columns(2)

            with col1:
                method = st.selectbox(
                    "Compression method",
                    ["auto", "simple", "raster"],
                    help=(
                        "• **auto**: Smart selection\n"
                        "• **simple**: Preserve text\n"
                        "• **raster**: Aggressive compression"
                    ),
                )
                # Type assertion for Pylance
                method = method  # type: ignore

                quality = st.slider(
                    "JPEG Quality",
                    min_value=1,
                    max_value=100,
                    value=85,
                    help="Higher = better quality, larger size",
                )

            with col2:
                aggressive = st.checkbox(
                    "Aggressive mode", help="Require higher compression ratios"
                )

                keep_text = st.checkbox(
                    "Preserve text", help="Never rasterize pages (keeps searchable text)"
                )

            # Advanced options in expander
            with st.expander("🔧 Expert Settings"):
                col3, col4 = st.columns(2)

                with col3:
                    min_reduction = st.number_input(
                        "Min reduction %",
                        min_value=0.0,
                        max_value=100.0,
                        value=8.0,
                        step=1.0,
                        help="Minimum acceptable compression percentage",
                    )

                    raster_dpi = st.number_input(
                        "Raster DPI",
                        min_value=50,
                        max_value=300,
                        value=110,
                        step=10,
                        help="Resolution for page rasterization",
                    )

                with col4:
                    target_reduction = st.number_input(
                        "Target reduction %",
                        min_value=0.0,
                        max_value=95.0,
                        value=0.0,
                        step=5.0,
                        help="Target compression (0 = no target)",
                    )

                    large_threshold = st.number_input(
                        "Large file threshold (MB)",
                        min_value=1,
                        max_value=100,
                        value=5,
                        help="Size threshold for auto rasterization",
                    )

            st.divider()

            if st.button("Compress PDF", type="primary", use_container_width=True):
                compress_pdf(
                    uploaded_file,
                    method=method,  # type: ignore
                    quality=quality,
                    aggressive=aggressive,
                    keep_text=keep_text,
                    min_reduction=min_reduction,
                    raster_dpi=raster_dpi,
                    target_reduction=target_reduction if target_reduction > 0 else None,
                    large_threshold=large_threshold,
                )


def compress_pdf(uploaded_file, method: Literal["auto", "simple", "raster"] = "auto", **kwargs):
    """Compress PDF with progress indicators."""

    # Create progress indicators
    progress_bar = st.progress(0)
    status_text = st.empty()

    # Initialize variables to avoid unbound errors
    tmp_input_path: Optional[Path] = None
    compressed_path: Optional[Path] = None

    try:
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_input:
            tmp_input.write(uploaded_file.getvalue())
            tmp_input_path = Path(tmp_input.name)

        progress_bar.progress(20)
        status_text.text("🔧 Initializing compressor...")

        # Create compressor with options
        compressor = PDFCompressor(
            quality=kwargs.get("quality", 85),
            min_reduction=kwargs.get("min_reduction", 8.0),
            raster_dpi=kwargs.get("raster_dpi", 110),
            large_pdf_threshold_mb=kwargs.get("large_threshold", 5),
            keep_text=kwargs.get("keep_text", False),
            target_reduction=kwargs.get("target_reduction"),
            aggressive=kwargs.get("aggressive", False),
            simple_progress=False,
        )

        progress_bar.progress(40)
        status_text.text("📄 Compressing PDF...")

        # Compress PDF
        with tempfile.NamedTemporaryFile(delete=False, suffix="_compressed.pdf") as tmp_output:
            tmp_output_path = Path(tmp_output.name)

        compressed_path = compressor.compress_pdf(tmp_input_path, tmp_output_path, method=method)

        progress_bar.progress(80)
        status_text.text("📊 Calculating results...")

        # Calculate compression results
        original_size = len(uploaded_file.getvalue())
        compressed_size = compressed_path.stat().st_size
        reduction = (1 - compressed_size / original_size) * 100

        progress_bar.progress(100)
        status_text.text("✅ Compression complete!")

        # Show results
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Original", format_size(original_size))
        with col2:
            st.metric("Compressed", format_size(compressed_size))
        with col3:
            st.metric("Reduction", f"{reduction:.1f}%")

        # Download button
        with open(compressed_path, "rb") as file:
            file_name = uploaded_file.name.replace(".pdf", "_compressed.pdf")
            st.download_button(
                label="📥 Download Compressed PDF",
                data=file.read(),
                file_name=file_name,
                mime="application/pdf",
                type="primary",
                use_container_width=True,
            )

        # Cleanup
        os.unlink(tmp_input_path)
        os.unlink(compressed_path)

        # Clear progress indicators after a delay
        time.sleep(2)
        progress_bar.empty()
        status_text.empty()

    except Exception as e:
        st.error(f"❌ Compression failed: {str(e)}")
        progress_bar.empty()
        status_text.empty()

        # Cleanup on error
        try:
            if tmp_input_path is not None:
                os.unlink(tmp_input_path)
            if compressed_path is not None and compressed_path.exists():
                os.unlink(compressed_path)
        except OSError:
            pass


if __name__ == "__main__":
    main()
