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


class TestWriteResultSplit:
    """챕터 분할 출력 테스트."""

    def _large_md(self) -> str:
        """500KB 이상의 마크다운을 생성한다."""
        chapters = []
        for i in range(5):
            chapters.append(f"# Chapter {i}\n\n{'x' * 120_000}\n")
        return "\n".join(chapters)

    def test_auto_split_large_file(self, tmp_path: Path) -> None:
        """500KB 이상이면 자동으로 디렉토리로 분할된다."""
        md = self._large_md()
        result = ConversionResult(markdown=md)
        out = tmp_path / "big.md"

        written = write_result(result, out)
        assert written.is_dir()
        assert written.name == "big"
        # 5개 챕터 파일 존재
        md_files = sorted(written.glob("*.md"))
        assert len(md_files) == 5
        assert md_files[0].name.startswith("00_")

    def test_auto_no_split_small_file(self, tmp_path: Path) -> None:
        """500KB 미만이면 단일 파일로 기록된다."""
        result = ConversionResult(markdown="# Small\n\nContent.")
        out = tmp_path / "small.md"

        written = write_result(result, out)
        assert written.is_file()
        assert written == out

    def test_force_split_true(self, tmp_path: Path) -> None:
        """force_split=True이면 크기와 무관하게 분할한다."""
        md = "# A\n\nSmall content.\n\n# B\n\nMore content.\n"
        result = ConversionResult(markdown=md)
        out = tmp_path / "forced.md"

        written = write_result(result, out, force_split=True)
        assert written.is_dir()
        assert written.name == "forced"

    def test_force_split_false(self, tmp_path: Path) -> None:
        """force_split=False이면 크기와 무관하게 단일 파일로 기록한다."""
        md = self._large_md()
        result = ConversionResult(markdown=md)
        out = tmp_path / "no_split.md"

        written = write_result(result, out, force_split=False)
        assert written.is_file()
        assert written == out

    def test_split_with_images(self, tmp_path: Path) -> None:
        """분할 시 이미지가 _images/ 디렉토리에 저장된다."""
        md = "# Heading\n\n" + "x" * 600_000 + "\n"
        images = {"page0.png": b"\x89PNG_data"}
        result = ConversionResult(markdown=md, images=images)
        out = tmp_path / "with_img.md"

        written = write_result(result, out)
        assert written.is_dir()
        images_dir = written / "_images"
        assert images_dir.is_dir()
        assert (images_dir / "page0.png").read_bytes() == b"\x89PNG_data"

    def test_split_with_front_matter(self, tmp_path: Path) -> None:
        """첫 heading 이전 내용은 00_front-matter.md로 저장된다."""
        md = "Preamble text.\n\n# Chapter 1\n\n" + "x" * 600_000 + "\n"
        result = ConversionResult(markdown=md)
        out = tmp_path / "fm.md"

        written = write_result(result, out, force_split=True)
        assert (written / "00_front-matter.md").exists()
        assert (written / "01_chapter-1.md").exists()

    def test_split_no_headings(self, tmp_path: Path) -> None:
        """heading이 없는 대용량 파일은 단일 front-matter로 분할된다."""
        md = "x" * 600_000
        result = ConversionResult(markdown=md)
        out = tmp_path / "nohead.md"

        written = write_result(result, out)
        assert written.is_dir()
        md_files = list(written.glob("*.md"))
        assert len(md_files) == 1
        assert md_files[0].name.startswith("00_")

    def test_split_creates_parent_dirs(self, tmp_path: Path) -> None:
        """분할 시에도 부모 디렉토리가 자동 생성된다."""
        md = "# H\n\n" + "x" * 600_000 + "\n"
        result = ConversionResult(markdown=md)
        out = tmp_path / "a" / "b" / "deep.md"

        written = write_result(result, out)
        assert written.is_dir()
        assert written.name == "deep"
