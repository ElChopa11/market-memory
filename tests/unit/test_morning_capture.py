"""Sydney morning MVP retain: one Neon capture on the send path, then one DM line.

HTTP and Postgres are mocked. Pytest does not open Neon or Telegram.
"""

from __future__ import annotations

import importlib
import json
import time
from datetime import date, datetime, timezone
from pathlib import Path

from mm_common.enums import DataQuality
from mm_common.env import PRINCIPAL_DM_CHAT_ID_ENV
from mm_common.http import ERROR_NONE
from mm_common.time import from_unix_ms
from mm_delivery.format import escape_markdown_v2
from mm_delivery.telegram import TelegramApiResult
from mm_desks.deliver_receipt import ALREADY_DELIVERED, decide_deliver, write_deliver_receipt
from mm_ingest.mvp_retain import (
    ANCHOR_EXISTS_SQL,
    CAPTURE_ROWS_SQL,
    CAPTURE_TIMEOUT_S,
    PRIOR_CAPTURE_SQL,
    PROOF_CAPTURE_KIND,
    morning_capture_if_sending,
    proof_anchor_exclusion_sql,
    proof_count_sql,
    proof_prior_exclusion_sql,
    load_mvp_retain_spec,
    run_morning_capture,
    run_proof_capture,
    sydney_anchor_date,
    us_cash_session_date,
)
from mm_lab_cli.cli import main
from mm_lab_cli.deliver import append_dm_status_lines

UTC = timezone.utc
ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = ROOT / ".github" / "workflows" / "hybrid-sydney-morning.yml"
RUNBOOK = ROOT / "docs" / "runbooks" / "mvp-retain.md"
ANCHOR = "2026-09-24T20:30:00Z"
NOW = datetime(2026, 9, 24, 20, 32, tzinfo=UTC)
PRIOR_ISO = "2026-09-23T20:32:00+00:00"
OLDER_ISO = "2026-09-22T20:32:00+00:00"
BRIEF = "Morning brief body. Not an order.\n"
DM_CHAT = "dm-only-chat"
RUN_ID = "actions-b1-36071921289"


class MemStore:
    def __init__(self) -> None:
        self.rows: list[dict] = []
        self.writes = 0
        self.readback: int | None = None
        self.fail: str | None = None
        self.last_envelopes: list = []

    def count_for_anchor(self, anchor_date: str) -> int:
        if self.fail == "count":
            raise RuntimeError("password=secret connection failed")
        if self.fail == "slow":
            time.sleep(0.4)
        return sum(
            1
            for row in self.rows
            if row.get("capture_kind") != PROOF_CAPTURE_KIND and row.get("anchor_date") == anchor_date
        )

    def prior_captured_at(self, anchor_date: str, before: str) -> str | None:
        if self.fail == "prior":
            raise RuntimeError("db down")
        candidates = [
            str(row["captured_at"])
            for row in self.rows
            if row.get("capture_kind") != PROOF_CAPTURE_KIND
            and row.get("anchor_date") != anchor_date
            and row.get("captured_at")
            and str(row["captured_at"]) < before
        ]
        return max(candidates) if candidates else None

    def persist(self, envelopes) -> None:
        if self.fail == "persist":
            raise RuntimeError("insert failed")
        self.writes += 1
        self.last_envelopes = list(envelopes)
        for envelope in envelopes:
            self.rows.append(dict(envelope.payload))

    def count_for_capture_id(self, capture_id: str) -> int:
        if self.fail == "readback":
            raise RuntimeError("select failed")
        if self.readback is not None:
            return self.readback
        return sum(
            1
            for row in self.rows
            if row.get("capture_id") == capture_id and row.get("capture_kind") == PROOF_CAPTURE_KIND
        )

    def count_for_captured_at(self, captured_at: str) -> int:
        if self.fail == "readback":
            raise RuntimeError("select failed")
        if self.readback is not None:
            return self.readback
        return sum(1 for row in self.rows if row.get("captured_at") == captured_at)


class HL:
    def __init__(self, *, fail: bool = False, mid: str | None = "1.25") -> None:
        self.fail = fail
        self.mid = mid
        self.closed = False

    def meta_and_asset_ctxs(self):
        if self.fail:
            raise ConnectionError("hl down")
        return []

    def spot_meta_and_asset_ctxs(self):
        return []

    def close(self) -> None:
        self.closed = True


