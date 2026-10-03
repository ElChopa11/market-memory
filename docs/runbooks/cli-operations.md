# CLI operations: Neon migrate and history backfill

Paper only. No live trading, no signing, no Telegram send.

This is the laptop path. You need a clone of this repo, Python 3.12, [uv](https://docs.astral.sh/uv/), and `POSTGRES_DSN` in the shell. Nothing in this file is a secret. Do not paste a DSN, API key, or object-store secret into git, a workflow, or a transcript you commit.

**CLI only.** There is no GitHub Actions trigger for these two commands. No `workflow_dispatch`, no `repository_dispatch`, and no `schedule`. A morning-deliver PAT cannot reach `uv run lab migrate` or `uv run lab history-backfill`. This document does not add a workflow. The existing CI job in `.github/workflows/test.yml` migrates an ephemeral Postgres service for tests; that job is not Neon and it does not run history backfill.

`neon-write` may exist under repository Settings → Environments. It is not a gate. Required reviewers are unavailable on this free private plan, so that Environment cannot hold an approval. Delete `neon-write` so the name does not imply protection. A soft `i_mean_it_migrate` or `i_mean_it_backfill` input is not a security gate and is not used.

The commands below are the entrypoints already in the repo:

| Step | Command | Where it lives |
|---|---|---|
| Schema | `uv run lab migrate` | `cmd_migrate` in `apps/lab-cli/src/mm_lab_cli/cli.py` (on main). No flags. |
| History | `uv run lab history-backfill` | same CLI module, subcommand from PR #114. Optional `--dsn` only. |

`lab history-backfill` is absent until that subcommand is in the checkout you run. `uv run lab history-backfill --help` then prints `usage: lab history-backfill [-h] [--dsn DSN]`. An argparse line `invalid choice: 'history-backfill'` means this checkout does not contain the subcommand yet.

On a fresh database the order is migrate, then this backfill once. Recurring ingest-persist is a separate change and is not a command in this runbook. The backfill does not migrate, does not brief, and does not deliver.

## Prove the rows

Exit 0 is the process status. The proof that schema and history landed is a query against the same `POSTGRES_DSN`, after both commands, in the same shell.

The probe prints the hostname and `sslmode` only. It does not print the user, the password, or the full DSN. It then prints `alembic_version` and one row per series: `count(*)`, `max(market_time)`, `max(as_of_knowledge)`. It exits 0 only when the host is a direct Neon host, Alembic head is `0012_heartbeat_if_not_exists`, and all ten series clear the floors below. Any other exit means the rows are not proven.

```bash
uv run python - <<'PY'
from urllib.parse import parse_qs, urlparse

from sqlalchemy import text
from mm_memory.db import dsn_from_env, make_engine

dsn = dsn_from_env()
parsed = urlparse(dsn)
host = parsed.hostname or ""
sslmode = (parse_qs(parsed.query).get("sslmode") or [""])[0]
print(f"host={host}")
print(f"sslmode={sslmode}")
if host in {"", "localhost", "127.0.0.1", "::1"}:
    raise SystemExit("POSTGRES_DSN is unset or local. Export the direct Neon host before this probe.")
if not host.endswith(".neon.tech"):
    raise SystemExit("host does not end with .neon.tech")
if "-pooler" in host:
    raise SystemExit("host contains -pooler. Use the direct Neon host.")
if sslmode != "require":
    raise SystemExit("sslmode is not require")

# Floors match the command windows: ~2y of daily sessions, full FRED
# series (not limit=2 or limit=5), and the CLI's HL minimum of 60.
EXPECTED = (
    ("polygon", "SPY", "ohlcv_close", 200),
    ("polygon", "QQQ", "ohlcv_close", 200),
    ("polygon", "UUP", "ohlcv_close", 200),
    ("polygon", "USO", "ohlcv_close", 200),
    ("fred", "US10Y", "fred_observation", 1000),
    ("fred", "US2Y", "fred_observation", 1000),
    ("hyperliquid.info", "BTC", "candle_close", 60),
    ("hyperliquid.info", "ETH", "candle_close", 60),
    ("hyperliquid.info", "UNI", "candle_close", 60),
    ("hyperliquid.info", "AAVE", "candle_close", 60),
)

version_sql = text("SELECT version_num FROM alembic_version")
series_sql = text(
    """
    SELECT s.name AS source,
           o.instrument,
           o.metric,
           count(*)::int AS rows,
           max(o.market_time) AS max_market_time,
           max(o.as_of_knowledge) AS max_as_of_knowledge
    FROM observation o
    JOIN source s ON s.id = o.source_id
    WHERE (s.name, o.metric) IN (
        ('polygon', 'ohlcv_close'),
        ('fred', 'fred_observation'),
        ('hyperliquid.info', 'candle_close')
    )
    GROUP BY s.name, o.instrument, o.metric
    ORDER BY s.name, o.instrument, o.metric
    """
)

def show(value):
    if value is None:
        return ""
    iso = getattr(value, "isoformat", None)
    return iso() if iso else str(value)

with make_engine().connect() as conn:
    version = conn.execute(version_sql).scalar()
    found = {
        (row.source, row.instrument, row.metric): row
        for row in conn.execute(series_sql).all()
    }

print(f"alembic_version={version}")
print("source\tinstrument\tmetric\trows\tmax_market_time\tmax_as_of_knowledge")
missing = []
for source, instrument, metric, floor in EXPECTED:
    row = found.get((source, instrument, metric))
    if row is None:
        print(f"{source}\t{instrument}\t{metric}\tMISSING")
        missing.append(f"{source} {instrument} {metric} missing")
        continue
    print(
        f"{source}\t{instrument}\t{metric}\t{row.rows}\t"
        f"{show(row.max_market_time)}\t{show(row.max_as_of_knowledge)}"
    )
    if row.rows < floor:
        missing.append(f"{source} {instrument} {metric} rows={row.rows} floor={floor}")
if version != "0012_heartbeat_if_not_exists":
    missing.append(f"alembic_version={version}")
if missing:
    raise SystemExit("rows not proven: " + "; ".join(missing))
print(f"series={len(EXPECTED)}")
PY
```

Leave `--dsn` unset on the backfill. The probe reads `POSTGRES_DSN` through `dsn_from_env`. A backfill that was pointed at a different database with `--dsn` can exit 0 while this probe reads another host.

How to read the result:

- `host` ends with `.neon.tech`, does not contain `-pooler`, and `sslmode=require`.
- `alembic_version=0012_heartbeat_if_not_exists`.
- Ten data lines. Instruments are `SPY`, `QQQ`, `UUP`, `USO` (metric `ohlcv_close`, source `polygon`); `US10Y` and `US2Y` (metric `fred_observation`, source `fred` — the FRED series ids `DGS10` and `DGS2` are not the `instrument` column); `BTC`, `ETH`, `UNI`, `AAVE` (metric `candle_close`, source `hyperliquid.info`).
- `max_market_time` is the latest bar or print (exchange or FRED date). `max_as_of_knowledge` is lab ingest time, locked to `ingested_at`. A fresh backfill stamps `max_as_of_knowledge` at the run clock. A recent `max_market_time` with a null or ancient `max_as_of_knowledge` is a different column. Both should be non-empty on a landed row.
- The last line is `series=10` and the process exit code is 0.

Floors in the probe: polygon count at least 200 per ticker (730 calendar days of sessions; a 10-day brief window fails this), FRED count at least 1000 per yield (full series; `limit=2` or `limit=5` fails this), Hyperliquid count at least 60 per coin (the CLI's own minimum).

**Example probe stdout (not a live Neon query).** Host, counts, and timestamps below are shape only. This session did not connect to Neon.

```text
host=ep-example.region.aws.neon.tech
sslmode=require
alembic_version=0012_heartbeat_if_not_exists
source	instrument	metric	rows	max_market_time	max_as_of_knowledge
fred	US10Y	fred_observation	16000	2026-09-23T00:00:00+00:00	2026-09-24T07:20:00+00:00
fred	US2Y	fred_observation	12000	2026-09-23T00:00:00+00:00	2026-09-24T07:20:00+00:00
hyperliquid.info	AAVE	candle_close	90	2026-09-23T00:00:00+00:00	2026-09-24T07:20:00+00:00
hyperliquid.info	BTC	candle_close	90	2026-09-23T00:00:00+00:00	2026-09-24T07:20:00+00:00
hyperliquid.info	ETH	candle_close	90	2026-09-23T00:00:00+00:00	2026-09-24T07:20:00+00:00
hyperliquid.info	UNI	candle_close	90	2026-09-23T00:00:00+00:00	2026-09-24T07:20:00+00:00
polygon	QQQ	ohlcv_close	500	2026-09-23T00:00:00+00:00	2026-09-24T07:20:00+00:00
polygon	SPY	ohlcv_close	500	2026-09-23T00:00:00+00:00	2026-09-24T07:20:00+00:00
polygon	USO	ohlcv_close	500	2026-09-23T00:00:00+00:00	2026-09-24T07:20:00+00:00
polygon	UUP	ohlcv_close	500	2026-09-23T00:00:00+00:00	2026-09-24T07:20:00+00:00
series=10
```

`relation "alembic_version" does not exist` or `relation "observation" does not exist` means this host has not had `uv run lab migrate` applied.

## Prepare the checkout

```bash
git clone <this repo> market-memory
cd market-memory
# Python 3.12
uv sync --all-packages
```

Export names in the shell. This file has no values.

| Name | Role |
|---|---|
| `POSTGRES_DSN` | Direct Neon host. Hostname ends with `.neon.tech`, does not contain `-pooler`, query includes `sslmode=require`. |
| `POLYGON_API_KEY` | Required before backfill HTTP. |
| `FRED_API_KEY` | Required before backfill HTTP. |
| `MINIO_ENDPOINT` or `S3_ENDPOINT` | Durable object-store endpoint. |
| `MINIO_ACCESS_KEY` or `MINIO_ROOT_USER` or `AWS_ACCESS_KEY_ID` | Object-store access key. |
| `MINIO_SECRET_KEY` or `MINIO_ROOT_PASSWORD` or `AWS_SECRET_ACCESS_KEY` | Object-store secret. |

Leave `MINIO_BUCKET` unset. The code default bucket name is `market-memory`. For Cloudflare R2, export `S3_REGION=auto`. Unset region means `us-east-1` (local MinIO). No `TELEGRAM_*`. No Hyperliquid key. Candles use public `/info`.

`uv run lab migrate` and `uv run lab history-backfill` read `POSTGRES_DSN` via `dsn_from_env` in `packages/memory/src/mm_memory/db.py`. `DATABASE_URL` and `NEON_API_KEY` are ignored. Setting either does not select a database.

If `POSTGRES_DSN` is unset, both commands use the local compose DSN `postgresql://lab:lab@localhost:5432/market_memory`. That is not Neon. A migrate that prints `migrated to ...` against that DSN has updated the laptop database.

## Migrate

```bash
export POSTGRES_DSN  # direct Neon host, sslmode=require; do not echo it
uv run lab migrate
```

`cmd_migrate` calls Alembic `upgrade` to `head`, then prints `current_revision`. There is no `--dsn` and no `--sql`.

**Example success stdout (format from `cmd_migrate`; not a live database apply).** This session had no Postgres. `alembic_head()` reads migration files only and returns `0012_heartbeat_if_not_exists` (28 characters, `packages/memory/src/mm_memory/migrations/versions/0012_heartbeat_if_not_exists.py`).

```text
migrated to 0012_heartbeat_if_not_exists
```

Alembic may also write INFO lines on stderr (`Context impl PostgresqlImpl`, `Will assume transactional DDL`). The success line is the stdout line above. Then run the [probe](#prove-the-rows). After migrate alone, `alembic_version` is head and the ten series are still missing. That is expected until the backfill commits.

## History backfill

```bash
# POSTGRES_DSN still exported. Also export POLYGON_API_KEY, FRED_API_KEY,
# and the object-store trio. For R2: export S3_REGION=auto
uv run lab history-backfill
```

No `--no-db`. No `--fixture`. Do not pass `--dsn` unless you also point the probe at that same database yourself; the probe in this runbook will not see `--dsn`.

What one run requests:

| Source | Endpoint | Window | Calls |
|---|---|---|---|
| Polygon | `GET /v2/aggs/ticker/{ticker}/range/1/day/{start}/{end}` `adjusted=true` `limit=50000` | 730 calendar days. Tickers from `config/briefing/macro.yaml` `live.polygon.symbols`: SPY, QQQ, UUP, USO. VIX is structural and is not called. Metric `ohlcv_close`. | 4 |
| FRED | `GET /fred/series/observations` | Full series for DGS10 (`US10Y`) and DGS2 (`US2Y`). `limit` omitted. `sort_order=asc` on this path. Metric `fred_observation`. | 2 |
| Hyperliquid | `POST https://api.hyperliquid.xyz/info` `candleSnapshot` interval `1d` | 90 calendar days. Coins from `config/instruments/perps.yaml`: BTC, ETH, UNI, AAVE. Metric `candle_close`. Open time is field `t`. | 4 |

2s10s is DGS10 minus DGS2. This command does not write a spread row. It does not write Δ1D, Δ5D, Δ20D, or z30d columns.

The process prints one JSON object with `"phase": "plan"`, then fetches. When that fetch has no errors it opens Postgres, commits, and prints a second JSON object with `"phase": "fetch"` and a `persist` object (`created`, `duplicates`, `contradicted`).

Exit 0 when there are no fetch errors and every Hyperliquid coin has at least 60 daily sessions. Exit 1 when the fetch records errors (Postgres is not opened) or when any coin is below 60 after the commit. Exit 2 when a vendor key or the object store is missing, before HTTP and before Postgres.

### Live local capture: plan, then refuse (not a Neon apply)

Captured 2026-09-24 by running `uv run lab history-backfill` with `POLYGON_API_KEY` and `FRED_API_KEY` unset. Exit code **2**. Stdout is one JSON line (pretty-printed here). Stderr is the refuse line. No HTTP. No Postgres. Dates move with the clock; this capture used `as_of` `2026-09-24T07:14:30.093326+00:00`, Polygon `2024-09-24` through `2026-09-24`, Hyperliquid start `2026-06-26T07:14:30.093326+00:00`.

```json
{
  "phase": "plan",
  "sequence": "after lab migrate on the fresh database, before recurring ingest-persist",
  "do_not_run": "DO NOT RUN until the Principal says so",
  "polygon": {
    "tickers": ["SPY", "QQQ", "UUP", "USO"],
    "slots": ["ES:SPY", "NQ:QQQ", "DXY:UUP", "CL:USO"],
    "lookback_calendar_days": 730,
    "metric": "ohlcv_close",
    "approx_api_calls": 4
  },
  "fred": {
    "series": {"US10Y": "DGS10", "US2Y": "DGS2"},
    "lookback": "full series (limit omitted; API default 100000). Not limit=5.",
    "metric": "fred_observation",
    "approx_api_calls": 2
  },
  "hyperliquid": {
    "coins": ["BTC", "ETH", "UNI", "AAVE"],
    "interval": "1d",
    "lookback_calendar_days": 90,
    "min_sessions": 60,
    "metric": "candle_close",
    "approx_api_calls": 4
  }
}
```

```text
history-backfill refused: missing POLYGON_API_KEY, FRED_API_KEY (values not printed)
```

The live line also includes endpoints, rate-limit sentences, and an `idempotency` string. Those fields are the same object `history_backfill_plan().as_public_dict()` prints. A truncated quote above is enough to recognize the plan. The refuse path still prints the full plan line before stderr.

### Example fetch success (shape from the CLI; counts not measured)

**Not a live vendor or Neon run.** `cmd_history_backfill` prints this as one `json.dumps` line after a clean fetch and a commit. Integers below are illustrative so the keys are visible. A real first run into an empty table has `errors` `[]`, `hl_below_minimum` `{}`, `persist.duplicates` `0`, `persist.contradicted` `0`, and `persist.created` equal to `envelopes`. `persist.object_store` is `s3` when the durable store is configured. Exit code 0.

```json
{
  "phase": "fetch",
  "errors": [],
  "polygon_bars": {"SPY": 500, "QQQ": 500, "UUP": 500, "USO": 500},
  "fred_rows": {"US10Y": 16000, "US2Y": 12000},
  "hl_sessions": {"BTC": 90, "ETH": 90, "UNI": 90, "AAVE": 90},
  "hl_below_minimum": {},
  "calls": {"polygon": 4, "fred": 2, "hyperliquid": 4},
  "pacer_slept_s": 0.0,
  "envelopes": 30360,
  "persist": {
    "created": 30360,
    "duplicates": 0,
    "contradicted": 0,
    "envelopes": 30360,
    "instruments": ["SPY", "QQQ", "UUP", "USO", "US10Y", "US2Y", "BTC", "ETH", "UNI", "AAVE"],
    "sources": ["polygon", "fred", "hyperliquid.info"],
    "object_store": "s3",
    "dry_run": false
  }
}
```

Then run the [probe](#prove-the-rows). Trust `series=10` from that probe.

## Re-running a half-finished backfill

A half-finished backfill is safe to re-run. The command does not resume a cursor. It fetches the window again and inserts only claims that are not already stored.

`claim_hash` is SHA-256 of source, instrument, metric, market time, value, and extras. It does not include `ingested_at`. `ObservationRepository.put_observation` selects on `claim_hash`, then `INSERT ... ON CONFLICT DO NOTHING` on `observation_claim_hash_uidx`. `persist_history_envelopes` skips the raw-object put when that claim already exists. A second run with the same values prints `persist.created` 0 and a `duplicates` count. It does not insert a second observation row.

Three stops, and what a re-run does:

| Stop | Database | Re-run |
|---|---|---|
| Exit 2 (missing key or object store) | Postgres was not opened. | Safe. Fix the env, run again. |
| Exit 1 during fetch (`errors` non-empty, including a zero-bar ticker or coin) | Postgres was not opened. Partial HTTP results are discarded. | Safe. The next run starts from the plan again. |
| Crash during persist | `session_scope` commits once at the end and rolls back on exception. A killed process leaves no `observation` rows from that attempt. Object-store puts can already have happened; those keys include `ingested_at`, so they are not a second row. | Safe. The next run inserts the claims. |
| Exit 1 after commit because a coin has fewer than 60 sessions | The fetched rows are committed. `hl_below_minimum` names the short coins. | Safe. Existing `claim_hash` values count as duplicates. Missing claims are inserted. |
| Exit 0, run again | Rows from the first commit stay. | Safe. Unchanged values are duplicates. A revised close or FRED print is a new `claim_hash` plus a `contradicts` link. History is not deleted. |

`uv run lab migrate` a second time is the same kind of re-run. Alembic upgrades to `head`. When `alembic_version` is already `0012_heartbeat_if_not_exists`, no further revision runs, and stdout is again `migrated to 0012_heartbeat_if_not_exists`. That line is success, not an "already applied" error. Revisions `0011` and `0012` create `schedule_heartbeat` with `IF NOT EXISTS`.

## Common failures

| What you see | Exit | Meaning |
|---|---|---|
| Stdout `migrated to 0012_heartbeat_if_not_exists` but the probe says `POSTGRES_DSN is unset or local` or `host=` is `localhost` | migrate exit 0 | `POSTGRES_DSN` was unset. The CLI used `postgresql://lab:lab@localhost:5432/market_memory`. Neon was not updated. Export the direct Neon DSN and run migrate again, then the probe. |
| `history-backfill refused: missing POLYGON_API_KEY, FRED_API_KEY (values not printed)` | 2 | One or both vendor keys are unset or blank. The plan JSON already printed. No HTTP. No Postgres. **Live capture** in the section above. |
| `Raw-object persistence is required but MinIO/S3 is not fully configured (need MINIO_ENDPOINT or S3_ENDPOINT, plus access and secret keys). Failing closed before any raw_object database pointer is created.` | 2 | Keys were present and the object store was not. No HTTP. No Postgres. **Live capture** 2026-09-24 with non-empty dummy key names set and object-store variables unset. The same sentence is `ObjectStoreConfigError` from `object_store_from_env`. |
| `psycopg.OperationalError: connection failed: connection to server at "127.0.0.1", port 5432 failed: Connection refused` wrapped as `sqlalchemy.exc.OperationalError` | 1 (uncaught traceback) | **Live capture** 2026-09-24 with `POSTGRES_DSN` unset, so migrate dialed localhost and nothing was listening. Stdout was empty (no `migrated to` line). The same exception class with a `*.neon.tech` host in the message is a network failure to Neon: DNS (`could not translate host name`), timeout, or a refused address. No schema change. |
| `password authentication failed` inside that `OperationalError` | traceback | TCP reached Postgres. The role or password in `POSTGRES_DSN` was rejected. No schema change. |
| `permission denied for schema public`, `permission denied for table`, or `must be owner` | traceback | The role can log in and cannot DDL (migrate) or INSERT (backfill). Migrate needs a role that can create tables in this database. A backfill failure here rolls back the `session_scope` transaction. These phrases are Postgres wording; this session did not reproduce them against Neon. |
| Second migrate prints `migrated to 0012_heartbeat_if_not_exists` and nothing like `already applied` | 0 | Head was already applied. See the re-run section. From the Alembic `upgrade` to `head` path in `cmd_migrate`, not from a second live apply in this session. |
| Fetch JSON `"errors": ["polygon SPY error_class=timeout"]` (also `unreachable`, `rate_limited`, `http_5xx`, `http_404`) or `hyperliquid BTC ...` or `fred error_class=...` | 1 | Vendor network or HTTP failure. Postgres was not opened. Re-run after the vendor answers. |
| Fetch JSON with `"hl_below_minimum": {"UNI": 12}` and exit 1 | 1 | Persist already committed. The probe shows the short count. Re-run is safe; it will not duplicate the rows that landed. |
| `lab: error: argument cmd: invalid choice: 'history-backfill'` | 2 | This checkout does not contain the PR #114 subcommand. |
| Probe `relation "observation" does not exist` | traceback | Connected to a database that has not been migrated. |

## After the probe

`series=10` and `alembic_version=0012_heartbeat_if_not_exists` on a direct Neon host is the landing check. Paper only. This path does not send Telegram, does not submit an order, and does not start a schedule.
