"""Phase 6f adversarial PIT: future scorecard packs stay invisible when decay attaches pairs."""

from __future__ import annotations

from pathlib import Path

from mm_desks.decay import run_decay_from_fixture
from mm_quant.scorecard import NOT_COMPARABLE

ROOT = Path(__file__).resolve().parents[2]
SCORECARD = ROOT / "tests" / "fixtures" / "phase6f" / "scorecard.json"


def test_decay_attached_scorecard_ignores_packs_after_as_of_knowledge() -> None:
    result = run_decay_from_fixture(SCORECARD, repo_root=ROOT)
    ids = set()
    for row in result.payload["scorecard_pairs"]:
        ids.add(row["left_id"])
        ids.add(row["right_id"])
    assert "FUTURE-PREOPEN-20260919" not in ids
    tagged = [
        row
        for row in result.payload["scorecard_pairs"]
        if row["verdict"] == NOT_COMPARABLE
    ]
    assert tagged
    for row in tagged:
        assert row["completeness_delta"] is None
        assert row["hash_identity"] is None
        assert row["comparable"] is False
