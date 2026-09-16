"""Watchlist: config items + observation ids from Hyperliquid memory."""

from __future__ import annotations

from mm_briefing.config import WatchlistSpec
from mm_briefing.hl import basis_mark_oracle, funding_value, oi_change_pct
from mm_briefing.models import HLInstrumentState, WatchItem


def build_watchlist(
    specs: tuple[WatchlistSpec, ...],
    hl: tuple[HLInstrumentState, ...],
) -> tuple[WatchItem, ...]:
    by_inst = {row.instrument: row for row in hl}
    items: list[WatchItem] = []
    for spec in specs:
        state = by_inst.get(spec.instrument)
        evidence = state.observation_ids() if state is not None else ()
        levels = spec.levels
        if state is not None and state.levels:
            # Config levels win; append HL-derived levels that are not already named.
            have = {name for name, _ in spec.levels}
            extra = tuple((name, value) for name, value in state.levels if name not in have)
            levels = spec.levels + extra
        no_trade = spec.no_trade
        if state is not None and state.data_quality != "ok" and "data_quality" not in no_trade:
            no_trade = f"{no_trade}; HL {spec.instrument} data_quality={state.data_quality}".strip("; ")
        why = spec.why_now
        if state is not None:
            extras: list[str] = []
            funding = funding_value(state)
            oi = oi_change_pct(state)
            basis = basis_mark_oracle(state)
            if funding is not None:
                extras.append(f"funding={funding:.4%}")
            if oi is not None:
                extras.append(f"OI {oi:+.1f}% vs prior print")
            if basis is not None:
                extras.append(f"mark-oracle basis {basis:+.2f}")
            if extras:
                why = f"{spec.why_now} ({'; '.join(extras)})"
        items.append(
            WatchItem(
                instrument=spec.instrument,
                why_now=why,
                evidence=evidence,
                levels=levels,
                invalidation=spec.invalidation,
                no_trade=no_trade,
            )
        )
    return tuple(items)
