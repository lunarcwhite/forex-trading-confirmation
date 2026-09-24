"""Shared decision evaluation. Single source of truth for:

- GET /api/v1/signals/latest (via app.main)
- GET /api/v1/scanner (via app.workers.scanner)
- GET /api/v1/analysis bias/indicators/structure projection (via app.main)

Rule spec: ARCHITECTURE.md sections 14-15. Pattern spec: CALCULATIONS.md 17.
"""

from __future__ import annotations

from app.candles import candles_for
from app.services.analysis.indicators import atr, bollinger, ema_last, rsi
from app.services.analysis.price_action import confirmation as pa_confirmation
from app.services.analysis.price_action import detect as pa_detect
from app.services.analysis.structure import classify_structure, find_swings
from app.services.analysis.supply_demand import (
    build_zone_book,
    select_entry_zone,
)
from app.services.analysis.zones import mtf_alignment
from app.services.news.service import news_risk
from app.services.strategy.rules import aggregate, evaluate_condition

MTF_TIMEFRAMES = ["D1", "H4", "H1", "M15", "M5"]
MIN_CANDLES = 34  # signal-valid first value (MACD); below → insufficient data
ENGINE_VERSION = "decision-v1"


def compute_bias(ema_50, ema_200, structure_bias: str) -> str:
    bias = "bullish" if ema_50 and ema_200 and ema_50 > ema_200 else "neutral"
    if structure_bias == "bearish":
        bias = "bearish"
    return bias


def timeframe_bias(symbol: str, timeframe: str) -> str | None:
    """Bias for one timeframe. None when data is insufficient (honest gap)."""
    cs, _ = candles_for(symbol, timeframe, 200)
    if len(cs) < MIN_CANDLES:
        return None
    closes = [c["close"] for c in cs]
    e50, e200 = ema_last(closes, 50), ema_last(closes, 200)
    st = classify_structure(*find_swings(
        [c["high"] for c in cs], [c["low"] for c in cs], 2))
    return compute_bias(e50, e200, st["bias"])


def location_signal(
    opens: list[float], highs: list[float], lows: list[float],
    closes: list[float], direction: str = "buy", book: dict | None = None,
) -> tuple[str, dict]:
    """Required location evidence (CALCULATIONS.md 14 + decision rule).

    BUY: PASS at support / live bullish FVG; FAIL at resistance / live
    bearish FVG or no location edge; NOT_READY when zones uncomputable.
    """
    from app.services.analysis.indicators import atr as _atr
    from app.services.analysis.supply_demand import build_zone_book as _book

    a = _atr(highs, lows, closes, 14)
    sh, sl = find_swings(highs, lows, 2)
    bk = book if book is not None else _book(opens, highs, lows, closes, a)
    live = [z for z in bk.get("supply_demand", []) if not z.get("mitigated")]
    live += bk.get("fvg_live", [])
    sup, res = bk.get("support", []), bk.get("resistance", [])
    ev = {"support": sup, "resistance": res,
          "fvg_live": bk.get("fvg_live", []),
          "supply_demand_live": live,
          "close": closes[-1] if closes else None}
    if not a or a <= 0 or (not sh and not sl and not live):
        return "NOT_READY", ev
    close = closes[-1]
    tol = 0.25 * a
    in_sup = any(z["low"] <= close <= z["high"] for z in sup)
    in_res = any(z["low"] <= close <= z["high"] for z in res)
    near_sup = any(z["low"] - tol <= close <= z["high"] + tol for z in sup)
    near_res = any(z["low"] - tol <= close <= z["high"] + tol for z in res)
    in_bull = any(z["low"] <= close <= z["high"]
                  and z["type"] in ("bullish", "demand") for z in live)
    in_bear = any(z["low"] <= close <= z["high"]
                  and z["type"] in ("bearish", "supply") for z in live)
    # Containment dominates proximity (flipped zones overlap after BOS).
    if direction == "buy":
        if in_res or in_bear:
            return "FAIL", ev
        if in_sup or in_bull:
            return "PASS", ev
        if near_res:
            return "FAIL", ev
        return ("PASS" if near_sup else "FAIL"), ev
    if in_sup or in_bull:
        return "FAIL", ev
    if in_res or in_bear:
        return "PASS", ev
    if near_sup:
        return "FAIL", ev
    return ("PASS" if near_res else "FAIL"), ev


def volatility_signal(closes: list[float]) -> tuple[str, dict]:
    """BB-width expansion guard (CALCULATIONS.md 8 + decision rule).

    PASS when calm/computable, FAIL on >1.5x width expansion vs prior
    window, NOT_READY below 21 closes.
    """
    now = bollinger(closes)
    prev = bollinger(closes[:-1]) if len(closes) >= 21 else None
    ev = {"width_now": now["width"] if now else None,
          "width_prev": prev["width"] if prev else None}
    if not now or not prev or not now["width"] or not prev["width"]:
        return "NOT_READY", ev
    if now["width"] > 1.5 * prev["width"]:
        return "FAIL", {**ev, "state": "volatility_expansion"}
    return "PASS", {**ev, "state": "normal"}


def spread_signal(
    spread_value: float | None, max_spread: float | None
) -> tuple[str, dict]:
    """Hard-filter input. MVP has no spread feed → NOT_APPLICABLE (spec §15:
    ignored by aggregation, non-blocking until a feed exists)."""
    if spread_value is None or max_spread is None:
        return "NOT_APPLICABLE", {"reason": "no spread feed (MVP)"}
    ok = spread_value <= max_spread
    return ("PASS" if ok else "FAIL",
            {"spread": spread_value, "max_spread": max_spread})


