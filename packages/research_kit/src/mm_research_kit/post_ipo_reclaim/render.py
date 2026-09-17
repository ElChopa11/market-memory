"""Render the Post-IPO / reclaim screen markdown. Language-gated."""

from __future__ import annotations

from mm_research_kit.errors import GateError
from mm_research_kit.post_ipo_reclaim.models import (
    DATA_QUALITY_VALUES,
    SCREEN_FOOTER,
    ScreenResult,
    ScreenRow,
)
from mm_research_kit.quant_review.language import assert_language_clean
from mm_research_kit.quant_review.models import QuantReasonCode, QuantVerdict


def render_screen(
    *,
    screen_date: str,
    as_of_knowledge: str,
    generated_at: str,
    universe_version: str,
    params_hash: str,
    snapshot_source: str,
    rows: tuple[ScreenRow, ...],
    coverage_notes: tuple[str, ...],
) -> str:
    allowed_verdicts = {v.value for v in QuantVerdict}
    allowed_codes = {c.value for c in QuantReasonCode}
    for row in rows:
        if row.verdict not in allowed_verdicts:
            raise GateError(f"{row.instrument}: unknown verdict {row.verdict}")
        if not row.reason_codes:
            raise GateError(f"{row.instrument}: every verdict needs a reason code")
        if set(row.reason_codes) - allowed_codes:
            raise GateError(f"{row.instrument}: unknown reason code in {row.reason_codes}")
        if row.data_quality not in DATA_QUALITY_VALUES:
            raise GateError(f"{row.instrument}: data_quality must be fresh|stale|partial|unavailable")

    counts: dict[str, int] = {}
    for row in rows:
        counts[row.verdict] = counts.get(row.verdict, 0) + 1

    compact_lines = []
    for row in rows:
        last = _metric(row, "last")
        chg = _metric(row, "session_chg_pct")
        vs_peer = _metric(row, "vs_peer_median_pp")
        vs_bench = _metric(row, "vs_benchmark_session_pp")
        mdd = _metric(row, "drawdown_vs_ref_high")
        reclaim = _metric(row, "reclaim_hold_sessions")
        compact_lines.append(
            "| {inst} | {asof} | {last} | {chg} | {vs_peer} | {vs_bench} | {mdd} | {reclaim} | {dq} | {verdict} | {codes} |".format(
                inst=row.instrument,
                asof=row.as_of_knowledge,
                last=_cell(last),
                chg=_cell(chg),
                vs_peer=_cell(vs_peer),
                vs_bench=_cell(vs_bench),
                mdd=_cell(mdd),
                reclaim=_cell(reclaim),
                dq=row.data_quality,
                verdict=row.verdict,
                codes=", ".join(row.reason_codes),
            )
        )
    compact = "\n".join(compact_lines) or "| (empty screen) | — | — | — | — | — | — | — | unavailable | INSUFFICIENT_DATA | INSUFFICIENT_HISTORY |"

    detail_blocks: list[str] = []
    for row in rows:
        metric_table = "\n".join(
            f"| {m.name} | {m.value} | {m.source} | {m.as_of} | {m.freshness} | {m.notes.replace('|', '/')} |"
            for m in row.metrics
        )
        detail_blocks.extend(
            [
                f"### {row.instrument}",
                "",
                f"- **Instrument:** {row.instrument} (`{'`, `'.join(row.raw_symbols)}`)",
                f"- **As-of (as_of_knowledge):** {row.as_of_knowledge}",
                f"- **Membership:** {row.membership} (Principal membership is `config/universe.yaml`; this screen does not change it)",
                f"- **Post-IPO flag:** {'yes' if row.post_ipo else 'no'}",
                f"- **Listing / issuance date:** {row.listing_date}",
                f"- **Sector / benchmark / peers:** {row.sector} / {row.benchmark or 'none'} / {', '.join(row.peers) or 'none'}",
                f"- **Data quality:** `{row.data_quality}` (`fresh|stale|partial|unavailable`)",
                f"- **Labels:** {', '.join(row.labels) or 'none'}",
                f"- **Verdict:** `{row.verdict}`",
                f"- **Reason code(s):** {', '.join(row.reason_codes)}",
                "",
                row.unusual,
                "",
                "| metric | value | source | as-of | freshness | notes |",
                "| --- | --- | --- | --- | --- | --- |",
                metric_table,
                "",
                f"- **Catalyst / why-now:** {row.catalyst}",
                f"- **Invalidation:** {row.invalidation}",
                f"- **Liquidity:** {row.liquidity}",
                f"- **What must change:** {row.what_must_change}",
                "",
            ]
        )

    cov = "\n".join(f"- {note}" for note in coverage_notes) or "- none"
    lines = [
        f"# Post-IPO / reclaim screen — {screen_date}",
        "",
        "Equities & Post-IPO Desk **research triage**. Relative-value / reclaim framing. **Not a trading decision.**",
        "",
        f"- **Screen date:** {screen_date}",
        f"- **Knowledge watermark (as_of_knowledge):** {as_of_knowledge}",
        f"- **Generated at:** {generated_at}",
        f"- **Universe:** `{universe_version}` (`config/equities/post_ipo_reclaim.yaml`, kind=`post_ipo_reclaim_screen`, status=`screen_only`)",
        f"- **Snapshot source:** {snapshot_source}",
        f"- **params_hash:** `{params_hash}`",
        f"- **Candidates scored:** {len(rows)}",
        f"- **Verdict counts:** " + ", ".join(f"{k}={v}" for k, v in sorted(counts.items())),
        f"- **Closed verdicts:** `RESEARCH_PRIORITY | MONITOR | DEFER | REJECT | INSUFFICIENT_DATA`",
        "- **Hard screen rule:** a beaten-down IPO is not a candidate just because it is down.",
        "",
        "## Coverage",
        "",
        cov,
        "",
        "## Compact screen",
        "",
        "| Instrument | as-of | last | session chg% | vs peer median | vs benchmark | drawdown vs ref high | reclaim hold | data quality | verdict | reason codes |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
        compact,
        "",
        "Metric cells that say unavailable were missing from the snapshot and were **not fabricated**.",
        "",
        "## Rows",
        "",
        *detail_blocks,
        "## Language",
        "",
        "Closed Quant verdicts only. Principal membership keys (`in_universe` / `watch_only`) stay on `config/universe.yaml` and are not this screen's labels. "
        "Relative-value / reclaim candidate unless a complete executable-arb package is evidenced (this screen does not score Track D).",
        "",
        SCREEN_FOOTER,
        "",
    ]
    text = "\n".join(lines)
    assert_language_clean(text)
    return text


def _metric(row: ScreenRow, name: str):
    for cell in row.metrics:
        if cell.name == name:
            return cell
    return None


def _cell(metric) -> str:
    if metric is None:
        return "unavailable"
    return f"{metric.value} ({metric.source}; {metric.freshness})"


def assert_screen_language(result: ScreenResult) -> None:
    assert_language_clean(result.markdown)
