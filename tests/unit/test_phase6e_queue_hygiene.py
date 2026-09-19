"""Phase 6e queue hygiene helpers: single-threaded READY→IN_PROGRESS; no auto-merge."""

from __future__ import annotations

from pathlib import Path

from mm_desks.queue import can_start, check_queue, refuse_forbidden
from mm_lab_cli.cli import main

ROOT = Path(__file__).resolve().parents[2]

MINIMAL = """
### IMP-100 — example ready

| Field | Value |
|---|---|
| **ID** | IMP-100 |
| **Priority** | P2 |
| **Type** | Desk product |
| **Desk** | Ops |
| **Owner** | Ops |
| **Problem** | example |
| **Evidence** | example |
| **Proposed outcome** | example |
| **Definition of done** | example |
| **Non-goals** | live trading |
| **Dependencies** | none |
| **Risk level** | Low |
| **Status** | READY |
| **PR** | — |
| **Lesson learned** | *(open)* |

### IMP-101 — example in progress

| Field | Value |
|---|---|
| **ID** | IMP-101 |
| **Priority** | P2 |
| **Type** | Desk product |
| **Desk** | Quant |
| **Owner** | Quant |
| **Problem** | example |
| **Evidence** | example |
| **Proposed outcome** | example |
| **Definition of done** | example |
| **Non-goals** | live trading |
| **Dependencies** | none |
| **Risk level** | Low |
| **Status** | IN_PROGRESS |
| **PR** | — |
| **Lesson learned** | *(open)* |

### SCHED-001 — incident

| Field | Value |
|---|---|
| **ID** | SCHED-001 |
| **Priority** | P1 |
| **Type** | Scheduler |
| **Desk** | Ops |
| **Owner** | Ops |
| **Problem** | miss |
| **Evidence** | miss |
| **Proposed outcome** | fix |
| **Definition of done** | verified |
| **Non-goals** | close early |
| **Dependencies** | none |
| **Risk level** | Medium |
| **Status** | OPEN |
| **PR** | — |
| **Lesson learned** | *(open)* |
"""

DUAL = MINIMAL.replace(
    "| **Status** | READY |",
    "| **Status** | IN_PROGRESS |",
    1,
)


def test_single_in_progress_is_ok_and_open_incident_is_not_a_slot() -> None:
    report = check_queue(MINIMAL)
    assert report.ok
    assert report.in_progress == ("IMP-101",)
    assert "SCHED-001" not in report.in_progress
    ok, reason = can_start("IMP-100", report)
    assert ok is False
    assert "IMP-101" in reason
    ok_incident, incident_reason = can_start("SCHED-001", report)
    assert ok_incident is False
    assert "incident" in incident_reason.lower()


def test_dual_in_progress_fails() -> None:
    report = check_queue(DUAL)
    assert not report.ok
    assert "IMP-100" in report.in_progress
    assert "IMP-101" in report.in_progress
    assert any("at most one" in err for err in report.errors)


def test_ready_may_start_when_slot_free() -> None:
    text = MINIMAL.replace("| **Status** | IN_PROGRESS |", "| **Status** | DONE |", 1)
    report = check_queue(text)
    assert report.ok
    assert report.in_progress == ()
    ok, reason = can_start("IMP-100", report)
    assert ok is True
    assert "does not write" in reason


def test_incident_eligible_ok_closed_requires_run_id() -> None:
    eligible = MINIMAL.replace("| **Status** | OPEN |", "| **Status** | ELIGIBLE |", 1)
    report = check_queue(eligible)
    assert report.ok
    closed = MINIMAL.replace("| **Status** | OPEN |", "| **Status** | CLOSED |", 1)
    bad = check_queue(closed)
    assert not bad.ok
    assert any("run_id" in err for err in bad.errors)
    cited = closed.replace("| **Lesson learned** | *(open)* |", "| **Lesson learned** | closed cite run_id=fred-test |")
    ok_closed = check_queue(cited)
    assert ok_closed.ok


def test_refuses_auto_merge_and_waiver() -> None:
    assert refuse_forbidden("merge")
    assert refuse_forbidden("waive")
    assert refuse_forbidden("auto-merge")
    assert refuse_forbidden(None) is None


def test_lab_queue_check_on_repo(capsys) -> None:
    rc = main(["queue", "check", "--repo-root", str(ROOT)])
    payload = capsys.readouterr().out
    assert rc == 0
    assert "SCHED-001" in payload
    assert "BRIEF-TAG-20260918" in payload
    assert '"auto_merge": false' in payload
    assert '"auto_waive": false' in payload


def test_lab_queue_refuses_merge(capsys) -> None:
    rc = main(["queue", "merge", "--repo-root", str(ROOT)])
    err = capsys.readouterr().err
    assert rc == 2
    assert "auto-merge" in err or "refuses" in err
