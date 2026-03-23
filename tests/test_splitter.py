"""splitter 모듈 단위 테스트."""

from __future__ import annotations

from pdf_to_markdown.splitter import (
    chapter_filename,
    rewrite_image_paths,
    should_split,
    split_by_chapters,
)

# ---------------------------------------------------------------------------
# should_split
# ---------------------------------------------------------------------------


class TestShouldSplit:
    """should_split() 크기 판단 테스트."""

    def test_below_threshold(self) -> None:
        md = "a" * 100
        assert should_split(md, threshold=500_000) is False

    def test_at_threshold(self) -> None:
        md = "a" * 500_000
        assert should_split(md, threshold=500_000) is True

    def test_above_threshold(self) -> None:
        md = "a" * 600_000
        assert should_split(md) is True

    def test_multibyte_utf8(self) -> None:
        """한글 한 글자는 UTF-8에서 3바이트."""
        md = "가" * 200_000  # 600,000 바이트
        assert should_split(md, threshold=500_000) is True

    def test_multibyte_below_threshold(self) -> None:
        md = "가" * 100_000  # 300,000 바이트
        assert should_split(md, threshold=500_000) is False

    def test_empty_string(self) -> None:
        assert should_split("") is False


# ---------------------------------------------------------------------------
# split_by_chapters
# ---------------------------------------------------------------------------


class TestSplitByChapters:
    """split_by_chapters() 챕터 분할 테스트."""

    def test_single_h1_no_front_matter(self) -> None:
        md = "# Introduction\n\nSome text here.\n"
        chapters = split_by_chapters(md)
        assert len(chapters) == 1
        assert chapters[0].title == "Introduction"
        assert chapters[0].index == 0

    def test_multiple_h1(self) -> None:
        md = "# Chapter 1\n\nText 1\n\n# Chapter 2\n\nText 2\n"
        chapters = split_by_chapters(md)
        assert len(chapters) == 2
        assert chapters[0].title == "Chapter 1"
        assert chapters[1].title == "Chapter 2"
        assert chapters[0].index == 0
        assert chapters[1].index == 1

    def test_front_matter_before_first_heading(self) -> None:
        md = "Some preamble text.\n\n# Chapter 1\n\nContent.\n"
        chapters = split_by_chapters(md)
        assert len(chapters) == 2
        assert chapters[0].title == "front-matter"
        assert chapters[0].index == 0
        assert chapters[1].title == "Chapter 1"
        assert chapters[1].index == 1

    def test_fallback_to_h2(self) -> None:
        md = "## Section A\n\nText A\n\n## Section B\n\nText B\n"
        chapters = split_by_chapters(md)
        assert len(chapters) == 2
        assert chapters[0].title == "Section A"
        assert chapters[1].title == "Section B"

    def test_no_headings(self) -> None:
        md = "Just plain text without any headings.\n"
        chapters = split_by_chapters(md)
        assert len(chapters) == 1
        assert chapters[0].title == "front-matter"
        assert "plain text" in chapters[0].content

    def test_empty_string(self) -> None:
        chapters = split_by_chapters("")
        assert len(chapters) == 1
        assert chapters[0].title == "front-matter"

    def test_code_block_heading_ignored(self) -> None:
        """코드 블록 내부의 #은 heading으로 인식하지 않는다."""
        md = (
            "# Real Heading\n\n"
            "```python\n"
            "# This is a comment, not a heading\n"
            "print('hello')\n"
            "```\n\n"
            "# Another Heading\n\n"
            "Text.\n"
        )
        chapters = split_by_chapters(md)
        assert len(chapters) == 2
        assert chapters[0].title == "Real Heading"
        assert chapters[1].title == "Another Heading"

    def test_tilde_code_block_ignored(self) -> None:
        """~~~ 코드 블록 내부의 #도 무시한다."""
        md = (
            "# Heading\n\n"
            "~~~\n"
            "# comment inside\n"
            "~~~\n\n"
            "More text.\n"
        )
        chapters = split_by_chapters(md)
        assert len(chapters) == 1
        assert chapters[0].title == "Heading"

    def test_h2_not_split_when_h1_exists(self) -> None:
        """h1이 있으면 h2는 분할 기준으로 사용하지 않는다."""
        md = "# Main\n\n## Sub\n\nContent.\n"
        chapters = split_by_chapters(md)
        assert len(chapters) == 1
        assert chapters[0].title == "Main"
        assert "## Sub" in chapters[0].content

    def test_korean_heading(self) -> None:
        md = "# 소개\n\n내용입니다.\n\n# 결론\n\n마지막 내용.\n"
        chapters = split_by_chapters(md)
        assert len(chapters) == 2
        assert chapters[0].title == "소개"
        assert chapters[1].title == "결론"

    def test_chapter_content_ends_with_newline(self) -> None:
        md = "# A\n\nContent A\n\n# B\n\nContent B"
        chapters = split_by_chapters(md)
        for ch in chapters:
            assert ch.content.endswith("\n")


