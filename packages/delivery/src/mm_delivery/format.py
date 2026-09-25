"""MarkdownV2-safe escaping and 4096-char chunking with ordered sequencing."""

from __future__ import annotations

TELEGRAM_MAX_MESSAGE_CHARS = 4096
MARKDOWN_V2_SPECIAL = set(r"_*[]()~`>#+-=|{}.!\\")


def escape_markdown_v2(text: str) -> str:
    """Escape Telegram MarkdownV2 reserved characters. Does not invent content.

    A fenced block (a line that is exactly ```) is a pre block. Inside it only
    ``\\`` and `` ` `` are escaped, so a fixed-width headline survives. Outside
    the fence every reserved character is escaped. Telegram does not render
    pipe tables; a fence is how a column block stays aligned.
    """
    if "```" not in text:
        return _escape_plain(text)
    lines = text.split("\n")
    out: list[str] = []
    in_fence = False
    for line in lines:
        if line.strip() == "```":
            in_fence = not in_fence
            out.append("```")
            continue
        if in_fence:
            out.append(line.replace("\\", "\\\\").replace("`", "\\`"))
        else:
            out.append(_escape_plain(line))
    return "\n".join(out)


def _escape_plain(text: str) -> str:
    out: list[str] = []
    for ch in text:
        if ch in MARKDOWN_V2_SPECIAL:
            out.append("\\")
        out.append(ch)
    return "".join(out)


def sequence_prefix(index: int, total: int) -> str:
    """Escaped ``[i/n]`` header counted against the 4096 limit."""
    return escape_markdown_v2(f"[{index}/{total}]\n")


def chunk_markdown_v2(text: str, *, limit: int = TELEGRAM_MAX_MESSAGE_CHARS) -> tuple[str, ...]:
    """Escape then split into ordered chunks, each ``<= limit`` (Telegram sendMessage cap)."""
    if limit < 32:
        raise ValueError("chunk limit too small for a sequenced Telegram message")
    escaped = escape_markdown_v2(text)
    if len(escaped) <= limit:
        return (escaped,)
    # Worst-case prefix ``[999/999]\\n`` after escape is well under 32 chars.
    prefix_budget = len(sequence_prefix(1, 999))
    body_limit = max(1, limit - prefix_budget)
    bodies = _split_escaped(escaped, body_limit)
    total = len(bodies)
    chunks: list[str] = []
    for i, body in enumerate(bodies, start=1):
        prefix = sequence_prefix(i, total)
        combined = prefix + body
        if len(combined) > limit:
            # Digit-width grew; re-prefix with the true total (already known).
            prefix = sequence_prefix(i, total)
            combined = prefix + body[: max(1, limit - len(prefix))]
        chunks.append(combined)
    return tuple(chunks)


def _split_escaped(escaped: str, budget: int) -> list[str]:
    """Split already-escaped text on newline/space without breaking ``\\x`` pairs."""
    if budget <= 0:
        raise ValueError("chunk budget must be positive")
    parts: list[str] = []
    cursor = 0
    n = len(escaped)
    while cursor < n:
        end = min(n, cursor + budget)
        if end < n:
            window = escaped[cursor:end]
            cut = window.rfind("\n")
            if cut < budget // 4:
                cut = window.rfind(" ")
            if cut <= 0:
                cut = len(window)
            else:
                cut += 1
            piece = window[:cut]
        else:
            piece = escaped[cursor:end]
        if piece.endswith("\\"):
            piece = piece[:-1]
        if not piece:
            piece = escaped[cursor : cursor + 1]
        parts.append(piece)
        cursor += len(piece)
    return parts
