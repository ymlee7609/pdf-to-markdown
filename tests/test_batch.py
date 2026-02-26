"""Tests for batch processing."""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from pdf_to_markdown.backends.pymupdf import PyMuPDFBackend
from pdf_to_markdown.batch import BatchResult, convert_directory
from pdf_to_markdown.converter import ConversionOptions

from .conftest import SMALL_PDF


@pytest.fixture
def backend() -> PyMuPDFBackend:
    return PyMuPDFBackend()


class TestBatchResult:
    def test_default_results_list(self) -> None:
        br = BatchResult()
        assert br.results == []

    def test_provided_results_preserved(self) -> None:
        br = BatchResult(results=[(Path("a.pdf"), None)])
        assert len(br.results) == 1


class TestBatchConversion:
    def test_empty_directory(
        self, backend: PyMuPDFBackend, tmp_path: Path
    ) -> None:
        input_dir = tmp_path / "empty"
        input_dir.mkdir()
        output_dir = tmp_path / "output"

        result = convert_directory(
            input_dir, output_dir, backend, ConversionOptions(extract_images=False)
        )
        assert result.total == 0
        assert result.success == 0
        assert result.failed == 0

    def test_single_file_batch(
        self, backend: PyMuPDFBackend, tmp_path: Path
    ) -> None:
        if not SMALL_PDF.exists():
            pytest.skip("Sample PDF not available")

        input_dir = tmp_path / "input"
        input_dir.mkdir()
        shutil.copy2(SMALL_PDF, input_dir / "test.pdf")

        output_dir = tmp_path / "output"
        result = convert_directory(
            input_dir, output_dir, backend, ConversionOptions(extract_images=False)
        )
        assert result.total == 1
        assert result.success == 1
        assert result.failed == 0

        md_files = list(output_dir.glob("*.md"))
        assert len(md_files) == 1

    def test_verbose_output(
        self,
        backend: PyMuPDFBackend,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        if not SMALL_PDF.exists():
            pytest.skip("Sample PDF not available")

        input_dir = tmp_path / "input"
        input_dir.mkdir()
        shutil.copy2(SMALL_PDF, input_dir / "test.pdf")

        output_dir = tmp_path / "output"
        convert_directory(
            input_dir,
            output_dir,
            backend,
            ConversionOptions(extract_images=False),
            verbose=True,
        )
        captured = capsys.readouterr()
        assert "Converting:" in captured.err

    def test_handles_bad_file(
        self, backend: PyMuPDFBackend, tmp_path: Path
    ) -> None:
        input_dir = tmp_path / "input"
        input_dir.mkdir()
        (input_dir / "bad.pdf").write_text("not a pdf")

        output_dir = tmp_path / "output"
        result = convert_directory(
            input_dir, output_dir, backend, ConversionOptions(extract_images=False)
        )
        assert result.total == 1
        assert result.failed == 1
        assert result.success == 0

    def test_verbose_failure_output(
        self,
        backend: PyMuPDFBackend,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        input_dir = tmp_path / "input"
        input_dir.mkdir()
        (input_dir / "bad.pdf").write_text("not a pdf")

        output_dir = tmp_path / "output"
        convert_directory(
            input_dir,
            output_dir,
            backend,
            ConversionOptions(extract_images=False),
            verbose=True,
        )
        captured = capsys.readouterr()
        assert "FAILED:" in captured.err
