"""Tests for core converter abstractions."""

from __future__ import annotations

from pathlib import Path

from pdf_to_markdown.converter import (
    ConversionOptions,
    ConversionResult,
    ConverterBackend,
)


class _DummyBackend:
    """Minimal implementation for Protocol conformance test."""

    @property
    def name(self) -> str:
        return "dummy"

    def is_available(self) -> bool:
        return True

    def convert(self, pdf_path: Path, options: ConversionOptions) -> ConversionResult:
        return ConversionResult(markdown="# Test", page_count=1, source_path=pdf_path)


class TestConversionOptions:
    def test_defaults(self) -> None:
        opts = ConversionOptions()
        assert opts.pages is None
        assert opts.extract_images is True
        assert opts.image_format == "png"
        assert opts.dpi == 150
        assert opts.show_progress is False

    def test_custom_values(self) -> None:
        opts = ConversionOptions(pages=[0, 1], extract_images=False, dpi=300)
        assert opts.pages == [0, 1]
        assert opts.extract_images is False
        assert opts.dpi == 300


class TestConversionResult:
    def test_defaults(self) -> None:
        result = ConversionResult(markdown="# Hello")
        assert result.markdown == "# Hello"
        assert result.images == {}
        assert result.page_count == 0
        assert result.source_path is None

    def test_with_images(self) -> None:
        imgs = {"page1.png": b"\x89PNG"}
        result = ConversionResult(markdown="text", images=imgs, page_count=5)
        assert len(result.images) == 1
        assert result.page_count == 5


class TestConverterBackendProtocol:
    def test_dummy_is_protocol_conformant(self) -> None:
        backend = _DummyBackend()
        assert isinstance(backend, ConverterBackend)

    def test_dummy_convert(self) -> None:
        backend = _DummyBackend()
        result = backend.convert(Path("test.pdf"), ConversionOptions())
        assert result.markdown == "# Test"
        assert result.page_count == 1
