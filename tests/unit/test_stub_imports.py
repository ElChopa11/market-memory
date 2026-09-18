"""Phase 1 packages stay hard-gated; no signing surface."""

from __future__ import annotations

from pathlib import Path

import mm_backtest
import mm_briefing
import mm_common
import mm_delivery
import mm_desks
import mm_execution
import mm_ingest
import mm_lab_cli
import mm_memory
import mm_paper
import mm_provenance
import mm_quant
import mm_research_kit
import mm_risk
import mm_source_health
import mm_unicorn

ROOT = Path(__file__).resolve().parents[2]
PHASE5 = {mm_desks, mm_quant, mm_delivery}
PHASE4 = {mm_memory, mm_backtest, mm_paper, mm_lab_cli, mm_source_health}
PHASE3 = {mm_briefing}
PHASE1 = {mm_ingest, mm_provenance}
PHASE2 = {mm_common, mm_research_kit}
FORBIDDEN_SNIPPETS = (
    "sign_l1_action",
    "private_key",
    "API_WALLET",
    "hl_trade",
    "submit_order",
    "wallet.json",
)


def test_stubs_import_and_are_hard_gated() -> None:
    for mod in (
        mm_common,
        mm_memory,
        mm_ingest,
        mm_provenance,
        mm_research_kit,
        mm_backtest,
        mm_risk,
        mm_paper,
        mm_execution,
        mm_briefing,
        mm_unicorn,
        mm_lab_cli,
        mm_source_health,
        mm_desks,
        mm_quant,
        mm_delivery,
    ):
        assert mod.LIVE_TRADING_ENABLED is False
        if mod in PHASE5:
            expected_phase = 5
        elif mod in PHASE4:
            expected_phase = 4
        elif mod in PHASE3:
            expected_phase = 3
        elif mod in PHASE2:
            expected_phase = 2
        elif mod in PHASE1:
            expected_phase = 1
        else:
            expected_phase = 0
        assert mod.__phase__ == expected_phase, mod.__name__


def test_execution_stub_has_no_signing_surface() -> None:
    assert not hasattr(mm_execution, "sign")
    assert not hasattr(mm_execution, "submit_order")
    assert not hasattr(mm_execution, "private_key")


def test_ingest_has_no_exchange_or_signing_module() -> None:
    ingest_root = ROOT / "packages" / "ingest"
    assert not (ingest_root / "src" / "mm_ingest" / "hl_trade.py").exists()
    assert not (ingest_root / "src" / "mm_ingest" / "exchange.py").exists()
    blob = "\n".join(path.read_text(encoding="utf-8") for path in ingest_root.rglob("*.py"))
    for snippet in FORBIDDEN_SNIPPETS:
        assert snippet not in blob, snippet
    assert "FORBIDDEN_INFO_TYPES" in blob
