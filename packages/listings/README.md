# mm-listings

Phase 6d **listings / IPO** library. Research-only. Upcoming IPOs and direct listings, index add/delete/rebalance as a **separate** event stream, post-listing tracking, and base rates from our own Market Memory history.

Package: `packages/listings` (`mm_listings`). Desk runner: `mm_desks.listings` (`lab desk run --desk listings`).

**Must not:** import `mm_execution`, invent prints, compute Quant R/sizing, or enable live trading.

See [../../docs/runbooks/listings-desk.md](../../docs/runbooks/listings-desk.md).
