"""Stub packages import and stay inert."""

from __future__ import annotations

import mm_backtest
import mm_briefing
import mm_common
import mm_execution
import mm_ingest
import mm_lab_cli
import mm_memory
import mm_paper
import mm_provenance
import mm_research_kit
import mm_risk
import mm_unicorn


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
    ):
        assert mod.__phase__ == 0
        assert mod.LIVE_TRADING_ENABLED is False


def test_execution_stub_has_no_signing_surface() -> None:
    assert not hasattr(mm_execution, "sign")
    assert not hasattr(mm_execution, "submit_order")
    assert not hasattr(mm_execution, "private_key")
