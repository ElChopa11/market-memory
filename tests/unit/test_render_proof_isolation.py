"""render_proof isolation. Same bar as capture_proof: explicit assertions.

The job entry point is ``python -m mm_briefing.render_proof``. These tests run that
function. Forbidden writers raise AssertionError if called. HTTP is a saved
Polygon, FRED, and metaAndAssetCtxs fixture. The token string is ``fixture``.
"""

from __future__ import annotations

import collections.abc
import json
import os
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path

import httpx
import yaml

from mm_ingest.mvp_retain import PRIOR_CAPTURE_SQL, PROOF_CAPTURE_KIND
from mm_briefing import render_proof

FRIDAY_PRIOR = "2026-09-25T20:32:00+00:00"
SATURDAY_PROOF = "2026-09-26T04:00:00+00:00"

ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = ROOT / ".github" / "workflows" / "hybrid-sydney-morning.yml"
FIXTURE_DIR = ROOT / "tests" / "fixtures" / "briefing"
AS_OF = datetime(2026, 9, 25, 8, 30, tzinfo=timezone.utc)
FIXTURE_TOKEN = "fixture"
MONDAY_ANCHOR_DATE = "2026-09-28"
PRIOR_BEFORE = "2026-09-27T20:32:00+00:00"
ALLOWED_SECRETS = frozenset({"POLYGON_API_KEY", "FRED_API_KEY"})
FORBIDDEN_SECRET_NAMES = (
    "TELEGRAM_BOT_TOKEN",
    "TELEGRAM_CHAT_ID",
    "TELEGRAM_CHAT_ID_PRINCIPAL_DM",
    "HEALTHCHECKS_PING_URL",
    "DATABASE_URL",
    "POSTGRES_DSN",
    "NEON_DATABASE_URL",
    "GITHUB_TOKEN",
    "GH_TOKEN",
)
UNREAD_ENV = (
    "DATABASE_URL",
    "POSTGRES_DSN",
    "NEON_DATABASE_URL",
    "TELEGRAM_BOT_TOKEN",
    "TELEGRAM_CHAT_ID",
    "TELEGRAM_CHAT_ID_PRINCIPAL_DM",
    "HEALTHCHECKS_PING_URL",
)
SENTINELS = {
    "TELEGRAM_BOT_TOKEN": "sentinel-telegram-bot-token-not-a-secret",
    "TELEGRAM_CHAT_ID": "sentinel-telegram-group-not-a-secret",
    "TELEGRAM_CHAT_ID_PRINCIPAL_DM": "sentinel-telegram-dm-not-a-secret",
    "HEALTHCHECKS_PING_URL": "sentinel-healthchecks-ping-not-a-secret",
}
SECRET_RE = re.compile(
    r"secrets\.([A-Za-z0-9_]+)|secrets\[\s*['\"]([A-Za-z0-9_]+)['\"]\s*\]"
)
STAMP_IF = (
    "github.event_name != 'workflow_dispatch' || "
    "(inputs.mode != 'capture_proof' && inputs.mode != 'render_proof')"
)
BRIEF_IF = (
    "(github.event_name != 'workflow_dispatch' || "
    "(inputs.mode != 'capture_proof' && inputs.mode != 'render_proof')) && "
    "(github.event_name == 'schedule' || (github.event_name == 'workflow_dispatch' && "
    "(inputs.i_mean_it_deliver == true || github.event.inputs.i_mean_it_deliver == 'true')))"
)
CAPTURE_JOB_IF = "github.event_name == 'workflow_dispatch' && inputs.mode == 'capture_proof'"
RENDER_JOB_IF = "github.event_name == 'workflow_dispatch' && inputs.mode == 'render_proof'"
STEP_READY = "steps.gate.outputs.ready == 'true'"
STEP_RECEIPT = "success() && steps.gate.outputs.ready == 'true'"
STEP_SEND_PATH = (
    "success() && steps.gate.outputs.ready == 'true' && "
    "steps.receipt.outputs.already_delivered != 'true'"
)
STEP_WROTE = "success() && steps.deliver.outputs.wrote == 'true'"
SIDE_EFFECT_NEEDLES = (
    "git push",
    "git commit",
    "healthchecks",
    "api.telegram.org",
    "telegram",
    "curl ",
    "curl\n",
)


