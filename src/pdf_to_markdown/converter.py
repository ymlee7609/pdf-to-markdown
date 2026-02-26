"""Core abstractions for PDF to Markdown conversion."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Protocol, runtime_checkable


@dataclass
class ConversionOptions:
    """Options controlling the conversion process."""

    pages: list[int] | None = None
    extract_images: bool = True
    image_format: str = "png"
    dpi: int = 150
    show_progress: bool = False


@dataclass
class ConversionResult:
    """Result of a PDF to Markdown conversion."""

    markdown: str
    images: dict[str, bytes] = field(default_factory=dict)
    page_count: int = 0
    source_path: Path | None = None


@runtime_checkable
class ConverterBackend(Protocol):
    """Protocol for PDF conversion backends."""

    @property
    def name(self) -> str:
        """Backend identifier."""
        ...

    def is_available(self) -> bool:
        """Check if the backend dependencies are installed."""
        ...

    def convert(self, pdf_path: Path, options: ConversionOptions) -> ConversionResult:
        """Convert a PDF file to Markdown."""
        ...
