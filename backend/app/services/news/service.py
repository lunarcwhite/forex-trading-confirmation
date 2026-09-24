"""News/event risk service (V2). Manual input path; licensed calendar API later.

Blackout rule (CALCULATIONS.md 18): a HIGH impact event for either pair
currency scheduled within [now-15min, now+60min] → ELEVATED (blocks entry).
Without DATABASE_URL or without rows the filter reports OFF — it never
assumes safe.
"""

from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone

IMPACTS = ("high", "medium", "low")
WINDOW_BEFORE_MIN = 60
WINDOW_AFTER_MIN = 15


def _now() -> datetime:
    return datetime.now(timezone.utc)


def create_event(currency: str, event_name: str, impact: str,
                 scheduled_at: str, source: str = "manual",
                 forecast: str | None = None,
                 previous: str | None = None) -> dict:
    from app.db import connect

    currency = (currency or "").upper()
    impact = (impact or "").lower()
    if len(currency) != 3:
        raise ValueError("currency must be 3 letters")
    if impact not in IMPACTS:
        raise ValueError(f"impact must be one of {IMPACTS}")
    if not event_name:
        raise ValueError("event_name required")
    try:
        sched = datetime.fromisoformat(scheduled_at)
        if sched.tzinfo is None:
            sched = sched.replace(tzinfo=timezone.utc)
    except (ValueError, TypeError):
        raise ValueError("scheduled_at must be ISO-8601")
    with connect() as conn:
        row = conn.execute(
            "insert into economic_events (currency, event_name, impact,"
            " scheduled_at, source, forecast_value, previous_value)"
            " values (%s,%s,%s,%s,%s,%s,%s) returning id",
            (currency, event_name, impact, sched, source, forecast, previous),
        ).fetchone()
        conn.commit()
    return {"id": str(row[0]), "currency": currency, "event_name": event_name,
            "impact": impact, "scheduled_at": sched.isoformat()}


def list_events(currency: str = "", hours: int = 72) -> list[dict]:
    from app.db import connect

    with connect() as conn:
        if currency:
            rows = conn.execute(
                "select id, currency, event_name, impact, scheduled_at, source"
                " from economic_events where currency=%s"
                " and scheduled_at between now() - interval '1 day'"
                " and now() + (%s || ' hours')::interval"
                " order by scheduled_at",
                (currency.upper(), str(hours)),
            ).fetchall()
        else:
            rows = conn.execute(
                "select id, currency, event_name, impact, scheduled_at, source"
                " from economic_events"
                " where scheduled_at between now() - interval '1 day'"
                " and now() + (%s || ' hours')::interval"
                " order by scheduled_at",
                (str(hours),),
            ).fetchall()
    return [{"id": str(r[0]), "currency": r[1], "event_name": r[2],
             "impact": r[3], "scheduled_at": r[4].isoformat(),
             "source": r[5]} for r in rows]


def news_risk(symbol: str, at: datetime | None = None) -> dict:
    """Evaluate event risk for a symbol. DB-free callers get OFF, never safe."""
    if not os.getenv("DATABASE_URL"):
        return {"state": "OFF", "events": [], "reason": "no calendar source"}
    try:
        base, quote = symbol.split("/")
    except ValueError:
        return {"state": "OFF", "events": [], "reason": "unknown symbol"}
    at = at or _now()
    start = at - timedelta(minutes=WINDOW_AFTER_MIN)
    end = at + timedelta(minutes=WINDOW_BEFORE_MIN)
    from app.db import connect

    try:
        with connect() as conn:
            rows = conn.execute(
                "select event_name, impact, scheduled_at, currency"
                " from economic_events"
                " where currency in (%s,%s) and scheduled_at between %s and %s"
                " order by scheduled_at",
                (base.upper(), quote.upper(), start, end),
            ).fetchall()
    except Exception:
        return {"state": "OFF", "events": [], "reason": "calendar unreachable"}
    events = [{"event_name": r[0], "impact": r[1],
               "scheduled_at": r[2].isoformat(), "currency": r[3]}
              for r in rows]
    hot = [e for e in events if e["impact"] == "high"]
    if hot:
        return {"state": "ELEVATED", "events": events,
                "reason": f"{len(hot)} high-impact event(s) in blackout window"}
    return {"state": "CLEAR", "events": events,
            "reason": "no high-impact events in window" if not events
            else "only medium/low impact in window"}
