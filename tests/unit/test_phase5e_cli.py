"""lab deliver / lab desk run delivery CLI. Dry-run default. No live Telegram."""

from __future__ import annotations

import json
from pathlib import Path

from mm_common.hashing import sha256_hex
from mm_lab_cli.cli import main

ROOT = Path(__file__).resolve().parents[2]
FIXTURE = ROOT / "tests" / "fixtures" / "phase5d" / "frozen_day.json"
PACK_MD = ROOT / "tests" / "fixtures" / "phase5e" / "desk-pack.md"
GOLDEN_SHA = ROOT / "tests" / "fixtures" / "phase5e" / "frozen_telegram_payload.sha256"


def test_lab_deliver_pack_no_send_golden(tmp_path: Path, capsys) -> None:
    args = [
        "deliver",
        "pack",
        "--desk",
        "ops",
        "--from-markdown",
        str(PACK_MD),
        "--as-of",
        "2026-09-18T00:00:00Z",
        "--no-send",
        "--repo-root",
        str(ROOT),
        "--out",
        str(tmp_path),
    ]
    assert main(args) == 0
    first = json.loads(capsys.readouterr().out)
    assert main(args) == 0
    second = json.loads(capsys.readouterr().out)
    assert first["payload_hash"] == second["payload_hash"]
    assert first["sent"] is False
    assert first["no_send"] is True
    sha_path = tmp_path / "briefs" / "2026-09-18" / "telegram-payload.sha256"
    envelope = (tmp_path / "briefs" / "2026-09-18" / "telegram-payload.json").read_bytes()
    assert sha_path.read_text(encoding="utf-8").strip() == sha256_hex(envelope)
    assert sha_path.read_text(encoding="utf-8").strip() == GOLDEN_SHA.read_text(encoding="utf-8").strip()
    assert first["payload_hash"] == GOLDEN_SHA.read_text(encoding="utf-8").strip()


def test_lab_deliver_from_coord_fixture(tmp_path: Path, capsys) -> None:
    rc = main(
        [
            "deliver",
            "--desk",
            "ops",
            "--fixture",
            str(FIXTURE),
            "--no-send",
            "--repo-root",
            str(ROOT),
            "--out",
            str(tmp_path),
        ]
    )
    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["sent"] is False
    assert payload["no_send"] is True
    assert (tmp_path / "briefs" / payload["as_of"][:10] / "telegram-payload.json").is_file() or (
        tmp_path / "briefs" / "2026-09-18" / "telegram-payload.json"
    ).is_file()


def test_lab_desk_run_send_without_token_fails_closed(capsys) -> None:
    rc = main(
        [
            "desk",
            "run",
            "--all",
            "--fixture",
            str(FIXTURE),
            "--repo-root",
            str(ROOT),
            "--send",
        ]
    )
    out = capsys.readouterr()
    assert rc == 2
    blob = out.out + out.err
    assert "missing_env" in blob or "TELEGRAM_BOT_TOKEN" in blob or "sent" in blob.lower()


def test_lab_deliver_test_without_i_mean_it_is_dry_run(tmp_path: Path, capsys) -> None:
    rc = main(
        [
            "deliver",
            "test",
            "--desk",
            "ops",
            "--repo-root",
            str(ROOT),
            "--out",
            str(tmp_path),
        ]
    )
    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["sent"] is False
    assert payload["test"] is True
    assert payload["no_send"] is True


def test_lab_deliver_inbound_status(capsys) -> None:
    assert main(["deliver", "inbound", "/status"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["ok"] is True
    assert payload["trading"] is False


def test_lab_deliver_inbound_buy_refused(capsys) -> None:
    assert main(["deliver", "inbound", "/buy BTC"]) == 2
    payload = json.loads(capsys.readouterr().out)
    assert payload["ok"] is False
    assert payload["trading"] is True


def test_lab_status_mentions_deliver(capsys) -> None:
    assert main(["status"]) == 0
    out = capsys.readouterr().out
    assert "Deliver" in out or "deliver" in out
    assert "HARD-GATED" in out
    assert "no-send" in out.lower() or "5e" in out
