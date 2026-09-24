"""Supply/demand zones + order blocks. Spec: CALCULATIONS.md 14.2-14.3.

MVP simplifications (documented in spec):
- Displacement threshold uses current ATR for all candles.
- Mitigation mirrors the FVG rule: full close through the zone.
- Order block search is bounded to the 3 base candles.
"""

from __future__ import annotations

from app.services.analysis.structure import find_swings


def _swings_before(swings: list[tuple[int, float]], j: int) -> list[tuple[int, float]]:
    return [s for s in swings if s[0] < j]


def find_zones(
    opens: list[float],
    highs: list[float],
    lows: list[float],
    closes: list[float],
    atr_value: float | None,
) -> list[dict]:
    """Detect displacement-based supply/demand + order blocks (chronological).

    Returns [{type: demand|supply, low, high, index, ob, mitigated}].
    """
    zones: list[dict] = []
    n = len(closes)
    if not atr_value or atr_value <= 0 or n < 7:
        return zones
    sh, sl = find_swings(highs, lows, 2)
    for i in range(3, n - 3):
        body = closes[i] - opens[i]
        if abs(body) <= 1.5 * atr_value:
            continue
        bull = body > 0
        ref = sh if bull else sl
        confirmed = False
        for j in range(i + 1, min(i + 4, n)):
            known = _swings_before(ref, j)
            if not known:
                continue
            if bull and closes[j] > known[-1][1]:
                confirmed = True
                break
            if not bull and closes[j] < known[-1][1]:
                confirmed = True
                break
        if not confirmed:
            continue
        base = list(range(max(0, i - 3), i))
        blo = min(lows[k] for k in base)
        bhi = max(highs[k] for k in base)
        ob = None
        for k in range(i - 1, max(0, i - 3) - 1, -1):
            bear = closes[k] < opens[k]
            if (bull and bear) or (not bull and not bear and closes[k] > opens[k]):
                ob = {"low": lows[k], "high": highs[k], "index": k}
                break
        mitigated = False
        for k in range(i + 1, n):
            if bull and closes[k] < blo:
                mitigated = True
                break
            if not bull and closes[k] > bhi:
                mitigated = True
                break
        zones.append({
            "type": "demand" if bull else "supply",
            "low": blo, "high": bhi, "index": i,
            "ob": ob, "mitigated": mitigated,
        })
    return zones


def build_zone_book(
    opens: list[float],
    highs: list[float],
    lows: list[float],
    closes: list[float],
    atr_value: float | None,
) -> dict:
    """All location evidence in one structure (shared by location + entry)."""
    from app.services.analysis.zones import cluster_sr, find_fvg

    sh, sl = find_swings(highs, lows, 2)
    sd = find_zones(opens, highs, lows, closes, atr_value)
    fvg = [z for z in find_fvg(highs, lows, closes)
           if not z.get("mitigated")] if len(highs) >= 3 else []
    return {
        "supply_demand": sd,
        "fvg_live": fvg,
        "support": cluster_sr(sl, atr_value) if atr_value else [],
        "resistance": cluster_sr(sh, atr_value) if atr_value else [],
    }


def select_entry_zone(
    book: dict, close: float, direction: str = "buy",
    last_range: tuple[float, float] | None = None,
) -> dict | None:
    """Newest zone of matching direction containing (or touching) the price."""
    want = "demand" if direction == "buy" else "supply"
    want_fvg = "bullish" if direction == "buy" else "bearish"
    cands: list[dict] = []
    for z in book.get("supply_demand", []):
        if z["type"] != want or z.get("mitigated"):
            continue
        cands.append({"kind": want, "low": z["low"], "high": z["high"],
                      "index": z["index"]})
        if z.get("ob"):
            cands.append({"kind": "order_block", "low": z["ob"]["low"],
                          "high": z["ob"]["high"], "index": z["ob"]["index"]})
    for f in book.get("fvg_live", []):
        if f.get("type") != want_fvg:
            continue
        cands.append({"kind": "fvg", "low": f["low"], "high": f["high"],
                      "index": f["index"]})
    lo, hi = (close, close) if not last_range else last_range
    holding = [c for c in cands
               if c["low"] <= close <= c["high"] or (lo <= c["high"] and hi >= c["low"])]
    if not holding:
        return None
    return max(holding, key=lambda c: c["index"])