def _workflow():
    text = WORKFLOW.read_text(encoding="utf-8")
    parsed = yaml.safe_load(text)
    return text, parsed


def _render_job(parsed):
    return parsed["jobs"]["render-proof"]


def _job_text(text: str) -> str:
    return text[text.index("\n  render-proof:\n") :]


def _secret_names(node) -> set[str]:
    found: set[str] = set()

    def walk(value) -> None:
        if isinstance(value, dict):
            for child in value.values():
                walk(child)
        elif isinstance(value, list):
            for child in value:
                walk(child)
        elif isinstance(value, str):
            for match in SECRET_RE.finditer(value):
                found.add(match.group(1) or match.group(2))

    walk(node)
    return found


def _scoped_secret_names(job: dict) -> set[str]:
    """Secrets referenced from job and step env, with, and run only."""
    found: set[str] = set()
    if "env" in job:
        found |= _secret_names(job["env"])
    for step in job.get("steps") or []:
        for key in ("env", "with", "run"):
            if key in step:
                found |= _secret_names(step[key])
    return found


def _job_runs(expr: str | None, event: str, mode: str | None, *, deliver: bool = False) -> bool:
    if expr is None:
        raise AssertionError("job has no if")
    if expr == STAMP_IF:
        return event != "workflow_dispatch" or mode not in {"capture_proof", "render_proof"}
    if expr == BRIEF_IF:
        mode_ok = event != "workflow_dispatch" or mode not in {"capture_proof", "render_proof"}
        deliver_ok = event == "schedule" or (event == "workflow_dispatch" and deliver)
        return mode_ok and deliver_ok
    if expr == CAPTURE_JOB_IF:
        return event == "workflow_dispatch" and mode == "capture_proof"
    if expr == RENDER_JOB_IF:
        return event == "workflow_dispatch" and mode == "render_proof"
    raise AssertionError(f"unrecognised job if: {expr}")


def _step_runs(
    expr: str | None,
    *,
    success: bool,
    ready: bool,
    already_delivered: bool,
    deliver_wrote: bool = False,
) -> bool:
    """Evaluate a step if. None means the step has no if of its own."""
    if expr is None:
        return True
    if expr == STEP_READY:
        return ready
    if expr == STEP_RECEIPT:
        return success and ready
    if expr == STEP_SEND_PATH:
        return success and ready and not already_delivered
    if expr == STEP_WROTE:
        return success and deliver_wrote
    raise AssertionError(f"unrecognised step if: {expr}")


class _EnvironSpy(collections.abc.MutableMapping):
    """Records named reads. A full iteration is its own failure: that reads every value."""

    def __init__(self, real) -> None:
        self._real = real
        self.reads: list[str] = []
        self.iterated = False

    def __getitem__(self, key):
        self.reads.append(str(key))
        return self._real[key]

    def __setitem__(self, key, value) -> None:
        self._real[key] = value

    def __delitem__(self, key) -> None:
        del self._real[key]

    def __iter__(self):
        self.iterated = True
        return iter(self._real)

    def __len__(self) -> int:
        return len(self._real)

    def get(self, key, default=None):
        self.reads.append(str(key))
        return self._real.get(key, default)

    def __contains__(self, key) -> bool:
        self.reads.append(str(key))
        return key in self._real


def _forbid(called: list[str], name: str):
    def _inner(*_args, **_kwargs):
        called.append(name)
        raise AssertionError(f"{name} must not run on render_proof")

    return _inner


