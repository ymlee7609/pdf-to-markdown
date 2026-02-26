"""Tests for the output writer."""

from __future__ import annotations

from pathlib import Path

from pdf_to_markdown.converter import ConversionResult
from pdf_to_markdown.output import write_result


class TestWriteResult:
    def test_write_markdown_only(self, tmp_path: Path) -> None:
        result = ConversionResult(markdown="# Hello World\n\nSome text.")
        out = tmp_path / "test.md"

        written = write_result(result, out)
        assert written == out
        assert out.read_text(encoding="utf-8") == "# Hello World\n\nSome text."

    def test_write_with_images(self, tmp_path: Path) -> None:
        images = {
            "img1.png": b"\x89PNG_fake_data",
            "img2.png": b"\x89PNG_other_data",
        }
        result = ConversionResult(markdown="# With Images", images=images)
        out = tmp_path / "doc.md"

        write_result(result, out)
        assert out.exists()

        images_dir = tmp_path / "doc_images"
        assert images_dir.is_dir()
        assert (images_dir / "img1.png").read_bytes() == b"\x89PNG_fake_data"
        assert (images_dir / "img2.png").read_bytes() == b"\x89PNG_other_data"

    def test_creates_parent_dirs(self, tmp_path: Path) -> None:
        result = ConversionResult(markdown="# Nested")
        out = tmp_path / "a" / "b" / "c" / "test.md"

        write_result(result, out)
        assert out.exists()

    def test_empty_images_no_dir(self, tmp_path: Path) -> None:
        result = ConversionResult(markdown="# No images", images={})
        out = tmp_path / "clean.md"

        write_result(result, out)
        assert out.exists()
        assert not (tmp_path / "clean_images").exists()

    def test_utf8_content(self, tmp_path: Path) -> None:
        result = ConversionResult(markdown="# UTF-8 테스트\n\n한국어 본문")
        out = tmp_path / "korean.md"

        write_result(result, out)
        content = out.read_text(encoding="utf-8")
        assert "한국어" in content
