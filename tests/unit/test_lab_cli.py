"""CLI smoke: lab status stays hard-gated; thesis commands enforce Phase 2 gates."""

from __future__ import annotations

import json
from pathlib import Path

from mm_lab_cli.cli import main

ROOT = Path(__file__).resolve().parents[2]


def test_lab_thesis_new_requires_intent(tmp_path: Path, capsys) -> None:
    rc = main(
        [
            "thesis",
            "new",
            "--research-root",
            str(tmp_path / "research"),
            "--templates-root",
            str(ROOT / "templates"),
            "--repo-root",
            str(tmp_path),
            "--no-db",
        ]
    )
    assert rc == 2
    assert "cannot create/mark thesis without intent" in capsys.readouterr().out


def test_lab_status_mentions_phase4_and_hard_gate(capsys) -> None:
    assert main(["status"]) == 0
    out = capsys.readouterr().out
    assert "Phase 4" in out
    assert "HARD-GATED" in out
    assert "ingested_at" in out
    assert "as_of_knowledge" in out
    assert "published_at and market_time never gate knowledge" in out
    assert "Research cannot access trading credentials" in out
    assert "lab brief" in out
    assert "lab backtest" in out
    assert "lab paper" in out
    assert "lab quant-review" in out
    assert "lab data source-health" in out


def test_lab_ingest_fails_closed_when_object_store_misconfigured(monkeypatch, capsys) -> None:
    monkeypatch.delenv("MM_OBJECT_STORE", raising=False)
    monkeypatch.delenv("MINIO_ENDPOINT", raising=False)
    monkeypatch.delenv("S3_ENDPOINT", raising=False)
    monkeypatch.delenv("MINIO_ACCESS_KEY", raising=False)
    monkeypatch.delenv("MINIO_ROOT_USER", raising=False)
    monkeypatch.delenv("AWS_ACCESS_KEY_ID", raising=False)
    monkeypatch.delenv("MINIO_SECRET_KEY", raising=False)
    monkeypatch.delenv("MINIO_ROOT_PASSWORD", raising=False)
    monkeypatch.delenv("AWS_SECRET_ACCESS_KEY", raising=False)
    rc = main(["ingest", "--fixture", str(ROOT / "tests" / "fixtures" / "hl_window.json")])
    assert rc == 2
    err = capsys.readouterr().err
    assert "Failing closed" in err
    assert "raw_object" in err


def test_lab_thesis_new_and_in_skeptic_gate(tmp_path: Path, capsys) -> None:
    research = tmp_path / "research"
    common = [
        "--research-root",
        str(research),
        "--templates-root",
        str(ROOT / "templates"),
        "--repo-root",
        str(tmp_path),
        "--no-db",
    ]
    assert (
        main(
            [
                "thesis",
                "new",
                "--goal",
                "BTC funding fade after crowding",
                "--owner",
                "Research",
                "--instrument",
                "BTC",
                *common,
            ]
        )
        == 0
    )
    created = json.loads(capsys.readouterr().out)
    slug = created["slug"]
    assert created["status"] == "in_research"
    assert (research / str(Path(created["path"]).parent.name) / slug / "intent.md").is_file() or (
        Path(created["path"]) / "intent.md"
    ).is_file()

    assert main(["thesis", "advance", slug, "--to", "in_skeptic", *common]) == 2
    err = capsys.readouterr().out
    assert "cannot mark in_skeptic without evidence links" in err

    assert (
        main(
            [
                "thesis",
                "link-evidence",
                slug,
                "--observation",
                "01ARZ3NDEKTSV4RRFFQ69G5FAV",
                "--role",
                "supports",
                *common,
            ]
        )
        == 0
    )
    capsys.readouterr()
    assert main(["skeptic", "open", slug, "--reviewer", "Skeptic", *common]) == 0
    capsys.readouterr()
    assert main(["skeptic", "record", slug, "--verdict", "reject", "--reviewer", "Skeptic", *common]) == 0
    rejected = json.loads(capsys.readouterr().out)
    assert rejected["status"] == "rejected"
    assert main(["thesis", "list", "--status", "rejected", *common]) == 0
    listed = json.loads(capsys.readouterr().out)
    assert listed["count"] >= 1
    assert any(row["slug"] == slug and row["status"] == "rejected" for row in listed["theses"])
