"""Normalize + validate candles. Bad rows rejected, never fabricated."""

from __future__ import annotations

from datetime import datetime, timezone


def _to_utc_iso(ts: str) -> str | None:
    try:
        dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc).isoformat()
    except (ValueError, TypeError):
        return None


def validate_row(r: dict) -> tuple[bool, str]:
    for k in ("timestamp", "open", "high", "low", "close"):
        if r.get(k) is None:
            return False, f"missing:{k}"
    try:
        o, h, l, c = float(r["open"]), float(r["high"]), float(r["low"]), float(r["close"])
    except (TypeError, ValueError):
        return False, "non-numeric"
    if min(o, h, l, c) <= 0:
        return False, "non-positive"
    if not (h >= max(o, c) and l <= min(o, c) and h >= l):
        return False, "malformed-ohlc"
    if _to_utc_iso(str(r["timestamp"])) is None:
        return False, "bad-timestamp"
    return True, "ok"


def normalize(rows: list[dict], symbol: str, timeframe: str) -> tuple[list[dict], dict]:
    """Returns (clean_rows, report). Dedupes on (symbol,timeframe,timestamp,source)."""
    seen: set[tuple] = set()
    clean, dup, bad = [], 0, 0
    for r in rows:
        ok, _ = validate_row(r)
        if not ok:
            bad += 1
            continue
        key = (symbol, timeframe, _to_utc_iso(str(r["timestamp"])), r.get("source", "?"))
        if key in seen:
            dup += 1
            continue
        seen.add(key)
        clean.append(
            {
                "symbol": symbol,
                "timeframe": timeframe,
                "timestamp": key[2],
                "open": float(r["open"]),
                "high": float(r["high"]),
                "low": float(r["low"]),
                "close": float(r["close"]),
                "volume": float(r.get("volume", 0) or 0),
                "source": r.get("source", "?"),
            }
        )
    clean.sort(key=lambda x: x["timestamp"])
    return clean, {
        "ingested": len(clean),
        "duplicates": dup,
        "invalid": bad,
        "data_quality": "ok" if clean else "DATA UNAVAILABLE",
    }
