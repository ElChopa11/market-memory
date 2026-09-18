"""One formatter module: tick, %, $M/$B, z, signed deltas. Unknowns are '?' named in gaps."""

from __future__ import annotations

from typing import Any, Mapping, Sequence

from mm_common.naming import (
    DECAY,
    LISTINGS,
    QUANT,
    RESEARCH,
    SCORECARD,
    WATCHLIST,
    sleeve_display,
    telegram_header,
    with_telegram_header,
)

UNKNOWN = "?"


def format_tick(value: float | None, tick: float = 0.5) -> str:
    if value is None:
        return UNKNOWN
    if tick <= 0:
        return f"{value}"
    snapped = round(float(value) / tick) * tick
    if abs(tick - int(tick)) < 1e-12:
        return f"{snapped:.0f}"
    decimals = max(0, str(tick).rstrip("0")[::-1].find("."))
    return f"{snapped:.{max(decimals, 1)}f}"


def format_pct(value: float | None) -> str:
    if value is None:
        return UNKNOWN
    return f"{float(value) * 100.0:.2f}%"


def format_notional(value: float | None) -> str:
    if value is None:
        return UNKNOWN
    abs_v = abs(float(value))
    sign = "-" if value < 0 else ""
    if abs_v >= 1_000_000_000:
        return f"{sign}${abs_v / 1_000_000_000:.1f}B"
    if abs_v >= 1_000_000:
        return f"{sign}${abs_v / 1_000_000:.1f}M"
    if abs_v >= 1_000:
        return f"{sign}${abs_v / 1_000:.1f}K"
    return f"{sign}${abs_v:.1f}"


def format_z(value: float | None) -> str:
    if value is None:
        return UNKNOWN
    return f"{float(value):.2f}"


def format_delta(value: float | None) -> str:
    if value is None:
        return UNKNOWN
    sign = "+" if value > 0 else ""
    return f"{sign}{float(value):.2f}"


def deltas(*, last: float | None, prior: float | None, window_20d: float | None) -> dict[str, str]:
    vs_prior = None if last is None or prior is None else last - prior
    vs_20d = None if last is None or window_20d is None else last - window_20d
    return {"vs_prior": format_delta(vs_prior), "vs_20d": format_delta(vs_20d)}


def monospace_table(headers: Sequence[str], rows: Sequence[Sequence[Any]], *, gaps: list[str] | None = None) -> str:
    str_rows = [[UNKNOWN if cell is None else str(cell) for cell in row] for row in rows]
    widths = [len(h) for h in headers]
    for row in str_rows:
        for i, cell in enumerate(row):
            if i < len(widths):
                widths[i] = max(widths[i], len(cell))
    def fmt(cells: Sequence[str]) -> str:
        return " | ".join(cell.ljust(widths[i]) for i, cell in enumerate(cells))

    lines = [fmt(list(headers)), "-+-".join("-" * w for w in widths)]
    for row in str_rows:
        padded = list(row) + [UNKNOWN] * (len(headers) - len(row))
        if gaps is not None:
            for i, cell in enumerate(padded):
                if cell == UNKNOWN:
                    gaps.append(headers[i] if i < len(headers) else f"col{i}")
        lines.append(fmt(padded[: len(headers)]))
    return "```\n" + "\n".join(lines) + "\n```"


def desk_header(
    slug: str,
    *,
    artifact_type: str | None = None,
    sleeve: str | None = None,
) -> str:
    """Telegram / pack banner from the naming layer. Unknown slug fails closed."""
    return telegram_header(slug, artifact_type=artifact_type, sleeve=sleeve)


def headed_markdown(
    markdown: str,
    slug: str,
    *,
    artifact_type: str | None = None,
    sleeve: str | None = None,
) -> str:
    return with_telegram_header(markdown, slug, artifact_type=artifact_type, sleeve=sleeve)


def ideas_header(n_shown: int, n_total: int) -> str:
    if n_total <= 0:
        return "no actionable setup"
    if n_shown < n_total:
        return f"{n_shown} ideas shown; {n_total - n_shown} cut (max 3)"
    return f"{n_shown} ideas"


