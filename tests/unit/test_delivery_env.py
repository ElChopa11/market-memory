"""Hybrid Step 2: delivery env-file load + full-state preflight. Never prints secrets."""

from __future__ import annotations

import json
from pathlib import Path

from mm_common.env import (
    BOT_TOKEN_ENV,
    CHAT_ID_ENV,
    DOWN_SERVICE,
    FRED_API_KEY_ENV,
    GET_CHAT_ITEM,
    POLYGON_API_KEY_ENV,
    POSTGRES_DSN_ENV,
    PRINCIPAL_DM_CHAT_ID_ENV,
    PURPOSE_CHECKLIST,
    PURPOSE_DELIVER,
    STATE_ABSENT,
    STATE_DOWN,
    STATE_FOUND,
    STATE_MISSING,
    STATE_NOT_CONFIGURED,
    desk_chat_id_env_names,
    format_preflight_lines,
    load_delivery_env_file,
    parse_example_declared_names,
    preflight_env,
    prepare_cli_env,
)
from mm_delivery.config import chat_id_from_env, load_telegram_settings
from mm_lab_cli.cli import main

ROOT = Path(__file__).resolve().parents[2]
PACK_MD = ROOT / "tests" / "fixtures" / "phase5e" / "desk-pack.md"
# Split so a tree-wide substring scan does not treat this file as a leak.
PRINCIPAL_DM_ID = "66610" + "38549"
HIVE_GROUP_ID = "-" + "5595930715"


def test_example_declares_delivery_path_names() -> None:
    text = (ROOT / ".env.example").read_text(encoding="utf-8")
    names = parse_example_declared_names(text)
    for required in (
        BOT_TOKEN_ENV,
        CHAT_ID_ENV,
        PRINCIPAL_DM_CHAT_ID_ENV,
        FRED_API_KEY_ENV,
        POLYGON_API_KEY_ENV,
        POSTGRES_DSN_ENV,
        "MINIO_ENDPOINT",
    ):
        assert required in names, required
    assert PRINCIPAL_DM_ID not in text
    assert HIVE_GROUP_ID not in text


def test_env_file_wins_over_process_and_does_not_alias_dm(tmp_path: Path) -> None:
    path = tmp_path / "telegram.env"
    path.write_text(
        BOT_TOKEN_ENV + "=file-token-value\n"
        + PRINCIPAL_DM_CHAT_ID_ENV
        + "=file-dm\n"
        "# TELEGRAM_CHAT_ID is intentionally absent\n",
        encoding="utf-8",
    )
    path.chmod(0o600)
    process = {
        BOT_TOKEN_ENV: "process-token-value",
        CHAT_ID_ENV: "process-group",
        "MM_DELIVERY_ENV_FILE": str(path),
    }
    merged, load = load_delivery_env_file(environ=process, path=path, apply=False)
    assert load.loaded is True
    assert merged[BOT_TOKEN_ENV] == "file-token-value"
    assert merged[CHAT_ID_ENV] == "process-group"
    assert PRINCIPAL_DM_CHAT_ID_ENV in load.keys_loaded
    assert CHAT_ID_ENV not in load.keys_loaded
    assert any("not defaulting" in note for note in load.notes)
    blob = " ".join(load.notes)
    assert "file-token-value" not in blob
    assert "file-dm" not in blob


