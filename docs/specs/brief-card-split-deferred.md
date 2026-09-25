# Brief card split — deferred

The brief v2 template is 6–8 Telegram cards. That split remains the target. It is deferred, not discarded.

Card order, from the template:

1. executive
2. dashboard
3. macro
4. crypto
5. positioning
6. catalysts
7. scenarios
8. audit

Skip a card that has nothing to say. Never send a card of dashes.

The eleven-capture window (capture 1 on Monday 28 Sep 2026 through capture 11 on Monday 12 Oct 2026) sends the morning brief as one Telegram message through the existing single send. Multi-send delivery is untested, so the product path does not use it.

Cards ship only after delivery can do both of these:

1. Receipt handling for partial sends (some cards sent, some failed).
2. Retry that never duplicates already-sent cards.

Until both exist, `lab brief close` stays one message of at most 4096 characters, and `lab deliver` keeps the existing single `sendMessage` path.
