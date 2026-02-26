"""Output writer for Markdown and images."""

from __future__ import annotations

from pathlib import Path

from pdf_to_markdown.converter import ConversionResult


def write_result(result: ConversionResult, output_path: Path) -> Path:
    """Write conversion result to disk.

    Args:
        result: Conversion result containing markdown and images.
        output_path: Path for the output markdown file.

    Returns:
        The resolved path of the written markdown file.
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(result.markdown, encoding="utf-8")

    if result.images:
        images_dir = output_path.parent / f"{output_path.stem}_images"
        images_dir.mkdir(parents=True, exist_ok=True)
        for name, data in result.images.items():
            (images_dir / name).write_bytes(data)

    return output_path
