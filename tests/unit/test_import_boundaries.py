"""Phase 5a import walls: opine packages vs execution; Intel vs opine."""

from __future__ import annotations

import importlib.util
import re
import subprocess
import sys
from pathlib import Path

import mm_delivery
import mm_desks
import mm_flow
import mm_macro
import mm_quant

ROOT = Path(__file__).resolve().parents[2]
CHECKER = ROOT / "scripts" / "check_import_boundaries.py"
EXECUTION_IMPORT_RE = re.compile(r"^[ \t]*(import mm_execution|from mm_execution)\b", re.MULTILINE)


def _load_checker():
    spec = importlib.util.spec_from_file_location("check_import_boundaries", CHECKER)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


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
    """CI git grep is statement-anchored. Comments mentioning mm_execution must not match."""
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
            "packages/flow",
            "packages/macro",
        ],
        check=False,
        capture_output=True,
        text=True,
        cwd=ROOT,
    )
    assert completed.returncode == 1, completed.stdout
    comment_src = ROOT / "packages" / "desks" / "src" / "mm_desks" / "roster.py"
    text = comment_src.read_text(encoding="utf-8")
    assert "mm_execution" in text
    assert EXECUTION_IMPORT_RE.search(text) is None


def test_comment_containing_mm_execution_does_not_fail_ast_or_grep() -> None:
    checker = _load_checker()
    source = '''# operators must not import mm_execution or from mm_execution
"""docs: never import mm_execution"""
x = "from mm_execution import sign"
'''
    assert checker.execution_imports_from_source(source) == set()
    assert EXECUTION_IMPORT_RE.search(source) is None


def test_real_mm_execution_import_is_detected() -> None:
    checker = _load_checker()
    assert checker.execution_imports_from_source("import mm_execution\n") == {"mm_execution"}
    assert checker.execution_imports_from_source("from mm_execution import foo\n") == {"mm_execution"}
    assert EXECUTION_IMPORT_RE.search("import mm_execution\n")
    assert EXECUTION_IMPORT_RE.search("from mm_execution.foo import bar\n")
    assert EXECUTION_IMPORT_RE.search("  import mm_execution as x\n")
    assert EXECUTION_IMPORT_RE.search("# import mm_execution\n") is None


def test_skeleton_packages_are_hard_gated() -> None:
    for mod in (mm_quant, mm_delivery):
        assert mod.LIVE_TRADING_ENABLED is False
        assert mod.__phase__ == 5
    assert mm_flow.LIVE_TRADING_ENABLED is False
    assert mm_flow.__phase__ == 6
    assert mm_macro.LIVE_TRADING_ENABLED is False
    assert mm_macro.__phase__ == 6
    assert mm_desks.LIVE_TRADING_ENABLED is False
    assert mm_desks.__phase__ == 6
    assert mm_desks.CRYPTO_TIER == "3a"
    assert mm_desks.EQUITIES_TIER == "3b"
    assert tuple(mm_desks.PIPELINE) == ("intel", "research", "quant", "ic_risk", "ops")
    assert tuple(mm_desks.PUBLISHING_DESKS) == mm_desks.PIPELINE
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
