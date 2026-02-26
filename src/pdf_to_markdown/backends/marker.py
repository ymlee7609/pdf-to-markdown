"""Marker backend for high-quality PDF to Markdown conversion."""

from __future__ import annotations

import io
from pathlib import Path

from pdf_to_markdown.converter import ConversionOptions, ConversionResult

try:
    from marker.converters.pdf import PdfConverter  # pragma: no cover
    from marker.models import create_model_dict  # pragma: no cover

    _MARKER_AVAILABLE = True  # pragma: no cover
except ImportError:
    _MARKER_AVAILABLE = False


class MarkerBackend:
    """Backend using marker-pdf for high-quality conversion."""

    def __init__(self) -> None:
        self._converter: PdfConverter | None = None

    @property
    def name(self) -> str:
        return "marker"

    def is_available(self) -> bool:
        return _MARKER_AVAILABLE

    def _get_converter(self) -> PdfConverter:
        """Lazy-load the Marker converter and models."""
        if self._converter is None:
            model_dict = create_model_dict()
            self._converter = PdfConverter(artifact_dict=model_dict)
        return self._converter

    def convert(self, pdf_path: Path, options: ConversionOptions) -> ConversionResult:
        import pymupdf

        pdf_path = Path(pdf_path)
        doc = pymupdf.open(str(pdf_path))
        page_count = len(doc)
        doc.close()

        converter = self._get_converter()
        rendered = converter(str(pdf_path))

        md_text = rendered.markdown

        images: dict[str, bytes] = {}
        if options.extract_images and rendered.images:
            for img_name, pil_image in rendered.images.items():
                buf = io.BytesIO()
                fmt = options.image_format.upper()
                if fmt == "JPG":
                    fmt = "JPEG"
                pil_image.save(buf, format=fmt)
                images[img_name] = buf.getvalue()

        return ConversionResult(
            markdown=md_text,
            images=images,
            page_count=page_count,
            source_path=pdf_path,
        )