WATCHLIST_DELIVERY_FOOTER = (
    "Not a call. Not a Quant verdict. Locked membership is not promotion. "
    "PLAYBOOK setups flagged only — trade math stays on lab playbook run. "
    "Ops publishes; Coord orchestrates."
)


def present_watchlist(canonical: Mapping[str, Any]) -> str:
    """Ops Telegram cut of an IMP-020 watchlist scan. Does not invent ideas or prints."""
    rows = canonical.get("rows") or []
    if not isinstance(rows, list):
        rows = []
    gaps: list[str] = []
    table_rows: list[tuple[str, str, str, str, str]] = []
    flagged: list[str] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        instrument = str(row.get("instrument") or UNKNOWN)
        membership = str(row.get("membership") or UNKNOWN)
        state = str(row.get("monitor_state") or UNKNOWN)
        freshness = str(row.get("freshness") or UNKNOWN)
        setup = "yes" if row.get("playbook_setup") else "no"
        table_rows.append((instrument, membership, state, freshness, setup))
        if state in {UNKNOWN, "UNAVAILABLE"} or freshness in {UNKNOWN, "unavailable"}:
            gaps.append(instrument)
        if row.get("playbook_setup"):
            flagged.append(instrument)
    table = monospace_table(
        ("instrument", "membership", "state", "freshness", "playbook_setup"),
        table_rows,
        gaps=gaps,
    )
    product = sleeve_display(WATCHLIST)
    completeness = canonical.get("completeness")
    completeness_s = UNKNOWN if completeness is None else f"{completeness}%"
    content_hash = canonical.get("content_hash") or UNKNOWN
    as_of = canonical.get("as_of_knowledge") or UNKNOWN
    status = canonical.get("status") or UNKNOWN
    named_gaps = list(canonical.get("gaps") or []) or gaps or ["none"]
    setup_line = (
        "PLAYBOOK setups flagged (not invented; math stays on lab playbook run): "
        + ", ".join(flagged)
        if flagged
        else "no PLAYBOOK setups flagged (inventory is not an idea list)"
    )
    body = "\n".join(
        [
            f"{product} (`{WATCHLIST}`)",
            f"as_of_knowledge: {as_of}",
            f"status: {status}",
            f"completeness: {completeness_s} of locked names with tape",
            f"content_hash: `{content_hash}`",
            "Send: no (default). Publisher: Ops. Coord is not the publisher.",
            "",
            table,
            "",
            setup_line,
            "",
            "## Gaps",
            "",
            *[f"- {item}" for item in named_gaps],
            "",
            WATCHLIST_DELIVERY_FOOTER,
        ]
    )
    return headed_markdown(body, RESEARCH, sleeve=WATCHLIST)


LISTINGS_DELIVERY_FOOTER = (
    "Not a call. Closed Quant verdicts only. Listings inherits Quant trade_math_hash "
    "and does not invent R. IC/Risk gates still required. No self-approve. "
    "Screen-only names are not universe promotion. Ops publishes; Coord orchestrates."
)


