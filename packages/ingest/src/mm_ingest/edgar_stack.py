"""EDGAR full-stack helper (IMP-024). Paper only.

Principal closure rule: open → eligible → closed(cite run_id) | retired.
``--no-db`` is ELIGIBLE only. CLOSED requires Postgres persist + provenance
ids + a published artifact that is allowed to carry the value, then an
operator-cited ``run_id``. This module never auto-closes incidents.
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
from mm_ingest.edgar import FILING_METRIC, LOCKUP_METRIC
from mm_ingest.licence import STANDING_RULE, may_publish_value, verdict_for
from mm_ingest.pipeline import persist_envelopes, stats_from_envelopes
from mm_ingest.sources import EDGAR_SOURCE_NAME

CLOSURE_OPEN = "OPEN"
CLOSURE_ELIGIBLE = "ELIGIBLE"
CLOSURE_CLOSED = "CLOSED"
CLOSURE_RETIRED = "RETIRED"
NO_DB_NOTE = "--no-db = ELIGIBLE only; CLOSED requires Postgres persist + cited run_id"


@dataclass(frozen=True)
class EdgarPublishedRow:
    instrument: str
    metric: str
    value: str | None
    file_date: str | None
    as_of_knowledge: str
    provenance_id: str
    claim_hash: str
    licence_verdict: str
    assume_180d: bool
    value_redacted: bool

    def as_public_dict(self) -> dict[str, Any]:
        return {
            "instrument": self.instrument,
            "metric": self.metric,
            "value": self.value,
            "file_date": self.file_date,
            "as_of_knowledge": self.as_of_knowledge,
            "provenance_id": self.provenance_id,
            "claim_hash": self.claim_hash,
            "licence_verdict": self.licence_verdict,
            "assume_180d": self.assume_180d,
            "value_redacted": self.value_redacted,
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
    """Never return CLOSED without a cited persist run_id. --no-db is ELIGIBLE."""
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
        raw_value = envelope.identity.value
        is_status = str(envelope.payload.get("error_class") or "") != ""
        value: str | None
        redacted = False
        if is_status or raw_value in {None, "", "unavailable"}:
            value = None
        elif not publish:
            value = None
            redacted = True
        else:
            value = str(raw_value)
        file_date = envelope.payload.get("file_date")
        if file_date is None and envelope.market_time is not None:
            file_date = envelope.market_time.date().isoformat()
        out.append(
            EdgarPublishedRow(
                instrument=envelope.instrument,
                metric=envelope.metric,
                value=value,
                file_date=str(file_date) if file_date else None,
                as_of_knowledge=envelope.as_of_knowledge.isoformat()
                if envelope.as_of_knowledge
                else envelope.ingested_at.isoformat(),
                provenance_id=envelope.claim_hash,
                claim_hash=envelope.claim_hash,
                licence_verdict=verdict,
                assume_180d=str(envelope.identity.extras.get("assume_180d") or "false").lower() == "true",
                value_redacted=redacted,
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
        f"- **Lockup:** prospectus formulas; **not** a flat 180 days",
        "",
        "| instrument | metric | value | file_date | as_of_knowledge | provenance_id | licence_verdict |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in result.rows:
        shown = row.value if row.value is not None else ("redacted" if row.value_redacted else "unavailable")
        lines.append(
            f"| {row.instrument} | {row.metric} | {shown} | {row.file_date or 'n/a'} | "
            f"{row.as_of_knowledge} | `{row.provenance_id}` | {row.licence_verdict} |"
        )
    if result.notes:
        lines.extend(["", "## Notes", ""])
        for note in result.notes:
            lines.append(f"- {note}")
    lines.extend(["", "## Footer", "", "Not a call. Paper only. No live path. Do not assume flat 180d lockups.", ""])
    return "\n".join(lines)


def run_edgar_stack(
    envelopes: list[ObservationEnvelope],
    *,
    no_db: bool,
    session: Any | None = None,
    run_id: str | None = None,
    as_of: datetime | None = None,
) -> EdgarStackResult:
    """Assemble EDGAR envelopes into a published artifact. Never auto-closes."""
    rows_env = edgar_envelopes(envelopes)
    persisted = False
    created = 0
    notes = [NO_DB_NOTE] if no_db else []
    cited = run_id
    if no_db:
        stats = stats_from_envelopes(rows_env, dry_run=True)
        created = 0
        notes.append("Postgres not attached; EDGAR --no-db stays ELIGIBLE, never CLOSED")
    elif session is not None and rows_env:
        stats = persist_envelopes(session, rows_env)
        persisted = True
        created = stats.created
        cited = cited or new_ulid()
        notes.append(f"Postgres persist attempted; created={created}; cite run_id to close")
    else:
        stats = stats_from_envelopes(rows_env, dry_run=True)
        notes.append("No session; treat as OPEN until Postgres is attached")
    lockups = [row for row in rows_env if row.metric == LOCKUP_METRIC]
    if any(str(row.identity.extras.get("assume_180d") or "").lower() == "true" for row in lockups):
        notes.append("REFUSED: assume_180d must stay false")
    if lockups:
        notes.append(f"lockup rows={len(lockups)}; filing rows={sum(1 for row in rows_env if row.metric == FILING_METRIC)}")
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
