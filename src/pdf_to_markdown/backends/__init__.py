"""Backend registry and factory."""

from __future__ import annotations

from pdf_to_markdown.converter import ConverterBackend


def get_backend(engine: str = "pymupdf") -> ConverterBackend:
    """Return a backend instance by name.

    Args:
        engine: Backend name ("pymupdf" or "marker").

    Raises:
        ValueError: If the engine name is unknown.
        RuntimeError: If the requested backend is not available.
    """
    if engine == "pymupdf":
        from pdf_to_markdown.backends.pymupdf import PyMuPDFBackend

        backend = PyMuPDFBackend()
    elif engine == "marker":
        from pdf_to_markdown.backends.marker import MarkerBackend

        backend = MarkerBackend()
    else:
        raise ValueError(f"Unknown engine: {engine!r}. Choose 'pymupdf' or 'marker'.")

    if not backend.is_available():
        raise RuntimeError(
            f"Backend {engine!r} is not available. "
            f"Install the required dependencies."
        )
    return backend
