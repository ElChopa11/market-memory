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


def test_skeleton_packages_are_hard_gated() -> None:
    for mod in (mm_desks, mm_quant, mm_delivery):
        assert mod.LIVE_TRADING_ENABLED is False
        assert mod.__phase__ == 5
    assert mm_desks.CRYPTO_TIER == "3a"
    assert mm_desks.EQUITIES_TIER == "3b"
    assert mm_quant.FactorRegistry().names() == ()
    assert mm_delivery.SEND_ENABLED is False
    assert not hasattr(mm_delivery, "send")
    assert not hasattr(mm_desks, "polygon")
    assert not hasattr(mm_quant, "sign")
