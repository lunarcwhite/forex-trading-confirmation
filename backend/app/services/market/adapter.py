"""Market data adapters. MVP: simulator + CSV + env-configured API stub."""

from __future__ import annotations

import csv
import os


class DataUnavailable(Exception):
    pass


class BaseAdapter:
    source: str = "unknown"

    def fetch(self, symbol: str, timeframe: str, limit: int = 200) -> list[dict]:
        raise NotImplementedError


class SimulatorAdapter(BaseAdapter):
    source = "simulator"

    def fetch(self, symbol: str, timeframe: str, limit: int = 200) -> list[dict]:
        from app.store import gen_candles

        return gen_candles(symbol, timeframe, limit)


class CsvAdapter(BaseAdapter):
    source = "csv_import"

    def __init__(self, path: str):
        self.path = path

    def fetch(self, symbol: str, timeframe: str, limit: int = 200) -> list[dict]:
        rows = []
        with open(self.path, newline="", encoding="utf-8") as f:
            for r in csv.DictReader(f):
                rows.append(
                    {
                        "timestamp": r["timestamp"],
                        "open": float(r["open"]),
                        "high": float(r["high"]),
                        "low": float(r["low"]),
                        "close": float(r["close"]),
                        "volume": float(r.get("volume", 0) or 0),
                        "source": self.source,
                    }
                )
        return rows[-limit:]


class ApiAdapter(BaseAdapter):
    """Primary provider. No hard-coded vendor; env-driven. MVP: honest stub."""

    def __init__(self):
        self.provider = os.getenv("MARKET_DATA_PROVIDER", "")
        self.source = f"primary:{self.provider}" if self.provider else "primary:unconfigured"

    def fetch(self, symbol: str, timeframe: str, limit: int = 200) -> list[dict]:
        if not self.provider:
            raise DataUnavailable("MARKET_DATA_PROVIDER not configured")
        raise DataUnavailable(f"provider '{self.provider}' not implemented in MVP")


def get_adapter(source: str, **kwargs) -> BaseAdapter:
    if source == "simulator":
        return SimulatorAdapter()
    if source == "csv_import":
        return CsvAdapter(kwargs["path"])
    if source == "primary":
        return ApiAdapter()
    raise ValueError(f"unknown source: {source}")
