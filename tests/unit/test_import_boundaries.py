"""Phase 5a import walls: opine packages vs execution; Intel vs opine."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import mm_delivery
import mm_desks
import mm_quant

ROOT = Path(__file__).resolve().parents[2]
CHECKER = ROOT / "scripts" / "check_import_boundaries.py"


def test_import_boundary_script_passes() -> None:
    completed = subprocess.run(
        [sys.executable, str(CHECKER)],
        check=False,
        capture_output=True,
        text=True,
        cwd=ROOT,
    )
    assert completed.returncode == 0, completed.stderr
    assert "import-boundary check passed" in completed.stdout


def test_ci_execution_import_grep_matches_statements_not_comments() -> None:
    """Same pattern as the pytest-and-lifecycle 'Opine packages cannot import mm_execution' step."""
    completed = subprocess.run(
        [
            "git",
            "grep",
            "-n",
            "-E",
            r"^[ \t]*(import mm_execution|from mm_execution)\b",
            "--",
            "packages/research_kit",
            "packages/desks",
            "packages/quant",
            "packages/delivery",
        ],
        check=False,
        capture_output=True,
        text=True,
        cwd=ROOT,
    )
    assert completed.returncode == 1, completed.stdout
    for name in ("research_kit", "desks", "quant", "delivery"):
        src = ROOT / "packages" / name / "src"
        for path in src.rglob("*.py"):
            text = path.read_text(encoding="utf-8")
            assert "import mm_execution" not in text, path
            assert "from mm_execution" not in text, path


def test_skeleton_packages_are_hard_gated() -> None:
    for mod in (mm_quant, mm_delivery):
        assert mod.LIVE_TRADING_ENABLED is False
        assert mod.__phase__ == 5
    assert mm_desks.LIVE_TRADING_ENABLED is False
    assert mm_desks.__phase__ == 6
    assert mm_desks.CRYPTO_TIER == "3a"
    assert mm_desks.EQUITIES_TIER == "3b"
    assert set(mm_quant.FactorRegistry().names()) == {
        "momentum_short",
        "momentum_long",
        "realised_vol_short",
        "realised_vol_long",
        "adx",
        "zscore",
        "funding_carry",
        "basis_carry",
        "relative_strength_btc",
        "relative_strength_sector",
        "breadth",
        "correlation_matrix",
        "beta",
    }
    assert mm_delivery.SEND_ENABLED is False
    assert hasattr(mm_delivery, "TelegramClient")
    assert hasattr(mm_delivery, "deliver")
    assert hasattr(mm_delivery, "prepare_payload")
    assert hasattr(mm_desks, "run_from_fixture")
    assert hasattr(mm_desks, "mesh_from_fixture")
    assert not hasattr(mm_desks, "polygon")
    assert not hasattr(mm_quant, "sign")
