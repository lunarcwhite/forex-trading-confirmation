"""Price action pattern detection. Spec: CALCULATIONS.md section 17.

Deterministic, OHLC-only. Evaluates the last two stored candles
(history is closed; no forming-candle concept in MVP).
Never infers a pattern from incomplete data.
"""

from __future__ import annotations


def _body(o: float, c: float) -> float:
    return abs(c - o)


def _is_bull(o: float, c: float) -> bool:
    return c > o


def _is_bear(o: float, c: float) -> bool:
    return c < o


def detect(opens, highs, lows, closes) -> dict:
    """Return {pattern, signal}. signal in bullish/bearish/None."""
    if len(closes) < 2 or not all(
        len(x) >= 2 for x in (opens, highs, lows, closes)
    ):
        return {"pattern": None, "signal": None, "reason": "NOT_READY"}
    o0, h0, l0, c0 = opens[-2], highs[-2], lows[-2], closes[-2]
    o1, h1, l1, c1 = opens[-1], highs[-1], lows[-1], closes[-1]
    if min(o0, c0, h0, l0, o1, c1, h1, l1) <= 0:
        return {"pattern": None, "signal": None, "reason": "NOT_READY"}

    # Engulfing (body engulf on previous body)
    if _is_bear(o0, c0) and _is_bull(o1, c1):
        if o1 <= c0 and c1 >= o0:
            return {"pattern": "bullish_engulfing", "signal": "bullish"}
    if _is_bull(o0, c0) and _is_bear(o1, c1):
        if o1 >= c0 and c1 <= o0:
            return {"pattern": "bearish_engulfing", "signal": "bearish"}

    # Pin bars on the last candle
    body = _body(o1, c1)
    if body > 0:
        lower = min(o1, c1) - l1
        upper = h1 - max(o1, c1)
        if lower >= 2 * body and upper <= body:
            return {"pattern": "bullish_pin", "signal": "bullish"}
        if upper >= 2 * body and lower <= body:
            return {"pattern": "bearish_pin", "signal": "bearish"}

    return {"pattern": None, "signal": None, "reason": "no_pattern"}


def confirmation(signal: str | None, direction: str = "buy") -> str:
    """Map a detected signal to PASS/FAIL/NOT_READY for a setup direction."""
    if signal is None:
        return "NOT_READY"
    want = "bullish" if direction == "buy" else "bearish"
    if signal == want:
        return "PASS"
    return "FAIL"