class Poly:
    def __init__(self, *, error: str = ERROR_NONE) -> None:
        self.error = error
        self.calls = 0
        self.closed = False

    def grouped_daily(self, session_date):
        self.calls += 1
        self.session_date = session_date
        return {"results": []}, self.error

    def close(self) -> None:
        self.closed = True


def _capture(store: MemStore, **kwargs):
    hl = kwargs.pop("hl", None) or HL()
    poly = kwargs.pop("poly", None) or Poly()
    return run_morning_capture(
        scheduled_for=kwargs.pop("scheduled_for", ANCHOR),
        dsn=kwargs.pop("dsn", "postgresql://example.invalid/market_memory"),
        now=kwargs.pop("now", NOW),
        timeout_s=kwargs.pop("timeout_s", 5),
        store=store,
        hl_client=hl,
        polygon_adapter=poly,
        **kwargs,
    )


def test_sydney_anchor_date_and_us_session() -> None:
    assert sydney_anchor_date(ANCHOR).isoformat() == "2026-09-25"
    assert us_cash_session_date(NOW).isoformat() == "2026-09-24"


def _line(rows: int, when: datetime, prior: str = "none") -> str:
    spec = load_mvp_retain_spec()
    return (
        f"CAPTURE: {rows}/{spec.expected_rows} rows ({spec.instrument_count} instruments) "
        f"@ {when.isoformat()} · prior {prior}"
    )


def test_expected_rows_follow_membership() -> None:
    spec = load_mvp_retain_spec()
    assert spec.expected_rows == (
        len(spec.bound_symbols) * len(spec.bound_metrics)
        + len(spec.price_only_metrics)
        + len(spec.equity_symbols)
    )
    assert spec.instrument_count == len(spec.bound_symbols) + 1 + len(spec.equity_symbols)


def test_happy_path_line_uses_readback_count() -> None:
    store = MemStore()
    result = _capture(store)
    assert result.wrote is True
    assert store.writes == 1
    assert result.capture_rows == 75
    assert result.captured_at == NOW.isoformat()
    assert result.prior_captured_at is None
    assert result.line == _line(75, NOW)
    assert result.anchor_date == "2026-09-25"
    assert {row["anchor_date"] for row in store.rows} == {"2026-09-25"}
    assert {row["captured_at"] for row in store.rows} == {NOW.isoformat()}


def test_readback_lower_than_written_shows_the_real_count() -> None:
    store = MemStore()
    store.readback = 10
    result = _capture(store)
    assert store.writes == 1
    assert len(store.rows) == 75
    assert result.capture_rows == 10
    assert result.line == _line(10, NOW)


def test_empty_grouped_daily_keeps_prior_session_closes_and_counts_them() -> None:
    """A shut US session is an empty grouped-daily body, not a holiday calendar.

    The earlier session's vendor bar time stays on market_time. as_of_knowledge
    stays the capture. Crypto still runs. The DM line counts the equity rows.
    """
    spec = load_mvp_retain_spec()
    shut = date(2026, 9, 28)
    prior = date(2026, 9, 25)
    now = datetime(2026, 9, 28, 20, 32, tzinfo=UTC)
    assert us_cash_session_date(now) == shut
    bar = datetime(2026, 9, 25, 20, 0, tzinfo=UTC)
    bar_ms = int(bar.timestamp() * 1000)

    class _ShutPoly:
        def __init__(self) -> None:
            self.dates: list[date] = []
            self.closed = False

        def grouped_daily(self, session_date: date):
            self.dates.append(session_date)
            if session_date == shut:
                return {"results": [], "resultsCount": 0}, ERROR_NONE
            if session_date == prior:
                results = [
                    {"T": ticker, "c": 100 + index, "t": bar_ms}
                    for index, ticker in enumerate(spec.equity_symbols)
                ]
                return {"results": results}, ERROR_NONE
            return {"results": []}, ERROR_NONE

        def close(self) -> None:
            self.closed = True

    class _Crypto(HL):
        def __init__(self) -> None:
            super().__init__()
            self.calls: list[str] = []

        def meta_and_asset_ctxs(self):
            self.calls.append("metaAndAssetCtxs")
            return []

        def spot_meta_and_asset_ctxs(self):
            self.calls.append("spotMetaAndAssetCtxs")
            return []

    store = MemStore()
    hl = _Crypto()
    poly = _ShutPoly()
    result = _capture(
        store,
        now=now,
        scheduled_for="2026-09-27T20:30:00Z",
        hl=hl,
        poly=poly,
    )
    assert result.wrote is True
    assert "FAILED" not in result.line
    assert result.line == _line(75, now)
    assert result.capture_rows == 75
    assert hl.calls == ["metaAndAssetCtxs", "spotMetaAndAssetCtxs"]
    assert poly.dates == [shut, prior]
    closes = [env for env in store.last_envelopes if env.metric == "close"]
    assert len(closes) == 17
    assert all(env.market_time == from_unix_ms(bar_ms) for env in closes)
    assert all(env.as_of_knowledge == now for env in closes)
    assert all(env.ingested_at == now for env in closes)
    assert all(env.market_time < env.as_of_knowledge for env in closes)
    assert all(env.data_quality is DataQuality.STALE for env in closes)
    assert all(env.identity.value is not None for env in closes)
    assert {env.payload["session_date"] for env in closes} == {"2026-09-25"}
    assert {env.payload["requested_session_date"] for env in closes} == {"2026-09-28"}
    crypto = [env for env in store.last_envelopes if env.metric != "close"]
    assert len(crypto) == 58


