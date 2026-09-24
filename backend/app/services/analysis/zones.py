"""Zones + SL/TP + MTF. Spec: CALCULATIONS.md sections 14-16."""

from __future__ import annotations


def cluster_sr(
    swings: list[tuple[int, float]], atr: float, min_touches: int = 2
) -> list[dict]:
    """Group swing prices within 0.25*ATR into zones."""
    if atr is None or atr <= 0 or not swings:
        return []
    tol = 0.25 * atr
    groups: list[list[float]] = []
    for _, price in sorted(swings, key=lambda x: x[1]):
        placed = False
        for g in groups:
            if abs(price - sum(g) / len(g)) <= tol:
                g.append(price)
                placed = True
                break
        if not placed:
            groups.append([price])
    zones = []
    for g in groups:
        if len(g) >= min_touches:
            zones.append(
                {
                    "low": min(g),
                    "high": max(g),
                    "touches": len(g),
                    "strength": "strong" if len(g) >= 3 else "moderate",
                }
            )
    return zones


def find_fvg(
    highs: list[float], lows: list[float], closes: list[float] | None = None
) -> list[dict]:
    """3-candle gaps. Mitigation needs closes; without it all are unmitigated."""
    zones = []
    for i in range(2, len(highs)):
        if lows[i] > highs[i - 2]:
            zones.append(
                {"type": "bullish", "low": highs[i - 2], "high": lows[i], "index": i}
            )
        elif highs[i] < lows[i - 2]:
            zones.append(
                {"type": "bearish", "low": highs[i], "high": lows[i - 2], "index": i}
            )
    if closes is not None:
        for z in zones:
            for c in closes[z["index"] + 1 :]:
                if z["type"] == "bullish" and c < z["low"]:
                    z["mitigated"] = True
                    break
                if z["type"] == "bearish" and c > z["high"]:
                    z["mitigated"] = True
                    break
            z.setdefault("mitigated", False)
    else:
        for z in zones:
            z["mitigated"] = False
    return zones


def suggest_sltp(
    direction: str,
    entry_ref: float,
    zone_low: float,
    zone_high: float,
    atr: float,
    spread: float = 0.0,
    min_rr: float = 2.0,
) -> dict:
    """MVP SL/TP. Returns error dict if invalid."""
    if atr is None or atr <= 0:
        return {"error": "RISK VALIDATION FAILED", "reason": "no atr"}
    if direction == "buy":
        sl_raw = min(zone_low - 0.2 * atr, entry_ref - 1.0 * atr)
        stop = sl_raw - spread
        sl_dist = entry_ref - stop
        if sl_dist <= 0:
            return {"error": "RISK VALIDATION FAILED", "reason": "sl_dist<=0"}
        tp = entry_ref + min_rr * sl_dist
        return {
            "entry": entry_ref,
            "stop_loss": stop,
            "take_profit": tp,
            "risk_reward": (tp - entry_ref) / sl_dist,
        }
    if direction == "sell":
        sl_raw = max(zone_high + 0.2 * atr, entry_ref + 1.0 * atr)
        stop = sl_raw + spread
        sl_dist = stop - entry_ref
        if sl_dist <= 0:
            return {"error": "RISK VALIDATION FAILED", "reason": "sl_dist<=0"}
        tp = entry_ref - min_rr * sl_dist
        return {
            "entry": entry_ref,
            "stop_loss": stop,
            "take_profit": tp,
            "risk_reward": (entry_ref - tp) / sl_dist,
        }
    return {"error": "RISK VALIDATION FAILED", "reason": "bad direction"}


BIAS_SCORE = {"bullish": 1, "neutral": 0, "bearish": -1}


def mtf_alignment(biases: dict) -> str:
    """biases: {D1,H4,H1,M15,M5}. M5 timing only."""
    need = ["D1", "H4", "H1", "M15", "M5"]
    if sum(1 for k in need if k in biases) < 3:
        return "MTF INVALID"
    h4, h1, m15, d1 = (
        biases.get("H4", "neutral"),
        biases.get("H1", "neutral"),
        biases.get("M15", "neutral"),
        biases.get("D1", "neutral"),
    )
    if h4 != "neutral" and h4 == h1 == m15 and d1 in (h4, "neutral"):
        return "strong"
    if h4 != "neutral" and h4 == h1 and m15 == "neutral":
        return "moderate"
    if h4 != "neutral" and h4 != h1:
        return "weak"
    return "weak"
