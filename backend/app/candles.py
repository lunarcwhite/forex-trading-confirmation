"""Candle source router: Postgres first, simulator fallback (honest source label)."""

from __future__ import annotations

import os


def candles_for(symbol: str, timeframe: str, limit: int = 200) -> tuple[list[dict], str]:
    if os.getenv("DATABASE_URL"):
        try:
            from app.services.market import pg_repository as pg

            rows = pg.load_candles(symbol, timeframe, limit)
            if rows:
                return rows, "postgres"
        except Exception:
            pass
    from app.store import gen_candles

    return gen_candles(symbol, timeframe, limit), "simulator"