def test_partial_polygon_persists_null_closes_and_reports_readback() -> None:
    store = MemStore()
    poly = Poly(error="http_5xx")
    result = _capture(store, poly=poly)
    assert result.wrote is True
    assert poly.calls == 1
    closes = [row for row in store.rows if row.get("metric") == "close"]
    assert len(closes) == 17
    assert all(row.get("value") is None for row in closes)
    assert result.capture_rows == len(store.rows)
    assert result.line.startswith(f"CAPTURE: {len(store.rows)}/{load_mvp_retain_spec().expected_rows} rows (")


def test_dsn_missing_is_failed_and_dm_still_sends(tmp_path, monkeypatch, capsys) -> None:
    result = run_morning_capture(scheduled_for=ANCHOR, dsn=None, now=NOW)
    assert result.line == "CAPTURE: FAILED dsn missing"
    assert result.wrote is False
    assert result.capture_rows is None
    rc, text, posted = _post_pack(monkeypatch, capsys, tmp_path, capture_line=result.line)
    assert rc == 0
    assert len(posted) == 1
    assert result.line in text
    assert posted[0]["chat_id"] == DM_CHAT


def test_db_error_is_failed_and_dm_still_sends(tmp_path, monkeypatch, capsys) -> None:
    store = MemStore()
    store.fail = "count"
    result = _capture(store)
    assert result.line == "CAPTURE: FAILED db error"
    assert "secret" not in result.line
    assert store.writes == 0
    rc, text, posted = _post_pack(monkeypatch, capsys, tmp_path, capture_line=result.line)
    assert rc == 0
    assert len(posted) == 1
    assert "CAPTURE: FAILED db error" in text
    assert "secret" not in text


def test_timeout_is_failed_timeout_and_dm_still_sends(tmp_path, monkeypatch, capsys) -> None:
    assert CAPTURE_TIMEOUT_S == 90
    store = MemStore()
    store.fail = "slow"
    result = _capture(store, timeout_s=0.05)
    assert result.line == "CAPTURE: FAILED timeout"
    assert result.wrote is False
    rc, text, posted = _post_pack(monkeypatch, capsys, tmp_path, capture_line=result.line)
    assert rc == 0
    assert len(posted) == 1
    assert "CAPTURE: FAILED timeout" in posted[0]["text"] or escape_markdown_v2(result.line) in posted[0]["text"]
    assert text.count("CAPTURE: FAILED timeout") == 1


def test_polygon_stall_is_inside_the_capture_cap_and_dm_still_sends(tmp_path, monkeypatch, capsys) -> None:
    """Grouped-daily sits inside the same wall clock as the Neon write."""

    class _Stall(Poly):
        def grouped_daily(self, session_date):
            time.sleep(2)
            return super().grouped_daily(session_date)

    store = MemStore()
    result = _capture(store, timeout_s=0.05, poly=_Stall())
    assert result.line == "CAPTURE: FAILED timeout"
    assert result.wrote is False
    assert store.writes == 0
    rc, _text, posted = _post_pack(monkeypatch, capsys, tmp_path, capture_line=result.line)
    assert rc == 0
    assert len(posted) == 1


