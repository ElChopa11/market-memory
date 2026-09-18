"""Phase 6e adversarial PIT: future packs stay invisible; as_of_knowledge is the clock."""

from __future__ import annotations

from pathlib import Path

from mm_desks.scorecard import run_scorecard_from_fixture

ROOT = Path(__file__).resolve().parents[2]
PACKS = ROOT / "tests" / "fixtures" / "phase6e" / "packs.json"


def test_scorecard_ignores_packs_after_as_of_knowledge() -> None:
    result = run_scorecard_from_fixture(PACKS, repo_root=ROOT)
    ids = {p.pack_id for p in result.packs}
    assert "FUTURE-PREOPEN-20260919" not in ids
    for pair in result.pairs:
        assert "FUTURE-PREOPEN-20260919" not in {pair.left_id, pair.right_id}
    assert any("lookahead" in g for g in result.gaps)
