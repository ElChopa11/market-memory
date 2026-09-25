"""Gated ingest persist workflow. Brief stays --no-db. Thursday cron untouched."""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
INGEST = ROOT / ".github" / "workflows" / "ingest-persist.yml"
HYBRID = ROOT / ".github" / "workflows" / "hybrid-sydney-morning.yml"


def _ingest() -> str:
    assert INGEST.is_file()
    return INGEST.read_text(encoding="utf-8")


def _hybrid() -> str:
    assert HYBRID.is_file()
    return HYBRID.read_text(encoding="utf-8")


def _hybrid_jobs(text: str) -> tuple[str, str]:
    stage1_key = "\n  stage1-stamp:\n"
    brief_key = "\n  brief-and-deliver:\n"
    stage1_start = text.index(stage1_key)
    brief_start = text.index(brief_key)
    return text[stage1_start:brief_start], text[brief_start:]


def test_ingest_persist_is_dispatch_only_and_gated() -> None:
    text = _ingest()
    assert "workflow_dispatch:" in text
    assert "schedule:" not in text
    assert "cron:" not in text
    assert "i_mean_it_persist:" in text
    assert "type: boolean" in text
    assert "default: false" in text
    assert text.count("default: false") == 1
    gate = (
        "if: github.event_name == 'workflow_dispatch' && "
        "(inputs.i_mean_it_persist == true || github.event.inputs.i_mean_it_persist == 'true')"
    )
    assert gate in text
    assert "I_MEAN_IT_PERSIST" in text
    assert 'I_MEAN_IT_PERSIST}" != "true"' in text
    commands = [line.strip() for line in text.splitlines() if "uv run lab ingest" in line]
    assert commands == ["uv run lab ingest --window 7d"]
    assert "--no-db" not in commands[0]
    assert "--no-objects" not in commands[0]
    assert "--fixture" not in commands[0]
    assert "uv run lab migrate" not in text
    assert not any("lab migrate" in line and not line.lstrip().startswith("#") for line in text.splitlines())
    jobs = text.split("\njobs:\n", 1)[1]
    assert "brief close" not in jobs
    assert "deliver pack" not in jobs
    assert "secrets.TELEGRAM" not in text
    assert "TELEGRAM_BOT_TOKEN:" not in text
    assert "TELEGRAM_CHAT_ID" not in text


def test_ingest_persist_wires_dsn_and_r2_without_bucket_secret() -> None:
    text = _ingest()
    assert "POSTGRES_DSN: ${{ secrets.POSTGRES_DSN }}" in text
    assert "MINIO_ENDPOINT: ${{ secrets.MINIO_ENDPOINT }}" in text
    assert "MINIO_ACCESS_KEY: ${{ secrets.MINIO_ACCESS_KEY }}" in text
    assert "MINIO_SECRET_KEY: ${{ secrets.MINIO_SECRET_KEY }}" in text
    assert "secrets.MINIO_BUCKET" not in text
    assert re.search(r"^[\t ]*MINIO_BUCKET:", text, flags=re.M) is None
    # Region is job env, not a secret.
    assert "S3_REGION: auto" in text
    assert "secrets.S3_REGION" not in text
    assert "contents: read" in text
    assert "contents: write" not in text
    assert "git push" not in text


def test_hybrid_sydney_morning_schedule_and_brief_no_db_unchanged() -> None:
    text = _hybrid()
    stage1, brief = _hybrid_jobs(text)
    assert text.count('cron: "30 20 * * 0-4"') == 1
    assert 'cron: "30 19 * * 0-4"' not in text
    assert "schedule:" in text
    assert "i_mean_it_persist" not in text
    assert "lab ingest" not in text
    assert "POSTGRES_DSN" not in text
    assert "MINIO_" not in text
    assert "S3_REGION" not in text
    assert "--no-db" in stage1
    assert "lab brief close --live --no-db" in brief
    assert "--no-db" in brief
    assert re.search(r"lab deliver pack[\s\S]*--no-db", brief) is not None
    # Deliver step still passes the flag as its own argv line.
    assert "\n            --no-db \\\n" in brief or "\n            --no-db\n" in brief