def _install_forbidden(monkeypatch, called: list[str]) -> None:
    targets = (
        "mm_desks.deliver_receipt.write_deliver_receipt",
        "mm_ingest.mvp_retain.run_morning_capture",
        "mm_ingest.mvp_retain.run_proof_capture",
        "mm_ingest.mvp_retain.persist_mvp_retain",
        "mm_ingest.mvp_retain._neon_session",
        "mm_ingest.pipeline.persist_envelopes",
        "mm_memory.db.make_engine",
        "mm_lab_cli.completion.stamp_cli_fire",
        "mm_lab_cli.briefing.stamp_cli_fire",
        "mm_lab_cli.deliver.stamp_cli_fire",
        "mm_desks.completions.write_completion",
        "mm_desks.completions.record_cli_completion",
        "mm_lab_cli.deadman.ping_deadman",
        "mm_lab_cli.deadman.ping_deadman_start",
        "mm_lab_cli.deadman.ping_deadman_success",
        "mm_lab_cli.deliver.ping_deadman_start",
        "mm_lab_cli.deliver.ping_deadman_success",
    )
    for target in targets:
        monkeypatch.setattr(target, _forbid(called, target))
    monkeypatch.setattr(
        "mm_delivery.telegram.TelegramClient.send_message",
        _forbid(called, "mm_delivery.telegram.TelegramClient.send_message"),
    )
    monkeypatch.setattr(
        "mm_ingest.mvp_retain.NeonRetainStore",
        _forbid(called, "mm_ingest.mvp_retain.NeonRetainStore"),
    )

    real_run = subprocess.run

    def _run(args, **kwargs):
        parts = args if isinstance(args, (list, tuple)) else [args]
        flat = " ".join(str(part) for part in parts).lower()
        if "git" in flat and ("commit" in flat or "push" in flat):
            called.append("git")
            raise AssertionError("git commit or push must not run on render_proof")
        if "healthchecks" in flat or "api.telegram.org" in flat or "telegram" in flat:
            called.append("subprocess-send")
            raise AssertionError("telegram or healthchecks subprocess must not run on render_proof")
        return real_run(args, **kwargs)

    monkeypatch.setattr(subprocess, "run", _run)


def _install_fixture_http(
    monkeypatch,
    *,
    polygon_status: dict[str, int] | None = None,
    fred_body: dict | None = None,
) -> None:
    polygon = json.loads((FIXTURE_DIR / "morning_polygon_aggs.json").read_text(encoding="utf-8"))
    fred = fred_body if fred_body is not None else json.loads(
        (FIXTURE_DIR / "morning_fred_rolled.json").read_text(encoding="utf-8")
    )
    hl_body = json.loads(
        (FIXTURE_DIR / "morning_hl_meta_and_asset_ctxs.json").read_text(encoding="utf-8")
    )
    status_for = polygon_status or {}
    original = httpx.Client

    def handler(request: httpx.Request) -> httpx.Response:
        host = request.url.host
        if host == "api.polygon.io":
            for ticker, body in polygon.items():
                if f"/ticker/{ticker}/" in request.url.path:
                    status = status_for.get(ticker, 200)
                    if status != 200:
                        return httpx.Response(status, json={"status": "ERROR"})
                    return httpx.Response(200, json=body)
            return httpx.Response(404, json={"status": "NOT_FOUND"})
        if host == "api.stlouisfed.org":
            return httpx.Response(200, json=fred)
        if host == "api.hyperliquid.xyz":
            payload = json.loads(request.content or b"{}")
            if str(payload.get("type")) == "metaAndAssetCtxs":
                return httpx.Response(200, json=hl_body)
            return httpx.Response(400, json={"error": "fixture transport refuses this info type"})
        return httpx.Response(404, json={"error": "fixture transport refuses this host"})

    def factory(*args, **kwargs):
        kwargs["transport"] = httpx.MockTransport(handler)
        return original(*args, **kwargs)

    monkeypatch.setattr(httpx, "Client", factory)


def _prior_captured_at(rows: list[dict], anchor_date: str, before: str, *, drop_proof: bool) -> str | None:
    """PRIOR_CAPTURE_SQL predicate. ``drop_proof`` is the capture_kind filter."""
    candidates = []
    for row in rows:
        if row.get("retain_series") != "mvp_retain":
            continue
        kind = row.get("capture_kind") or ""
        if drop_proof and kind == PROOF_CAPTURE_KIND:
            continue
        if (row.get("anchor_date") or "") == anchor_date:
            continue
        captured = row.get("captured_at")
        if captured is None or str(captured).strip() == "":
            continue
        if str(captured) >= before:
            continue
        candidates.append(str(captured))
    return max(candidates) if candidates else None


class _MemStore:
    """In-memory stand-in for the morning prior query. Same kind filter as PRIOR_CAPTURE_SQL."""

    def __init__(self) -> None:
        self.rows: list[dict] = []
        self.writes = 0

    def prior_captured_at(self, anchor_date: str, before: str) -> str | None:
        candidates = [
            str(row["captured_at"])
            for row in self.rows
            if row.get("capture_kind") != PROOF_CAPTURE_KIND
            and row.get("anchor_date") != anchor_date
            and row.get("captured_at")
            and str(row["captured_at"]) < before
        ]
        return max(candidates) if candidates else None


