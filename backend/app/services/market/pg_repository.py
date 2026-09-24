"""Postgres candle repository. Mirrors the SQL unique constraint."""

from __future__ import annotations

from app.db import connect


def pair_id(conn, symbol: str) -> str:
    row = conn.execute(
        "select id from currency_pairs where symbol=%s", (symbol,)
    ).fetchone()
    if not row:
        raise KeyError(f"unknown symbol: {symbol}")
    return row[0]


def save_candles(rows: list[dict]) -> dict:
    """rows: normalized dicts (symbol,timeframe,timestamp,open,high,low,close,volume,source)."""
    if not rows:
        return {"saved": 0}
    with connect() as conn:
        with conn.cursor() as cur:
            ids: dict[str, str] = {}
            for s in {r["symbol"] for r in rows}:
                ids[s] = str(pair_id(conn, s))
            existing = set()
            for pid, tf, ts, src in cur.execute(
                """select currency_pair_id::text, timeframe, timestamp, source
                   from market_candles
                   where currency_pair_id = any(%s)""",
                ([ids[s] for s in ids],),
            ).fetchall():
                existing.add((pid, tf, ts.isoformat(), src))
            n = 0
            for r in rows:
                key = (ids[r["symbol"]], r["timeframe"], r["timestamp"], r["source"])
                if key in existing:
                    continue
                cur.execute(
                    """insert into market_candles
                       (currency_pair_id, timeframe, timestamp, open, high, low, close, volume, source)
                       values (%s,%s,%s,%s,%s,%s,%s,%s,%s)
                       on conflict do nothing""",
                    (ids[r["symbol"]], r["timeframe"], r["timestamp"], r["open"],
                     r["high"], r["low"], r["close"], r.get("volume", 0), r["source"]),
                )
                existing.add(key)
                n += 1
        conn.commit()
    return {"saved": n}


def load_candles(symbol: str, timeframe: str, limit: int = 200) -> list[dict]:
    with connect() as conn:
        rows = conn.execute(
            """select c.timestamp, c.open, c.high, c.low, c.close, c.volume, c.source
               from market_candles c join currency_pairs p on p.id=c.currency_pair_id
               where p.symbol=%s and c.timeframe=%s
               order by c.timestamp desc limit %s""",
            (symbol, timeframe, limit),
        ).fetchall()
    out = [
        {"timestamp": r[0].isoformat(), "open": float(r[1]), "high": float(r[2]),
         "low": float(r[3]), "close": float(r[4]), "volume": float(r[5]), "source": r[6]}
        for r in rows
    ]
    out.reverse()
    return out
