"""Render source-health markdown. Health/provenance only — no market prints."""

from __future__ import annotations

from datetime import datetime

from mm_common.hashing import sha256_hex
from mm_common.time import in_ops_tz
from mm_source_health.models import HealthReport, SourceHealth, overall_status

NO_DECISION_FOOTER = (
    "**Informational only — no decision, no recommendation, no order intent.**\n"
    "This is a Data & Market Memory source-health report. It does not quote markets, "
    "change universe membership, size a trade, submit an order, or approve risk."
)

LIMITATIONS = (
    "No paid-data purchases; FRED stays unavailable without env FRED_API_KEY (set locally or in CI secrets; never committed).",
    "Stooq failures are classified (timeout / http_404 / http_5xx / parse / tos_or_blocked). Bounded GET retry on timeout/5xx/429 only; 404 is terminal. No ToS-violating scrape workaround.",
    "CoinGecko/Stooq/FRED are not written into Market Memory; last success for those is this probe or unknown.",
    "Calendar health is YAML presence (no live economic-calendar API).",
    "This report never copies mids, marks, yields, or CSV Close values into the artifact.",
)


def render_report(
    *,
    generated_at: datetime,
    sources: tuple[SourceHealth, ...],
    command: str = "lab data source-health",
) -> HealthReport:
    overall = overall_status(sources)
    lines: list[str] = [
        "# Source health report",
        "",
        f"- Generated at (UTC): {generated_at.isoformat()}",
        f"- Generated at (Australia/Sydney): {in_ops_tz(generated_at).isoformat()}",
        f"- Command: `{command}`",
        f"- Overall: **{overall}**",
        "- This is health/provenance, not a market brief. No prints, quotes, or recommendations.",
        "",
        "## Inventory",
        "",
        "| Source | Pulse role | Status | Latency | Error class | Last success | Credentials | Notes |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for row in sources:
        lines.append(
            "| {name} | {role} | {status} | {lat} | {err} | {last} | {cred} | {notes} |".format(
                name=_cell(row.display_name),
                role=_cell(row.pulse_role),
                status=_cell(row.status),
                lat=_latency(row.latency_ms),
                err=_cell(row.error_class),
                last=_ts(row.last_success_at),
                cred=_cell(row.credentials_present),
                notes=_cell("; ".join(row.notes) if row.notes else ""),
            )
        )
    lines.extend(["", "## Per source", ""])
    for row in sources:
        lines.extend(
            [
                f"### {row.display_name}",
                "",
                f"- Source id: `{row.source_id}`",
                f"- Status: `{row.status}`",
                f"- Pulse role: `{row.pulse_role}`",
                f"- Endpoint: `{row.endpoint or 'n/a'}`",
                f"- Probe: {row.probe or 'n/a'}",
                f"- Latency: {_latency(row.latency_ms)}",
                f"- Error class: `{row.error_class}`",
                f"- Last success: {_ts(row.last_success_at)}",
                f"- Credentials present: `{row.credentials_present}` (values never printed)",
                "- Notes:",
            ]
        )
        if row.notes:
            for note in row.notes:
                lines.append(f"  - {note}")
        else:
            lines.append("  - (none)")
        lines.append("")
    lines.extend(["## Limitations", ""])
    for item in LIMITATIONS:
        lines.append(f"- {item}")
    lines.extend(["", NO_DECISION_FOOTER, ""])
    markdown = "\n".join(lines)
    return HealthReport(
        generated_at=generated_at,
        overall=overall,
        sources=sources,
        markdown=markdown,
        content_hash=sha256_hex(markdown),
        limitations=LIMITATIONS,
    )


def _latency(value: float | None) -> str:
    if value is None:
        return "n/a"
    return f"{value:.1f} ms"


def _ts(value: datetime | None) -> str:
    if value is None:
        return "unknown"
    return value.isoformat()


def _cell(value: str) -> str:
    return value.replace("|", "/").replace("\n", " ").strip()
