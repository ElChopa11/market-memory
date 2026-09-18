"""Phase 5a output-contract template matches Principal OUTPUT CONTRACT."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TEMPLATE = ROOT / "templates" / "output-contract.md"

REQUIRED_HEADINGS = (
    "## HEADER",
    "## TAPE",
    "## WHAT CHANGED",
    "## TRADE IDEAS (intent-only)",
    "## QUANT NOTE",
    "## SKEPTIC FLAGS",
    "## RISK STATUS",
    "## BOOK",
    "## DATA GAPS",
    "## Writer hard rules",
)


def test_output_contract_has_principal_sections_and_hard_rules() -> None:
    text = TEMPLATE.read_text(encoding="utf-8")
    for heading in REQUIRED_HEADINGS:
        assert heading in text, heading
    assert "intent-only" in text
    assert "never invent" in text.lower()
    assert "as_of_knowledge" in text
    assert "self-approve" in text.lower()
    assert "BLOCK is terminal" in text.replace("**", "")
    assert "FAIL return" in text
    assert "FAIL archive" in text
    assert "live.yaml" in text
