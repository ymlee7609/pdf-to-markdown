"""Tests for the PyMuPDF4LLM backend."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from pdf_to_markdown.backends.pymupdf import PyMuPDFBackend
from pdf_to_markdown.converter import ConversionOptions, ConverterBackend


@pytest.fixture
def backend() -> PyMuPDFBackend:
    return PyMuPDFBackend()


class TestPyMuPDFBackend:
    def test_name(self, backend: PyMuPDFBackend) -> None:
        assert backend.name == "pymupdf"

    def test_is_available(self, backend: PyMuPDFBackend) -> None:
        assert backend.is_available() is True

    def test_is_available_false_when_import_fails(self, backend: PyMuPDFBackend) -> None:
        with patch.dict("sys.modules", {"pymupdf4llm": None}):
            assert backend.is_available() is False

    def test_protocol_conformance(self, backend: PyMuPDFBackend) -> None:
        assert isinstance(backend, ConverterBackend)

    def test_convert_small_pdf(self, backend: PyMuPDFBackend, small_pdf: Path) -> None:
        if not small_pdf.exists():
            pytest.skip("Sample PDF not available")

        result = backend.convert(small_pdf, ConversionOptions(extract_images=False))
        assert len(result.markdown) > 0
        assert result.page_count > 0
        assert result.source_path == small_pdf

    def test_convert_with_images(self, backend: PyMuPDFBackend, small_pdf: Path) -> None:
        if not small_pdf.exists():
            pytest.skip("Sample PDF not available")

        result = backend.convert(small_pdf, ConversionOptions(extract_images=True))
        assert len(result.markdown) > 0

    def test_convert_page_range(self, backend: PyMuPDFBackend, small_pdf: Path) -> None:
        if not small_pdf.exists():
            pytest.skip("Sample PDF not available")

        result = backend.convert(
            small_pdf, ConversionOptions(pages=[0], extract_images=False)
        )
        assert len(result.markdown) > 0

    def test_convert_korean_pdf(self, backend: PyMuPDFBackend, korean_pdf: Path) -> None:
        if not korean_pdf.exists():
            pytest.skip("Korean sample PDF not available")

        result = backend.convert(
            korean_pdf, ConversionOptions(pages=[0], extract_images=False)
        )
        assert len(result.markdown) > 0

    def test_convert_nonexistent_file(self, backend: PyMuPDFBackend) -> None:
        with pytest.raises(Exception):
            backend.convert(Path("/nonexistent.pdf"), ConversionOptions())

    @pytest.mark.slow
    def test_convert_large_pdf(self, backend: PyMuPDFBackend, medium_pdf: Path) -> None:
        if not medium_pdf.exists():
            pytest.skip("Medium sample PDF not available")

        result = backend.convert(medium_pdf, ConversionOptions(extract_images=False))
        assert len(result.markdown) > 100
        assert result.page_count > 1
