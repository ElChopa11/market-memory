"""Two triggers on one Sydney Morning anchor keep two completion records and one DM.

db3b106 replaced grok.sydney_morning__20260924T203000Z.json because the writer
keyed the file on the anchor and overwrote when the new status rank was >= the
old rank. Both fires were ``late``. The first run_id disappeared from the tree.
"""

from __future__ import annotations

import fnmatch
import json
from datetime import datetime, timezone
from pathlib import Path

from mm_desks.completions import completion_filename, load_disk_completions, record_cli_completion
from mm_desks.deliver_receipt import ALREADY_DELIVERED, attempt_deliver

UTC = timezone.utc
ROOT = Path(__file__).resolve().parents[2]
ROUTINE = "grok.sydney_morning"
FIRST_RUN = "actions-b1-36071921289"
SECOND_RUN = "actions-b1-36078428152"
# Thursday 24 Sep 2026 20:31 UTC is Friday 06:31 AEST, the catalog 06:30 anchor.
FIRED_FIRST = datetime(2026, 9, 24, 23, 17, 7, tzinfo=UTC)
FIRED_SECOND = datetime(2026, 9, 25, 0, 38, 10, tzinfo=UTC)
SENT_STDOUT = json.dumps({"reason": "ok", "sent": True, "source": "lab.deliver"})


def _send(calls: list[str]):
    def _inner() -> tuple[int, str]:
        calls.append("telegram")
        return 0, SENT_STDOUT

    return _inner


def test_two_triggers_keep_distinct_rows_and_one_dm(tmp_path: Path) -> None:
    dest = tmp_path / "completions"
    first = record_cli_completion(
        root=ROOT,
        routine_id=ROUTINE,
        fired_at=FIRED_FIRST,
        run_id=FIRST_RUN,
        exit_status=0,
        cli="lab schedule heartbeat (actions-b1)",
        source="github.actions",
        persist_db=False,
        completions_dir=dest,
    )
    assert first.scheduled_anchor_ts == datetime(2026, 9, 24, 20, 30, tzinfo=UTC)
    assert first.status == "late"
    first_path = dest / completion_filename(first)
    assert first_path.is_file()
    first_bytes = first_path.read_bytes()
    assert FIRST_RUN.encode() in first_bytes

    second = record_cli_completion(
        root=ROOT,
        routine_id=ROUTINE,
        fired_at=FIRED_SECOND,
        run_id=SECOND_RUN,
        exit_status=0,
        cli="lab schedule heartbeat (actions-b1)",
        source="github.actions",
        persist_db=False,
        completions_dir=dest,
    )
    assert second.scheduled_anchor_ts == first.scheduled_anchor_ts
    second_path = dest / completion_filename(second)
    assert second_path != first_path
    assert second_path.is_file()
    assert first_path.read_bytes() == first_bytes

    rows = load_disk_completions(dest)
    by_run = {row.run_id: row for row in rows}
    assert set(by_run) == {FIRST_RUN, SECOND_RUN}
    assert by_run[FIRST_RUN].delta_seconds == first.delta_seconds
    assert by_run[SECOND_RUN].fired_at_ts == FIRED_SECOND

    # Actions commit-back globs this shape. The run_id suffix must still match.
    rel = f"ops/reports/scheduler/completions/{first_path.name}"
    assert fnmatch.fnmatch(rel, "ops/reports/scheduler/completions/grok.sydney_morning__*.json")

    calls: list[str] = []
    delivered = attempt_deliver(
        completions_dir=dest,
        routine_id=ROUTINE,
        scheduled_anchor_ts=first.scheduled_anchor_ts,
        run_id=FIRST_RUN,
        send=_send(calls),
        delivered_at=FIRED_FIRST,
    )
    assert delivered.outcome == "sent"
    assert delivered.telegram is True
    assert calls == ["telegram"]
    assert delivered.receipt_path is not None
    assert json.loads(delivered.receipt_path.read_text(encoding="utf-8"))["run_id"] == FIRST_RUN

    calls.clear()
    again = attempt_deliver(
        completions_dir=dest,
        routine_id=ROUTINE,
        scheduled_anchor_ts="2026-09-24T20:30:00Z",
        run_id=SECOND_RUN,
        send=_send(calls),
        delivered_at=FIRED_SECOND,
    )
    assert again.outcome == ALREADY_DELIVERED
    assert again.telegram is False
    assert calls == []
    assert first_path.read_bytes() == first_bytes
    assert json.loads(delivered.receipt_path.read_text(encoding="utf-8"))["run_id"] == FIRST_RUN


def test_legacy_anchor_file_is_not_replaced(tmp_path: Path) -> None:
    dest = tmp_path / "completions"
    dest.mkdir()
    legacy = dest / "grok.sydney_morning__20260924T203000Z.json"
    legacy.write_text(
        json.dumps({"routine_id": ROUTINE, "run_id": FIRST_RUN, "status": "late"}) + "\n",
        encoding="utf-8",
    )
    before = legacy.read_bytes()
    record_cli_completion(
        root=ROOT,
        routine_id=ROUTINE,
        fired_at=FIRED_SECOND,
        run_id=SECOND_RUN,
        exit_status=0,
        source="github.actions",
        persist_db=False,
        completions_dir=dest,
    )
    assert legacy.read_bytes() == before
    names = sorted(path.name for path in dest.glob("*.json"))
    assert "grok.sydney_morning__20260924T203000Z.json" in names
    assert any(SECOND_RUN in name for name in names)


def test_same_run_id_retry_does_not_rewrite(tmp_path: Path) -> None:
    dest = tmp_path / "completions"
    record_cli_completion(
        root=ROOT,
        routine_id=ROUTINE,
        fired_at=FIRED_FIRST,
        run_id=FIRST_RUN,
        exit_status=0,
        source="github.actions",
        persist_db=False,
        completions_dir=dest,
    )
    path = next(dest.glob("*.json"))
    before = path.read_bytes()
    record_cli_completion(
        root=ROOT,
        routine_id=ROUTINE,
        fired_at=FIRED_SECOND,
        run_id=FIRST_RUN,
        exit_status=0,
        source="github.actions",
        persist_db=False,
        completions_dir=dest,
    )
    assert path.read_bytes() == before
    assert list(dest.glob("*.json")) == [path]


def test_restored_first_trigger_survives_next_to_the_overwritten_legacy_file() -> None:
    """db3b106 left only the second trigger on the anchor-keyed path."""
    directory = ROOT / "ops" / "reports" / "scheduler" / "completions"
    legacy = json.loads((directory / "grok.sydney_morning__20260924T203000Z.json").read_text(encoding="utf-8"))
    restored = json.loads(
        (directory / f"grok.sydney_morning__20260924T203000Z__{FIRST_RUN}.json").read_text(encoding="utf-8")
    )
    assert legacy["run_id"] == SECOND_RUN
    assert legacy["delta_seconds"] == 14890
    assert restored["run_id"] == FIRST_RUN
    assert restored["delta_seconds"] == 10027
    assert restored["fired_at_ts"].startswith("2026-09-24T23:17:07")
    assert restored["scheduled_anchor_ts"] == legacy["scheduled_anchor_ts"]
