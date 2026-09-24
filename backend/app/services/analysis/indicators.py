"""MVP indicator engine. Spec: CALCULATIONS.md sections 2-9.

Returns None when insufficient data (caller maps to NOT_READY).
No I/O, no AI, deterministic.
"""

from __future__ import annotations

import math


def sma(closes: list[float], n: int) -> float | None:
    if n <= 0 or len(closes) < n:
        return None
    return sum(closes[-n:]) / n


def ema_series(closes: list[float], n: int) -> list[float | None]:
    """Full series; first n-1 entries None, index n-1 is SMA seed."""
    out: list[float | None] = [None] * len(closes)
    if n <= 0 or len(closes) < n:
        return out
    k = 2.0 / (n + 1)
    seed = sum(closes[:n]) / n
    out[n - 1] = seed
    for i in range(n, len(closes)):
        prev = out[i - 1]
        assert prev is not None
        out[i] = closes[i] * k + prev * (1 - k)
    return out


def ema_last(closes: list[float], n: int) -> float | None:
    s = ema_series(closes, n)
    return s[-1] if s else None


def _wilder_smooth(values: list[float], n: int) -> list[float | None]:
    out: list[float | None] = [None] * len(values)
    if len(values) < n or n <= 0:
        return out
    seed = sum(values[:n]) / n
    out[n - 1] = seed
    for i in range(n, len(values)):
        prev = out[i - 1]
        assert prev is not None
        out[i] = (prev * (n - 1) + values[i]) / n
    return out


def rsi(closes: list[float], n: int = 14) -> float | None:
    if len(closes) < n + 1:
        return None
    gains = [max(closes[i] - closes[i - 1], 0.0) for i in range(1, len(closes))]
    losses = [max(closes[i - 1] - closes[i], 0.0) for i in range(1, len(closes))]
    ag = _wilder_smooth(gains, n)[-1]
    al = _wilder_smooth(losses, n)[-1]
    if ag is None or al is None:
        return None
    if al == 0:
        return 100.0
    if ag == 0:
        return 0.0
    return 100.0 - 100.0 / (1.0 + ag / al)


def macd(
    closes: list[float], fast: int = 12, slow: int = 26, signal: int = 9
) -> dict | None:
    if len(closes) < slow + signal - 1:
        return None
    ef = ema_series(closes, fast)
    es = ema_series(closes, slow)
    line = [None if a is None or b is None else a - b for a, b in zip(ef, es)]
    valid = [x for x in line if x is not None]
    sig = ema_series(valid, signal)
    if not valid or sig[-1] is None:
        return None
    return {
        "macd_line": valid[-1],
        "signal_line": sig[-1],
        "hist": valid[-1] - sig[-1],
    }


def atr(
    highs: list[float], lows: list[float], closes: list[float], n: int = 14
) -> float | None:
    if not (len(highs) == len(lows) == len(closes)) or len(closes) < n + 1:
        return None
    trs = []
    for i in range(1, len(closes)):
        trs.append(
            max(
                highs[i] - lows[i],
                abs(highs[i] - closes[i - 1]),
                abs(lows[i] - closes[i - 1]),
            )
        )
    return _wilder_smooth(trs, n)[-1]


def adx(
    highs: list[float], lows: list[float], closes: list[float], n: int = 14
) -> float | None:
    m = len(closes)
    if not (len(highs) == len(lows) == m) or m < 2 * n + 1:
        return None
    pdm, mdm, trs = [], [], []
    for i in range(1, m):
        up = highs[i] - highs[i - 1]
        dn = lows[i - 1] - lows[i]
        pdm.append(up if up > dn and up > 0 else 0.0)
        mdm.append(dn if dn > up and dn > 0 else 0.0)
        trs.append(
            max(
                highs[i] - lows[i],
                abs(highs[i] - closes[i - 1]),
                abs(lows[i] - closes[i - 1]),
            )
        )
    satr = _wilder_smooth(trs, n)
    sp = _wilder_smooth(pdm, n)
    sm = _wilder_smooth(mdm, n)
    dxs: list[float] = []
    for i in range(len(trs)):
        if satr[i] is None or sp[i] is None or sm[i] is None or satr[i] == 0:
            continue
        pdi = 100.0 * sp[i] / satr[i]
        mdi = 100.0 * sm[i] / satr[i]
        denom = pdi + mdi
        dxs.append(0.0 if denom == 0 else 100.0 * abs(pdi - mdi) / denom)
    if len(dxs) < n:
        return None
    return _wilder_smooth(dxs, n)[-1]


def bollinger(
    closes: list[float], n: int = 20, mult: float = 2.0
) -> dict | None:
    if len(closes) < n:
        return None
    window = closes[-n:]
    basis = sum(window) / n
    var = sum((x - basis) ** 2 for x in window) / n
    upper = basis + mult * math.sqrt(var)
    lower = basis - mult * math.sqrt(var)
    last = closes[-1]
    pct_b = None if upper == lower else (last - lower) / (upper - lower)
    return {
        "basis": basis,
        "upper": upper,
        "lower": lower,
        "pct_b": pct_b,
        "width": (upper - lower) / basis if basis != 0 else None,
    }