def _seeded_rows() -> list[dict]:
    return [
        {
            "retain_series": "mvp_retain",
            "anchor_date": "2026-09-26",
            "captured_at": FRIDAY_PRIOR,
            "capture_kind": "lab_snapshot",
        },
        {
            "retain_series": "mvp_retain",
            "anchor_date": "2026-09-27",
            "captured_at": SATURDAY_PROOF,
            "capture_kind": PROOF_CAPTURE_KIND,
            "capture_id": "11111111-1111-4111-8111-111111111111",
        },
    ]


def test_render_proof_secret_allowlist_is_exactly_polygon_and_fred() -> None:
    text, parsed = _workflow()
    job = _render_job(parsed)
    job_text = _job_text(text)
    scoped = _scoped_secret_names(job)
    entire = _secret_names(job)
    assert scoped == ALLOWED_SECRETS
    assert entire == ALLOWED_SECRETS
    for name in FORBIDDEN_SECRET_NAMES:
        assert name not in entire
        assert name not in job_text
    assert "HEALTHCHECKS" not in job_text
    assert "NEON" not in job_text.upper()
    assert "secrets: inherit" not in job_text
    assert "secrets:inherit" not in job_text.replace(" ", "")
    assert job.get("secrets") is None
    assert "uses" not in job
    for step in job["steps"]:
        assert "secrets" not in step
        uses = step.get("uses")
        if uses is not None:
            assert not str(uses).endswith((".yml", ".yaml"))
            assert "/.github/workflows/" not in str(uses)
    assert job["permissions"] == {"contents": "read"}
    assert "contents: write" not in job_text


def test_render_proof_forbidden_writers_raise_and_sentinels_are_unread(monkeypatch, capsys, tmp_path) -> None:
    called: list[str] = []
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.delenv("POSTGRES_DSN", raising=False)
    monkeypatch.delenv("NEON_DATABASE_URL", raising=False)
    for key, value in SENTINELS.items():
        monkeypatch.setenv(key, value)
    monkeypatch.setenv("POLYGON_API_KEY", FIXTURE_TOKEN)
    monkeypatch.setenv("FRED_API_KEY", FIXTURE_TOKEN)
    summary = tmp_path / "summary.md"
    monkeypatch.setenv("GITHUB_STEP_SUMMARY", str(summary))
    spy = _EnvironSpy(os.environ)
    monkeypatch.setattr(os, "environ", spy)
    _install_forbidden(monkeypatch, called)
    _install_fixture_http(monkeypatch)
    monkeypatch.setattr(render_proof, "utcnow", lambda: AS_OF)
    monkeypatch.chdir(ROOT)

    rc = render_proof.main()
    captured = capsys.readouterr()
    assert rc == 0
    assert called == []
    assert spy.iterated is False
    for key in UNREAD_ENV:
        assert key not in spy.reads
    blob = captured.out + captured.err + summary.read_text(encoding="utf-8")
    for value in SENTINELS.values():
        assert value not in blob
    assert "US Close 2026-09-24" in captured.out
    assert "EQUITY T-1 BY DESIGN (close 2026-09-24)" in captured.out
    assert "characters=" in captured.out
    assert "lines=" in captured.out
    assert "US Close unavailable" not in captured.out
    assert summary.is_file()
    summary_text = summary.read_text(encoding="utf-8")
    tail = [line for line in summary_text.splitlines() if line.startswith(("HL ", "Polygon ", "FRED "))]
    assert tail == [
        "HL ok as-of 2026-09-25",
        "Polygon SPY ok as-of 2026-09-24",
        "Polygon QQQ ok as-of 2026-09-24",
        "Polygon UUP ok as-of 2026-09-24",
        "Polygon USO ok as-of 2026-09-24",
        "FRED DGS10 ok as-of 2026-09-24",
    ]
    assert "RENDER_PROOF FAIL" not in captured.out
    assert "SOURCE DOWN" not in summary_text
    _, parsed = _workflow()
    text = WORKFLOW.read_text(encoding="utf-8")
    assert "uv run python -m mm_briefing.render_proof" in _job_text(text)
    assert _render_job(parsed)["steps"][-1]["run"].strip().endswith(
        "uv run python -m mm_briefing.render_proof"
    )


