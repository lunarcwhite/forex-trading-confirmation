"""Ingestion worker CLI. Usage:
python -m app.workers.ingest --symbol EUR/USD --timeframe H1 --limit 200 --source simulator
"""

from __future__ import annotations

import argparse
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "backend"))

from app.services.market.adapter import DataUnavailable, get_adapter
from app.services.market.normalizer import normalize
from app.services.market.repository import upsert


def run(symbol: str, timeframe: str, limit: int, source: str, csv_path: str = "",
        store: str = "auto") -> dict:
    try:
        adapter = get_adapter(source, path=csv_path) if source == "csv_import" else get_adapter(source)
        raw = adapter.fetch(symbol, timeframe, limit)
    except DataUnavailable as e:
        return {"status": "DATA UNAVAILABLE", "reason": str(e)}
    clean, report = normalize(raw, symbol, timeframe)
    use_pg = (store == "postgres") or (store == "auto" and os.getenv("DATABASE_URL"))
    if use_pg:
        try:
            from app.services.market import pg_repository as pg

            stored = pg.save_candles(clean)
            return {"status": "ok", **report, **stored, "source": source, "store": "postgres"}
        except Exception as e:
            if store == "postgres":
                return {"status": "STORE FAILED", "reason": str(e)}
    stored = upsert(clean)
    return {"status": "ok", **report, **stored, "source": source, "store": "jsonl"}


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--symbol", default="EUR/USD")
    p.add_argument("--timeframe", default="H1")
    p.add_argument("--limit", type=int, default=200)
    p.add_argument("--source", default="simulator", choices=["simulator", "csv_import", "primary"])
    p.add_argument("--csv-path", default="")
    p.add_argument("--store", default="auto", choices=["auto", "postgres", "jsonl"])
    a = p.parse_args()
    print(run(a.symbol, a.timeframe, a.limit, a.source, a.csv_path, a.store))


if __name__ == "__main__":
    main()
