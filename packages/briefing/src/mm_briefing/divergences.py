"""Explicit cross-asset divergence rules. No LLM."""

from __future__ import annotations

from typing import Any

from mm_briefing.models import AssetPrint, Divergence, MacroSnapshot


def evaluate_divergences(snapshot: MacroSnapshot, rules: dict[str, Any] | None = None) -> tuple[Divergence, ...]:
    by_symbol = snapshot.by_symbol()
    spec = (rules or {}).get("rules") if rules and "rules" in rules else (rules or {})
    out: list[Divergence] = []

    equity_vol = spec.get("equity_vol") or {}
    if equity_vol.get("enabled", True):
        found = _opposite(
            by_symbol.get("ES"),
            by_symbol.get("VIX"),
            min_a=float(equity_vol.get("es_abs_pct") or 0.3),
            min_b=float(equity_vol.get("vix_abs_pct") or 3.0),
            rule_id="equity_vol",
            title="Equity / vol divergence",
            detail_fn=lambda es, vix: (
                f"ES {fmt_pct(es.change_pct)} while VIX {fmt_pct(vix.change_pct)} since prior US close"
            ),
        )
        if found:
            out.append(found)

    crypto_equity = spec.get("crypto_equity") or {}
    if crypto_equity.get("enabled", True):
        found = _opposite(
            by_symbol.get("BTC"),
            by_symbol.get("ES"),
            min_a=float(crypto_equity.get("btc_abs_pct") or 0.8),
            min_b=float(crypto_equity.get("es_abs_pct") or 0.3),
            rule_id="crypto_equity",
            title="Crypto / equity divergence",
            detail_fn=lambda btc, es: (
                f"BTC {fmt_pct(btc.change_pct)} vs ES {fmt_pct(es.change_pct)} since prior US close"
            ),
        )
        if found:
            out.append(found)

    usd_equity = spec.get("usd_equity") or {}
    if usd_equity.get("enabled", True):
        found = _same_sign(
            by_symbol.get("DXY"),
            by_symbol.get("ES"),
            min_a=float(usd_equity.get("dxy_abs_pct") or 0.25),
            min_b=float(usd_equity.get("es_abs_pct") or 0.3),
            rule_id="usd_equity",
            title="USD / equity co-move",
            detail_fn=lambda dxy, es: (
                f"DXY {fmt_pct(dxy.change_pct)} with ES {fmt_pct(es.change_pct)} (unusual USD+risk co-move)"
            ),
        )
        if found:
            out.append(found)

    yields_equity = spec.get("yields_equity") or {}
    if yields_equity.get("enabled", True):
        us10y = by_symbol.get("US10Y")
        es = by_symbol.get("ES")
        min_bp = float(yields_equity.get("us10y_abs_bp") or 5.0)
        min_es = float(yields_equity.get("es_abs_pct") or 0.3)
        if us10y and es and us10y.change_bp is not None and es.change_pct is not None:
            if abs(us10y.change_bp) >= min_bp and abs(es.change_pct) >= min_es:
                if us10y.change_bp > 0 and es.change_pct > 0:
                    out.append(
                        Divergence(
                            rule_id="yields_equity",
                            title="Yields up with equities bid",
                            detail=(
                                f"US10Y {us10y.change_bp:+.1f}bp with ES {fmt_pct(es.change_pct)} "
                                "since prior US close"
                            ),
                            evidence=("US10Y", "ES"),
                        )
                    )

    oil_usd = spec.get("oil_usd") or {}
    if oil_usd.get("enabled", True):
        found = _same_sign(
            by_symbol.get("CL"),
            by_symbol.get("DXY"),
            min_a=float(oil_usd.get("cl_abs_pct") or 1.0),
            min_b=float(oil_usd.get("dxy_abs_pct") or 0.25),
            rule_id="oil_usd",
            title="Oil / USD co-move",
            detail_fn=lambda cl, dxy: (
                f"CL {fmt_pct(cl.change_pct)} with DXY {fmt_pct(dxy.change_pct)} (typically inverse)"
            ),
        )
        if found:
            out.append(found)

    return tuple(sorted(out, key=lambda row: row.rule_id))


