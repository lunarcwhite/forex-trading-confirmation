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

CSV_COLUMNS = ("currency", "event_name", "impact", "scheduled_at")
CSV_OPTIONAL = ("source", "external_id", "forecast", "previous")


def calendar_source() -> dict:
    """Configured calendar provenance (env ECONOMIC_CALENDAR_SOURCE).

    No network fetch in this slice: rows reach the DB via manual POST or
    CSV import (priority 1–2). ICS/API values are recognized as configured
    but unfetched — reported honestly, never synthesized into rows.
    """
    raw = (os.getenv("ECONOMIC_CALENDAR_SOURCE", "") or "").strip()
    if not raw:
        return {"configured_source": "manual", "mode": "manual",
                "fetched": False,
                "note": "manual input only (set ECONOMIC_CALENDAR_SOURCE for provenance)"}
    low = raw.lower()
    if low.startswith("ics:") or low.startswith("api:"):
        return {"configured_source": raw, "mode": low.split(":")[0],
                "fetched": False,
                "note": "remote fetch not implemented; use CSV import"}
    return {"configured_source": raw, "mode": raw.lower(),
            "fetched": False, "note": "file/manual provenance"}


def source_status() -> dict:
    """Configured source + distinct row sources present in the DB."""
    from app.db import connect

    status = calendar_source()
    try:
        with connect() as conn:
            rows = conn.execute(
                "select distinct source from economic_events"
            ).fetchall()
        status["row_sources"] = sorted(r[0] for r in rows)
    except Exception:
        status["row_sources"] = []
        status["note"] = "calendar unreachable"
    return status


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


def _clean_row(raw: dict, line: int) -> dict:
    """Validate one CSV/JSON row. Raises ValueError with line context."""
    currency = str(raw.get("currency", "") or "").strip().upper()
    impact = str(raw.get("impact", "") or "").strip().lower()
    name = str(raw.get("event_name", "") or "").strip()
    sched_raw = str(raw.get("scheduled_at", "") or "").strip()
    if len(currency) != 3 or not currency.isalpha():
        raise ValueError(f"line {line}: currency must be 3 letters")
    if impact not in IMPACTS:
        raise ValueError(f"line {line}: impact must be one of {IMPACTS}")
    if not name:
        raise ValueError(f"line {line}: event_name required")
    try:
        sched = datetime.fromisoformat(sched_raw)
        if sched.tzinfo is None:
            sched = sched.replace(tzinfo=timezone.utc)
    except (ValueError, TypeError):
        raise ValueError(f"line {line}: scheduled_at must be ISO-8601")
    return {"currency": currency, "event_name": name, "impact": impact,
            "scheduled_at": sched,
            "source": str(raw.get("source") or "csv").strip() or "csv",
            "external_id": str(raw.get("external_id") or "").strip() or None,
            "forecast": raw.get("forecast"), "previous": raw.get("previous")}


def parse_csv(text: str) -> tuple[list[dict], list[str]]:
    """Parse CSV text into raw row dicts. Returns (rows, errors).

    Header must be currency,event_name,impact,scheduled_at plus optional
    source,external_id,forecast,previous (order-insensitive, extras rejected).
    """
    import csv
    import io

    rows: list[dict] = []
    errors: list[str] = []
    try:
        reader = csv.DictReader(io.StringIO(text or ""))
    except Exception as e:
        return [], [f"csv unreadable: {e}"]
    if reader.fieldnames is None:
        return [], ["csv empty: header required"]
    fields = [f.strip() for f in reader.fieldnames]
    allowed = set(CSV_COLUMNS + CSV_OPTIONAL)
    if not set(CSV_COLUMNS) <= set(fields):
        return [], [f"csv header must include {', '.join(CSV_COLUMNS)}"]
    unknown = [f for f in fields if f not in allowed]
    if unknown:
        return [], [f"csv unknown columns: {', '.join(unknown)}"]
    for i, rec in enumerate(reader, start=2):
        if all((v or "").strip() == "" for v in rec.values()):
            continue  # skip blank lines honestly
        rows.append({**{k: rec.get(k) for k in fields}, "_line": i})
    return rows, errors


def import_rows(raw_rows: list[dict], default_source: str = "csv") -> dict:
    """Bulk-insert validated rows with (source, external_id) dedupe.

    Returns {inserted, skipped, errors}. Per-row failures never abort the
    batch; dedupe hits are skipped (reported, not silently dropped).
    """
    from app.db import connect

    inserted, skipped = 0, []
    errors: list[str] = []
    with connect() as conn:
        with conn.cursor() as cur:
            for rec in raw_rows:
                line = rec.pop("_line", "?")
                try:
                    if not rec.get("source"):
                        rec["source"] = default_source
                    clean = _clean_row(rec, line)
                except ValueError as e:
                    errors.append(str(e))
                    continue
                if clean["external_id"]:
                    dup = cur.execute(
                        "select id from economic_events"
                        " where source=%s and external_id=%s",
                        (clean["source"], clean["external_id"]),
                    ).fetchone()
                    if dup:
                        skipped.append(str(dup[0]))
                        continue
                row = cur.execute(
                    "insert into economic_events (currency, event_name, impact,"
                    " scheduled_at, source, external_id, forecast_value,"
                    " previous_value) values (%s,%s,%s,%s,%s,%s,%s,%s)"
                    " returning id",
                    (clean["currency"], clean["event_name"], clean["impact"],
                     clean["scheduled_at"], clean["source"],
                     clean["external_id"],
                     str(clean["forecast"]) if clean["forecast"] not in (None, "") else None,
                     str(clean["previous"]) if clean["previous"] not in (None, "") else None),
                ).fetchone()
                inserted += 1
                _ = row
        conn.commit()
    return {"inserted": inserted, "skipped": len(skipped), "errors": errors}
