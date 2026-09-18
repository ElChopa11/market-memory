"""Render Quant Cards and the dated board markdown."""

from __future__ import annotations

from mm_research_kit.quant_review.language import arbitrage_label_ok, assert_language_clean
from mm_research_kit.quant_review.models import (
    BOARD_FOOTER,
    LABEL_ARBITRAGE,
    QuantCard,
    QuantVerdict,
)
from mm_research_kit.errors import GateError


def render_card(card: QuantCard) -> str:
    if not card.reason_codes:
        raise GateError(f"{card.instrument}: every verdict needs a reason code")
    if card.verdict not in {v.value for v in QuantVerdict}:
        raise GateError(f"{card.instrument}: unknown verdict {card.verdict}")
    if not arbitrage_label_ok(card):
        raise GateError(f"{card.instrument}: ARBITRAGE label requires a complete Track D package")
    evidence_rows = "\n".join(
        f"| {row.claim.replace('|', '/')} | {row.source} | {row.timestamp} | {row.capture} | {row.evidence_confidence:.2f} | {row.provenance.replace('|', '/')} |"
        for row in card.evidence
    ) or "| none — no attributable evidence in this snapshot | — | — | — | 0.00 | empty snapshot |"
    promo = card.promotion
    lines = [
        f"# Quant Card — {card.instrument}",
        "",
        f"- **Instrument:** {card.instrument} (`{'`, `'.join(card.raw_symbols)}`)",
        f"- **Review date:** {card.review_date}",
        f"- **Knowledge watermark (as_of_knowledge):** {card.as_of_knowledge}",
        f"- **Track(s):** {', '.join(card.tracks) or 'none'}",
        f"- **Sector:** {card.sector}",
        f"- **Benchmark:** {card.benchmark}",
        f"- **Peers:** {', '.join(card.peers) or 'none'}",
        f"- **Data-quality status:** {card.data_quality}",
        f"- **Labels:** {', '.join(card.labels) or 'none'}",
        f"- **Verdict:** {card.verdict}",
        f"- **Reason code(s):** {', '.join(card.reason_codes)}",
        f"- **Independent Skeptic review required:** {'yes' if promo.independent_skeptic_review_required else 'no'}",
        f"- **Independent Skeptic verdict:** {promo.independent_skeptic_verdict} (not claimed as pass)",
        f"- **Promotion checklist:** "
        + ", ".join(
            f"{k}={'yes' if v else 'no'}"
            for k, v in promo.as_dict().items()
            if k != "independent_skeptic_verdict"
        ),
        "",
        "## What is objectively unusual?",
        "",
        card.unusual,
        "",
        "## Evidence",
        "",
        "| claim | source | timestamp | capture | evidence_confidence | provenance |",
        "| --- | --- | --- | --- | --- | --- |",
        evidence_rows,
        "",
        "evidence_confidence is data reliability (0–1), not a board verdict.",
        "",
        "## Relative performance and structure",
        "",
        card.relative_and_structure,
        "",
        "## Why overlooked",
        "",
        card.why_overlooked,
        "",
        "## Alternative / skeptic case",
        "",
        card.alternative_case,
        "",
        "## Catalyst / condition to monitor",
        "",
        card.catalyst,
        "",
        "## Single invalidation",
        "",
        card.invalidation,
        "",
        "## Liquidity / execution suitability",
        "",
        card.liquidity,
        "",
        "## What must change for promotion / re-review",
        "",
        card.what_must_change,
        "",
        BOARD_FOOTER,
        "",
    ]
    text = "\n".join(lines)
    assert_language_clean(text)
    return text


def render_board(
    *,
    review_date: str,
    as_of_knowledge: str,
    generated_at: str,
    universe_version: str,
    params_hash: str,
    cards: tuple[QuantCard, ...],
    coverage_notes: tuple[str, ...],
    concentration_warnings: tuple[str, ...],
    what_changed: str,
    prior_board: str | None,
    universe_config: str = "config/quant_review_universe.yaml",
) -> str:
    for card in cards:
        if not card.reason_codes:
            raise GateError(f"{card.instrument}: every verdict needs a reason code")
        if not arbitrage_label_ok(card):
            raise GateError(f"{card.instrument}: ARBITRAGE label requires a complete Track D package")
    priority = [c for c in cards if c.verdict == QuantVerdict.RESEARCH_PRIORITY.value]
    monitor = [c for c in cards if c.verdict == QuantVerdict.MONITOR.value]
    arb = [c for c in cards if c.executable_arb or LABEL_ARBITRAGE in c.labels]
    post_ipo = [c for c in cards if c.post_ipo]
    counts: dict[str, int] = {}
    for card in cards:
        counts[card.verdict] = counts.get(card.verdict, 0) + 1
    compact = "\n".join(
        f"| {c.instrument} | {', '.join(c.tracks)} | {c.verdict} | {', '.join(c.reason_codes)} | {', '.join(c.labels) or '—'} |"
        for c in cards
    )
    priority_block = (
        "\n".join(f"- `{c.instrument}` — {c.unusual}" for c in priority)
        if priority
        else "- none this review (honest empty is preferred over a forced shortlist)"
    )
    arb_block = (
        "\n".join(
            f"- `{c.instrument}` — Track D complete; label {LABEL_ARBITRAGE}."
            for c in arb
        )
        if arb
        else "- empty (expected unless a complete two-venue package is evidenced)"
    )
    post_block = (
        "\n".join(
            f"- `{c.instrument}` — verdict {c.verdict}; post-IPO down-alone is not RESEARCH_PRIORITY."
            for c in post_ipo
        )
        if post_ipo
        else "- none flagged post-IPO on this universe"
    )
    conc = "\n".join(f"- {note}" for note in concentration_warnings) or "- none"
    cov = "\n".join(f"- {note}" for note in coverage_notes) or "- none"
    lines = [
        f"# Quant Review Board — {review_date}",
        "",
        "Disciplined decision board. **Not a call generator.** Not sizing. Not an execution approval.",
        "",
        f"- **Review date:** {review_date}",
        f"- **Knowledge watermark (as_of_knowledge):** {as_of_knowledge}",
        f"- **Generated at:** {generated_at}",
        f"- **Universe version:** {universe_version} (`{universe_config}`)",
        f"- **params_hash:** `{params_hash}`",
        f"- **Names reviewed:** {len(cards)}",
        f"- **Verdict counts:** "
        + ", ".join(f"{k}={v}" for k, v in sorted(counts.items())),
        f"- **Prior board:** {prior_board or 'none'}",
        f"- **Independent Skeptic:** required on any RESEARCH_PRIORITY before a thesis pack; not claimed as pass on this board.",
        "",
        "## Coverage",
        "",
        cov,
        "",
        "## Compact verdicts",
        "",
        "| Instrument | Tracks | Verdict | Reason codes | Labels |",
        "| --- | --- | --- | --- | --- |",
        compact,
        "",
        f"## RESEARCH_PRIORITY (≤3; {len(priority)} this review)",
        "",
        priority_block,
        "",
        "## Executable-arbitrage list",
        "",
        arb_block,
        "",
        "## Post-IPO reclaim list",
        "",
        post_block,
        "",
        "## MONITOR",
        "",
        "\n".join(f"- `{c.instrument}` — {', '.join(c.reason_codes)}" for c in monitor) or "- none",
        "",
        "## Sector concentration / duplicate-beta warnings",
        "",
        conc,
        "",
        "## What changed since prior review",
        "",
        what_changed,
        "",
        BOARD_FOOTER,
        "",
    ]
    text = "\n".join(lines)
    assert_language_clean(text)
    return text
