"""Tests for the Marker backend."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from pdf_to_markdown.backends.marker import _MARKER_AVAILABLE, MarkerBackend
from pdf_to_markdown.converter import ConversionOptions, ConverterBackend


class TestMarkerBackendUnavailable:
    """Tests that always run regardless of marker installation."""

    def test_name(self) -> None:
        backend = MarkerBackend()
        assert backend.name == "marker"

    def test_is_available_matches_import(self) -> None:
        backend = MarkerBackend()
        assert backend.is_available() == _MARKER_AVAILABLE

    def test_protocol_conformance(self) -> None:
        backend = MarkerBackend()
        assert isinstance(backend, ConverterBackend)


class TestMarkerBackendMocked:
    """Test Marker backend convert logic using mocks."""

    def test_convert_with_mock(self, small_pdf: Path) -> None:
        if not small_pdf.exists():
            pytest.skip("Sample PDF not available")

        backend = MarkerBackend()

        mock_converter = MagicMock()
        mock_converter.return_value = SimpleNamespace(
            markdown="# Mocked output",
            images={},
        )
        backend._converter = mock_converter

        result = backend.convert(small_pdf, ConversionOptions(extract_images=False))
        assert result.markdown == "# Mocked output"
        assert result.page_count > 0
        assert result.images == {}

    def test_convert_with_images_mock(self, small_pdf: Path) -> None:
        if not small_pdf.exists():
            pytest.skip("Sample PDF not available")

        backend = MarkerBackend()

        mock_img = MagicMock()
        mock_img.save = MagicMock(side_effect=lambda buf, format: buf.write(b"fake_png"))

        mock_converter = MagicMock()
        mock_converter.return_value = SimpleNamespace(
            markdown="# With images",
            images={"page1.png": mock_img},
        )
        backend._converter = mock_converter

        result = backend.convert(small_pdf, ConversionOptions(extract_images=True))
        assert "page1.png" in result.images
        assert result.images["page1.png"] == b"fake_png"

    def test_convert_jpg_format_normalization(self, small_pdf: Path) -> None:
        if not small_pdf.exists():
            pytest.skip("Sample PDF not available")

        backend = MarkerBackend()

        saved_formats: list[str] = []

        def capture_save(buf: object, format: str) -> None:
            saved_formats.append(format)
            buf.write(b"fake_jpg")  # type: ignore[union-attr]

        mock_img = MagicMock()
        mock_img.save = MagicMock(side_effect=capture_save)

        mock_converter = MagicMock()
        mock_converter.return_value = SimpleNamespace(
            markdown="# JPG test",
            images={"page1.jpg": mock_img},
        )
        backend._converter = mock_converter

        result = backend.convert(
            small_pdf,
            ConversionOptions(extract_images=True, image_format="jpg"),
        )
        assert saved_formats == ["JPEG"]
        assert "page1.jpg" in result.images

    def test_get_converter_lazy_init(self) -> None:
        backend = MarkerBackend()
        assert backend._converter is None

        mock_model_dict = {"model": "mock"}
        mock_converter_instance = MagicMock()

        with (
            patch(
                "pdf_to_markdown.backends.marker.create_model_dict",
                create=True,
                return_value=mock_model_dict,
            ),
            patch(
                "pdf_to_markdown.backends.marker.PdfConverter",
                create=True,
                return_value=mock_converter_instance,
            ) as mock_cls,
        ):
            converter = backend._get_converter()

        mock_cls.assert_called_once_with(artifact_dict=mock_model_dict)
        assert converter is mock_converter_instance
        assert backend._converter is mock_converter_instance

    def test_get_converter_reuses_instance(self) -> None:
        backend = MarkerBackend()
        sentinel = MagicMock()
        backend._converter = sentinel

        assert backend._get_converter() is sentinel


@pytest.mark.skipif(not _MARKER_AVAILABLE, reason="marker-pdf is not installed")
class TestMarkerBackendAvailable:
    @pytest.fixture
    def backend(self) -> MarkerBackend:
        return MarkerBackend()

    def test_convert_small_pdf(self, backend: MarkerBackend, small_pdf: Path) -> None:
        if not small_pdf.exists():
            pytest.skip("Sample PDF not available")

        result = backend.convert(small_pdf, ConversionOptions(extract_images=False))
        assert len(result.markdown) > 0
        assert result.page_count > 0
        assert result.source_path == small_pdf
