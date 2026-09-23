"""Split a Market Pulse brief into sequential Telegram cards.

Product order is the Stage A card list, not a 4096-character chop of one body.
Empty cards are omitted. A card that is only dashes is omitted. Stage B/C
panels (positioning, scenarios, regime labels, confidence) are not invented:
regime stays ``INSUFFICIENT DATA`` inside the executive card, and positioning
/ scenarios are skipped until methodology and stored history exist.
"""

from __future__ import annotations

import re

from mm_briefing.health import CARD_ORDER, INSUFFICIENT_DATA, load_presentation_config

_PULSE_TITLES = ("# US Close Brief", "# US Pre-Market Brief")

# Section heading (without hashes) → card id.
HEADING_CARD = {
    "Data health": "dashboard",
    "Data quality by source": "audit",
    "Cross-asset snapshot": "macro",
    "What changed since prior US close": "audit",
    "What moved": "macro",
    "What was unexpected": "audit",
    "Lab right/wrong hooks": "audit",
    "Assumption changes": "audit",
    "Monitor into Asia / Europe / next US": "catalysts",
    "Today's market-event calendar": "catalysts",
    "Cross-asset divergences": "audit",
    "Hyperliquid market structure": "crypto",
    "Hyperliquid into the next session": "crypto",
    "Watchlist": "audit",
}

_EMPTY_CALENDAR = (
    "none in the look-ahead window",
    "no dated catalysts remaining in the look-ahead window",
)


def is_pulse_brief(markdown: str) -> bool:
    for line in markdown.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        return stripped.startswith(_PULSE_TITLES)
    return False


def message_texts_for_pulse(markdown: str) -> tuple[str, ...] | None:
    """Card bodies for delivery, or None when this markdown is not a pulse brief."""
    if not is_pulse_brief(markdown):
        return None
    cards = split_brief_cards(markdown)
    if not cards:
        return None
    return tuple(body for _card_id, body in cards)


def split_brief_cards(markdown: str) -> tuple[tuple[str, str], ...]:
    """Return ``(card_id, body)`` in configured order, skipping empty cards."""
    if not is_pulse_brief(markdown):
        return ()
    order = load_presentation_config().card_order or CARD_ORDER
    preamble, sections, trailing = _split_sections(markdown)
    if sections:
        title, body = sections[-1]
        body, footer = _peel_footer(body)
        sections[-1] = (title, body)
        if footer:
            trailing = f"{trailing}\n\n{footer}".strip() if trailing else footer
    buckets: dict[str, list[str]] = {card_id: [] for card_id in order}
    if _meaningful(preamble):
        buckets.setdefault("executive", []).append(preamble.strip())
    for title, body in sections:
        card_id = HEADING_CARD.get(title, "audit")
        if card_id not in buckets:
            buckets[card_id] = []
        if not _section_keep(title, body):
            continue
        if card_id == "macro" and not _macro_has_print(body):
            # All-n/a price table is not a dashboard of dashes. Keep the rows on audit.
            buckets.setdefault("audit", []).append(f"## {title}\n\n{body.strip()}")
            continue
        buckets[card_id].append(f"## {title}\n\n{body.strip()}")
    if _meaningful(trailing):
        buckets.setdefault("audit", []).append(trailing.strip())
    built: list[tuple[str, str]] = []
    for card_id in order:
        parts = [part.strip() for part in buckets.get(card_id, []) if part.strip()]
        if not parts:
            continue
        text = "\n\n".join(parts).strip()
        if not _meaningful(text) or _is_dash_card(text):
            continue
        built.append((card_id, text))
    total = len(built)
    numbered: list[tuple[str, str]] = []
    for index, (card_id, text) in enumerate(built, start=1):
        body = f"{card_id} ({index}/{total})\n\n{text}\n"
        numbered.append((card_id, body))
    return tuple(numbered)


def _split_sections(markdown: str) -> tuple[str, list[tuple[str, str]], str]:
    lines = markdown.replace("\r\n", "\n").split("\n")
    preamble: list[str] = []
    sections: list[tuple[str, str]] = []
    current_title: str | None = None
    current: list[str] = []
    started = False
    for line in lines:
        if line.startswith("## "):
            started = True
            if current_title is None:
                preamble = current
            else:
                sections.append((current_title, "\n".join(current).strip()))
            current_title = line[3:].strip()
            current = []
            continue
        current.append(line)
    trailing = ""
    if not started:
        return "\n".join(lines).strip(), [], ""
    if current_title is None:
        preamble = current
    else:
        sections.append((current_title, "\n".join(current).strip()))
    return "\n".join(preamble).strip(), sections, trailing


def _peel_footer(body: str) -> tuple[str, str]:
    marker = "**Informational only"
    index = body.find(marker)
    if index < 0:
        return body, ""
    head = body[:index].rstrip()
    if head.endswith("---"):
        head = head[: -len("---")].rstrip()
    return head, body[index:].strip()


def _meaningful(text: str) -> bool:
    stripped = text.strip()
    if not stripped:
        return False
    if stripped == INSUFFICIENT_DATA:
        return True
    return True


def _section_keep(title: str, body: str) -> bool:
    lowered = " ".join(body.lower().split())
    if title in {"Today's market-event calendar"} and _only_empty_calendar(lowered):
        return False
    if title.startswith("Hyperliquid") and "no hyperliquid observations" in lowered and "obs " not in lowered:
        return False
    if not body.strip():
        return False
    return True


def _only_empty_calendar(lowered: str) -> bool:
    # Drop the source/as-of preamble lines and see if the only event is "none".
    if any(phrase in lowered for phrase in _EMPTY_CALENDAR):
        # A real dated event has a timestamp-like digit group beyond the as-of line.
        event_lines = [
            line
            for line in lowered.splitlines()
            if line.strip().startswith("- ") or line.strip().startswith("* ")
        ]
        if not event_lines:
            return True
        return all(any(phrase in line for phrase in _EMPTY_CALENDAR) for line in event_lines)
    return False


def _macro_has_print(body: str) -> bool:
    for line in body.splitlines():
        stripped = line.strip()
        if stripped.startswith("|") and not stripped.startswith("|---") and not stripped.lower().startswith("| slot"):
            cells = [cell.strip() for cell in stripped.strip("|").split("|")]
            if len(cells) >= 3 and cells[2].lower() not in {"n/a", "—", "-", ""}:
                return True
        match = re.search(r"last\s+([^\s/]+)", stripped, flags=re.IGNORECASE)
        if match and match.group(1).lower() not in {"n/a", "—", "-"}:
            return True
    return False


def _is_dash_card(text: str) -> bool:
    """True when the card has no letters or digits beyond the card id line."""
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if not lines:
        return True
    body = "\n".join(lines[1:]) if len(lines) > 1 else ""
    if not body.strip():
        return True
    alnum = re.sub(r"[^0-9A-Za-z]+", "", body)
    return len(alnum) == 0