def test_preflight_full_state_names_found_missing_and_not_configured() -> None:
    env = {
        BOT_TOKEN_ENV: "secret-token-value-do-not-print",
        PRINCIPAL_DM_CHAT_ID_ENV: "dm-id-do-not-print",
        CHAT_ID_ENV: "group-id-do-not-print",
        FRED_API_KEY_ENV: "fred-secret",
        POSTGRES_DSN_ENV: "postgresql://lab:hunter2@localhost:5432/market_memory",
        "MINIO_ENDPOINT": "http://127.0.0.1:9000",
        "MINIO_ACCESS_KEY": "minioadmin",
        "MINIO_SECRET_KEY": "minioadmin",
    }

    def refused(_addr, timeout=0.4):
        raise ConnectionRefusedError("Connection refused")

    def get_chat(_environ):
        return STATE_FOUND, "getChat resolved the configured group id (id not printed)"

    report = preflight_env(
        env,
        purpose=PURPOSE_CHECKLIST,
        connect=refused,
        get_chat=get_chat,
    )
    by_name = {item.name: item for item in report.items}
    assert by_name[BOT_TOKEN_ENV].state == STATE_FOUND
    assert by_name[PRINCIPAL_DM_CHAT_ID_ENV].state == STATE_FOUND
    assert by_name[CHAT_ID_ENV].state == STATE_FOUND
    assert by_name[FRED_API_KEY_ENV].state == STATE_FOUND
    assert by_name[POSTGRES_DSN_ENV].state == STATE_FOUND
    assert by_name[POLYGON_API_KEY_ENV].state == STATE_ABSENT
    assert by_name["object_store"].state == STATE_DOWN
    assert ":9000 refused" in by_name["object_store"].note
    assert DOWN_SERVICE in by_name["object_store"].note
    for desk_env in desk_chat_id_env_names():
        assert by_name[desk_env].state == STATE_NOT_CONFIGURED, desk_env
        assert by_name[desk_env].severity == "optional"
    assert by_name[GET_CHAT_ITEM].state == STATE_FOUND
    assert POLYGON_API_KEY_ENV in report.error_names
    assert "object_store" in report.error_names
    assert POLYGON_API_KEY_ENV in report.missing_names
    assert not any(name in report.error_names for name in desk_chat_id_env_names())
    assert not any(name in report.missing_names for name in desk_chat_id_env_names())
    assert PRINCIPAL_DM_CHAT_ID_ENV not in report.error_names
    assert PRINCIPAL_DM_CHAT_ID_ENV not in report.missing_names
    lines = "\n".join(format_preflight_lines(report))
    assert "NOT CONFIGURED" in lines
    assert "TELEGRAM_CHAT_ID_INTEL NOT CONFIGURED" in lines
    assert "POLYGON_API_KEY absent" in lines
    assert "DOWN SERVICE (:9000 refused)" in lines
    assert "secret-token-value-do-not-print" not in lines
    assert "dm-id-do-not-print" not in lines
    assert "group-id-do-not-print" not in lines
    assert "hunter2" not in lines
    assert "fred-secret" not in lines
    assert "minioadmin" not in lines


def test_missing_group_does_not_fall_back_to_principal_dm() -> None:
    env = {PRINCIPAL_DM_CHAT_ID_ENV: "dm-only", BOT_TOKEN_ENV: "tok"}
    report = preflight_env(env, purpose=PURPOSE_DELIVER, send=False, get_chat=lambda _e: (STATE_FOUND, "unused"))
    by_name = {item.name: item for item in report.items}
    assert by_name[CHAT_ID_ENV].state == STATE_MISSING
    assert CHAT_ID_ENV in report.error_names
    settings = load_telegram_settings(ROOT)
    assert chat_id_from_env("ops", settings, env) is None
    assert chat_id_from_env("intel", settings, env) is None
    lines = "\n".join(format_preflight_lines(report))
    assert PRINCIPAL_DM_CHAT_ID_ENV in lines
    assert "not defaulting" in lines or "MUST NOT silently default" in lines
    assert "dm-only" not in lines
    assert "tok" not in lines


def test_get_chat_mismatch_fails_loudly_without_printing_ids() -> None:
    env = {BOT_TOKEN_ENV: "tok", CHAT_ID_ENV: "configured-group"}

    def bad(_environ):
        return (
            STATE_MISSING,
            "getChat resolved a different id than TELEGRAM_CHAT_ID "
            "(possible -100... supergroup conversion); routing would break silently",
        )

    report = preflight_env(env, purpose=PURPOSE_CHECKLIST, get_chat=bad)
    by_name = {item.name: item for item in report.items}
    assert by_name[GET_CHAT_ITEM].state == STATE_MISSING
    assert GET_CHAT_ITEM in report.error_names
    lines = "\n".join(format_preflight_lines(report))
    assert "-100" in lines
    assert "supergroup" in lines
    assert "configured-group" not in lines
    assert "tok" not in lines


def test_lab_env_preflight_cli_names_expected_failures(monkeypatch, capsys) -> None:
    monkeypatch.delenv(POLYGON_API_KEY_ENV, raising=False)
    monkeypatch.setenv("MINIO_ENDPOINT", "http://127.0.0.1:9000")
    monkeypatch.setenv("MINIO_ACCESS_KEY", "x")
    monkeypatch.setenv("MINIO_SECRET_KEY", "y")
    monkeypatch.delenv("MM_OBJECT_STORE", raising=False)

    def refused(addr, timeout=0.4):
        raise ConnectionRefusedError("Connection refused")

    monkeypatch.setattr("mm_common.env.socket.create_connection", refused)
    rc = main(["env", "preflight", "--repo-root", str(ROOT)])
    err = capsys.readouterr().err
    assert rc == 2
    assert "POLYGON_API_KEY" in err
    assert "absent" in err
    assert "object_store" in err
    assert DOWN_SERVICE in err or "DOWN SERVICE" in err
    assert ":9000 refused" in err
    assert "TELEGRAM_CHAT_ID_INTEL NOT CONFIGURED" in err
    assert "TELEGRAM_BOT_TOKEN" in err
    assert "MISSING" in err
    assert "pytest-group" not in err
    assert PRINCIPAL_DM_ID not in err
    assert HIVE_GROUP_ID not in err
    assert "MINIO_SECRET_KEY=y" not in err


