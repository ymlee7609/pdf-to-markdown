"""PyMuPDF4LLM backend for PDF to Markdown conversion."""

from __future__ import annotations

import tempfile
from pathlib import Path

from pdf_to_markdown.converter import ConversionOptions, ConversionResult


class PyMuPDFBackend:
    """Backend using pymupdf4llm for conversion."""

    @property
    def name(self) -> str:
        return "pymupdf"

    def is_available(self) -> bool:
        try:
            import pymupdf4llm  # noqa: F401

            return True
        except ImportError:
            return False

    def convert(self, pdf_path: Path, options: ConversionOptions) -> ConversionResult:
        import pymupdf
        import pymupdf4llm

        pdf_path = Path(pdf_path)
        doc = pymupdf.open(str(pdf_path))
        page_count = len(doc)
        doc.close()

        kwargs: dict = {}
        if options.pages is not None:
            kwargs["pages"] = options.pages
        kwargs["show_progress"] = options.show_progress

        images: dict[str, bytes] = {}

        if options.extract_images:
            with tempfile.TemporaryDirectory() as tmp_dir:
                kwargs["write_images"] = True
                kwargs["image_path"] = tmp_dir
                kwargs["image_format"] = options.image_format
                kwargs["dpi"] = options.dpi

                md_text = pymupdf4llm.to_markdown(str(pdf_path), **kwargs)

                tmp_path = Path(tmp_dir)
                for img_file in tmp_path.iterdir():
                    if img_file.is_file():
                        images[img_file.name] = img_file.read_bytes()
        else:
            kwargs["write_images"] = False
            md_text = pymupdf4llm.to_markdown(str(pdf_path), **kwargs)

        return ConversionResult(
            markdown=md_text,
            images=images,
            page_count=page_count,
            source_path=pdf_path,
        )