def present_listings(canonical: Mapping[str, Any]) -> str:
    """Ops Telegram cut of an IMP-017 listings screen. Does not invent prints or math."""
    ideas = canonical.get("ideas") or []
    if not isinstance(ideas, list):
        ideas = []
    index_events = canonical.get("index_events") or []
    if not isinstance(index_events, list):
        index_events = []
    gaps: list[str] = []
    table_rows: list[tuple[str, str, str, str, str]] = []
    for row in ideas:
        if not isinstance(row, dict):
            continue
        instrument = str(row.get("instrument") or UNKNOWN)
        kind = str(row.get("kind") or UNKNOWN)
        verdict = str(row.get("quant_verdict") or UNKNOWN)
        liquidity = str(row.get("liquidity_verdict") or UNKNOWN)
        math_hash = str(row.get("trade_math_hash") or "not inherited")
        table_rows.append((instrument, kind, verdict, liquidity, math_hash[:12]))
        track = row.get("track") if isinstance(row.get("track"), dict) else {}
        if track.get("status") in {UNKNOWN, "unavailable"} or verdict == "INSUFFICIENT_DATA":
            gaps.append(instrument)
    table = monospace_table(
        ("instrument", "kind", "quant_verdict", "liquidity", "trade_math"),
        table_rows,
        gaps=gaps,
    )
    idx_rows: list[tuple[str, str, str]] = []
    for row in index_events:
        if not isinstance(row, dict):
            continue
        idx_rows.append(
            (
                str(row.get("instrument") or UNKNOWN),
                str(row.get("kind") or UNKNOWN),
                str(row.get("index_name") or UNKNOWN),
            )
        )
    idx_table = monospace_table(("instrument", "kind", "index"), idx_rows, gaps=gaps) if idx_rows else "no index events"
    product = sleeve_display(LISTINGS)
    completeness = canonical.get("completeness")
    completeness_s = UNKNOWN if completeness is None else f"{completeness}%"
    content_hash = canonical.get("content_hash") or UNKNOWN
    as_of = canonical.get("as_of_knowledge") or UNKNOWN
    status = canonical.get("status") or UNKNOWN
    named_gaps = list(canonical.get("gaps") or []) or gaps or ["none"]
    br = canonical.get("base_rates") if isinstance(canonical.get("base_rates"), dict) else {}
    if br.get("claimed"):
        base_line = f"own-history n={br.get('n')} median_30d={br.get('median_30d')}"
    else:
        base_line = str(br.get("reason") or "no base-rate claim")
    body = "\n".join(
        [
            f"{product} (`{LISTINGS}`)",
            f"as_of_knowledge: {as_of}",
            f"status: {status}",
            f"completeness: {completeness_s}",
            f"content_hash: `{content_hash}`",
            f"base rates: {base_line}",
            "Send: no (default). Publisher: Ops. Coord is not the publisher.",
            "Screen-only. Does not expand Principal membership.",
            "",
            table,
            "",
            "Index events (separate stream):",
            idx_table,
            "",
            "## Gaps",
            "",
            *[f"- {item}" for item in named_gaps],
            "",
            LISTINGS_DELIVERY_FOOTER,
        ]
    )
    return headed_markdown(body, RESEARCH, sleeve=LISTINGS)


SCORECARD_DELIVERY_FOOTER = (
    "Not a call. Like-for-like only when product, schedule_anchor, and universe match "
    "and no incomparable tag applies. Tagged artifacts (including BRIEF-TAG-20260918 "
    "90m vs 30m pre-open) are not scored as equals. Quant owns the math; Ops publishes; "
    "Coord orchestrates. Prompt-hash decay watch is 6f (`lab decay watch`)."
)


def present_scorecard(canonical: Mapping[str, Any]) -> str:
    """Ops Telegram cut of an IMP-030 pack scorecard. Does not invent like-for-like scores."""
    pairs = canonical.get("pairs") or []
    if not isinstance(pairs, list):
        pairs = []
    gaps: list[str] = []
    table_rows: list[tuple[str, str, str, str]] = []
    for row in pairs:
        if not isinstance(row, dict):
            continue
        left = str(row.get("left_id") or UNKNOWN)
        right = str(row.get("right_id") or UNKNOWN)
        verdict = str(row.get("verdict") or UNKNOWN)
        reasons = ",".join(row.get("reason_codes") or []) or "—"
        if verdict == "NOT_COMPARABLE" or not row.get("comparable"):
            gaps.append(f"{left} vs {right}")
        table_rows.append((left, right, verdict, reasons))
    table = monospace_table(("left", "right", "verdict", "reasons"), table_rows, gaps=None)
    product = sleeve_display(SCORECARD)
    completeness = canonical.get("completeness")
    completeness_s = UNKNOWN if completeness is None else f"{completeness}%"
    content_hash = canonical.get("content_hash") or UNKNOWN
    as_of = canonical.get("as_of_knowledge") or UNKNOWN
    status = canonical.get("status") or UNKNOWN
    named_gaps = list(canonical.get("gaps") or []) or gaps or ["none"]
    decay = canonical.get("decay_stub") if isinstance(canonical.get("decay_stub"), dict) else {}
    if not decay:
        decay = canonical.get("decay_watch") if isinstance(canonical.get("decay_watch"), dict) else {}
    decay_line = (
        f"decay watch watch_enabled={decay.get('watch_enabled', False)} "
        f"overall={decay.get('overall') or 'n/a'} item={decay.get('item') or 'IMP-031'}"
    )
    body = "\n".join(
        [
            f"{product} (`{SCORECARD}`)",
            f"as_of_knowledge: {as_of}",
            f"status: {status}",
            f"completeness: {completeness_s}",
            f"content_hash: `{content_hash}`",
            decay_line,
            "Send: no (default). Publisher: Ops. Coord is not the publisher.",
            "Incomparable packs stay tagged. No invented like-for-like score.",
            "",
            table,
            "",
            "## Gaps",
            "",
            *[f"- {item}" for item in named_gaps],
            "",
            SCORECARD_DELIVERY_FOOTER,
        ]
    )
    return headed_markdown(body, QUANT, sleeve=SCORECARD)


