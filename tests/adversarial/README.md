# Adversarial tests (Phase 4)

Leakage, look-ahead, and stale-data blocks.

- `test_lookahead.py` — intentional look-ahead fixture (`future_close`, early `available_at`) must be refused.
- `test_point_in_time.py` — replay cannot see future bars or observations; delayed ingest uses `available_at` / `ingested_at`, never `market_time` / `published_at` alone.
