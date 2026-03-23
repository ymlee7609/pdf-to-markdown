"""Tests for the CLI module."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

from pdf_to_markdown.cli import build_parser, main, parse_pages
from pdf_to_markdown.output import write_result


class TestParsePages:
    def test_single_page(self) -> None:
        assert parse_pages("0") == [0]

    def test_multiple_pages(self) -> None:
        assert parse_pages("0,3,5") == [0, 3, 5]

    def test_page_range(self) -> None:
        assert parse_pages("2-5") == [2, 3, 4, 5]

    def test_mixed(self) -> None:
        assert parse_pages("0,5-7,10") == [0, 5, 6, 7, 10]

    def test_deduplicate(self) -> None:
        assert parse_pages("1,1,2") == [1, 2]

    def test_whitespace(self) -> None:
        assert parse_pages(" 1 , 3 - 5 ") == [1, 3, 4, 5]

    def test_invalid_range(self) -> None:
        with pytest.raises(ValueError, match="Invalid page range"):
            parse_pages("5-2")

    def test_invalid_format(self) -> None:
        with pytest.raises(ValueError):
            parse_pages("abc")

    def test_empty_string(self) -> None:
        assert parse_pages("") == []


class TestBuildParser:
    def test_minimal_args(self) -> None:
        parser = build_parser()
        args = parser.parse_args(["input.pdf"])
        assert args.input == Path("input.pdf")
        assert args.output is None
        assert args.engine == "pymupdf"

    def test_all_args(self) -> None:
        parser = build_parser()
        args = parser.parse_args([
            "input.pdf",
            "-o", "output.md",
            "--engine", "marker",
            "--pages", "0-5",
            "--no-images",
            "--image-format", "jpg",
            "--dpi", "300",
            "--verbose",
        ])
        assert args.input == Path("input.pdf")
        assert args.output == Path("output.md")
        assert args.engine == "marker"
        assert args.pages == "0-5"
        assert args.no_images is True
        assert args.image_format == "jpg"
        assert args.dpi == 300
        assert args.verbose is True


class TestMainCLI:
    def test_nonexistent_file(self) -> None:
        code = main(["/nonexistent/file.pdf"])
        assert code == 1

    def test_invalid_engine(self) -> None:
        with pytest.raises(SystemExit):
            main(["input.pdf", "--engine", "unknown"])

    def test_invalid_pages(self) -> None:
        code = main(["input.pdf", "--pages", "5-2"])
        assert code == 1

    def test_convert_single_file(self, small_pdf: Path, tmp_output: Path) -> None:
        if not small_pdf.exists():
            pytest.skip("Sample PDF not available")

        out_file = tmp_output / "test.md"
        code = main([str(small_pdf), "-o", str(out_file), "--no-images"])
        assert code == 0
        assert out_file.exists()
        content = out_file.read_text(encoding="utf-8")
        assert len(content) > 0

    def test_convert_directory(self, sample_dir: Path, tmp_output: Path) -> None:
        if not sample_dir.exists():
            pytest.skip("Sample directory not available")

        import shutil

        test_dir = tmp_output / "input"
        test_dir.mkdir(parents=True)
        from .conftest import SMALL_PDF as small_path

        small = small_path
        if not small.exists():
            pytest.skip("Small sample PDF not available")
        shutil.copy2(small, test_dir / small.name)

        out_dir = tmp_output / "batch_out"
        code = main([str(test_dir), "-o", str(out_dir), "--no-images"])
        assert code == 0

        md_files = list(out_dir.glob("*.md"))
        assert len(md_files) == 1

    def test_verbose_single_file(self, small_pdf: Path, tmp_output: Path) -> None:
        if not small_pdf.exists():
            pytest.skip("Sample PDF not available")

        out_file = tmp_output / "verbose.md"
        code = main([str(small_pdf), "-o", str(out_file), "--no-images", "-v"])
        assert code == 0

    def test_verbose_split_output(self, small_pdf: Path, tmp_output: Path) -> None:
        if not small_pdf.exists():
            pytest.skip("Sample PDF not available")

        out_file = tmp_output / "verbose_split.md"
        code = main([str(small_pdf), "-o", str(out_file), "--no-images", "-v", "--split"])
        assert code == 0

    def test_convert_error_returns_1(self, tmp_path: Path) -> None:
        bad_pdf = tmp_path / "bad.pdf"
        bad_pdf.write_text("not a pdf")
        out_file = tmp_path / "out.md"
        code = main([str(bad_pdf), "-o", str(out_file)])
        assert code == 1

    def test_backend_runtime_error(self, tmp_path: Path) -> None:
        """Cover cli.py lines 132-134: get_backend raises RuntimeError."""
        pdf = tmp_path / "test.pdf"
        pdf.write_text("fake")

        with patch(
            "pdf_to_markdown.cli.get_backend",
            side_effect=RuntimeError("Backend unavailable"),
        ):
            code = main([str(pdf), "--engine", "pymupdf"])
        assert code == 1


class TestGetBackend:
    def test_get_pymupdf(self) -> None:
        from pdf_to_markdown.backends import get_backend

        backend = get_backend("pymupdf")
        assert backend.name == "pymupdf"

    def test_get_unknown_raises(self) -> None:
        from pdf_to_markdown.backends import get_backend

        with pytest.raises(ValueError, match="Unknown engine"):
            get_backend("nonexistent")

    def test_get_marker_unavailable(self) -> None:
        from pdf_to_markdown.backends import get_backend
        from pdf_to_markdown.backends.marker import _MARKER_AVAILABLE

        if _MARKER_AVAILABLE:
            pytest.skip("Marker is installed")
        with pytest.raises(RuntimeError, match="not available"):
            get_backend("marker")


class TestSplitFlags:
    """--split/--no-split CLI 플래그 테스트."""

    def test_split_flag_parsed(self) -> None:
        parser = build_parser()
        args = parser.parse_args(["input.pdf", "--split"])
        assert args.split is True
        assert args.no_split is False

    def test_no_split_flag_parsed(self) -> None:
        parser = build_parser()
        args = parser.parse_args(["input.pdf", "--no-split"])
        assert args.split is False
        assert args.no_split is True

    def test_no_flags_defaults(self) -> None:
        parser = build_parser()
        args = parser.parse_args(["input.pdf"])
        assert args.split is False
        assert args.no_split is False

    def test_mutually_exclusive(self) -> None:
        parser = build_parser()
        with pytest.raises(SystemExit):
            parser.parse_args(["input.pdf", "--split", "--no-split"])

    def test_split_passed_to_write_result(
        self, small_pdf: Path, tmp_output: Path,
    ) -> None:
        if not small_pdf.exists():
            pytest.skip("Sample PDF not available")

        out_file = tmp_output / "split_test.md"
        with patch("pdf_to_markdown.cli.write_result", wraps=write_result) as mock_wr:
            main([str(small_pdf), "-o", str(out_file), "--no-images", "--split"])
            mock_wr.assert_called_once()
            _, kwargs = mock_wr.call_args
            assert kwargs.get("force_split") is True

    def test_no_split_passed_to_write_result(
        self, small_pdf: Path, tmp_output: Path,
    ) -> None:
        if not small_pdf.exists():
            pytest.skip("Sample PDF not available")

        out_file = tmp_output / "nosplit_test.md"
        with patch("pdf_to_markdown.cli.write_result", wraps=write_result) as mock_wr:
            main([str(small_pdf), "-o", str(out_file), "--no-images", "--no-split"])
            mock_wr.assert_called_once()
            _, kwargs = mock_wr.call_args
            assert kwargs.get("force_split") is False


class TestMinChunkSize:
    """--min-chunk-size CLI 플래그 테스트."""

    def test_min_chunk_size_parsed(self) -> None:
        parser = build_parser()
        args = parser.parse_args(["input.pdf", "--min-chunk-size", "50000"])
        assert args.min_chunk_size == 50000

    def test_min_chunk_size_default(self) -> None:
        parser = build_parser()
        args = parser.parse_args(["input.pdf"])
        assert args.min_chunk_size == 0

    def test_min_chunk_size_passed_to_write_result(
        self, small_pdf: Path, tmp_output: Path,
    ) -> None:
        if not small_pdf.exists():
            pytest.skip("Sample PDF not available")

        out_file = tmp_output / "chunk_test.md"
        with patch("pdf_to_markdown.cli.write_result", wraps=write_result) as mock_wr:
            main([str(small_pdf), "-o", str(out_file), "--no-images", "--min-chunk-size", "50000"])
            mock_wr.assert_called_once()
            _, kwargs = mock_wr.call_args
            assert kwargs.get("min_chunk_size") == 50000


class TestMainModule:
    def test_main_module_importable(self) -> None:
        """Cover __main__.py import lines."""
        import pdf_to_markdown.__main__ as mod

        assert hasattr(mod, "main")

    def test_main_module_via_subprocess(self) -> None:
        """Cover __main__.py by running as subprocess."""
        result = subprocess.run(
            [sys.executable, "-m", "pdf_to_markdown", "--help"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert "pdf2md" in result.stdout or "Convert PDF" in result.stdout
