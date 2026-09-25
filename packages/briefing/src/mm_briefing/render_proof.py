"""Live close render for workflow mode ``render_proof``.

Same path as ``lab brief close --live --no-db``: ``generate_from_sources(..., live=True)``.
No completion stamp, receipt, capture, Neon session, deliver, Telegram send, or Healthchecks ping.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

from mm_briefing.config import load_briefing_settings, repo_root
from mm_briefing.engine import default_macro_fetcher, generate_from_sources
from mm_common.time import utcnow


def render_close_proof(*, root: Path | None = None, generated_at=None) -> str:
    """Return the close markdown. Callers print it. This function does not write a capture."""
    base = repo_root(root)
    settings = load_briefing_settings(base)
    as_of = generated_at or utcnow()
    doc, _decision = generate_from_sources(
        "close",
        settings=settings,
        as_of=as_of,
        macro_fetcher=default_macro_fetcher(settings, None),
        session=None,
        fixture=None,
        generated_at=as_of,
        live=True,
    )
    if doc is None:
        raise SystemExit("close render produced no document")
    return doc.markdown


def emit_render_proof(text: str) -> None:
    """Print the message and, on Actions, the step summary. Counts are len(text) and splitlines()."""
    chars = len(text)
    lines = len(text.splitlines())
    print(text)
    print(f"characters={chars}")
    print(f"lines={lines}")
    raw = os.environ.get("GITHUB_STEP_SUMMARY")
    if not raw:
        return
    Path(raw).write_text(
        "\n".join(
            [
                "## Render proof",
                "",
                f"characters={chars}",
                f"lines={lines}",
                "",
                "````",
                text.rstrip("\n"),
                "````",
                "",
            ]
        ),
        encoding="utf-8",
    )


def main() -> int:
    emit_render_proof(render_close_proof())
    return 0


if __name__ == "__main__":
    sys.exit(main())
