"""Dev candle store (JSONL). Unique key mirrors SQL constraint."""

from __future__ import annotations

import json
import os

STORE_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "data", "candles.jsonl")


def _load_all(path: str = STORE_PATH) -> dict[tuple, dict]:
    rows: dict[tuple, dict] = {}
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                r = json.loads(line)
                rows[(r["symbol"], r["timeframe"], r["timestamp"], r["source"])] = r
    return rows


def upsert(rows: list[dict], path: str = STORE_PATH) -> dict:
    existing = _load_all(path)
    added = 0
    for r in rows:
        key = (r["symbol"], r["timeframe"], r["timestamp"], r["source"])
        if key not in existing:
            existing[key] = r
            added += 1
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        for r in sorted(existing.values(), key=lambda x: (x["symbol"], x["timeframe"], x["timestamp"])):
            f.write(json.dumps(r) + "\n")
    return {"added": added, "total": len(existing)}
