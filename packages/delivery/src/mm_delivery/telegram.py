"""Telegram Bot API client over the shared httpx stack. No paid SDK. No secrets in git."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

import httpx

from mm_common.http import (
    DEFAULT_TIMEOUT,
    ERROR_MISSING_ENV,
    ERROR_NONE,
    HttpGetResult,
    http_post,
    missing_env_notes,
)
from mm_delivery.config import BOT_TOKEN_ENV, TelegramSettings, bot_token_from_env

TELEGRAM_API_BASE = "https://api.telegram.org"
TOKEN_REDACT = "***"


def redact_telegram(text: str, token: str | None = None) -> str:
    """Strip bot tokens from URLs and copy. Never print TELEGRAM_BOT_TOKEN."""
    cleaned = text.replace(f"{BOT_TOKEN_ENV}=", f"{BOT_TOKEN_ENV}=***")
    if token:
        cleaned = cleaned.replace(token, TOKEN_REDACT)
        cleaned = cleaned.replace(f"/bot{token}/", f"/bot{TOKEN_REDACT}/")
    return cleaned


@dataclass(frozen=True)
class TelegramApiResult:
    method: str
    ok: bool
    error_class: str
    attempts: int
    status_code: int | None
    payload: Any = None
    notes: tuple[str, ...] = ()

    def canonical(self) -> dict[str, Any]:
        return {
            "method": self.method,
            "ok": self.ok,
            "error_class": self.error_class,
            "attempts": self.attempts,
            "status_code": self.status_code,
            "notes": list(self.notes),
        }


class TelegramClient:
    """Bot API wrapper. Token is constructor-only; never written to dry-run files."""

    def __init__(
        self,
        token: str | None,
        *,
        base_url: str = TELEGRAM_API_BASE,
        timeout_seconds: float = DEFAULT_TIMEOUT,
        max_attempts: int = 2,
        backoff_s: float = 0.25,
        client: httpx.Client | None = None,
        rate_limit: Any | None = None,
    ) -> None:
        self._token = (token or "").strip() or None
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds
        self.max_attempts = max_attempts
        self.backoff_s = backoff_s
        self._owns_client = client is None
        self._client = client or httpx.Client(timeout=timeout_seconds)
        self.rate_limit = rate_limit

    @classmethod
    def from_settings(
        cls,
        settings: TelegramSettings,
        *,
        environ: dict[str, str] | None = None,
        client: httpx.Client | None = None,
        rate_limit: Any | None = None,
        base_url: str | None = None,
    ) -> TelegramClient:
        return cls(
            bot_token_from_env(environ),
            base_url=base_url or settings.api_base_url,
            timeout_seconds=settings.rate_limit.timeout_seconds,
            max_attempts=settings.rate_limit.max_attempts,
            backoff_s=settings.rate_limit.backoff_s,
            client=client,
            rate_limit=rate_limit,
        )

    def close(self) -> None:
        if self._owns_client:
            self._client.close()

    def __enter__(self) -> TelegramClient:
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()

    def method_url(self, method: str) -> str:
        if not self._token:
            raise RuntimeError("missing env TELEGRAM_BOT_TOKEN; Telegram unavailable (error_class=missing_env)")
        return f"{self.base_url}/bot{self._token}/{method}"

    def _allow(self) -> bool:
        if self.rate_limit is None:
            return True
        allow = getattr(self.rate_limit, "allow", None)
        if callable(allow):
            return bool(allow())
        return True

    def call(self, method: str, body: Mapping[str, Any], *, files: Any = None) -> TelegramApiResult:
        if not self._token:
            return TelegramApiResult(
                method=method,
                ok=False,
                error_class=ERROR_MISSING_ENV,
                attempts=0,
                status_code=None,
                notes=missing_env_notes(BOT_TOKEN_ENV, source="telegram"),
            )
        if not self._allow():
            return TelegramApiResult(
                method=method,
                ok=False,
                error_class="rate_limited",
                attempts=0,
                status_code=None,
                notes=("telegram rate_limit exhausted; not sent",),
            )
        url = self.method_url(method)
        result: HttpGetResult = http_post(
            self._client,
            url,
            json_body=None if files is not None else body,
            data=body if files is not None else None,
            files=files,
            max_attempts=self.max_attempts,
            backoff_s=self.backoff_s,
            parse_json=True,
        )
        notes: list[str] = []
        if result.exception_name:
            notes.append(redact_telegram(result.exception_name, self._token))
        payload = result.json_payload
        ok = bool(result.ok and isinstance(payload, dict) and payload.get("ok") is True)
        error_class = result.error_class
        if result.ok and isinstance(payload, dict) and payload.get("ok") is not True:
            error_class = "telegram_api_error"
            desc = payload.get("description")
            if desc:
                notes.append(redact_telegram(str(desc), self._token))
        return TelegramApiResult(
            method=method,
            ok=ok,
            error_class=error_class if not ok else ERROR_NONE,
            attempts=result.attempts,
            status_code=result.status_code,
            payload=payload if ok else None,
            notes=tuple(notes),
        )

    def send_message(
        self,
        *,
        chat_id: str,
        text: str,
        parse_mode: str = "MarkdownV2",
        message_thread_id: int | None = None,
        disable_web_page_preview: bool = True,
    ) -> TelegramApiResult:
        body: dict[str, Any] = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": parse_mode,
            "disable_web_page_preview": disable_web_page_preview,
        }
        if message_thread_id is not None:
            body["message_thread_id"] = int(message_thread_id)
        return self.call("sendMessage", body)

    def send_document(
        self,
        *,
        chat_id: str,
        document: str,
        caption: str | None = None,
        message_thread_id: int | None = None,
        files: Any = None,
    ) -> TelegramApiResult:
        body: dict[str, Any] = {"chat_id": chat_id, "document": document}
        if caption:
            body["caption"] = caption
        if message_thread_id is not None:
            body["message_thread_id"] = int(message_thread_id)
        return self.call("sendDocument", body, files=files)

    def send_photo(
        self,
        *,
        chat_id: str,
        photo: str,
        caption: str | None = None,
        message_thread_id: int | None = None,
        files: Any = None,
    ) -> TelegramApiResult:
        body: dict[str, Any] = {"chat_id": chat_id, "photo": photo}
        if caption:
            body["caption"] = caption
        if message_thread_id is not None:
            body["message_thread_id"] = int(message_thread_id)
        return self.call("sendPhoto", body, files=files)