def test_render_proof_gating_skips_every_other_job_and_steps_have_no_side_effects() -> None:
    text, parsed = _workflow()
    jobs = parsed["jobs"]
    assert "render-proof" in jobs
    assert "stage1-stamp" in jobs
    assert "brief-and-deliver" in jobs
    assert "capture-proof" in jobs
    for name, job in jobs.items():
        runs = _job_runs(job.get("if"), "workflow_dispatch", "render_proof", deliver=True)
        if name == "render-proof":
            assert runs is True
            continue
        assert runs is False
        for step in job.get("steps") or []:
            # Job if is false, and a skipped job never sets ready or wrote.
            # A step with no if of its own still does not run.
            step_open = _step_runs(
                step.get("if"), success=False, ready=False, already_delivered=False, deliver_wrote=False
            )
            assert (runs and step_open) is False
            if step.get("if") is not None:
                assert step_open is False

    render_cases = (
        ("schedule", None),
        ("schedule", "normal"),
        ("schedule", "render_proof"),
        ("workflow_dispatch", None),
        ("workflow_dispatch", "normal"),
        ("workflow_dispatch", "capture_proof"),
        ("workflow_dispatch", ""),
        ("push", "render_proof"),
        ("workflow_dispatch", "render_proof"),
    )
    render_if = jobs["render-proof"]["if"]
    for event, mode in render_cases:
        assert _job_runs(render_if, event, mode) is (
            event == "workflow_dispatch" and mode == "render_proof"
        )

    for deliver in (True, False):
        assert _job_runs(jobs["brief-and-deliver"]["if"], "workflow_dispatch", "render_proof", deliver=deliver) is False
        assert _job_runs(jobs["stage1-stamp"]["if"], "workflow_dispatch", "render_proof", deliver=deliver) is False
        assert _job_runs(jobs["capture-proof"]["if"], "workflow_dispatch", "render_proof", deliver=deliver) is False

    brief = jobs["brief-and-deliver"]
    named = {step.get("name"): step for step in brief["steps"] if step.get("name")}
    capture = named["Morning MVP retain (non-fatal; one capture per Sydney anchor)"]
    deliver = named["Deliver pack to Principal DM (--to-principal-dm --i-mean-it)"]
    receipt = named["Deliver-receipt gate (scheduled_anchor, before brief or Telegram)"]
    assert capture["if"] == STEP_SEND_PATH
    assert deliver["if"] == STEP_SEND_PATH
    assert receipt["if"] == STEP_RECEIPT
    for step in (capture, deliver, receipt):
        assert _step_runs(step["if"], success=False, ready=False, already_delivered=False) is False
        assert "HEALTHCHECKS" not in (capture["run"] if step is capture else "")
    assert "HEALTHCHECKS_PING_URL" in deliver["env"]
    assert "HEALTHCHECKS_PING_URL" in receipt["env"]
    ping_steps = [
        step
        for job in jobs.values()
        for step in job.get("steps") or []
        if "HEALTHCHECKS" in yaml.safe_dump(step)
    ]
    assert ping_steps
    for step in ping_steps:
        assert _step_runs(step.get("if"), success=False, ready=False, already_delivered=False) is False

    render_blob = "\n".join(str(step.get("run") or "") for step in jobs["render-proof"]["steps"]).lower()
    module = (ROOT / "packages" / "briefing" / "src" / "mm_briefing" / "render_proof.py").read_text(
        encoding="utf-8"
    )
    for needle in SIDE_EFFECT_NEEDLES:
        assert needle not in render_blob
    for needle in (
        "send_message",
        "ping_deadman",
        "stamp_cli_fire",
        "write_deliver_receipt",
        "NeonRetainStore",
        "git commit",
        "git push",
        "curl",
        "api.telegram.org",
        "healthchecks.io",
    ):
        assert needle not in module
    assert "git push" not in _job_text(text)
    assert "git commit" not in _job_text(text)


