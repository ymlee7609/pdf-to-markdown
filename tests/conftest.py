"""Shared test fixtures."""

from __future__ import annotations

from pathlib import Path

import pytest

SAMPLE_DIR = Path(__file__).resolve().parent.parent / "sample"

_NOKIA_PDF = (
    "Nokia_Autonomous_Networks_What_is_the_current_state"
    "_and_how_to_move_forward__White_Paper_EN.pdf"
)
SMALL_PDF = SAMPLE_DIR / _NOKIA_PDF
MEDIUM_PDF = SAMPLE_DIR / "IG1339_Autonomous_Networks_L4_High_Value_Scenarios_v2.4.0.pdf"
KOREAN_PDF = SAMPLE_DIR / "MOAI-CustomGPT_예제50.pdf"
LARGE_PDF = SAMPLE_DIR / "1560737201_Manual_U9500H_User Guide.pdf"
STRESS_PDF_1 = (
    SAMPLE_DIR
    / "CCIE Routing and Switching v5.0 Official Cert Guide, Volume 1 (5th Edition).pdf"
)
STRESS_PDF_2 = (
    SAMPLE_DIR
    / "CCIE Routing and Switching v5.0 Official Cert Guide, Volume 2 (5th Edition).pdf"
)


@pytest.fixture
def small_pdf() -> Path:
    """Smallest sample PDF (~261K) for fast unit tests."""
    return SMALL_PDF


@pytest.fixture
def medium_pdf() -> Path:
    """Medium sample PDF (~1.4M) with tables and figures."""
    return MEDIUM_PDF


@pytest.fixture
def korean_pdf() -> Path:
    """Korean text PDF (~1.7M) for UTF-8 testing."""
    return KOREAN_PDF


@pytest.fixture
def sample_dir() -> Path:
    """Path to the sample directory."""
    return SAMPLE_DIR


@pytest.fixture
def tmp_output(tmp_path: Path) -> Path:
    """Temporary output directory."""
    return tmp_path / "output"
