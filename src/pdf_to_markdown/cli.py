"""Command-line interface for PDF to Markdown converter."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from pdf_to_markdown.backends import get_backend
from pdf_to_markdown.batch import convert_directory
from pdf_to_markdown.converter import ConversionOptions
from pdf_to_markdown.output import write_result


def parse_pages(pages_str: str) -> list[int]:
    """Parse a page specification string into a list of page numbers.

    Supports comma-separated values and ranges:
        "0,5-7,10" -> [0, 5, 6, 7, 10]

    Args:
        pages_str: Page specification string.

    Returns:
        Sorted, deduplicated list of page numbers.

    Raises:
        ValueError: If the format is invalid.
    """
    result: set[int] = set()
    for part in pages_str.split(","):
        part = part.strip()
        if not part:
            continue
        if "-" in part:
            start_str, end_str = part.split("-", 1)
            start = int(start_str.strip())
            end = int(end_str.strip())
            if start > end:
                raise ValueError(f"Invalid page range: {part}")
            result.update(range(start, end + 1))
        else:
            result.add(int(part))
    return sorted(result)


def build_parser() -> argparse.ArgumentParser:
    """Build the argument parser."""
    parser = argparse.ArgumentParser(
        prog="pdf2md",
        description="Convert PDF files to Markdown.",
    )
    parser.add_argument(
        "input",
        type=Path,
        help="Input PDF file or directory containing PDFs.",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=None,
        help="Output markdown file or directory (default: same name as input).",
    )
    parser.add_argument(
        "--engine",
        choices=["pymupdf", "marker"],
        default="pymupdf",
        help="Conversion backend (default: pymupdf).",
    )
    parser.add_argument(
        "--pages",
        type=str,
        default=None,
        help="Page numbers to convert (e.g., '0,5-7,10').",
    )
    parser.add_argument(
        "--no-images",
        action="store_true",
        default=False,
        help="Do not extract images.",
    )
    parser.add_argument(
        "--image-format",
        choices=["png", "jpg"],
        default="png",
        help="Image output format (default: png).",
    )
    parser.add_argument(
        "--dpi",
        type=int,
        default=150,
        help="Image DPI (default: 150).",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        default=False,
        help="Print verbose output.",
    )

    split_group = parser.add_mutually_exclusive_group()
    split_group.add_argument(
        "--split",
        action="store_true",
        default=False,
        help="Force chapter splitting regardless of file size.",
    )
    split_group.add_argument(
        "--no-split",
        action="store_true",
        default=False,
        help="Disable chapter splitting regardless of file size.",
    )
    parser.add_argument(
        "--min-chunk-size",
        type=int,
        default=0,
        help="Minimum chunk size in bytes for chapter merging (default: 0, no merging).",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """CLI entry point.

    Returns:
        Exit code (0 for success, 1 for failure).
    """
    parser = build_parser()
    args = parser.parse_args(argv)

    pages = None
    if args.pages:
        try:
            pages = parse_pages(args.pages)
        except ValueError as exc:
            print(f"Error: Invalid page specification: {exc}", file=sys.stderr)
            return 1

    options = ConversionOptions(
        pages=pages,
        extract_images=not args.no_images,
        image_format=args.image_format,
        dpi=args.dpi,
        show_progress=args.verbose,
    )

    try:
        backend = get_backend(args.engine)
    except (ValueError, RuntimeError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    input_path: Path = args.input

    # 분할 옵션 결정
    force_split: bool | None = None
    if args.split:
        force_split = True
    elif args.no_split:
        force_split = False

    if input_path.is_dir():
        output_dir = args.output or input_path.parent / f"{input_path.name}_output"
        output_dir.mkdir(parents=True, exist_ok=True)
        batch = convert_directory(
            input_path, output_dir, backend, options, args.verbose,
            force_split=force_split,
            min_chunk_size=args.min_chunk_size,
        )
        print(
            f"Batch complete: {batch.success}/{batch.total} succeeded, "
            f"{batch.failed} failed.",
            file=sys.stderr,
        )
        return 1 if batch.failed > 0 else 0

    if not input_path.is_file():
        print(f"Error: {input_path} is not a file or directory.", file=sys.stderr)
        return 1

    output_path = args.output or input_path.with_suffix(".md")

    try:
        result = backend.convert(input_path, options)
        written = write_result(
            result, output_path,
            force_split=force_split,
            min_chunk_size=args.min_chunk_size,
        )
        if args.verbose:
            if written.is_dir():
                chapter_count = len(list(written.glob("*.md")))
                print(
                    f"Converted {result.page_count} pages -> {written}/ "
                    f"({chapter_count} chapters)",
                    file=sys.stderr,
                )
            else:
                print(
                    f"Converted {result.page_count} pages -> {written}",
                    file=sys.stderr,
                )
        return 0
    except Exception as exc:
        print(f"Error converting {input_path}: {exc}", file=sys.stderr)
        return 1
