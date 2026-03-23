"""마크다운 및 이미지 출력 작성기."""

from __future__ import annotations

from pathlib import Path

from pdf_to_markdown.converter import ConversionResult
from pdf_to_markdown.splitter import (
    SPLIT_THRESHOLD,
    Chapter,
    chapter_filename,
    merge_small_chapters,
    rewrite_image_paths,
    should_split,
    split_by_chapters,
)


def write_result(
    result: ConversionResult,
    output_path: Path,
    *,
    split_threshold: int = SPLIT_THRESHOLD,
    force_split: bool | None = None,
    min_chunk_size: int = 0,
) -> Path:
    """변환 결과를 디스크에 기록한다.

    500KB 이상이면 챕터별로 분할하여 디렉토리에 저장한다.

    Args:
        result: 마크다운과 이미지를 포함하는 변환 결과.
        output_path: 출력 마크다운 파일 경로.
        split_threshold: 분할 기준 바이트 수.
        force_split: True=강제 분할, False=강제 단일, None=자동 판단.
        min_chunk_size: 최소 청크 크기(바이트). 이 크기 미만인 챕터를 병합한다.

    Returns:
        기록된 마크다운 파일 또는 디렉토리 경로.
    """
    output_path = Path(output_path)

    # 분할 여부 결정
    do_split = force_split
    if do_split is None:
        do_split = should_split(result.markdown, split_threshold)

    if do_split:
        return _write_split(result, output_path, min_chunk_size=min_chunk_size)
    return _write_single(result, output_path)


def _write_single(result: ConversionResult, output_path: Path) -> Path:
    """단일 마크다운 파일로 기록한다."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(result.markdown, encoding="utf-8")

    if result.images:
        images_dir = output_path.parent / f"{output_path.stem}_images"
        images_dir.mkdir(parents=True, exist_ok=True)
        for name, data in result.images.items():
            (images_dir / name).write_bytes(data)

    return output_path


def _write_split(
    result: ConversionResult,
    output_path: Path,
    *,
    min_chunk_size: int = 0,
) -> Path:
    """챕터별로 분할하여 디렉토리에 기록한다."""
    # output_path가 "document.md"이면 "document/" 디렉토리 생성
    out_dir = output_path.parent / output_path.stem
    out_dir.mkdir(parents=True, exist_ok=True)

    chapters = split_by_chapters(result.markdown)
    chapters = merge_small_chapters(chapters, min_chunk_size)

    # 기존 이미지 경로 접두어 파악
    old_image_prefix = f"{output_path.stem}_images"

    for ch in chapters:
        fname = chapter_filename(ch.index, ch.title)
        content = rewrite_image_paths(ch.content, old_image_prefix, "_images")
        (out_dir / fname).write_text(content, encoding="utf-8")

    # 이미지를 공유 _images/ 디렉토리에 저장
    if result.images:
        images_dir = out_dir / "_images"
        images_dir.mkdir(parents=True, exist_ok=True)
        for name, data in result.images.items():
            (images_dir / name).write_bytes(data)

    # INDEX.md 생성
    index_content = _build_index_md(chapters, result)
    (out_dir / "INDEX.md").write_text(index_content, encoding="utf-8")

    return out_dir


def _format_size(size_bytes: int) -> str:
    """바이트 수를 사람이 읽기 쉬운 크기로 변환한다."""
    if size_bytes < 1024:
        return f"{size_bytes}B"
    return f"{size_bytes / 1024:.1f}KB"


def _build_index_md(
    chapters: list[Chapter],
    result: ConversionResult,
) -> str:
    """분할된 챕터 목록으로 INDEX.md 내용을 생성한다.

    Args:
        chapters: 분할된 챕터 목록.
        result: 변환 결과 (원본 PDF 메타데이터 포함).

    Returns:
        INDEX.md 마크다운 문자열.
    """
    lines: list[str] = ["# INDEX", ""]

    # 메타데이터
    if result.source_path:
        lines.append(f"- **Source**: {result.source_path.name}")
    if result.page_count:
        lines.append(f"- **Pages**: {result.page_count}")
    lines.append(f"- **Chapters**: {len(chapters)}")
    lines.append("")

    # 챕터 테이블
    lines.append("| # | Title | File | Size | Chars |")
    lines.append("|---|-------|------|------|-------|")

    for ch in chapters:
        fname = chapter_filename(ch.index, ch.title)
        size_bytes = len(ch.content.encode("utf-8"))
        char_count = len(ch.content)
        size_str = _format_size(size_bytes)
        lines.append(
            f"| {ch.index} | {ch.title} | {fname} | {size_str} | {char_count} |"
        )

    lines.append("")
    return "\n".join(lines)
