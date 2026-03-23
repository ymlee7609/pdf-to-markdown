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
        # 5개 챕터 파일 + INDEX.md 존재
        md_files = sorted(written.glob("*.md"))
        assert len(md_files) == 6
        chapter_files = [f for f in md_files if f.name != "INDEX.md"]
        assert len(chapter_files) == 5
        assert chapter_files[0].name.startswith("00_")

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
        md_files = [f for f in written.glob("*.md") if f.name != "INDEX.md"]
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

    def test_split_with_min_chunk_size(self, tmp_path: Path) -> None:
        """min_chunk_size 지정 시 작은 챕터가 병합되어 파일 수가 줄어든다."""
        # 5개의 작은 챕터 (각 약 100바이트)
        parts = [f"# Ch {i}\n\nContent {i}.\n" for i in range(5)]
        md = "\n".join(parts)
        result = ConversionResult(markdown=md)
        out = tmp_path / "merged.md"

        # 병합 없이 분할: 5개 챕터 파일
        written_no_merge = write_result(result, out, force_split=True, min_chunk_size=0)
        count_no_merge = len([
            f for f in written_no_merge.glob("*.md") if f.name != "INDEX.md"
        ])

        # 큰 min_chunk_size로 병합: 파일 수 감소
        out2 = tmp_path / "merged2.md"
        written_merged = write_result(result, out2, force_split=True, min_chunk_size=50000)
        count_merged = len([
            f for f in written_merged.glob("*.md") if f.name != "INDEX.md"
        ])

        assert count_no_merge == 5
        assert count_merged < count_no_merge

    def test_split_min_chunk_size_zero_no_merge(self, tmp_path: Path) -> None:
        """min_chunk_size=0이면 기존 동작과 동일하다."""
        md = "# A\n\nText A.\n\n# B\n\nText B.\n"
        result = ConversionResult(markdown=md)
        out = tmp_path / "no_merge.md"

        written = write_result(result, out, force_split=True, min_chunk_size=0)
        chapter_files = [f for f in written.glob("*.md") if f.name != "INDEX.md"]
        assert len(chapter_files) == 2


class TestIndexGeneration:
    """INDEX.md 생성 테스트."""

    def test_split_generates_index(self, tmp_path: Path) -> None:
        """분할 시 INDEX.md 파일이 생성된다."""
        md = "# Chapter 1\n\nText.\n\n# Chapter 2\n\nMore text.\n"
        result = ConversionResult(markdown=md)
        out = tmp_path / "doc.md"

        written = write_result(result, out, force_split=True)
        assert (written / "INDEX.md").exists()

    def test_index_contains_all_chapters(self, tmp_path: Path) -> None:
        """INDEX에 모든 챕터가 포함된다."""
        md = "# Alpha\n\nA.\n\n# Beta\n\nB.\n\n# Gamma\n\nC.\n"
        result = ConversionResult(markdown=md)
        out = tmp_path / "doc.md"

        written = write_result(result, out, force_split=True)
        index = (written / "INDEX.md").read_text(encoding="utf-8")
        assert "Alpha" in index
        assert "Beta" in index
        assert "Gamma" in index
        assert "**Chapters**: 3" in index

    def test_index_metadata_with_source(self, tmp_path: Path) -> None:
        """원본 PDF 정보가 INDEX에 포함된다."""
        from pathlib import Path as P

        md = "# Heading\n\nContent.\n"
        result = ConversionResult(
            markdown=md, page_count=42, source_path=P("report.pdf"),
        )
        out = tmp_path / "doc.md"

        written = write_result(result, out, force_split=True)
        index = (written / "INDEX.md").read_text(encoding="utf-8")
        assert "**Source**: report.pdf" in index
        assert "**Pages**: 42" in index

    def test_index_not_generated_for_single(self, tmp_path: Path) -> None:
        """단일 파일 출력 시 INDEX.md가 생성되지 않는다."""
        result = ConversionResult(markdown="# Small\n\nContent.")
        out = tmp_path / "single.md"

        written = write_result(result, out)
        assert written.is_file()
        assert not (tmp_path / "INDEX.md").exists()
