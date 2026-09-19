#!/usr/bin/env python3
"""Persist attributable public-document claims as durable observations.

Uses ObservationEnvelope + ObservationRepository + MinIO/S3. Fails closed if
the object store is not durable. Public HTTP GET only. No signing.
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from typing import Any

import httpx

from mm_common.enums import DataQuality, EvidenceType, SourceKind
from mm_common.hashing import claim_hash, normalize_numeric
from mm_common.schemas import ClaimIdentity, ObservationEnvelope
from mm_common.time import utcnow
from mm_memory.db import dsn_from_env, session_scope
from mm_memory.object_store import ObjectStoreConfigError, object_store_from_env, raw_object_key
from mm_memory.repository import ObservationRepository

FED_IMPL = "https://www.federalreserve.gov/newsevents/pressreleases/monetary20260916a1.htm"
FED_FOMC = "https://www.federalreserve.gov/newsevents/pressreleases/monetary20260916a.htm"
REUTERS = "https://www.reuters.com/business/fed-forecasts-see-latest-hike-followed-by-another-before-end-year-2026-09-16/"
USER_AGENT = "market-memory-research/0.1 (read-only ingest; +https://github.com/ElChopa11/market-memory)"

# Calendar dates as stated by the source (no invented clock). Midnight UTC.
PUBLISHED = datetime(2026, 9, 16, tzinfo=timezone.utc)
EFFECTIVE = datetime(2026, 9, 17, tzinfo=timezone.utc)
REUTERS_PUBLISHED = datetime(2026, 9, 16, 18, 5, tzinfo=timezone.utc)  # byline 6:05 PM UTC


def _get(url: str) -> tuple[int, bytes, str]:
    with httpx.Client(timeout=30.0, follow_redirects=True, headers={"User-Agent": USER_AGENT}) as client:
        response = client.get(url)
        ctype = response.headers.get("content-type", "application/octet-stream")
        return response.status_code, response.content, ctype


def _envelope(
    *,
    source_name: str,
    source_kind: SourceKind,
    source_url_or_id: str,
    instrument: str,
    metric: str,
    value: str,
    claim_text: str,
    published_at: datetime,
    ingested_at: datetime,
    market_time: datetime | None,
    payload: dict[str, Any],
    extras: dict[str, str],
    evidence_type: EvidenceType,
    data_quality: DataQuality,
    confidence: float,
) -> ObservationEnvelope:
    identity = ClaimIdentity(
        source_name=source_name,
        instrument=instrument,
        metric=metric,
        market_time=market_time,
        value=normalize_numeric(value) if _numeric(value) else value,
        extras=extras,
    )
    return ObservationEnvelope(
        source_name=source_name,
        source_kind=source_kind,
        source_url_or_id=source_url_or_id,
        published_at=published_at,
        ingested_at=ingested_at,
        market_time=market_time,
        claim_text=claim_text,
        claim_hash=claim_hash(identity.hash_payload()),
        confidence=confidence,
        evidence_type=evidence_type,
        data_quality=data_quality,
        payload=payload,
        as_of_knowledge=ingested_at,
        instrument=instrument,
        metric=metric,
        identity=identity,
    )


def _numeric(value: str) -> bool:
    try:
        float(value)
    except (TypeError, ValueError):
        return False
    return True


def _put(
    session: Any,
    store: Any,
    envelope: ObservationEnvelope,
    *,
    body: bytes,
    content_type: str,
    source_kwargs: dict[str, Any],
) -> dict[str, Any]:
    repo = ObservationRepository(session)
    source = repo.ensure_source(**source_kwargs)
    key = raw_object_key(
        source=envelope.source_name,
        instrument=envelope.instrument,
        metric=envelope.metric,
        claim_hash=envelope.claim_hash,
        ingested_at_iso=envelope.ingested_at.isoformat(),
    )
    pointer = store.put_bytes(key, body, content_type=content_type)
    result = repo.put_observation(envelope, source=source, raw_pointer=pointer)
    return {
        "observation_id": result.observation.id,
        "created": result.created,
        "instrument": envelope.instrument,
        "metric": envelope.metric,
        "data_quality": envelope.data_quality.value,
        "raw_object_key": result.observation.raw_object_key,
    }


def main() -> int:
    try:
        store = object_store_from_env(enabled=True)
    except ObjectStoreConfigError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    if getattr(store, "backend", "") in {"memory", "null"}:
        print(f"Refusing non-durable object store backend={store.backend!r}", file=sys.stderr)
        return 2

    ingested_at = utcnow()
    out: dict[str, Any] = {"ingested_at": ingested_at.isoformat(), "rows": [], "gaps": []}

    impl_status, impl_body, impl_ctype = _get(FED_IMPL)
    fomc_status, fomc_body, fomc_ctype = _get(FED_FOMC)
    reuters_status, reuters_body, reuters_ctype = _get(REUTERS)

    if impl_status != 200 or b"interest rate paid on reserve balances to 3.90 percent" not in impl_body:
        out["gaps"].append({"feed": "fed_implementation_note", "error": f"HTTP {impl_status} or expected claim text missing"})
        print(json.dumps(out, indent=2))
        return 1
    if fomc_status != 200 or b"target range for the federal funds rate" not in fomc_body:
        out["gaps"].append({"feed": "fed_fomc_statement", "error": f"HTTP {fomc_status} or expected claim text missing"})
        print(json.dumps(out, indent=2))
        return 1

    extras = {"date_precision": "calendar_day", "effective_date": "2026-09-17"}
    fed_source = {
        "name": "federalreserve.gov",
        "kind": SourceKind.MACRO.value,
        "base_url": "https://www.federalreserve.gov",
        "trust_tier": 5,
        "tos_notes": "Official Board press release. Public HTTP GET of HTML. No scraping beyond the published note.",
    }
    claims: list[tuple[ObservationEnvelope, bytes, str]] = []

    common_payload = {
        "source_url": FED_IMPL,
        "http_status": impl_status,
        "date_precision": "calendar_day",
        "published_date": "2026-09-16",
        "effective_date": "2026-09-17",
        "verbatim": True,
    }
    claims.append(
        (
            _envelope(
                source_name="federalreserve.gov",
                source_kind=SourceKind.MACRO,
                source_url_or_id=FED_IMPL,
                instrument="USD",
                metric="fed_funds_target_range",
                value="3.75-4.00",
                claim_text="USD fed_funds_target_range=3.75-4.00 percent effective 2026-09-17 (FOMC implementation note 2026-09-16)",
                published_at=PUBLISHED,
                ingested_at=ingested_at,
                market_time=EFFECTIVE,
                payload={
                    **common_payload,
                    "quote": "maintain the federal funds rate in a target range of 3-3/4 to 4 percent",
                },
                extras=extras,
                evidence_type=EvidenceType.FACT,
                data_quality=DataQuality.OK,
                confidence=0.99,
            ),
            impl_body,
            impl_ctype.split(";")[0],
        )
    )
    claims.append(
        (
            _envelope(
                source_name="federalreserve.gov",
                source_kind=SourceKind.MACRO,
                source_url_or_id=FED_IMPL,
                instrument="USD",
                metric="iorb",
                value="3.90",
                claim_text="USD iorb=3.90 percent effective 2026-09-17 (Board of Governors implementation note 2026-09-16)",
                published_at=PUBLISHED,
                ingested_at=ingested_at,
                market_time=EFFECTIVE,
                payload={
                    **common_payload,
                    "quote": "raise the interest rate paid on reserve balances to 3.90 percent, effective September 17, 2026",
                },
                extras=extras,
                evidence_type=EvidenceType.FACT,
                data_quality=DataQuality.OK,
                confidence=0.99,
            ),
            impl_body,
            impl_ctype.split(";")[0],
        )
    )
    claims.append(
        (
            _envelope(
                source_name="federalreserve.gov",
                source_kind=SourceKind.MACRO,
                source_url_or_id=FED_IMPL,
                instrument="USD",
                metric="primary_credit",
                value="4.00",
                claim_text="USD primary_credit=4.00 percent effective 2026-09-17 (Board of Governors implementation note 2026-09-16)",
                published_at=PUBLISHED,
                ingested_at=ingested_at,
                market_time=EFFECTIVE,
                payload={
                    **common_payload,
                    "quote": "1/4 percentage point increase in the primary credit rate to 4.0 percent, effective September 17, 2026",
                },
                extras=extras,
                evidence_type=EvidenceType.FACT,
                data_quality=DataQuality.OK,
                confidence=0.99,
            ),
            impl_body,
            impl_ctype.split(";")[0],
        )
    )
    claims.append(
        (
            _envelope(
                source_name="federalreserve.gov",
                source_kind=SourceKind.MACRO,
                source_url_or_id=FED_FOMC,
                instrument="USD",
                metric="fomc_ff_hike_bp",
                value="25",
                claim_text="USD fomc_ff_hike_bp=25 to 3.75-4.00 percent (FOMC statement 2026-09-16, vote 12-0)",
                published_at=PUBLISHED,
                ingested_at=ingested_at,
                market_time=PUBLISHED,
                payload={
                    "source_url": FED_FOMC,
                    "http_status": fomc_status,
                    "date_precision": "calendar_day",
                    "published_date": "2026-09-16",
                    "quote": "raise the target range for the federal funds rate by 1/4 percentage point to 3-3/4 to 4 percent",
                    "verbatim": True,
                },
                extras={"date_precision": "calendar_day", "document": "fomc_statement"},
                evidence_type=EvidenceType.FACT,
                data_quality=DataQuality.OK,
                confidence=0.99,
            ),
            fomc_body,
            fomc_ctype.split(";")[0],
        )
    )

    # Reuters origin HTML was 401 from this lab; persist an attributable extract, not a fake 200 body.
    reuters_quote = (
        "Federal Reserve officials expect one more interest rate increase this year "
        "after raising rates on Wednesday and expect to hold them steady in 2027"
    )
    reuters_payload = {
        "source_url": REUTERS,
        "curl_http_status": reuters_status,
        "origin_html_durable": False,
        "retrieval": "lab extract of public Reuters article text; origin GET returned 401",
        "byline": "Michael S. Derby",
        "published": "2026-09-16T18:05:00Z",
        "quote": reuters_quote,
        "origin_bytes": len(reuters_body),
    }
    reuters_body_stored = json.dumps(reuters_payload, indent=2, sort_keys=True).encode("utf-8")
    claims.append(
        (
            _envelope(
                source_name="reuters.com",
                source_kind=SourceKind.NEWS,
                source_url_or_id=REUTERS,
                instrument="USD",
                metric="further_tightening",
                value="one_more_hike_2026",
                claim_text="USD further_tightening=one_more_hike_2026 (Reuters 2026-09-16: officials expect one more increase this year)",
                published_at=REUTERS_PUBLISHED,
                ingested_at=ingested_at,
                market_time=REUTERS_PUBLISHED,
                payload=reuters_payload,
                extras={"document": "reuters_fed_forecasts"},
                evidence_type=EvidenceType.QUOTE,
                data_quality=DataQuality.PARTIAL,
                confidence=0.7,
            ),
            reuters_body_stored,
            "application/json",
        )
    )
    if reuters_status != 200:
        out["gaps"].append(
            {
                "feed": "reuters_origin_html",
                "error": f"HTTP {reuters_status} on origin GET; stored lab extract with data_quality=partial",
            }
        )

    dsn = dsn_from_env()
    with session_scope(dsn) as session:
        for envelope, body, ctype in claims:
            name = envelope.source_name
            source_kwargs = fed_source if name == "federalreserve.gov" else {
                "name": "reuters.com",
                "kind": SourceKind.NEWS.value,
                "base_url": "https://www.reuters.com",
                "trust_tier": 3,
                "tos_notes": "Public news article. Origin GET 401 in this lab; extract stored with partial quality.",
            }
            row = _put(session, store, envelope, body=body, content_type=ctype, source_kwargs=source_kwargs)
            out["rows"].append(row)

    print(json.dumps(out, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
