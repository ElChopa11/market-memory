"""SRC-FRED-MISSING-ENV OPEN under environment-propagation; IMP-022 DONE; persist pack retained."""

from __future__ import annotations

import json
from pathlib import Path

from mm_desks.queue import load_queue

ROOT = Path(__file__).resolve().parents[2]
CLOSE_JSON = (
    ROOT
    / "ops"
    / "reports"
    / "incident-closures"
    / "20260919-101938-aest-fred-fullstack-close.json"
)
CORRECTION_MD = (
    ROOT
    / "ops"
    / "reports"
    / "incident-closures"
    / "20260919-environment-audit-record-correction.md"
)
UNGATED_MD = ROOT / "ops" / "reports" / "20260919-telegram-ungated-pre-hybrid.md"
RUN_ID = "fred-fullstack-20260919-101938-aest"


def test_src_fred_reopened_env_propagation_imp022_done() -> None:
    queue = (ROOT / "ops" / "improvement-queue.md").read_text(encoding="utf-8")
    board_lines = [line for line in queue.splitlines() if line.startswith("| IMP-")]
    assert any("IMP-022" in line and "DONE" in line for line in board_lines)
    assert any(RUN_ID in line for line in board_lines if "IMP-022" in line)
    assert not any("IMP-022" in line and "IN_PROGRESS" in line for line in board_lines)
    assert any("IMP-024" in line and "DONE" in line for line in board_lines)
    assert not any("IMP-024" in line and "IN_PROGRESS" in line for line in board_lines)
    assert any("IMP-047" in line and "DONE" in line for line in board_lines)
    assert any("IMP-040" in line and "DONE" in line for line in board_lines)
    assert "`IN_PROGRESS` count: **0**" in queue
    for item_id in ("IMP-023", "IMP-035"):
        assert any(item_id in line and "READY" in line for line in board_lines), item_id
        assert not any(item_id in line and "IN_PROGRESS" in line for line in board_lines)
    for item_id in ("IMP-036", "IMP-037", "IMP-038"):
        assert any(item_id in line and "BACKLOG" in line for line in board_lines), item_id
        assert not any(item_id in line and "IN_PROGRESS" in line for line in board_lines)
    assert "| **ID** | SRC-FRED-MISSING-ENV |" in queue
    assert RUN_ID in queue
    assert "Closed on full-stack persist run_id" in queue
    assert "environment-propagation" in queue
    fred_block = queue.split("### SRC-FRED-MISSING-ENV", 1)[1].split("### ", 1)[0]
    assert "| **Status** | OPEN |" in fred_block
    incident_lines = [line for line in queue.splitlines() if line.startswith("| SRC-FRED-MISSING-ENV |")]
    assert incident_lines
    assert any("OPEN" in line and "environment-propagation" in line for line in incident_lines)
    assert not any("| CLOSED |" in line for line in incident_lines)
    for item_id in (
        "SCHED-001",
        "BRIEF-TAG-20260918",
        "SRC-STOOQ-404",
        "SRC-OBJECT-STORE",
        "TG-UNGATED-PRE-HYBRID",
    ):
        assert item_id in queue
    assert "DOWN SERVICE" in queue
    assert "**ungated**" in queue
    assert queue.count("| **Status** | OPEN |") == 6
    live = (ROOT / "config" / "risk" / "environments" / "live.yaml").read_text(encoding="utf-8")
    assert "live_trading_enabled: false" in live
    report = load_queue(ROOT)
    assert report.ok, report.errors
    assert report.in_progress == ()
    assert report.auto_merge is False
    assert report.auto_waive is False
    public = report.as_public_dict()
    assert "SRC-STOOQ-404" in public["open_incidents"]
    assert "SCHED-001" in public["open_incidents"]
    assert "BRIEF-TAG-20260918" in public["open_incidents"]
    assert "SRC-FRED-MISSING-ENV" in public["open_incidents"]
    assert "SRC-OBJECT-STORE" in public["open_incidents"]
    assert "TG-UNGATED-PRE-HYBRID" in public["open_incidents"]
    fred = next(item for item in report.items if item.item_id == "SRC-FRED-MISSING-ENV")
    assert fred.status == "OPEN"
    assert "environment-propagation" in " ".join(fred.fields.values()).lower()
    assert "run_id" in " ".join(fred.fields.values()).lower()
    obj = next(item for item in report.items if item.item_id == "SRC-OBJECT-STORE")
    assert obj.status == "OPEN"
    assert "DOWN SERVICE" in " ".join(obj.fields.values())
    ungated = next(item for item in report.items if item.item_id == "TG-UNGATED-PRE-HYBRID")
    assert ungated.status == "OPEN"
    blob = " ".join(ungated.fields.values())
    assert "ungated" in blob.lower()
    assert "22:02" in blob
    assert "00:03" in blob
    imp022 = next(item for item in report.items if item.item_id == "IMP-022")
    assert imp022.status == "DONE"
    assert RUN_ID in imp022.fields.get("Lesson learned", "")


def test_fred_close_pack_has_no_secrets_and_meets_criteria() -> None:
    assert CLOSE_JSON.is_file()
    pack = json.loads(CLOSE_JSON.read_text(encoding="utf-8"))
    assert pack["ticket"] == "SRC-FRED-MISSING-ENV"
    assert pack["run_ids"]["fullstack_close"] == RUN_ID
    assert pack["postgres_attached"] is True
    assert pack["ingest"]["no_db"] is False
    assert pack["ingest"]["created_rows"] == 5
    assert len(pack["observation_ids"]) == 5
    assert pack["latest_print"]["instrument"] == "US10Y"
    assert pack["latest_print"]["value"] == 4.94
    assert pack["source_health"]["fred"]["status"] == "ok"
    assert pack["source_health"]["fred"]["credentials_present"] == "yes"
    assert pack["source_health"]["fred"]["error_class"] == "none"
    assert pack["source_health"]["postgres"]["status"] == "ok"
    assert pack["eligible_vs_closed_recommendation"] == "CLOSED"
    assert pack["secrets_printed"] is False
    assert pack["fred_api_key_value"] is None
    assert "***" in pack["dsn_shape"]
    blob = json.dumps(pack)
    assert "FRED_API_KEY=" not in blob
    assert CORRECTION_MD.is_file()
    correction = CORRECTION_MD.read_text(encoding="utf-8")
    assert "environment-propagation" in correction
    assert "DOWN SERVICE" in correction
    assert RUN_ID in correction
    assert UNGATED_MD.is_file()
    ungated = UNGATED_MD.read_text(encoding="utf-8")
    assert "ungated" in ungated.lower()
    assert "22:02" in ungated
    assert "00:03" in ungated
    assert "Coord" in ungated
