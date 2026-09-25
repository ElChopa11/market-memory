# MVP retain (Sydney morning)

Paper only. One capture per Sydney anchor date, on the send path of `brief-and-deliver`, before the Principal DM. `already_delivered` does not capture. A capture error does not fail the job and does not add a second Telegram message.

The DM line uses the **read-back** row count:

`CAPTURE: <n>/<expected> rows (<instruments> instruments) @ <captured_at UTC> · prior <prior_captured_at or none>`

`<n>` is `COUNT(*)` for that `captured_at` after commit. `<expected>` is the membership product: bound perps × their metrics, plus DRV `mid_px`, plus one close per equity. With the current list that is 19 × 3 + 1 + 17 = 75 rows and 37 instruments, so a full capture reads `CAPTURE: 75/75 rows (37 instruments)`. A partial capture shows a smaller numerator against the same 75. Partial fetches persist what landed; nulls stay null.

`captured_at` is the actual capture time (UTC) and is lockstep on `published_at`, `ingested_at`, and `as_of_knowledge`. `prior_captured_at` is the latest capture for a different anchor date, or null. When it is earlier, each row stores `interval_seconds`. The anchor date is the Sydney calendar date of the stamp's `SCHEDULED_FOR`.

Every weekday captures. There is no holiday calendar. Crypto is read on every capture. When the US cash session's grouped-daily body is empty, equity closes come from the most recent earlier weekday whose body has bars. `market_time` is that vendor bar time. `as_of_knowledge` stays the capture time. Those equity rows are `STALE`. An empty equity lane does not fail the capture and does not change the DM line to `CAPTURE: FAILED`.

The whole capture — both Hyperliquid calls, every Polygon grouped-daily read, the Neon write, and the read-back — has one 90-second wall clock. Exceeding it prints `CAPTURE: FAILED timeout` and the brief still sends.

The deliver receipt field `capture_rows` is that same read-back count, or null when the capture failed or was not rewritten.

## Proof of write

Neon SQL editor (read-only). Substitute the `captured_at` from the DM line. Do not dispatch the morning workflow to check this — a dispatch that sends is a second DM.

```sql
SELECT COUNT(*) AS capture_rows
FROM observation
WHERE payload_json->>'retain_series' = 'mvp_retain'
  AND payload_json->>'captured_at' = '<captured_at>';
```

One row set per anchor date:

```sql
SELECT payload_json->>'anchor_date' AS anchor_date,
       payload_json->>'captured_at' AS captured_at,
       COUNT(*) AS capture_rows
FROM observation
WHERE payload_json->>'retain_series' = 'mvp_retain'
GROUP BY 1, 2
ORDER BY 2;
```

Fixture dry-run (no Neon): `uv run lab retain --fixture PATH --no-db`.

## Proof write

`workflow_dispatch` input `mode=capture_proof` on `.github/workflows/hybrid-sydney-morning.yml` runs `lab retain proof` on the Actions runner. It does not stamp, brief, deliver, write a receipt, or ping. Rows are tagged `payload_json.capture_kind = 'proof'` and carry `capture_id`. No new column and no migration: both tags sit in the existing `payload_json`.

Those rows are excluded from the morning anchor-day key and from prior selection (`capture_kind <> 'proof'`). A weekend proof does not become Monday's prior and does not block Monday's write.

The job log and step summary print:

`CAPTURE_PROOF: <n>/<expected> rows (<instruments> instruments) @ <captured_at UTC> capture_id <id>`

and the SQL below. `<n>` is the Neon read-back for that `capture_id`.

```sql
SELECT COUNT(*) AS capture_rows
FROM observation
WHERE payload_json->>'retain_series' = 'mvp_retain'
  AND payload_json->>'capture_kind' = 'proof'
  AND payload_json->>'capture_id' = '<capture_id>';
```

Exclusion from prior selection (expect 0):

```sql
SELECT COUNT(*) AS proof_rows_eligible_as_prior
FROM observation
WHERE payload_json->>'retain_series' = 'mvp_retain'
  AND COALESCE(payload_json->>'capture_kind', '') <> 'proof'
  AND payload_json->>'capture_id' = '<capture_id>';
```

Exclusion from the one-capture-per-anchor-day key (expect 0):

```sql
SELECT COUNT(*) AS proof_rows_on_anchor_key
FROM observation
WHERE payload_json->>'retain_series' = 'mvp_retain'
  AND COALESCE(payload_json->>'capture_kind', '') <> 'proof'
  AND payload_json->>'anchor_date' IS NOT NULL
  AND payload_json->>'capture_id' = '<capture_id>';
```
