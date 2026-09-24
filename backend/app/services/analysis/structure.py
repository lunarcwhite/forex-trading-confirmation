"""Market structure. Spec: CALCULATIONS.md sections 11-13."""

from __future__ import annotations


def find_swings(
    highs: list[float], lows: list[float], n: int = 2
) -> tuple[list[tuple[int, float]], list[tuple[int, float]]]:
    """Returns (swing_highs, swing_lows) as (index, price). Last n candles unconfirmed."""
    sh: list[tuple[int, float]] = []
    sl: list[tuple[int, float]] = []
    m = len(highs)
    if m < 2 * n + 1 or len(lows) != m:
        return sh, sl
    for i in range(n, m - n):
        wh = highs[i - n : i + n + 1]
        if highs[i] == max(wh) and highs[i] > highs[i - 1] and highs[i] >= highs[i + 1]:
            sh.append((i, highs[i]))
        wl = lows[i - n : i + n + 1]
        if lows[i] == min(wl) and lows[i] < lows[i - 1] and lows[i] <= lows[i + 1]:
            sl.append((i, lows[i]))
    return sh, sl


def classify_structure(
    swing_highs: list[tuple[int, float]], swing_lows: list[tuple[int, float]]
) -> dict:
    if len(swing_highs) < 2 or len(swing_lows) < 2:
        return {"bias": "neutral", "pattern": "insufficient_swings"}
    hh = swing_highs[-1][1] > swing_highs[-2][1]
    hl = swing_lows[-1][1] > swing_lows[-2][1]
    lh = swing_highs[-1][1] < swing_highs[-2][1]
    ll = swing_lows[-1][1] < swing_lows[-2][1]
    if hh and hl:
        return {"bias": "bullish", "pattern": "HH_HL"}
    if lh and ll:
        return {"bias": "bearish", "pattern": "LH_LL"}
    return {"bias": "neutral", "pattern": "range"}


def structure_strength(close_last: float, swing_prev: float, atr: float | None) -> str:
    if atr is None or atr <= 0:
        return "weak"
    disp = abs(close_last - swing_prev) / atr
    if disp > 2.0:
        return "strong"
    if disp >= 1.0:
        return "moderate"
    return "weak"


def bos_choch(
    closes: list[float],
    swing_highs: list[tuple[int, float]],
    swing_lows: list[tuple[int, float]],
    prior_bias: str = "neutral",
) -> dict | None:
    """Close-based BOS/CHoCH on last close vs last swings."""
    if not closes or not swing_highs or not swing_lows:
        return None
    last = closes[-1]
    sh = swing_highs[-1][1]
    sl = swing_lows[-1][1]
    if last > sh:
        kind = "CHoCH_bullish" if prior_bias == "bearish" else "BOS_bullish"
        return {"event": kind, "level": sh}
    if last < sl:
        kind = "CHoCH_bearish" if prior_bias == "bullish" else "BOS_bearish"
        return {"event": kind, "level": sl}
    return None