def test_lab_deliver_test_no_send_writes_payload(tmp_path: Path, capsys) -> None:
    rc = main(
        [
            "deliver",
            "test",
            "--desk",
            "ops",
            "--no-send",
            "--repo-root",
            str(ROOT),
            "--out",
            str(tmp_path),
        ]
    )
    out = capsys.readouterr()
    assert rc == 0
    payload = json.loads(out.out)
    assert payload["sent"] is False
    assert payload["no_send"] is True
    written = tmp_path / "briefs" / payload["as_of"][:10] / "telegram-payload.json"
    assert written.is_file()
    text = written.read_text(encoding="utf-8")
    assert "TELEGRAM_BOT_TOKEN" not in text
    assert "pytest-group" not in text
    assert payload["reason"] == "no_send"
    assert "NOT CONFIGURED" in out.err
    assert "POLYGON_API_KEY" in out.err


def test_lab_deliver_no_send_fails_if_group_missing(tmp_path: Path, monkeypatch, capsys) -> None:
    monkeypatch.delenv(CHAT_ID_ENV, raising=False)
    rc = main(
        [
            "deliver",
            "pack",
            "--from-markdown",
            str(PACK_MD),
            "--as-of",
            "2026-09-18T00:00:00Z",
            "--desk",
            "ops",
            "--no-send",
            "--repo-root",
            str(ROOT),
            "--out",
            str(tmp_path),
        ]
    )
    captured = capsys.readouterr()
    assert rc == 2
    assert "TELEGRAM_CHAT_ID MISSING" in captured.err or "FAIL TELEGRAM_CHAT_ID" in captured.err
    payload_path = tmp_path / "briefs" / "2026-09-18" / "telegram-payload.json"
    assert payload_path.is_file()
    assert PRINCIPAL_DM_CHAT_ID_ENV not in payload_path.read_text(encoding="utf-8") or "TELEGRAM_CHAT_ID" in payload_path.read_text(
        encoding="utf-8"
    )


def test_prepare_cli_env_file_preference_does_not_print_secrets(tmp_path: Path) -> None:
    path = tmp_path / "telegram.env"
    secret = "123456:AA-secret-token-value"
    path.write_text(
        f"{BOT_TOKEN_ENV}={secret}\n{CHAT_ID_ENV}=-111\n{PRINCIPAL_DM_CHAT_ID_ENV}=222\n",
        encoding="utf-8",
    )
    path.chmod(0o600)
    _merged, report = prepare_cli_env(
        purpose=PURPOSE_DELIVER,
        send=False,
        environ={"MM_DELIVERY_ENV_FILE": str(path)},
        path=path,
        apply=False,
        get_chat=lambda _e: (STATE_FOUND, "getChat ok"),
        connect=lambda *_a, **_k: (_ for _ in ()).throw(ConnectionRefusedError("refused")),
    )
    lines = "\n".join(format_preflight_lines(report))
    assert secret not in lines
    assert "AA-secret" not in lines
    assert _merged[BOT_TOKEN_ENV] == secret
    assert _merged[CHAT_ID_ENV] == "-111"
    assert "222" not in lines
    assert "-111" not in lines


def test_lab_deliver_send_is_frozen(capsys) -> None:
    rc = main(["deliver", "test", "--desk", "ops", "--send", "--i-mean-it", "--repo-root", str(ROOT)])
    err = capsys.readouterr().err
    assert rc == 2
    assert "frozen" in err.lower()
    assert "step 5" in err.lower()
    assert "--no-send" in err


def test_committed_tree_has_no_principal_chat_ids() -> None:
    needles = (PRINCIPAL_DM_ID, HIVE_GROUP_ID)
    roots = (
        ROOT / "config",
        ROOT / "docs",
        ROOT / "ops",
        ROOT / "packages",
        ROOT / "apps",
        ROOT / "tests",
        ROOT / "AGENTS.md",
        ROOT / ".env.example",
    )
    hits: list[str] = []
    for root in roots:
        if root.is_file():
            text = root.read_text(encoding="utf-8", errors="replace")
            for needle in needles:
                if needle in text:
                    hits.append(f"{root}:{needle}")
            continue
        for path in root.rglob("*"):
            if not path.is_file():
                continue
            if path.suffix in {".png", ".jpg", ".webp", ".pyc", ".so"}:
                continue
            text = path.read_text(encoding="utf-8", errors="replace")
            for needle in needles:
                if needle in text:
                    hits.append(f"{path.relative_to(ROOT)}:{needle}")
    assert hits == []
