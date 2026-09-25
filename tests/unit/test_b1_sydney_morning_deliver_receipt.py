"""Sydney Morning deliver receipt: first writer wins on scheduled_anchor.

No live Telegram. ``send`` is a stand-in for ``lab deliver pack`` stdout + exit code.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from mm_desks.completions import completion_filename, load_disk_completions
from mm_desks.deliver_receipt import (
    ALREADY_DELIVERED,
    NOT_SENT,
    PROCEED,
    accept_delivery,
    assert_receipt_committable,
    attempt_deliver,
    decide_deliver,
    deliver_sent,
    receipt_filename,
    validate_receipt_payload,
    write_deliver_receipt,
)
from mm_desks.scheduler import Completion

UTC = timezone.utc
ROUTINE = "grok.sydney_morning"
ANCHOR_A = "2026-09-23T20:30:00+00:00"
ANCHOR_A_Z = "2026-09-23T20:30:00Z"
ANCHOR_B = "2026-09-24T20:30:00+00:00"
SENT_STDOUT = json.dumps({"reason": "ok", "sent": True, "source": "lab.deliver"}, indent=2)
FAILED_STDOUT = json.dumps({"reason": "missing_token", "sent": False, "source": "lab.deliver"}, indent=2)


def _send_ok(calls: list[str]):
    def _send() -> tuple[int, str]:
        calls.append("telegram")
        return 0, SENT_STDOUT

    return _send


def _send_fail(calls: list[str], *, returncode: int = 2, stdout: str = FAILED_STDOUT):
    def _send() -> tuple[int, str]:
        calls.append("telegram")
        return returncode, stdout

    return _send


def test_second_deliver_same_anchor_skips_telegram(tmp_path: Path) -> None:
    completions = tmp_path / "completions"
    calls: list[str] = []
    first = attempt_deliver(
        completions_dir=completions,
        routine_id=ROUTINE,
        scheduled_anchor_ts=ANCHOR_A,
        run_id="actions-b1-1",
        send=_send_ok(calls),
        delivered_at=datetime(2026, 9, 24, 20, 31, tzinfo=UTC),
    )
    assert first.outcome == "sent"
    assert first.telegram is True
    assert first.receipt_created is True
    assert first.receipt_path is not None and first.receipt_path.is_file()

    calls.clear()
    second = attempt_deliver(
        completions_dir=completions,
        routine_id=ROUTINE,
        scheduled_anchor_ts=ANCHOR_A_Z,
        run_id="actions-b1-2",
        send=_send_ok(calls),
    )
    assert second.outcome == ALREADY_DELIVERED
    assert second.telegram is False
    assert calls == []
    assert decide_deliver(completions, ROUTINE, ANCHOR_A_Z) == ALREADY_DELIVERED
    body = json.loads(first.receipt_path.read_text(encoding="utf-8"))
    assert body["run_id"] == "actions-b1-1"
    assert body["sent"] is True
    assert body["scheduled_anchor_ts"].startswith("2026-09-23T20:30:00")


def test_failed_send_writes_no_receipt(tmp_path: Path) -> None:
    completions = tmp_path / "completions"
    calls: list[str] = []
    failed = attempt_deliver(
        completions_dir=completions,
        routine_id=ROUTINE,
        scheduled_anchor_ts=ANCHOR_A,
        run_id="actions-b1-fail",
        send=_send_fail(calls),
    )
    assert failed.outcome == NOT_SENT
    assert failed.telegram is True
    assert failed.receipt_path is None
    assert failed.receipt_created is False
    assert list(completions.rglob("*.json")) == []
    assert decide_deliver(completions, ROUTINE, ANCHOR_A) == PROCEED

    path, created = write_deliver_receipt(
        completions_dir=completions,
        routine_id=ROUTINE,
        scheduled_anchor_ts=ANCHOR_A,
        run_id="actions-b1-fail",
        sent=False,
    )
    assert path is None and created is False
    assert list(completions.rglob("*.json")) == []

    # Exit 0 with sent false, and sent true with a nonzero exit, both leave the anchor open.
    for rc, stdout in ((0, FAILED_STDOUT), (2, SENT_STDOUT), (0, "not json")):
        assert accept_delivery(stdout, rc) is False
        again = attempt_deliver(
            completions_dir=completions,
            routine_id=ROUTINE,
            scheduled_anchor_ts=ANCHOR_A,
            run_id="actions-b1-fail",
            send=_send_fail(calls, returncode=rc, stdout=stdout),
        )
        assert again.outcome == NOT_SENT
    assert list(completions.rglob("*.json")) == []
    assert deliver_sent('{"sent": "true"}') is False
    assert deliver_sent(SENT_STDOUT) is True


def test_different_anchors_do_not_share_a_receipt(tmp_path: Path) -> None:
    completions = tmp_path / "completions"
    calls: list[str] = []
    first = attempt_deliver(
        completions_dir=completions,
        routine_id=ROUTINE,
        scheduled_anchor_ts=ANCHOR_A,
        run_id="actions-b1-a",
        send=_send_ok(calls),
        delivered_at=datetime(2026, 9, 24, 20, 31, tzinfo=UTC),
    )
    assert first.receipt_created is True
    calls.clear()
    second = attempt_deliver(
        completions_dir=completions,
        routine_id=ROUTINE,
        scheduled_anchor_ts=ANCHOR_B,
        run_id="actions-b1-b",
        send=_send_ok(calls),
        delivered_at=datetime(2026, 9, 25, 20, 31, tzinfo=UTC),
    )
    assert second.outcome == "sent"
    assert second.telegram is True
    assert calls == ["telegram"]
    assert first.receipt_path != second.receipt_path
    assert first.receipt_path is not None and second.receipt_path is not None
    assert first.receipt_path.name != second.receipt_path.name
    assert decide_deliver(completions, ROUTINE, ANCHOR_A) == ALREADY_DELIVERED
    assert json.loads(second.receipt_path.read_text(encoding="utf-8"))["run_id"] == "actions-b1-b"


def test_receipt_filename_matches_completion_anchor_token() -> None:
    anchor = datetime(2026, 9, 23, 20, 30, tzinfo=UTC)
    record = Completion(
        routine_id=ROUTINE,
        run_id="r",
        scheduled_anchor_ts=anchor,
        fired_at_ts=anchor,
        delta_seconds=0,
        status="ok",
        as_of_knowledge=anchor,
    )
    token = "20260923T203000Z"
    assert completion_filename(record) == f"{ROUTINE}__{token}__r.json"
    assert token in completion_filename(record)
    assert receipt_filename(ROUTINE, ANCHOR_A) == f"{ROUTINE}__{token}.deliver.json"
    assert receipt_filename(ROUTINE, ANCHOR_A_Z) == receipt_filename(ROUTINE, ANCHOR_A)


def test_receipt_is_not_a_completion_row(tmp_path: Path) -> None:
    completions = tmp_path / "completions"
    completions.mkdir()
    anchor = "2026-09-23T20:30:00+00:00"
    (completions / f"{ROUTINE}__20260923T203000Z.json").write_text(
        json.dumps(
            {
                "routine_id": ROUTINE,
                "run_id": "stamp-1",
                "scheduled_anchor_ts": anchor,
                "fired_at_ts": "2026-09-23T20:31:00+00:00",
                "delta_seconds": 60,
                "status": "ok",
                "as_of_knowledge": "2026-09-23T20:31:00+00:00",
                "source": "test",
            }
        ),
        encoding="utf-8",
    )
    path, created = write_deliver_receipt(
        completions_dir=completions,
        routine_id=ROUTINE,
        scheduled_anchor_ts=anchor,
        run_id="actions-b1-1",
        sent=True,
        delivered_at=datetime(2026, 9, 24, 20, 32, tzinfo=UTC),
    )
    assert created is True and path is not None
    assert path.parent.name == "receipts"
    rows = load_disk_completions(completions)
    assert len(rows) == 1
    assert rows[0].run_id == "stamp-1"
    assert rows[0].status == "ok"


def test_first_writer_is_not_replaced(tmp_path: Path) -> None:
    completions = tmp_path / "completions"
    when = datetime(2026, 9, 24, 20, 31, tzinfo=UTC)
    path, created = write_deliver_receipt(
        completions_dir=completions,
        routine_id=ROUTINE,
        scheduled_anchor_ts=ANCHOR_A,
        run_id="first",
        sent=True,
        delivered_at=when,
    )
    assert created is True and path is not None
    again, created_again = write_deliver_receipt(
        completions_dir=completions,
        routine_id=ROUTINE,
        scheduled_anchor_ts=ANCHOR_A_Z,
        run_id="second",
        sent=True,
        delivered_at=datetime(2026, 9, 24, 22, 31, tzinfo=UTC),
    )
    assert created_again is False
    assert again == path
    assert json.loads(path.read_text(encoding="utf-8"))["run_id"] == "first"


def test_corrupt_receipt_does_not_send(tmp_path: Path) -> None:
    completions = tmp_path / "completions"
    path_dir = completions / "receipts"
    path_dir.mkdir(parents=True)
    name = receipt_filename(ROUTINE, ANCHOR_A)
    (path_dir / name).write_text("{not json", encoding="utf-8")
    calls: list[str] = []
    with pytest.raises(ValueError, match="not usable"):
        attempt_deliver(
            completions_dir=completions,
            routine_id=ROUTINE,
            scheduled_anchor_ts=ANCHOR_A,
            run_id="actions-b1-x",
            send=_send_ok(calls),
        )
    assert calls == []


def test_receipt_commit_scope(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    completions = repo / "ops" / "reports" / "scheduler" / "completions"
    path, created = write_deliver_receipt(
        completions_dir=completions,
        routine_id=ROUTINE,
        scheduled_anchor_ts=ANCHOR_A,
        run_id="actions-b1-1",
        sent=True,
        delivered_at=datetime(2026, 9, 24, 20, 31, tzinfo=UTC),
    )
    assert created is True and path is not None
    rel = assert_receipt_committable(path, repo_root=repo)
    assert rel == f"ops/reports/scheduler/completions/receipts/{ROUTINE}__20260923T203000Z.deliver.json"
    body = json.loads(path.read_text(encoding="utf-8"))
    assert body["sent"] is True
    assert "telegram" not in json.dumps(body).lower()

    outside = repo / "ops" / "reports" / "scheduler" / "completions" / path.name
    outside.write_text(path.read_text(encoding="utf-8"), encoding="utf-8")
    with pytest.raises(ValueError, match="outside"):
        assert_receipt_committable(outside, repo_root=repo)


def test_receipt_rejects_secret_material() -> None:
    raw = {
        "kind": "deliver_receipt",
        "routine_id": ROUTINE,
        "scheduled_anchor_ts": ANCHOR_A,
        "run_id": "has-private_key",
        "sent": True,
        "delivered_at_ts": "2026-09-24T20:31:00+00:00",
        "source": "github.actions",
    }
    with pytest.raises(ValueError, match="secret-like"):
        validate_receipt_payload(raw)