def unexpected_moves(session: MacroSnapshot, overnight: MacroSnapshot) -> tuple[str, ...]:
    """Close-brief hooks: session outcome vs overnight tape."""
    overnight_map = overnight.by_symbol()
    session_map = session.by_symbol()
    notes: list[str] = []
    es_on = overnight_map.get("ES")
    es_sess = session_map.get("ES")
    if es_on and es_sess and es_on.change_pct is not None and es_sess.change_pct is not None:
        if abs(es_sess.change_pct - es_on.change_pct) >= 0.40:
            notes.append(
                f"ES session {fmt_pct(es_sess.change_pct)} vs overnight {fmt_pct(es_on.change_pct)}"
            )
    btc_on = overnight_map.get("BTC")
    btc_sess = session_map.get("BTC")
    if btc_on and btc_sess and btc_on.change_pct is not None and btc_sess.change_pct is not None:
        if abs(btc_sess.change_pct - btc_on.change_pct) >= 0.80:
            notes.append(
                f"BTC session {fmt_pct(btc_sess.change_pct)} vs overnight {fmt_pct(btc_on.change_pct)}"
            )
    vix_sess = session_map.get("VIX")
    if vix_sess and vix_sess.change_pct is not None and abs(vix_sess.change_pct) >= 8.0:
        notes.append(f"VIX session move {fmt_pct(vix_sess.change_pct)} is large vs a quiet overnight")
    eth_sess = session_map.get("ETH")
    if btc_sess and eth_sess and btc_sess.change_pct is not None and eth_sess.change_pct is not None:
        if btc_sess.change_pct - eth_sess.change_pct >= 1.0:
            notes.append(
                f"ETH lagged BTC on the cash session ({fmt_pct(eth_sess.change_pct)} vs {fmt_pct(btc_sess.change_pct)})"
            )
    return tuple(notes)


def assumption_changes(session: MacroSnapshot, overnight: MacroSnapshot) -> tuple[str, ...]:
    overnight_map = overnight.by_symbol()
    session_map = session.by_symbol()
    notes: list[str] = []
    dxy_on = overnight_map.get("DXY")
    dxy_sess = session_map.get("DXY")
    if dxy_on and dxy_sess and dxy_on.change_pct is not None and dxy_sess.change is not None and dxy_on.change is not None:
        if dxy_on.change * (dxy_sess.last - (dxy_sess.open or dxy_on.last or 0)) < 0 and abs(dxy_sess.change_pct or 0) >= 0.2:
            notes.append("USD overnight direction did not hold into the cash close")
    vix_on = overnight_map.get("VIX")
    vix_sess = session_map.get("VIX")
    if vix_on and vix_sess and (vix_on.change_pct or 0) < 0 and (vix_sess.change_pct or 0) < -8:
        notes.append("Vol crush extended: overnight bid-for-risk assumption still in force")
    us10y_on = overnight_map.get("US10Y")
    us10y_sess = session_map.get("US10Y")
    if us10y_on and us10y_sess and us10y_on.change_bp is not None and us10y_sess.change_bp is not None:
        if us10y_on.change_bp > 0 and us10y_sess.change_bp > us10y_on.change_bp + 2:
            notes.append("Higher-yield overnight backup continued into the US session")
    if not notes:
        notes.append("No named macro assumption flipped vs the overnight tape")
    return tuple(notes)


def fmt_pct(value: float | None) -> str:
    if value is None:
        return "n/a"
    return f"{value:+.2f}%"


def fmt_px(value: float | None, *, digits: int = 2) -> str:
    if value is None:
        return "n/a"
    return f"{value:.{digits}f}"


def _opposite(
    a: AssetPrint | None,
    b: AssetPrint | None,
    *,
    min_a: float,
    min_b: float,
    rule_id: str,
    title: str,
    detail_fn,
) -> Divergence | None:
    if a is None or b is None or a.change_pct is None or b.change_pct is None:
        return None
    if abs(a.change_pct) < min_a or abs(b.change_pct) < min_b:
        return None
    if a.change_pct == 0 or b.change_pct == 0:
        return None
    if (a.change_pct > 0) == (b.change_pct > 0):
        return None
    return Divergence(
        rule_id=rule_id,
        title=title,
        detail=detail_fn(a, b),
        evidence=(a.symbol, b.symbol),
    )


def _same_sign(
    a: AssetPrint | None,
    b: AssetPrint | None,
    *,
    min_a: float,
    min_b: float,
    rule_id: str,
    title: str,
    detail_fn,
) -> Divergence | None:
    if a is None or b is None or a.change_pct is None or b.change_pct is None:
        return None
    if abs(a.change_pct) < min_a or abs(b.change_pct) < min_b:
        return None
    if a.change_pct == 0 or b.change_pct == 0:
        return None
    if (a.change_pct > 0) != (b.change_pct > 0):
        return None
    return Divergence(
        rule_id=rule_id,
        title=title,
        detail=detail_fn(a, b),
        evidence=(a.symbol, b.symbol),
    )