def test_render_proof_writes_zero_rows_and_prior_ignores_proof_and_render(
    monkeypatch, capsys, tmp_path
) -> None:
    rows = _seeded_rows()
    store = _MemStore()
    store.rows.extend(rows)
    before = list(store.rows)
    called: list[str] = []

    def _persist(*_args, **_kwargs):
        store.rows.append(
            {
                "retain_series": "mvp_retain",
                "anchor_date": MONDAY_ANCHOR_DATE,
                "captured_at": "2026-09-27T20:31:00+00:00",
                "capture_kind": "render_proof",
            }
        )
        called.append("persist_mvp_retain")
        raise AssertionError("render_proof wrote a capture row")

    monkeypatch.setattr("mm_ingest.mvp_retain.persist_mvp_retain", _persist)
    monkeypatch.setattr("mm_ingest.pipeline.persist_envelopes", _persist)
    monkeypatch.setattr("mm_ingest.mvp_retain.NeonRetainStore", _persist)
    monkeypatch.setattr("mm_ingest.mvp_retain.run_morning_capture", _persist)
    monkeypatch.setattr("mm_ingest.mvp_retain.run_proof_capture", _persist)
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.setenv("POLYGON_API_KEY", FIXTURE_TOKEN)
    monkeypatch.setenv("FRED_API_KEY", FIXTURE_TOKEN)
    monkeypatch.setenv("GITHUB_STEP_SUMMARY", str(tmp_path / "summary.md"))
    _install_fixture_http(monkeypatch)
    monkeypatch.setattr(render_proof, "utcnow", lambda: AS_OF)
    monkeypatch.chdir(ROOT)

    rc = render_proof.main()
    capsys.readouterr()
    assert rc == 0
    assert called == []
    assert store.rows == before
    assert store.writes == 0
    assert not any(row.get("capture_kind") == "render_proof" for row in store.rows)

    # Without the kind filter the later proof row would be Monday's prior.
    assert _prior_captured_at(store.rows, MONDAY_ANCHOR_DATE, PRIOR_BEFORE, drop_proof=False) == SATURDAY_PROOF
    chosen = _prior_captured_at(store.rows, MONDAY_ANCHOR_DATE, PRIOR_BEFORE, drop_proof=True)
    assert chosen == FRIDAY_PRIOR
    assert chosen != SATURDAY_PROOF
    assert store.prior_captured_at(MONDAY_ANCHOR_DATE, PRIOR_BEFORE) == FRIDAY_PRIOR
    assert "COALESCE(payload_json->>'capture_kind', '') <> 'proof'" in PRIOR_CAPTURE_SQL
    assert "render_proof" not in PRIOR_CAPTURE_SQL
    assert "mode" not in PRIOR_CAPTURE_SQL
    # The proof row is in the table and is not selected. render_proof added no row to select.
    assert any(row.get("capture_kind") == PROOF_CAPTURE_KIND for row in store.rows)
    assert _prior_captured_at(
        [row for row in store.rows if row.get("capture_kind") == PROOF_CAPTURE_KIND],
        MONDAY_ANCHOR_DATE,
        PRIOR_BEFORE,
        drop_proof=True,
    ) is None


def test_render_proof_missing_env_exits_nonzero(monkeypatch, capsys, tmp_path) -> None:
    """Polygon and FRED keys are unwired. The job must not exit 0."""
    monkeypatch.delenv("POLYGON_API_KEY", raising=False)
    monkeypatch.delenv("FRED_API_KEY", raising=False)
    monkeypatch.delenv("DATABASE_URL", raising=False)
    summary = tmp_path / "summary.md"
    monkeypatch.setenv("GITHUB_STEP_SUMMARY", str(summary))
    _install_fixture_http(monkeypatch)
    monkeypatch.setattr(render_proof, "utcnow", lambda: AS_OF)
    monkeypatch.chdir(ROOT)

    rc = render_proof.main()
    captured = capsys.readouterr()
    text = summary.read_text(encoding="utf-8")
    assert rc == 1
    assert "RENDER_PROOF FAIL: POLYGON missing_env" in captured.out
    assert "RENDER_PROOF FAIL: FRED missing_env" in captured.out
    assert "RENDER_PROOF FAIL: POLYGON missing_env" in text
    assert "RENDER_PROOF FAIL: FRED missing_env" in text
    assert "SOURCE DOWN" not in captured.out
    assert "SOURCE DOWN" not in text
    assert "POLYGON missing_env" in captured.out
    assert "FRED missing_env" in captured.out
    tail = text.rstrip().splitlines()[-6:]
    assert tail == [
        "HL ok as-of 2026-09-25",
        "Polygon SPY missing_env as-of none",
        "Polygon QQQ missing_env as-of none",
        "Polygon UUP missing_env as-of none",
        "Polygon USO missing_env as-of none",
        "FRED DGS10 missing_env as-of none",
    ]
    assert FIXTURE_TOKEN not in captured.out


