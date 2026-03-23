"""마크다운 문서의 챕터별 분할 로직."""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass

# 챕터 분할 크기 기준 (바이트)
SPLIT_THRESHOLD = 500_000


@dataclass
class Chapter:
    """분할된 챕터 데이터."""

    title: str
    content: str
    index: int


def should_split(markdown: str, threshold: int = SPLIT_THRESHOLD) -> bool:
    """마크다운이 분할 기준 크기를 초과하는지 확인한다.

    Args:
        markdown: 마크다운 텍스트.
        threshold: 분할 기준 바이트 수.

    Returns:
        분할이 필요하면 True.
    """
    return len(markdown.encode("utf-8")) >= threshold


def split_by_chapters(markdown: str) -> list[Chapter]:
    """마크다운을 챕터(heading) 단위로 분할한다.

    ``# `` (level 1) heading을 기준으로 분할하며,
    level 1 heading이 없으면 ``## `` (level 2)로 폴백한다.
    코드 블록 내부의 ``#``은 heading으로 인식하지 않는다.

    Args:
        markdown: 마크다운 텍스트.

    Returns:
        챕터 목록. heading이 없으면 전체를 단일 챕터로 반환한다.
    """
    if not markdown.strip():
        return [Chapter(title="front-matter", content="", index=0)]

    # 코드 블록 영역을 찾아서 heading 검색에서 제외
    code_block_ranges = _find_code_block_ranges(markdown)

    # level 1 heading 위치 탐색
    positions = _find_heading_positions(markdown, level=1, exclude_ranges=code_block_ranges)

    # level 1이 없으면 level 2로 폴백
    if not positions:
        positions = _find_heading_positions(markdown, level=2, exclude_ranges=code_block_ranges)

    # heading이 전혀 없으면 전체를 단일 챕터로 반환
    if not positions:
        return [Chapter(title="front-matter", content=markdown, index=0)]

    chapters: list[Chapter] = []
    idx = 0

    # 첫 heading 이전 내용이 있으면 front-matter로 저장
    first_pos = positions[0]
    front = markdown[:first_pos].strip()
    if front:
        chapters.append(Chapter(title="front-matter", content=front + "\n", index=idx))
        idx += 1

    # 각 heading 기준으로 분할
    for i, pos in enumerate(positions):
        end = positions[i + 1] if i + 1 < len(positions) else len(markdown)
        section = markdown[pos:end]

        # heading 텍스트 추출
        first_line_end = section.find("\n")
        if first_line_end == -1:
            heading_line = section
        else:
            heading_line = section[:first_line_end]

        title = re.sub(r"^#+\s*", "", heading_line).strip()
        if not title:
            title = f"chapter-{idx}"

        chapters.append(Chapter(title=title, content=section.rstrip() + "\n", index=idx))
        idx += 1

    return chapters


def chapter_filename(index: int, title: str) -> str:
    """챕터 인덱스와 제목으로 파일명을 생성한다.

    Args:
        index: 챕터 인덱스 (0부터 시작).
        title: 챕터 제목.

    Returns:
        ``"01_slugified-title.md"`` 형태의 파일명.
    """
    slug = _slugify(title)
    return f"{index:02d}_{slug}.md"


def rewrite_image_paths(content: str, old_prefix: str, new_prefix: str) -> str:
    """마크다운 내 이미지 참조 경로를 치환한다.

    ``![alt](old_prefix/img.png)`` → ``![alt](new_prefix/img.png)``

    Args:
        content: 마크다운 텍스트.
        old_prefix: 기존 이미지 경로 접두어.
        new_prefix: 새 이미지 경로 접두어.

    Returns:
        이미지 경로가 치환된 마크다운 텍스트.
    """
    if not old_prefix:
        return content
    escaped = re.escape(old_prefix)
    pattern = rf"(!\[[^\]]*\]\()({escaped}/)"
    return re.sub(pattern, rf"\1{new_prefix}/", content)


def _find_code_block_ranges(markdown: str) -> list[tuple[int, int]]:
    """코드 블록(``` 또는 ~~~) 영역의 (시작, 끝) 위치 목록을 반환한다."""
    ranges: list[tuple[int, int]] = []
    pattern = re.compile(r"^(`{3,}|~{3,})", re.MULTILINE)
    matches = list(pattern.finditer(markdown))

    i = 0
    while i < len(matches) - 1:
        open_match = matches[i]
        open_char = open_match.group(1)[0]
        open_len = len(open_match.group(1))

        # 같은 문자로 같은 길이 이상인 닫는 fence 찾기
        for j in range(i + 1, len(matches)):
            close_match = matches[j]
            close_char = close_match.group(1)[0]
            close_len = len(close_match.group(1))
            if close_char == open_char and close_len >= open_len:
                ranges.append((open_match.start(), close_match.end()))
                i = j + 1
                break
        else:
            # 닫는 fence를 못 찾으면 문서 끝까지
            ranges.append((open_match.start(), len(markdown)))
            break
    return ranges


def _find_heading_positions(
    markdown: str,
    level: int,
    exclude_ranges: list[tuple[int, int]],
) -> list[int]:
    """지정된 레벨의 heading 시작 위치를 반환한다.

    Args:
        markdown: 마크다운 텍스트.
        level: heading 레벨 (1 또는 2).
        exclude_ranges: 제외할 영역 (코드 블록).

    Returns:
        heading 시작 위치 목록.
    """
    prefix = "#" * level
    pattern = re.compile(rf"^{prefix}\s+", re.MULTILINE)
    positions: list[int] = []

    for match in pattern.finditer(markdown):
        pos = match.start()
        if not _in_ranges(pos, exclude_ranges):
            positions.append(pos)

    return positions


def _in_ranges(pos: int, ranges: list[tuple[int, int]]) -> bool:
    """위치가 주어진 범위 목록 안에 있는지 확인한다."""
    return any(start <= pos < end for start, end in ranges)


def _slugify(text: str, max_length: int = 50) -> str:
    """제목을 파일명에 적합한 slug로 변환한다.

    알파벳, 숫자, 한글, 하이픈만 허용한다.

    Args:
        text: 원본 텍스트.
        max_length: 최대 길이.

    Returns:
        slugified 문자열.
    """
    # NFD → NFC 정규화
    text = unicodedata.normalize("NFC", text)
    # 소문자 변환
    text = text.lower()
    # 허용 문자 외 제거 (알파벳, 숫자, 한글, 공백, 하이픈)
    text = re.sub(r"[^\w\s가-힣-]", "", text)
    # 공백/밑줄을 하이픈으로
    text = re.sub(r"[\s_]+", "-", text)
    # 연속 하이픈 정리
    text = re.sub(r"-{2,}", "-", text)
    # 양쪽 하이픈 제거
    text = text.strip("-")
    # 길이 제한
    if len(text) > max_length:
        text = text[:max_length].rstrip("-")
    return text or "untitled"