def risk_condition(plan: dict, min_rr: float = 2.0) -> str:
    """Risk rule from a real trade plan. Empty/invalid plan → FAIL."""
    rr = plan.get("risk_reward") if plan else None
    if rr is None or rr + 1e-9 < min_rr:
        return "FAIL"
    return "PASS"


def evaluate(symbol: str, timeframe: str = "H1", direction: str = "buy") -> dict:
    """Evaluate the Trend Pullback BUY setup. Never fabricates patterns."""
    cs, source = candles_for(symbol, timeframe, 200)
    closes = [c["close"] for c in cs]
    highs = [c["high"] for c in cs]
    lows = [c["low"] for c in cs]
    opens = [c["open"] for c in cs]
    e50, e200, r = ema_last(closes, 50), ema_last(closes, 200), rsi(closes, 14)
    a = atr(highs, lows, closes, 14)
    sh, sl = find_swings(highs, lows, 2)
    st = classify_structure(sh, sl)
    bias = compute_bias(e50, e200, st["bias"])
    pa = pa_detect(opens, highs, lows, closes)
    book = build_zone_book(opens, highs, lows, closes, a)
    loc, loc_ev = location_signal(opens, highs, lows, closes, direction,
                                  book=book)
    vol, vol_ev = volatility_signal(closes)
    spr, spr_ev = spread_signal(None, None)  # no feed in MVP
    news = news_risk(symbol)
    news_result = {"ELEVATED": "FAIL", "CLEAR": "PASS",
                   "OFF": "NOT_APPLICABLE"}.get(news["state"], "NOT_READY")
    plan, _ = trade_plan({"last_close": closes[-1] if closes else None,
                          "indicators": {"atr_14": a}})
    results = [
        ("trend", evaluate_condition(e50, "greater_than", ref=e200), True),
        ("momentum", evaluate_condition(r, "greater_than_or_equal", value=50), True),
        ("structure", evaluate_condition(bias, "in", value=["bullish"]), True),
        ("location", loc, True),
        ("price_action", pa_confirmation(pa["signal"], direction), True),
        ("volatility", vol, True),
        ("risk", risk_condition(plan), True),
        ("spread", spr, True),
        ("news", news_result, True),
    ]
    state = aggregate(results, direction=direction, structure_bias=bias)
    biases: dict[str, str] = {}
    for tf in MTF_TIMEFRAMES:
        b = bias if tf == timeframe else timeframe_bias(symbol, tf)
        if b is not None:
            biases[tf] = b
    alignment = mtf_alignment(biases)
    mtf = {"biases": biases, "alignment": alignment}
    invalidations: list[str] = []
    # MTF gate (CALCULATIONS.md 16.1): conflicting/insufficient higher
    # timeframes invalidate the setup — downgrade only, never upgrade.
    if alignment == "weak":
        invalidations.append(
            f"Conflicting timeframe (H4 {biases.get('H4')} vs "
            f"H1 {biases.get('H1')})")
        state = "NO_TRADE"
    elif alignment == "MTF INVALID":
        invalidations.append("Insufficient multi-timeframe data")
        state = "NO_TRADE"
    return {
        "symbol": symbol,
        "timeframe": timeframe,
        "direction": "BUY" if direction == "buy" else "SELL",
        "state": state,
        "bias": bias,
        "structure": st,
        "indicators": {"ema_50": e50, "ema_200": e200, "rsi_14": r, "atr_14": a},
        "confirmations": [t for t, x, _ in results if x == "PASS"],
        "missing_conditions": [t for t, x, q in results
                               if x in ("FAIL", "NOT_READY") and q],
        "results": [{"type": t, "result": x, "required": q} for t, x, q in results],
        "invalidations": invalidations,
        "price_action": pa,
        "news": news,
        "last_close": closes[-1] if closes else None,
        "last_range": (lows[-1], highs[-1]) if lows and highs else None,
        "candle_timestamp": cs[-1]["timestamp"] if cs else None,
        "zones": {k: v for k, v in book.items()},
        "mtf": mtf,
        "data_quality": "ok" if len(cs) >= 34 else "DATA UNAVAILABLE",
        "source": source,
        "engine_version": ENGINE_VERSION,
    }


def trade_plan(ev: dict, min_rr: float = 2.0) -> tuple[dict, dict]:
    """SL/TP suggestion per CALCULATIONS.md 15. Returns (plan, entry_zone).

    Prefers the newest live demand/OB/FVG zone holding the price
    (`entry_source` names it). Falls back to the labeled ATR proxy when no
    zone holds (e.g. simulator data) instead of fabricating a zone.
    Shared by /api/v1/signals/latest and signal persistence.
    """
    from app.services.analysis.zones import suggest_sltp

    plan: dict = {}
    entry_zone: dict = {}
    try:
        entry = ev["last_close"]
        a14 = ev["indicators"].get("atr_14")
        if entry is None or not a14:
            return {}, {}
        book = ev.get("zones") or {}
        direction = "buy" if (ev.get("direction", "BUY") == "BUY") else "sell"
        z = select_entry_zone(book, entry, direction, ev.get("last_range"))
        if z is None:  # labeled fallback, never a fabricated zone
            zl, zh = entry - 0.5 * a14, entry
            source = "atr_proxy"
        else:
            zl, zh, source = z["low"], z["high"], z["kind"]
        plan = suggest_sltp(direction, entry, zl, zh, a14, 0.0, min_rr)
        if "error" in plan:
            return {}, {}
        plan["entry_source"] = source
        entry_zone = {"min": zl, "max": zh, "source": source}
    except (IndexError, TypeError, KeyError):
        return {}, {}
    return plan, entry_zone
