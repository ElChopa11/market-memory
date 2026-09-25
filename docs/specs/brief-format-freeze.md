# Brief format freeze

The morning Telegram brief format approved via the dry-run render is frozen from capture 1 (Monday 28 Sep 2026) through capture 11 (Monday 12 Oct 2026).

The approved layout is the dry-run in `ops/reports/renders/brief-template-dryrun.txt` (the MarkdownV2 bytes Telegram receives; `parse_mode=MarkdownV2`). The comparison against the previous production format, from the same recorded inputs, is `ops/reports/renders/brief-current-dryrun.txt`. Prices and health percentages move with the tape. The freeze is which sections and omissions are present. Source, Quality, and Label are not message columns; labels are in [brief-row-labels.md](brief-row-labels.md).

During that window the only permitted change is a defect fix that restores the approved layout. New panels, new fixed sentences, and the card split wait until after capture 11.

The standing rule still applies inside that window: a line that says the same thing every morning is not information. A defect fix may remove a line that violates that rule. It may not add one.
