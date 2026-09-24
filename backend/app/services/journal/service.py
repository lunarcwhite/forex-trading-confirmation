"""Journal entries on Postgres (V2). Spec: PRD.md 16, DATABASE.md 26.

PG-first with file-store fallback in the API layer (no DB → legacy).
Snapshots are server-resolved, never client-supplied: an owned signal_id
embeds the immutable PG signal snapshot; a paper trade_ref carries its
paper signal_snapshot (upgraded to the PG snapshot when it points at an
owned signal). Missing links stay {} — never fabricated.
"""

from __future__ import annotations

TEXT_FIELDS = ("thesis", "market_context", "entry_reason", "exit_reason",
               "lesson", "notes")
MAX_TEXT = 2000
MAX_EMOTION = 50


def validate(data: dict) -> dict:
    """Clean text fields. Raises ValueError when nothing to store or over bounds."""
    out: dict = {}
    for k in TEXT_FIELDS:
        v = data.get(k, "")
        v = "" if v is None else str(v)
        if len(v) > MAX_TEXT:
            raise ValueError(f"{k} max {MAX_TEXT} chars")
        out[k] = v
    emotion = data.get("emotion", "")
    emotion = "" if emotion is None else str(emotion)
    if len(emotion) > MAX_EMOTION:
        raise ValueError(f"emotion max {MAX_EMOTION} chars")
    out["emotion"] = emotion
    signal_id = data.get("signal_id") or ""
    signal_id = str(signal_id).strip()
    out["signal_id"] = signal_id or None
    trade_ref = data.get("trade_id", data.get("trade_ref", ""))
    trade_ref = "" if trade_ref is None else str(trade_ref).strip()
    out["trade_ref"] = trade_ref or None
    if (not out["signal_id"] and not out["trade_ref"]
            and not any(out[k] for k in (*TEXT_FIELDS, "emotion"))):
        raise ValueError("thesis, notes, signal_id, or trade_id required")
    return out


def _row_to_dict(r) -> dict:
    keys = ["id", "user_id", "signal_id", "trade_ref", "thesis",
            "market_context", "entry_reason", "exit_reason", "emotion",
            "lesson", "notes", "decision_snapshot", "created_at", "updated_at"]
    d = dict(zip(keys, r))
    d["id"] = str(d["id"])
    d["user_id"] = str(d["user_id"])
    d["signal_id"] = str(d["signal_id"]) if d["signal_id"] else None
    # Legacy file-store shape uses trade_id; keep both keys.
    d["trade_id"] = d["trade_ref"]
    for k in ("created_at", "updated_at"):
        if d[k] is not None:
            d[k] = d[k].isoformat()
    return d


def create_entry(user_id: str, data: dict,
                 paper_snapshot: dict | None = None) -> dict:
    """Insert a PG journal row. Owner-checked signal link.

    paper_snapshot: optional paper-trade signal_snapshot (dict) when the
    entry references a file-store trade. Upgraded to the PG snapshot when
    it points at a signal owned by user_id.
    Raises LookupError (foreign signal) and ValueError (validation).
    """
    from app.db import connect
    from app.services.decision.persist import signal_snapshot

    clean = validate(data)
    signal_id = clean["signal_id"]
    snapshot: dict = {}
    if signal_id:
        try:
            snapshot = signal_snapshot(user_id, signal_id)
        except LookupError:
            raise LookupError("signal not found")
    elif paper_snapshot:
        ref_sid = (paper_snapshot or {}).get("signal_id")
        if ref_sid:
            try:
                snapshot = signal_snapshot(user_id, str(ref_sid))
                signal_id = str(ref_sid)
            except LookupError:
                snapshot = dict(paper_snapshot)
        else:
            snapshot = dict(paper_snapshot)
    with connect() as conn:
        with conn.cursor() as cur:
            import json

            row = cur.execute(
                "insert into journal_entries (user_id, signal_id, trade_ref,"
                " thesis, market_context, entry_reason, exit_reason, emotion,"
                " lesson, notes, decision_snapshot)"
                " values (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"
                " returning id, user_id, signal_id, trade_ref, thesis,"
                " market_context, entry_reason, exit_reason, emotion, lesson,"
                " notes, decision_snapshot, created_at, updated_at",
                (user_id, signal_id, clean["trade_ref"], clean["thesis"],
                 clean["market_context"], clean["entry_reason"],
                 clean["exit_reason"], clean["emotion"], clean["lesson"],
                 clean["notes"], json.dumps(snapshot)),
            ).fetchone()
        conn.commit()
    return _row_to_dict(row)


def list_entries(user_id: str, limit: int = 50) -> list[dict]:
    """Newest-first PG rows for one user."""
    from app.db import connect

    with connect() as conn:
        rows = conn.execute(
            "select id, user_id, signal_id, trade_ref, thesis, market_context,"
            " entry_reason, exit_reason, emotion, lesson, notes,"
            " decision_snapshot, created_at, updated_at from journal_entries"
            " where user_id=%s order by created_at desc limit %s",
            (user_id, limit),
        ).fetchall()
    return [_row_to_dict(r) for r in rows]