def test_second_run_same_anchor_does_not_write() -> None:
    store = MemStore()
    first = _capture(store)
    assert first.wrote is True
    assert store.writes == 1
    second = _capture(store, now=datetime(2026, 9, 24, 22, 31, tzinfo=UTC))
    assert second.wrote is False
    assert store.writes == 1
    assert second.line == "CAPTURE: exists for 2026-09-25, not rewritten"
    assert second.capture_rows is None


def test_already_delivered_does_not_capture(tmp_path: Path) -> None:
    completions = tmp_path / "completions"
    path, created = write_deliver_receipt(
        completions_dir=completions,
        routine_id="grok.sydney_morning",
        scheduled_anchor_ts=ANCHOR,
        run_id=RUN_ID,
        sent=True,
        delivered_at=NOW,
        capture_rows=75,
    )
    assert created is True and path is not None
    body = json.loads(path.read_text(encoding="utf-8"))
    assert body["capture_rows"] == 75
    assert decide_deliver(completions, "grok.sydney_morning", ANCHOR) == ALREADY_DELIVERED
    calls: list[str] = []

    def _run():
        calls.append("capture")
        return _capture(MemStore())

    assert morning_capture_if_sending(already_delivered=True, run=_run) is None
    assert calls == []
    sent = morning_capture_if_sending(already_delivered=False, run=_run)
    assert sent is not None and sent.wrote is True
    assert calls == ["capture"]


def test_prior_captured_at_is_the_previous_anchor_date() -> None:
    store = MemStore()
    store.rows.append(
        {
            "retain_series": "mvp_retain",
            "anchor_date": "2026-09-23",
            "captured_at": OLDER_ISO,
        }
    )
    store.rows.append(
        {
            "retain_series": "mvp_retain",
            "anchor_date": "2026-09-24",
            "captured_at": PRIOR_ISO,
        }
    )
    result = _capture(store)
    assert result.prior_captured_at == PRIOR_ISO
    assert result.line.endswith(f"· prior {PRIOR_ISO}")
    fresh = [row for row in store.rows if row.get("anchor_date") == "2026-09-25"]
    assert fresh
    assert {row["prior_captured_at"] for row in fresh} == {PRIOR_ISO}
    assert {row["interval_seconds"] for row in fresh} == {86400}


def test_fetch_failure_does_not_write() -> None:
    store = MemStore()
    result = _capture(store, hl=HL(fail=True))
    assert result.line == "CAPTURE: FAILED fetch"
    assert store.writes == 0


def test_readback_query_failure_is_mismatch() -> None:
    store = MemStore()
    store.fail = "readback"
    result = _capture(store)
    assert result.line == "CAPTURE: FAILED read-back mismatch"
    assert store.writes == 1
    assert result.capture_rows is None


def test_status_lines_are_late_then_deadman_then_capture() -> None:
    late = "LATE: grok.sydney_morning fired +2h 46m past anchor. run_id x."
    deadman = "DEADMAN: ping ok"
    capture = _line(75, NOW)
    text = append_dm_status_lines(BRIEF, late=late, deadman=deadman, capture=capture)
    assert text.index(late) < text.index(deadman) < text.index(capture)
    without_deadman = append_dm_status_lines(BRIEF, late=late, capture=capture)
    assert "DEADMAN:" not in without_deadman
    assert without_deadman.index(late) < without_deadman.index(capture)


def test_live_send_orders_late_deadman_then_capture(tmp_path, monkeypatch, capsys) -> None:
    """#129 DEADMAN stays between LATE and CAPTURE on the one DM."""
    monkeypatch.delenv("HEALTHCHECKS_PING_URL", raising=False)
    line = _line(75, NOW)
    sent = datetime(2026, 9, 24, 23, 16, 50, tzinfo=UTC)
    rc, text, posted = _post_pack(monkeypatch, capsys, tmp_path, capture_line=line, sent_at=sent)
    assert rc == 0
    assert len(posted) == 1
    assert text.index("LATE:") < text.index("DEADMAN: MISSING") < text.index(line)
    assert posted[0]["text"].index("LATE:") < posted[0]["text"].index("DEADMAN:")
    assert posted[0]["text"].index("DEADMAN:") < posted[0]["text"].index("CAPTURE:")


