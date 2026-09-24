"""Deterministic simulator provider (source='simulator'). No external calls."""

from __future__ import annotations

import hashlib
import math
from datetime import datetime, timedelta, timezone

BASE_PRICES = {"EUR/USD": 1.1750, "GBP/USD": 1.3400, "USD/JPY": 150.0, "XAU/USD": 2650.0}


def gen_candles(symbol: str, timeframe: str, limit: int = 200) -> list[dict]:
    base = BASE_PRICES.get(symbol, 1.0)
    seed = int(hashlib.md5(f"{symbol}:{timeframe}".encode()).hexdigest()[:8], 16)
    out = []
    t0 = datetime(2026, 1, 1, tzinfo=timezone.utc)
    for i in range(limit):
        drift = 0.0008 * base * i / 100.0  # gentle uptrend
        wave = 0.0015 * base * math.sin((i + seed % 50) / 8.0)
        close = base + drift + wave
        open_ = base + drift + 0.0015 * base * math.sin((i + seed % 50 - 1) / 8.0)
        high = max(open_, close) + 0.0006 * base
        low = min(open_, close) - 0.0006 * base
        out.append(
            {
                "timestamp": (t0 + timedelta(hours=i)).isoformat(),
                "open": round(open_, 5),
                "high": round(high, 5),
                "low": round(low, 5),
                "close": round(close, 5),
                "volume": 0.0,
                "source": "simulator",
            }
        )
    return out