DECAY_DELIVERY_FOOTER = (
    "Not a call. Prompt and config hashes are versioned. Mismatch emits a "
    "NOTIFY/queue signal. Does not waive Skeptic or Risk. Does not invent "
    "like-for-like scores for tagged incomparable packs. Quant owns the math; "
    "Ops publishes; Coord orchestrates."
)


def present_decay(canonical: Mapping[str, Any]) -> str:
    """Ops Telegram cut of an IMP-031 decay watch. Does not invent scorecard numbers."""
    watch = canonical.get("decay_watch") if isinstance(canonical.get("decay_watch"), dict) else {}
    rows = canonical.get("rows") or watch.get("rows") or []
    if not isinstance(rows, list):
        rows = []
    table_rows: list[tuple[str, str, str]] = []
    gaps: list[str] = list(canonical.get("gaps") or [])
    for row in rows:
        if not isinstance(row, dict):
            continue
        path = str(row.get("path") or UNKNOWN)
        verdict = str(row.get("verdict") or UNKNOWN)
        kind = str(row.get("kind") or UNKNOWN)
        table_rows.append((path, kind, verdict))
        if verdict not in {"MATCH", ""}:
            gaps.append(path)
    table = monospace_table(("path", "kind", "verdict"), table_rows, gaps=None)
    pairs = canonical.get("scorecard_pairs") or []
    pair_note = "no attached scorecard pairs"
    if isinstance(pairs, list) and pairs:
        tagged = [
            f"{row.get('left_id')} vs {row.get('right_id')}"
            for row in pairs
            if isinstance(row, dict) and (row.get("verdict") == "NOT_COMPARABLE" or not row.get("comparable"))
        ]
        pair_note = (
            "attached scorecard pairs kept honest; NOT_COMPARABLE stays tagged"
            if tagged
            else "attached scorecard pairs passed through without re-scoring"
        )
    product = sleeve_display(DECAY)
    completeness = canonical.get("completeness")
    completeness_s = UNKNOWN if completeness is None else f"{completeness}%"
    content_hash = canonical.get("content_hash") or UNKNOWN
    as_of = canonical.get("as_of_knowledge") or UNKNOWN
    status = canonical.get("status") or UNKNOWN
    overall = canonical.get("overall") or watch.get("overall") or UNKNOWN
    signal = canonical.get("queue_signal") if isinstance(canonical.get("queue_signal"), dict) else {}
    signal_kind = signal.get("kind") or "none"
    named_gaps = list(dict.fromkeys(gaps)) or ["none"]
    body = "\n".join(
        [
            f"{product} (`{DECAY}`)",
            f"as_of_knowledge: {as_of}",
            f"status: {status}",
            f"overall: {overall}",
            f"completeness: {completeness_s}",
            f"content_hash: `{content_hash}`",
            f"queue_signal: {signal_kind} (does not write the queue)",
            pair_note,
            "Send: no (default). Publisher: Ops. Coord is not the publisher.",
            "",
            table,
            "",
            "## Gaps",
            "",
            *[f"- {item}" for item in named_gaps],
            "",
            DECAY_DELIVERY_FOOTER,
        ]
    )
    return headed_markdown(body, QUANT, sleeve=DECAY)

