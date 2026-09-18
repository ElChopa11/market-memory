# mm-listings

Phase 6d **listings / IPO** library. Research-owned screen (not a sixth desk). Upcoming IPOs and direct listings, index add/delete/rebalance as a **separate** event stream, post-listing tracking, and base rates from our own Market Memory history.

Package: `packages/listings` (`mm_listings`). Research runner: `mm_desks.listings` (`lab listings scan --no-send`). Ops publishes: `lab deliver listings --no-send`.

**Must not:** import `mm_execution`, invent prints, compute Quant R/sizing, promote universe membership, or enable live trading.

See [../../docs/runbooks/listings.md](../../docs/runbooks/listings.md).