# ---------------------------------------------------------------------------
# chapter_filename
# ---------------------------------------------------------------------------


class TestChapterFilename:
    """chapter_filename() 파일명 생성 테스트."""

    def test_basic(self) -> None:
        assert chapter_filename(1, "Introduction") == "01_introduction.md"

    def test_front_matter(self) -> None:
        assert chapter_filename(0, "front-matter") == "00_front-matter.md"

    def test_korean_title(self) -> None:
        name = chapter_filename(2, "시스템 아키텍처")
        assert name == "02_시스템-아키텍처.md"

    def test_special_characters(self) -> None:
        name = chapter_filename(3, "What's Next? (v2.0)")
        assert "?" not in name
        assert "(" not in name
        assert name.startswith("03_")
        assert name.endswith(".md")

    def test_long_title_truncated(self) -> None:
        long_title = "A" * 100
        name = chapter_filename(1, long_title)
        # 파일명에서 접두어(01_)와 접미어(.md) 제외한 slug 부분이 50자 이하
        slug = name[3:-3]  # "01_" 제거, ".md" 제거
        assert len(slug) <= 50

    def test_empty_title(self) -> None:
        name = chapter_filename(0, "")
        assert name == "00_untitled.md"

    def test_zero_padded_index(self) -> None:
        name = chapter_filename(5, "Test")
        assert name.startswith("05_")

    def test_double_digit_index(self) -> None:
        name = chapter_filename(12, "Test")
        assert name.startswith("12_")


# ---------------------------------------------------------------------------
# rewrite_image_paths
# ---------------------------------------------------------------------------


class TestRewriteImagePaths:
    """rewrite_image_paths() 이미지 경로 치환 테스트."""

    def test_basic_rewrite(self) -> None:
        content = "![alt](old_dir/img.png)"
        result = rewrite_image_paths(content, "old_dir", "_images")
        assert result == "![alt](_images/img.png)"

    def test_multiple_images(self) -> None:
        content = "![a](prefix/a.png) text ![b](prefix/b.jpg)"
        result = rewrite_image_paths(content, "prefix", "_images")
        assert "![a](_images/a.png)" in result
        assert "![b](_images/b.jpg)" in result

    def test_no_match(self) -> None:
        content = "![alt](other/img.png)"
        result = rewrite_image_paths(content, "nonexistent", "_images")
        assert result == content

    def test_empty_old_prefix(self) -> None:
        content = "![alt](img.png)"
        result = rewrite_image_paths(content, "", "_images")
        assert result == content

    def test_preserves_non_image_content(self) -> None:
        content = "Some text\n![alt](dir/img.png)\nMore text"
        result = rewrite_image_paths(content, "dir", "_images")
        assert "Some text" in result
        assert "More text" in result
        assert "![alt](_images/img.png)" in result
