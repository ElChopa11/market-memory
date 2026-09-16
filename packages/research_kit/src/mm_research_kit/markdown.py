"""Get/set `- **Field:** value` lines and `##` sections in research artifacts."""

from __future__ import annotations

import re

_FIELD_LINE = re.compile(r"^(- \*\*(.+?):\*\*)(\s*)(.*)$")


def get_field(text: str, field: str) -> str | None:
    wanted = field.strip().lower()
    prefix_hit: str | None = None
    for line in text.splitlines():
        match = _FIELD_LINE.match(line)
        if not match:
            continue
        name = match.group(2).strip()
        value = match.group(4).strip()
        if name.lower() == wanted:
            return value
        if prefix_hit is None and name.lower().startswith(wanted):
            prefix_hit = value
    return prefix_hit


def set_field(text: str, field: str, value: str) -> str:
    wanted = field.strip().lower()
    ended_with_newline = text.endswith("\n")
    lines = text.splitlines()
    idx = _find_field_line(lines, wanted, exact=True)
    if idx is None:
        idx = _find_field_line(lines, wanted, exact=False)
    if idx is None:
        raise KeyError(f"markdown field not found: {field}")
    match = _FIELD_LINE.match(lines[idx])
    assert match is not None
    lines[idx] = f"- **{match.group(2)}:** {value}"
    result = "\n".join(lines)
    if ended_with_newline or text == "":
        result += "\n"
    return result


def _find_field_line(lines: list[str], wanted: str, *, exact: bool) -> int | None:
    for idx, line in enumerate(lines):
        match = _FIELD_LINE.match(line)
        if not match:
            continue
        name = match.group(2).strip().lower()
        if exact and name == wanted:
            return idx
        if not exact and name.startswith(wanted):
            return idx
    return None


def set_section_body(text: str, heading: str, body: str) -> str:
    """Replace content under ``## heading`` until the next ``## `` heading."""
    ended_with_newline = text.endswith("\n")
    lines = text.splitlines()
    start = None
    needle = f"## {heading}"
    for idx, line in enumerate(lines):
        if line.strip() == needle:
            start = idx
            break
    if start is None:
        raise KeyError(f"markdown section not found: {heading}")
    end = len(lines)
    for idx in range(start + 1, len(lines)):
        if lines[idx].startswith("## "):
            end = idx
            break
    block = [lines[start], ""]
    stripped = body.strip()
    if stripped:
        block.extend(stripped.splitlines())
        block.append("")
    result_lines = lines[:start] + block + lines[end:]
    result = "\n".join(result_lines)
    if ended_with_newline or text == "":
        result += "\n"
    return result


def append_bullet_under_heading(text: str, heading: str, bullet: str) -> str:
    ended_with_newline = text.endswith("\n")
    lines = text.splitlines()
    start = None
    needle = f"## {heading}"
    for idx, line in enumerate(lines):
        if line.strip() == needle:
            start = idx
            break
    if start is None:
        raise KeyError(f"markdown section not found: {heading}")
    end = len(lines)
    for idx in range(start + 1, len(lines)):
        if lines[idx].startswith("## "):
            end = idx
            break
    section = lines[start:end]
    if any(line.strip() == bullet for line in section):
        return text if ended_with_newline or not text else text
    insert_at = end
    while insert_at > start + 1 and lines[insert_at - 1].strip() == "":
        insert_at -= 1
    result_lines = lines[:insert_at] + [bullet] + lines[insert_at:]
    result = "\n".join(result_lines)
    if ended_with_newline or text == "":
        result += "\n"
    return result


def first_token(value: str | None) -> str:
    if not value:
        return ""
    token = value.split("/")[0].strip().split()[0].strip()
    return token.lower()
