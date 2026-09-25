# MVP retain (Sydney morning)

Paper only. One capture per Sydney anchor date, on the send path of `brief-and-deliver`, before the Principal DM. `already_delivered` does not capture. A capture error does not fail the job and does not add a second Telegram message.

The DM line uses the **read-back** row count:

`CAPTURE: <n>/37 rows @ <captured_at UTC> · prior <prior_captured_at or none>`

`<n>` is `COUNT(*)` for that `captured_at` after commit. A full capture is 75 observation rows (19 perps × 3 metrics + DRV `mid_px` + 17 closes). The `/37` is the instrument membership. Partial fetches persist what landed; nulls stay null.

`captured_at` is the actual capture time (UTC) and is lockstep on `published_at`, `ingested_at`, and `as_of_knowledge`. `prior_captured_at` is the latest capture for a different anchor date, or null. When it is earlier, each row stores `interval_seconds`. The anchor date is the Sydney calendar date of the stamp's `SCHEDULED_FOR`.

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
