# Brief format freeze

The morning Telegram brief format approved via the dry-run render is frozen from capture 1 (Monday 28 Sep 2026) through capture 11 (Monday 12 Oct 2026).

The approved layout is the dry-run in `ops/reports/renders/brief-template-dryrun.txt` (the MarkdownV2 bytes Telegram receives; `parse_mode=MarkdownV2`). That layout includes the 14 Hyperliquid perp lines and the single `EQUITY T-1 BY DESIGN` header. The comparison against the previous production format, from the same recorded inputs, is `ops/reports/renders/brief-current-dryrun.txt`. Prices and health percentages move with the tape. The freeze is which sections and omissions are present. Source, Quality, and Label are not message columns; labels are in [brief-row-labels.md](brief-row-labels.md). Lines inside the pre block are at most 42 characters. Headings are plain text, without a `#` marker.

During that window the only permitted changes are a defect fix that restores the approved layout, and the equity-close exception below. New panels, new fixed sentences, and the card split wait until after capture 11.

The standing rule still applies inside that window: a line that says the same thing every morning is not information. A defect fix may remove a line that violates that rule. It may not add one, other than the exception below.

## Exception: 16 rank-eligible equity closes

Principal, 2026-09-30. Scope memo `docs/specs/scope-equity-close-print-2026-09-30.md` (PR #144). Through capture 11 the Sydney-morning `close.md` may add these 16 lines inside the fence, after the `SPY` / `QQQ` rows and before `US10Y`, in this order:

`CRCL TSLA SPCX NVDA BB GLXY IBIT BMNR MRNA GOOG HOOD NOW CBRS MSTR STRC AMD`

That list is `config/ingest/mvp_retain.yaml` `polygon.tickers` minus `QQQ`. Levels are this capture's Polygon grouped-daily closes already on the retain envelopes (`payload.value`, `payload.session_date`, `market_time`). A missing name goes on the existing `gaps:` line. The level is omitted when the row does not qualify. No second `QQQ` line.

Nothing else is added. Coinglass stays HELD. Chart stays STAND_BY. No Entry, SL, or TP. Solitary NO QUALIFIED TRADE stays as it is. Message shape stays one message. GMGN stays parked. The exception ends at capture 11.

### Day-7 dry-run checklist

Before Day-7 scoring, re-hash the box A1 file and compare it to `DONCAPO_A1_SHA256` in `tests/unit/test_equity_close_lines.py`:

`b5f33450ad9222d031b70cf060949688506dc59e906444dfb01a1930b78e86f1`

The file is not in git. Box path: `/workspace/drafts/ops/dry-runs/6d5fab42cc6884b4/ping-mvp-a1.md`. Fail the dry-run score if the digest mismatches. Do not copy the file into the repo.

```bash
sha256sum /workspace/drafts/ops/dry-runs/6d5fab42cc6884b4/ping-mvp-a1.md
python -c "import hashlib,pathlib; p=pathlib.Path('/workspace/drafts/ops/dry-runs/6d5fab42cc6884b4/ping-mvp-a1.md'); print(hashlib.sha256(p.read_bytes()).hexdigest())"
```
