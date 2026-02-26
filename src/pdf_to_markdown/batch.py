"""Batch processing for directory-level PDF conversion."""

from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path

from pdf_to_markdown.converter import ConversionOptions, ConversionResult, ConverterBackend
from pdf_to_markdown.output import write_result


@dataclass
class BatchResult:
    """Summary of a batch conversion run."""

    total: int = 0
    success: int = 0
    failed: int = 0
    results: list[tuple[Path, ConversionResult | None]] = None  # type: ignore[assignment]

    def __post_init__(self) -> None:
        if self.results is None:
            self.results = []


def convert_directory(
    input_dir: Path,
    output_dir: Path,
    backend: ConverterBackend,
    options: ConversionOptions,
    verbose: bool = False,
) -> BatchResult:
    """Convert all PDF files in a directory.

    Args:
        input_dir: Directory containing PDF files.
        output_dir: Directory for output markdown files.
        backend: Converter backend to use.
        options: Conversion options.
        verbose: Print progress information.

    Returns:
        BatchResult with conversion summary.
    """
    pdf_files = sorted(input_dir.glob("*.pdf"))
    batch = BatchResult(total=len(pdf_files))

    for pdf_file in pdf_files:
        out_path = output_dir / f"{pdf_file.stem}.md"
        if verbose:
            print(f"Converting: {pdf_file.name}", file=sys.stderr)
        try:
            result = backend.convert(pdf_file, options)
            write_result(result, out_path)
            batch.success += 1
            batch.results.append((pdf_file, result))
            if verbose:
                print(f"  -> {out_path} ({result.page_count} pages)", file=sys.stderr)
        except Exception as exc:
            batch.failed += 1
            batch.results.append((pdf_file, None))
            if verbose:
                print(f"  FAILED: {exc}", file=sys.stderr)

    return batch