def test_live_send_appends_capture_on_the_same_dm(tmp_path, monkeypatch, capsys) -> None:
    monkeypatch.setattr("mm_lab_cli.deadman._http_get", lambda url, timeout: (200, "OK"))
    monkeypatch.setenv("HEALTHCHECKS_PING_URL", "https://hc-ping.example/secret-uuid-not-for-logs")
    line = _line(75, NOW)
    rc, text, posted = _post_pack(monkeypatch, capsys, tmp_path, capture_line=line, sent_at=NOW)
    assert rc == 0
    assert len(posted) == 1
    assert text.count(line) == 1
    assert "LATE:" not in text
    assert escape_markdown_v2(line) in posted[0]["text"]


def test_dry_run_does_not_append_capture(tmp_path, monkeypatch, capsys) -> None:
    line = "CAPTURE: FAILED dsn missing"
    rc, text, posted = _post_pack(monkeypatch, capsys, tmp_path, capture_line=line, live=False)
    assert rc == 0
    assert "CAPTURE:" not in text
    assert posted == []


def test_cli_morning_missing_dsn_exits_zero(monkeypatch, capsys) -> None:
    monkeypatch.delenv("POSTGRES_DSN", raising=False)

    def boom(*_args, **_kwargs):
        raise AssertionError("neon store opened")

    monkeypatch.setattr("mm_ingest.mvp_retain.NeonRetainStore", boom)
    assert main(["retain", "morning", "--scheduled-for", ANCHOR]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["line"] == "CAPTURE: FAILED dsn missing"
    assert payload["capture_rows"] is None
    assert payload["wrote"] is False


def test_receipt_without_capture_rows_stays_valid(tmp_path: Path) -> None:
    path, created = write_deliver_receipt(
        completions_dir=tmp_path,
        routine_id="grok.sydney_morning",
        scheduled_anchor_ts=ANCHOR,
        run_id=RUN_ID,
        sent=True,
        delivered_at=NOW,
    )
    assert created is True and path is not None
    body = json.loads(path.read_text(encoding="utf-8"))
    assert "capture_rows" not in body


PROOF_ID = "11111111-1111-4111-8111-111111111111"
MONDAY_ANCHOR = "2026-09-27T20:30:00Z"
MONDAY_NOW = datetime(2026, 9, 27, 20, 40, tzinfo=UTC)
FRIDAY_PRIOR = "2026-09-25T20:32:00+00:00"
SATURDAY_PROOF = "2026-09-26T04:00:00+00:00"


def _proof(store: MemStore, **kwargs):
    hl = kwargs.pop("hl", None) or HL()
    poly = kwargs.pop("poly", None) or Poly()
    return run_proof_capture(
        dsn=kwargs.pop("dsn", "postgresql://example.invalid/market_memory"),
        now=kwargs.pop("now", NOW),
        scheduled_for=kwargs.pop("scheduled_for", ANCHOR),
        timeout_s=kwargs.pop("timeout_s", 5),
        store=store,
        hl_client=hl,
        polygon_adapter=poly,
        capture_id=kwargs.pop("capture_id", PROOF_ID),
        **kwargs,
    )


def test_proof_same_anchor_does_not_block_the_morning_write() -> None:
    store = MemStore()
    proof_now = datetime(2026, 9, 27, 20, 31, tzinfo=UTC)
    proof = _proof(store, now=proof_now, scheduled_for=MONDAY_ANCHOR)
    assert proof.wrote is True
    assert proof.capture_rows == 75
    assert proof.capture_id == PROOF_ID
    assert proof.line == (
        (
            f"CAPTURE_PROOF: 75/{load_mvp_retain_spec().expected_rows} rows "
            f"({load_mvp_retain_spec().instrument_count} instruments) "
            f"@ {proof_now.isoformat()} capture_id {PROOF_ID}"
        )
    )
    assert {row["capture_kind"] for row in store.rows} == {PROOF_CAPTURE_KIND}
    assert {row["capture_id"] for row in store.rows} == {PROOF_ID}
    assert {row["anchor_date"] for row in store.rows} == {"2026-09-28"}
    assert all(env.identity.extras.get("capture_kind") == PROOF_CAPTURE_KIND for env in store.last_envelopes)
    real = _capture(store, scheduled_for=MONDAY_ANCHOR, now=MONDAY_NOW)
    assert real.wrote is True
    assert store.writes == 2
    assert "exists" not in real.line
    assert real.line.startswith(
        f"CAPTURE: 75/{load_mvp_retain_spec().expected_rows} rows "
        f"({load_mvp_retain_spec().instrument_count} instruments) @ {MONDAY_NOW.isoformat()}"
    )
    morning_rows = [row for row in store.rows if row.get("capture_kind") != PROOF_CAPTURE_KIND]
    assert len(morning_rows) == 75
    assert {row["anchor_date"] for row in morning_rows} == {"2026-09-28"}


def test_proof_is_excluded_from_prior_selection() -> None:
    store = MemStore()
    store.rows.append(
        {
            "retain_series": "mvp_retain",
            "anchor_date": "2026-09-26",
            "captured_at": FRIDAY_PRIOR,
            "capture_kind": "lab_snapshot",
        }
    )
    store.rows.append(
        {
            "retain_series": "mvp_retain",
            "anchor_date": "2026-09-27",
            "captured_at": SATURDAY_PROOF,
            "capture_kind": PROOF_CAPTURE_KIND,
            "capture_id": PROOF_ID,
        }
    )
    monday_now = datetime(2026, 9, 27, 20, 32, tzinfo=UTC)
    result = _capture(store, scheduled_for=MONDAY_ANCHOR, now=monday_now)
    assert result.wrote is True
    assert result.prior_captured_at == FRIDAY_PRIOR
    fresh = [row for row in store.rows if row.get("anchor_date") == "2026-09-28"]
    assert fresh
    assert {row["prior_captured_at"] for row in fresh} == {FRIDAY_PRIOR}
    assert {row["interval_seconds"] for row in fresh} == {172800}
    assert SATURDAY_PROOF not in {row.get("prior_captured_at") for row in fresh}


def test_proof_sql_excludes_proof_from_anchor_and_prior() -> None:
    assert "<> 'proof'" in ANCHOR_EXISTS_SQL
    assert "<> 'proof'" in PRIOR_CAPTURE_SQL
    count = proof_count_sql(PROOF_ID)
    prior = proof_prior_exclusion_sql(PROOF_ID)
    anchor = proof_anchor_exclusion_sql(PROOF_ID)
    assert f"payload_json->>'capture_id' = '{PROOF_ID}'" in count
    assert "capture_kind' = 'proof'" in count
    assert "proof_rows_eligible_as_prior" in prior
    assert "<> 'proof'" in prior
    assert "proof_rows_on_anchor_key" in anchor
    assert "anchor_date" in anchor


def test_cli_proof_missing_dsn_exits_nonzero(monkeypatch, capsys) -> None:
    monkeypatch.delenv("POSTGRES_DSN", raising=False)

    def boom(*_args, **_kwargs):
        raise AssertionError("neon store opened")

    monkeypatch.setattr("mm_ingest.mvp_retain.NeonRetainStore", boom)
    assert main(["retain", "proof"]) == 1
    out = capsys.readouterr().out
    assert out.startswith("CAPTURE_PROOF: FAILED dsn missing")
    assert "postgres" not in out.lower()


def test_runbook_has_the_readback_sql() -> None:
    text = RUNBOOK.read_text(encoding="utf-8")
    assert "SELECT COUNT(*) AS capture_rows" in text
    assert "payload_json->>'retain_series' = 'mvp_retain'" in text
    assert "payload_json->>'captured_at' = '<captured_at>'" in text
    assert "payload_json->>'captured_at'" in CAPTURE_ROWS_SQL
    assert "payload_json->>'retain_series' = 'mvp_retain'" in CAPTURE_ROWS_SQL
    assert "capture_kind' = 'proof'" in text
    assert "proof_rows_eligible_as_prior" in text
    assert "proof_rows_on_anchor_key" in text


def test_workflow_capture_runs_before_send_and_is_nonfatal() -> None:
    text = WORKFLOW.read_text(encoding="utf-8")
    stage1_key = "\n  stage1-stamp:\n"
    brief_key = "\n  brief-and-deliver:\n"
    stage1 = text[text.index(stage1_key) : text.index(brief_key)]
    brief = text[text.index(brief_key) :]
    assert "lab retain morning" not in stage1
    assert "POSTGRES_DSN" not in stage1
    assert 'cron: "30 20 * * 0-4"' not in brief
    assert text.count('cron: "30 20 * * 0-4"') == 1
    assert text.count('cron: "30 22 * * 0-4"') == 1
    assert "repository_dispatch" not in text
    retain_name = "- name: Morning MVP retain"
    deliver_name = "uv run lab deliver pack"
    assert retain_name in brief
    assert brief.index(retain_name) < brief.index(deliver_name)
    assert brief.index("uv run lab brief close") < brief.index(retain_name)
    step = brief[brief.index(retain_name) : brief.index("- name: Deliver pack")]
    assert "continue-on-error: true" in step
    assert "steps.receipt.outputs.already_delivered != 'true'" in step
    assert "secrets.POSTGRES_DSN" in step
    assert "lab retain morning" in step
    assert "--scheduled-for" in step
    assert "--send" not in step
    assert "exit 0" in step
    command = brief[brief.index(deliver_name) : brief.index('> "/tmp/sydney-deliver-')]
    assert "--capture-line" in command
    assert "--to-principal-dm" in command
    assert "--i-mean-it" in command
    assert brief.count(deliver_name) == 1
    assert "capture_rows=capture_rows" in brief
    proof_key = "\n  capture-proof:\n"
    render_key = "\n  render-proof:\n"
    assert proof_key in text and render_key in text
    assert text.index(brief_key) < text.index(proof_key) < text.index(render_key)
    proof = text[text.index(proof_key) : text.index(render_key)]
    assert "needs:" not in proof
    assert "inputs.mode == 'capture_proof'" in proof
    assert "uv run lab retain proof" in proof
    assert "secrets.POSTGRES_DSN" in proof
    assert "secrets.POLYGON_API_KEY" in proof
    assert "GITHUB_STEP_SUMMARY" in proof
    assert "continue-on-error" not in proof
    assert "TELEGRAM" not in proof
    assert "HEALTHCHECKS" not in proof
    assert "lab brief" not in proof
    assert "lab deliver" not in proof
    assert "write_deliver_receipt" not in proof
    assert "git push" not in proof
    assert "mode:" in text
    assert "capture_proof" in text
    assert text.count("workflow_dispatch:") == 1


def _post_pack(
    monkeypatch,
    capsys,
    tmp_path: Path,
    *,
    capture_line: str,
    live: bool = True,
    sent_at: datetime | None = None,
) -> tuple[int, str, list[dict[str, str]]]:
    monkeypatch.delenv("TELEGRAM_CHAT_ID", raising=False)
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "test-token")
    monkeypatch.setenv(PRINCIPAL_DM_CHAT_ID_ENV, DM_CHAT)
    monkeypatch.setattr("mm_lab_cli.deliver.utcnow", lambda: sent_at or NOW)
    posted: list[dict[str, str]] = []

    class _FakeApi:
        def send_message(self, *, chat_id, text, **kwargs):
            posted.append({"chat_id": str(chat_id), "text": str(text)})
            return TelegramApiResult(
                method="sendMessage",
                ok=True,
                error_class="none",
                attempts=1,
                status_code=200,
                payload={"ok": True},
            )

        def close(self) -> None:
            return None

    deliver_module = importlib.import_module("mm_delivery.deliver")
    monkeypatch.setattr(deliver_module.TelegramClient, "from_settings", lambda *args, **kwargs: _FakeApi())
    brief = tmp_path / "brief.md"
    brief.write_text(BRIEF, encoding="utf-8")
    args = [
        "deliver",
        "pack",
        "--from-markdown",
        str(brief),
        "--as-of",
        "2026-09-24T23:16:50Z",
        "--scheduled-for",
        ANCHOR,
        "--run-id",
        RUN_ID,
        "--capture-line",
        capture_line,
        "--desk",
        "ops",
        "--to-principal-dm",
        "--repo-root",
        str(ROOT),
        "--out",
        str(tmp_path / "out"),
        "--ignore-quiet-hours",
    ]
    if live:
        args.append("--i-mean-it")
    else:
        args.append("--no-send")
    rc = main(args)
    captured = capsys.readouterr()
    assert "test-token" not in captured.out
    payload_path = tmp_path / "out" / "briefs" / "2026-09-24" / "telegram-payload.json"
    assert payload_path.is_file()
    envelope = json.loads(payload_path.read_text(encoding="utf-8"))
    return rc, str(envelope["text"]), posted
