# Spec: Chart's watchlist CRM scan as a morning-brief section

Status: DRAFT (docs). Code lives on an UNMERGED branch only. Freeze: nothing in this spec touches `morning.py`, deliver, or the 06:30 workflow before capture 11 (Mon 12 Oct 2026) has scored. It lands as the first post-freeze change, and only on the Principal's go.
Owner: Coord Don. Data owner: Chart. Requested by: Principal (2026-10-09 01:50 AEDT; "start building asap" ~02:00 AEDT).
Mockup: `/workspace/drafts/don/crm-brief-section-mockup.md`.

## 1. Hard rules (Principal rulings, binding)

1. Words, σ and % only. No entry, stop, target or R:R, and no price, price-as-level, or level of any kind (rulings 2026-10-07/08; level rule 2026-10-08 23:28).
2. Nothing may reference the TradingView Long Position drawings (Principal-owned, desk use prohibited, ruling 2026-10-09 00:42). That covers their paper bands, their stops, and distance-to-level from them. Their horizontal lines and rectangles are excluded the same way. "% to DV" in this section is the CRM indicator's own deep-value zone as read on the CRM panel, never a drawn object.
3. Forming-bar CRM signals stay UNREAD and are never rendered as signals.
4. The track-record caveat always renders: BUY→26w counters are on-screen history only, not a backtest.
5. Data and awareness only, never a trade instruction. Q4 memo levels (UNAUTHORISED, ruling 4) are never an input.

## 2. Data source

**Today (manual).** Chart reads the CRM (Cycle Risk Map) indicator by hand in TradingView on layout `agBhIcW6` ("Long Term Quant Bot"), on 1W and 3D, across the CoinBase (6) and Crypto (29) watchlists, and files a markdown note under `/workspace/drafts/chart/`. There is no API: the CRM is a TradingView indicator.

**For the brief (machine-readable sidecar).** At the end of each scan Chart writes `crm-scan.json` next to the markdown, in schema `crm-scan/v1`:

| Field | Type | Rule |
|---|---|---|
| `schema` | str | must be `crm-scan/v1` |
| `captured_at` | ISO-8601 UTC | when the scan finished (end of the read window) |
| `timeframe` | `1W` or `3D` | the timeframe the rows are read on |
| `forming_bar` | str | must be `UNREAD`, otherwise the scan is rejected |
| `symbols_scanned` | int 0–999 | optional |
| `source_md`, `source_md_sha256` | str | provenance; never rendered |
| `nearest[]` | rows | full CRM readings, ordered nearest-to-DV first |
| `warming[]` | rows | perps whose CRM is still warming up (σ only, no score) |
| `stretched[]` | rows | most stretched names (+ optional word `note`) |
| `insufficient[]` | symbols | NaN σ / thin history |

Row keys (allow-list; **any other key rejects the whole scan**): `symbol` (short ticker, `-P` for perps), `cr` (int 0–100), `label` (word), `sigma` (σ vs 1Y VWAP, −20…+20), `to_deep_value_pct` (−100…+100), `below_realized` (bool), `buy_26w_n` (int), `buy_26w_pct`, `buy_26w_hit_pct` (0–100), `note` (word). The schema has no field that can hold a price.

**At capture time.** The step runs `lab brief close --live --no-db … --crm-scan <path>`. A scan only reaches the brief if that flag is passed, and today's workflow never passes it.

**Getting the file to the runner (open question Q2).** The 06:30 run happens on GitHub Actions, and Actions can't see `/workspace` on the box. Options:
- (a) Chart's scan job commits `crm-scan.json` to a data path through a bot push. This is blocked while the box `gh` token is invalid, and it adds commits on main.
- (b) The workflow fetches the file from an object store or gist URL kept in a secret.
- (c) Render the section box-side and send it as a separate DM (the current interim, ruled 2026-10-09).

Wiring the workflow is a separate post-freeze PR, and it is NOT in the code branch.

**Freshness.** `generated_at − captured_at` must be ≤ 12h. That allows a scan from ~18:30 AEDT the evening before up to the 06:30 run. Older renders `CRM scan unavailable (stale)`. A stamp more than 5 min after render time renders `(future stamp)`. Chart's 01:09–01:35 AEDT scan is ~5h old at 06:30.

## 3. Placement

It is the last block inside the single monospace fence, after `Catalysts` (or whichever earlier section is last that morning), with one blank line before it. The heading is a plain line with no `#`, in the same style as `Positioning` and `Catalysts`. It is added after the equity-close insert, as a post-render insert (the same pattern as `equity_close_lines.apply_equity_close`). It stays one Telegram message and must remain under 4096 chars after MarkdownV2 escaping (`mm_delivery.format`).

## 4. Render rules

- Every line is ≤ 42 chars (`PHONE_LINE_MAX`, asserted equal to `morning.PHONE_LINE_MAX`).
- **Compact (default), ≤ 8 lines:**
  - A heading `CRM <tf>, DV=deep value (Chart HH:MM AEDT)`.
  - Up to 4 nearest rows that have a DV %: `SYM[*] CR Label ±σ x.x% to DV`. `*` means below realized.
  - One `Stretched:` line, packed to width.
  - A footnote line with `*below realized. Forming bars UNREAD.`, then `Not backtested. Not a trade instruction.`
- **Full (opt-in), ~25 lines:**
  - Up to 5 nearest rows, with a `BUY->26w nN ±x% y% hit` sub-line each.
  - Warming perps, stretched names (with notes), and thin-history names.
  - The full caveat sentence.