def test_render_proof_source_down_still_renders_and_names_the_reason(monkeypatch, capsys, tmp_path) -> None:
    """Key is present. HTTP failure and empty data render, and the summary names them."""
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.setenv("POLYGON_API_KEY", FIXTURE_TOKEN)
    monkeypatch.setenv("FRED_API_KEY", FIXTURE_TOKEN)
    summary = tmp_path / "summary.md"
    monkeypatch.setenv("GITHUB_STEP_SUMMARY", str(summary))
    _install_fixture_http(
        monkeypatch,
        polygon_status={"SPY": 404},
        fred_body={"observations": [{"date": "2026-09-24", "value": "."}]},
    )
    monkeypatch.setattr(render_proof, "utcnow", lambda: AS_OF)
    monkeypatch.chdir(ROOT)

    rc = render_proof.main()
    captured = capsys.readouterr()
    text = summary.read_text(encoding="utf-8")
    assert rc == 0
    assert "RENDER_PROOF FAIL" not in captured.out
    assert "US Close unavailable" in captured.out
    assert "SOURCE DOWN: Polygon SPY http_404" in text
    assert "SOURCE DOWN: FRED DGS10 empty" in text
    assert "SOURCE DOWN: Polygon SPY http_404" in captured.out
    assert "SOURCE DOWN: FRED DGS10 empty" in captured.out
    tail = [line for line in text.splitlines() if line.startswith(("HL ", "Polygon ", "FRED "))]
    assert tail[-6:] == [
        "HL ok as-of 2026-09-25",
        "Polygon SPY down as-of none",
        "Polygon QQQ ok as-of 2026-09-24",
        "Polygon UUP ok as-of 2026-09-24",
        "Polygon USO ok as-of 2026-09-24",
        "FRED DGS10 down as-of none",
    ]
    assert text.rstrip().splitlines()[-6:] == tail[-6:]


def test_render_proof_timeout_is_source_down_not_missing_env() -> None:
    from datetime import datetime, timezone

    from mm_briefing.models import AssetPrint, MacroSnapshot

    moment = datetime(2026, 9, 25, 8, 30, tzinfo=timezone.utc)
    assets = []
    for symbol, ticker in (("ES", "SPY"), ("NQ", "QQQ"), ("DXY", "UUP"), ("CL", "USO")):
        last = None if symbol == "ES" else 1.0
        assets.append(
            AssetPrint(
                symbol=symbol,
                name=ticker,
                last=last,
                prior_close=1.0 if last is not None else None,
                source="polygon",
                as_of=moment,
                quoted_symbol=ticker,
            )
        )
    assets.append(
        AssetPrint(
            symbol="US10Y",
            name="US10Y",
            last=None,
            prior_close=None,
            source="fred",
            as_of=moment,
        )
    )
    snapshot = MacroSnapshot(
        as_of=moment,
        prior_us_close=moment,
        assets=tuple(assets),
        data_quality="unavailable",
        source="live",
        notes=(
            "polygon unavailable (error_class=timeout) for 1 slot(s): ES",
            "fred failed for 1 series (error_class=timeout)",
        ),
    )
    sources = render_proof.proof_sources(snapshot, ())
    assert render_proof.fail_lines(sources) == ()
    assert "SOURCE DOWN: Polygon SPY timeout" in render_proof.down_lines(sources)
    assert "SOURCE DOWN: FRED DGS10 timeout" in render_proof.down_lines(sources)
    by_name = {row.name: row for row in sources}
    assert by_name["Polygon SPY"].status == "down"
    assert by_name["Polygon QQQ"].status == "ok"
    assert by_name["FRED DGS10"].status == "down"
    assert by_name["HL"].status == "down"
