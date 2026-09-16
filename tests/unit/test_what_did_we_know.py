"""Point-in-time query contract: ingested_at, never published_at alone."""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy.dialects import postgresql

from mm_memory.queries import what_did_we_know_statement


def test_what_did_we_know_filters_ingested_at_not_published_at() -> None:
    ts = datetime(2026, 9, 10, tzinfo=timezone.utc)
    sql = str(
        what_did_we_know_statement(ts).compile(
            dialect=postgresql.dialect(),
            compile_kwargs={"literal_binds": True},
        )
    ).lower()
    where, _, _ = sql.partition("order by")
    predicate = where.split("where", 1)[1]
    assert "ingested_at" in predicate
    assert "published_at" not in predicate
    assert "as_of_knowledge" not in predicate
