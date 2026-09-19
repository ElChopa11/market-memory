"""EDGAR stack helper (IMP-024). Paper only.

``--no-db`` is ELIGIBLE only (same closure rule as FRED). Never auto-closes
incidents. Lockup values publish only when ``licence_verdict`` is ok_gov.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

from mm_common.hashing import claim_hash
from mm_common.ids import new_ulid
from mm_common.schemas import ObservationEnvelope
from mm_common.time import utcnow
from mm_ingest.edgar import METRIC_FILING, METRIC_LOCKUP
from mm_ingest.licence import STANDING_RULE, may_publish_value, verdict_for
from mm_ingest.pipeline import persist_envelopes, stats_from_envelopes
from mm_ingest.sources import EDGAR_SOURCE_NAME

CLOSURE_OPEN = "OPEN"
CLOSURE_ELIGIBLE = "ELIGIBLE"
CLOSURE_CLOSED = "CLOSED"
NO_DB_NOTE = "--no-db = ELIGIBLE only; CLOSED requires Postgres persist + cited run_id"


@dataclass(frozen=True)
class EdgarPublishedRow:
    instrument: str
    metric: str
    observation_id: str
    claim_hash: str
    file_date: str | None
    as_of_knowledge: str
    assume_180d: bool | None
    staged_calendar_dates: tuple[str, ...]
    lock_up_period: str | None
    licence_verdict: str
    value_redacted: bool
    error_class: str | None

    def as_public_dict(self) -> dict[str, Any]:
        return {
            "instrument": self.instrument,
            "metric": self.metric,
            "observation_id": self.observation_id,
            "claim_hash": self.claim_hash,
            "file_date": self.file_date,
            "as_of_knowledge": self.as_of_knowledge,
            "assume_180d": self.assume_180d,
            "staged_calendar_dates": list(self.staged_calendar_dates),
            "lock_up_period": self.lock_up_period,
            "licence_verdict": self.licence_verdict,
            "value_redacted": self.value_redacted,
            "error_class": self.error_class,
        }


@dataclass
class EdgarStackResult:
    closure: str
    run_id: str | None
    no_db: bool
    persisted: bool
    notes: list[str] = field(default_factory=list)
    rows: list[EdgarPublishedRow] = field(default_factory=list)
    created: int = 0
    envelopes: int = 0
    markdown: str = ""
    content_hash: str = ""

    def as_public_dict(self) -> dict[str, Any]:
        return {
            "source": EDGAR_SOURCE_NAME,
            "closure": self.closure,
            "run_id": self.run_id,
            "no_db": self.no_db,
            "persisted": self.persisted,
            "created": self.created,
            "envelopes": self.envelopes,
            "notes": list(self.notes),
            "standing_rule": STANDING_RULE,
            "rows": [row.as_public_dict() for row in self.rows],
            "content_hash": self.content_hash,
            "auto_close": False,
        }


def edgar_envelopes(envelopes: list[ObservationEnvelope]) -> list[ObservationEnvelope]:
    return [row for row in envelopes if row.source_name == EDGAR_SOURCE_NAME]


def closure_for(*, no_db: bool, persisted: bool, run_id: str | None) -> str:
    if no_db:
        return CLOSURE_ELIGIBLE
    if persisted and run_id:
        return CLOSURE_ELIGIBLE
    return CLOSURE_OPEN


def published_rows(envelopes: list[ObservationEnvelope]) -> list[EdgarPublishedRow]:
    publish = may_publish_value(EDGAR_SOURCE_NAME)
    verdict = verdict_for(EDGAR_SOURCE_NAME).verdict
    out: list[EdgarPublishedRow] = []
    for envelope in edgar_envelopes(envelopes):
        error = str(envelope.payload.get("error_class") or "") or None
        obs_id = str(envelope.payload.get("observation_id") or envelope.source_url_or_id or "")
        file_date = envelope.payload.get("file_date")
        staged = envelope.payload.get("staged_calendar_dates") or []
        assume = envelope.payload.get("assume_180d")
        period = envelope.payload.get("lock_up_period")
        redacted = False
        shown_period = None if period is None else str(period)
        dates = tuple(str(x) for x in staged) if isinstance(staged, list) else ()
        if not publish and envelope.metric in {METRIC_LOCKUP, METRIC_FILING} and not error:
            shown_period = None
            dates = ()
            redacted = True
        out.append(
            EdgarPublishedRow(
                instrument=envelope.instrument,
                metric=envelope.metric,
                observation_id=obs_id,
                claim_hash=envelope.claim_hash,
                file_date=None if file_date is None else str(file_date),
                as_of_knowledge=envelope.as_of_knowledge.isoformat()
                if envelope.as_of_knowledge
                else envelope.ingested_at.isoformat(),
                assume_180d=None if assume is None else bool(assume),
                staged_calendar_dates=dates,
                lock_up_period=shown_period,
                licence_verdict=verdict,
                value_redacted=redacted,
                error_class=error,
            )
        )
    return out


def render_edgar_artifact(result: EdgarStackResult) -> str:
    lines = [
        f"# EDGAR stack — {result.closure}",
        "",
        f"- **Source:** `{EDGAR_SOURCE_NAME}`",
        f"- **Closure:** {result.closure} (Principal rule: open→eligible→closed(cite run_id)|retired)",
        f"- **--no-db:** {'yes' if result.no_db else 'no'}",
        f"- **Persisted:** {'yes' if result.persisted else 'no'}",
        f"- **run_id:** {result.run_id or 'none'}",
        f"- **Auto-close:** no",
        f"- **content_hash:** `{result.content_hash}`",
        f"- **Standing rule:** {STANDING_RULE}",
        "",
        "| instrument | metric | observation_id | file_date | as_of_knowledge | assume_180d | claim_hash |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in result.rows:
        lines.append(
            f"| {row.instrument} | {row.metric} | `{row.observation_id}` | "
            f"{row.file_date or 'n/a'} | {row.as_of_knowledge} | {row.assume_180d} | `{row.claim_hash}` |"
        )
    if result.notes:
        lines.extend(["", "## Notes", ""])
        for note in result.notes:
            lines.append(f"- {note}")
    lines.extend(["", "## Footer", "", "Not a call. Paper only. No live path. file_date is not the knowledge clock.", ""])
    return "\n".join(lines)


def run_edgar_stack(
    envelopes: list[ObservationEnvelope],
    *,
    no_db: bool,
    session: Any | None = None,
    run_id: str | None = None,
    as_of: datetime | None = None,
) -> EdgarStackResult:
    rows_env = edgar_envelopes(envelopes)
    persisted = False
    created = 0
    notes = [NO_DB_NOTE] if no_db else []
    cited = run_id
    if no_db:
        stats = stats_from_envelopes(rows_env, dry_run=True)
        notes.append("Postgres not attached; lockup confirmation is ELIGIBLE from stored filing, never CLOSED")
    elif session is not None and rows_env:
        stats = persist_envelopes(session, rows_env)
        persisted = True
        created = stats.created
        cited = cited or new_ulid()
        notes.append(f"Postgres persist attempted; created={created}; cite run_id to close")
    else:
        stats = stats_from_envelopes(rows_env, dry_run=True)
        notes.append("No session; treat as OPEN until Postgres is attached")
    closure = closure_for(no_db=no_db, persisted=persisted, run_id=cited)
    published = published_rows(rows_env)
    payload = {
        "as_of": (as_of or utcnow()).isoformat(),
        "closure": closure,
        "no_db": no_db,
        "persisted": persisted,
        "rows": [row.as_public_dict() for row in published],
        "notes": notes,
    }
    digest = claim_hash(payload)
    result = EdgarStackResult(
        closure=closure,
        run_id=cited if persisted else None,
        no_db=no_db,
        persisted=persisted,
        notes=notes,
        rows=published,
        created=created,
        envelopes=stats.envelopes,
        content_hash=digest,
    )
    result.markdown = render_edgar_artifact(result)
    return result


def write_edgar_artifact(result: EdgarStackResult, out_dir: Path, *, day: str) -> Path:
    dest = Path(out_dir) / "ops" / "reports" / "edgar"
    dest.mkdir(parents=True, exist_ok=True)
    path = dest / f"{day}.md"
    path.write_text(result.markdown, encoding="utf-8")
    return path