- Numbers come only from typed fields: σ to 2 dp with a sign, % to 1 dp, and CR as an integer. Free text is never copied from Chart's markdown.
- Standing rule: no line that says the same thing every morning. The "Middle" list and the 3D σ are left out. 3D shows only if it diverges from 1W (Q5).

## 5. Level-free guard (two layers, fail closed)

1. **Input:**
   - Symbols must match `^[A-Z][A-Z0-9]{0,11}(-P)?$`.
   - Words (`label`, `note`) must match `^[A-Za-z][A-Za-z .-/]{0,23}$`, which allows no digits.
   - They are also checked against a banned-word list: entry, stop, SL, TP, target, take profit, R:R, RR, risk/reward, level(s), band(s), long/short position, position tool, drawing(s), invalidation, limit, buy at, sell at, price. Currency signs `$ € £ ¥ ₩` and `USD/USDT/USDC` are rejected too.
   - Numbers must be range-checked and finite. CR must be an integer.
   - Unknown keys reject the scan.
2. **Output:**
   - Every rendered line passes `level_free()`. It rejects a currency sign, a banned word, or any numeric token that isn't one of: σ-suffixed, %-suffixed, an integer 0–100 (CR), `nN`, `Nw`, `1W`/`3D`, or the `HH:MM` clock.
   - So `BTC 62000.5`, `ETH 3000`, `XRP 0.52` and `SOL $150` all fail.
   - A digit-bearing ticker also fails. That's fail-safe, and listed as Q6.

Any failure replaces the whole section with `CRM scan unavailable (level guard)`. Nothing partial is shown.

## 6. Failure behaviour

- The section never raises and never blocks the brief. `apply_crm_scan` catches everything and either returns the unavailable line or leaves the markdown unchanged.
- One line, `CRM scan unavailable (<reason>)`. Reasons: `missing`, `malformed`, `stale`, `future stamp`, `level guard`, `empty`, `width`, `length`, `error`.
- Flag omitted (`crm_scan=None`) means no section and a byte-for-byte identical brief and content hash.
- Tension with the standing rule (Q4): if the scan is missing every day, `CRM scan unavailable` becomes a fixed sentence.

## 7. Tests (`tests/unit/test_crm_scan.py`)

- Width lockstep with `morning.PHONE_LINE_MAX`.
- The compact render equals the mockup lines exactly, is ≤ 8 lines, and every line is ≤ 42.
- Full render: ≤ 42, level-free, and keeps UNREAD, not-a-backtest and not-a-trade.
- UNREAD and the backtest caveat render even when no row is below realized.
- `None` returns the same markdown object, and the section is the last block inside the fence.
- Missing, malformed, stale (>12h) and future-stamp scans each give one unavailable line.
- `forming_bar != UNREAD` is rejected.
- Level-shaped inputs (entry word, stop word, `$`, CR 62000, CR 42.5, an unknown `target` key, a symbol with a price, `R:R` note, `Long Position` note, NaN σ) each degrade to unavailable.
- `level_free()` table tests.
- Integration: `generate_from_fixture("close", frozen_day.json)` with no scan gives identical markdown and hash. With a scan, the section is appended inside the fence and the hash changes. With `CrmUnavailable` the brief still renders with all fence lines ≤ 42.
- Existing suites must stay green, especially the frozen `close.md` / set1 sha gates, which prove the default path is untouched.

## 8. Files that change post-freeze

On the branch (draft PR, unmerged until after C11 scores):
- `packages/briefing/src/mm_briefing/crm_scan.py`: new loader, guard and renderer.
- `packages/briefing/src/mm_briefing/render.py`: `render_close(..., crm_scan=None)`, applied after the equity insert.
- `packages/briefing/src/mm_briefing/engine.py`: `crm_scan` passed through `generate_close`, `generate_from_fixture` and `generate_from_sources`.
- `apps/lab-cli/src/mm_lab_cli/briefing.py`: a `--crm-scan PATH` flag (close only).
- `tests/unit/test_crm_scan.py` and `tests/fixtures/briefing/crm_scan_20261009.json`.
- `docs/specs/crm-brief-section.md`: this spec.

NOT changed on the branch: `morning.py`, `deliver.py`, `.github/workflows/*` (no cron and no step changes), and `ops/host/*`.

Later, a separate PR after the freeze and the Principal's go: wire `--crm-scan` into `hybrid-sydney-morning.yml` once Q2 is settled, plus a `brief-format-freeze.md` / `brief-v2-template.md` note recording the new section.

## 9. Open questions

1. **Automation:** Chart's scan is manual today (a browser read of a TradingView indicator). Does it run automatically before 06:30? If not, who runs it and by when? It is unread on mornings when Chart doesn't scan.
2. **Transport to the runner:** Actions can't read the box. Should it be a repo commit, an object store or gist, or a box-side separate DM?
3. **Hyperliquid perps warming up:** most HL perps have no CRM score yet. The compact view skips them. Should they appear at all before warm-up ends, and when does warm-up end per symbol?
4. **Standing rule vs the unavailable line:** should `CRM scan unavailable` print daily, or be omitted after N consecutive misses?
5. **3D σ:** show it only when it diverges from 1W by more than a threshold (e.g. 0.25σ)?
6. **Digit-bearing tickers** (e.g. 1INCH) trip the output guard and blank the section. Should there be an allow-list?
7. **Layout hygiene:** `agBhIcW6` carries the Principal-owned Q4 drawings. Should the scan move to a clean layout so the source is unambiguous? The values don't depend on the drawings, but the screenshots do show them.
8. **Compact vs full** as the default. Should the full view be a weekly variant?
9. **Content-hash and score impact:** adding the section changes the brief hash. Do the post-C11 scoresheet and receipts need a note?
