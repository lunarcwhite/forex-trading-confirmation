"""Persist engine decisions to Postgres: setup → confirmations → signal → audit.

Explicit, login-required recording (no write-on-GET spam). Snapshots are
immutable copies of engine output; `signals.decision` never changes after
insert (only status transitions). Refuses to record when data is missing.
"""

from __future__ import annotations

import json

from app.db import connect
from app.services.decision.evaluate import evaluate, trade_plan

STATUS_OF = {"ENTER": "confirmed", "WAIT": "waiting", "NO_TRADE": "invalidated"}
CONF_OF = {"PASS": "pass", "FAIL": "fail", "NOT_READY": "pending",
           "NOT_APPLICABLE": "not_applicable"}

# DATABASE.md 38 — allowed lifecycle transitions (decision immutable).
TRANSITIONS = {
    "generated": ("active", "expired"),
    "active": ("executed", "ignored", "expired", "invalidated"),
    "executed": (),
    "ignored": (),
    "expired": (),
    "invalidated": (),
}


def transition_signal(user_id: str, signal_id: str, new_status: str) -> dict:
    """Move a signal along its lifecycle. Returns the updated row.

    Raises LookupError (unknown / not owned) and ValueError (bad transition).
    """
    if new_status not in TRANSITIONS:
        raise ValueError(f"unknown status: {new_status}")
    with connect() as conn:
        with conn.cursor() as cur:
            row = cur.execute(
                "select status from signals where id=%s and user_id=%s",
                (signal_id, user_id),
            ).fetchone()
            if not row:
                raise LookupError("signal not found")
            current = row[0]
            if new_status not in TRANSITIONS[current]:
                raise ValueError(f"{current} -> {new_status} not allowed")
            cur.execute(
                "update signals set status=%s, status_updated_at=now(),"
                " updated_at=now() where id=%s",
                (new_status, signal_id),
            )
        conn.commit()
    return {"id": signal_id, "from": current, "to": new_status}


def signal_snapshot(user_id: str, signal_id: str) -> dict:
    """Owner-checked immutable snapshots for paper/journal linkage."""
    with connect() as conn:
        row = conn.execute(
            "select decision, direction, confirmation_snapshot, risk_snapshot,"
            " analysis_snapshot, engine_version, generated_at from signals"
            " where id=%s and user_id=%s",
            (signal_id, user_id),
        ).fetchone()
    if not row:
        raise LookupError("signal not found")
    return {"signal_id": signal_id, "decision": row[0], "direction": row[1],
            "confirmation": row[2], "risk": row[3], "analysis": row[4],
            "engine_version": row[5], "generated_at": row[6].isoformat()}


def _ensure_strategy(cur, user_id: str) -> str:
    """Get-or-create the user's Trend Pullback strategy version (idempotent)."""
    from app.services.strategy.service import PRESETS

    preset = PRESETS["trend-pullback"]
    row = cur.execute(
        "select id from strategies where user_id=%s and name=%s",
        (user_id, preset["name"]),
    ).fetchone()
    if row:
        ver = cur.execute(
            "select id from strategy_versions where strategy_id=%s and version_number=1",
            (row[0],),
        ).fetchone()
        if ver:
            return str(ver[0])
        sid = str(row[0])
    else:
        sid = str(
            cur.execute(
                "insert into strategies (user_id, name, description, direction, status)"
                " values (%s,%s,%s,%s,'active') returning id",
                (user_id, preset["name"], "MVP preset", preset["direction"]),
            ).fetchone()[0]
        )
    vid = str(
        cur.execute(
            "insert into strategy_versions (strategy_id, version_number, description,"
            " configuration, status) values (%s,1,%s,%s,'active') returning id",
            (sid, "MVP preset v1",
             json.dumps({"preset": "trend-pullback", "engine": "decision-v1"})),
        ).fetchone()[0]
    )
    for i, r in enumerate(preset["rules"]):
        cur.execute(
            "insert into strategy_rules (strategy_version_id, rule_type, name,"
            " condition, required, weight, sort_order)"
            " values (%s,%s,%s,%s,%s,%s,%s)",
            (vid, r["rule_type"], r["name"], json.dumps(r["condition"]),
             r["required"], r["weight"], i),
        )
    return vid


def record_signal(user_id: str, symbol: str, timeframe: str = "H1") -> dict:
    """Evaluate and store the full evidence chain. Returns ids + state."""
    from app.services.risk.position import PAIR_DEFAULTS

    if symbol not in PAIR_DEFAULTS:
        raise ValueError("unknown symbol")
    ev = evaluate(symbol, timeframe)
    if ev["data_quality"] != "ok":
        raise ValueError("DATA UNAVAILABLE: refusing to record without data")
    plan, entry_zone = trade_plan(ev)
    direction = "buy" if ev["direction"] == "BUY" else "sell"
    decision = ev["state"].lower()
    passed = len(ev["confirmations"])
    total = passed + len(ev["missing_conditions"])

    with connect() as conn:
        with conn.cursor() as cur:
            pair = cur.execute(
                "select id from currency_pairs where symbol=%s", (symbol,)
            ).fetchone()
            if not pair:
                raise ValueError("unknown symbol")
            version_id = _ensure_strategy(cur, user_id)
            analysis_id = cur.execute(
                "insert into market_analyses (currency_pair_id, timeframe,"
                " candle_timestamp, bias, trend_state, momentum_state,"
                " data_quality, engine_version)"
                " values (%s,%s,%s,%s,%s,%s,%s,%s) returning id",
                (str(pair[0]), timeframe, ev["candle_timestamp"], ev["bias"],
                 "confirmed" if "trend" in ev["confirmations"] else "unconfirmed",
                 "confirmed" if "momentum" in ev["confirmations"] else "unconfirmed",
                 ev["data_quality"], ev["engine_version"]),
            ).fetchone()[0]
            setup_id = cur.execute(
                "insert into setups (user_id, currency_pair_id, strategy_version_id,"
                " market_analysis_id, direction, status, entry_min, entry_max,"
                " stop_loss, take_profit, risk_reward, quality,"
                " invalidation_reason) values"
                " (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) returning id",
                (user_id, str(pair[0]), version_id, str(analysis_id), direction,
                 STATUS_OF[ev["state"]], entry_zone.get("min"), entry_zone.get("max"),
                 plan.get("stop_loss"), plan.get("take_profit"),
                 plan.get("risk_reward"), f"{passed}/{total}",
                 json.dumps({"missing": ev["missing_conditions"],
                             "invalidations": ev["invalidations"]})
                 if ev["state"] == "NO_TRADE" else None),
            ).fetchone()[0]
            for r in ev["results"]:
                cur.execute(
                    "insert into setup_confirmations (setup_id, confirmation_type,"
                    " status, evidence, missing_reason)"
                    " values (%s,%s,%s,%s,%s)",
                    (str(setup_id), r["type"], CONF_OF[r["result"]],
                     json.dumps(ev["price_action"])
                     if r["type"] == "price_action" else "{}",
                     None if r["result"] == "PASS"
                     else f"{r['type']} {r['result']}"),
                )
            analysis_snap = {"bias": ev["bias"], "indicators": ev["indicators"],
                             "structure": ev["structure"], "mtf": ev["mtf"],
                             "data_quality": ev["data_quality"],
                             "source": ev["source"]}
            confirmation_snap = {"confirmations": ev["confirmations"],
                                 "missing": ev["missing_conditions"],
                                 "results": ev["results"]}
            risk_snap = {"plan": plan, "entry_zone": entry_zone}
            signal_id = cur.execute(
                "insert into signals (setup_id, user_id, decision, direction,"
                " strategy_version_id, decision_reason, confirmation_snapshot,"
                " risk_snapshot, analysis_snapshot, engine_version)"
                " values (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) returning id",
                (str(setup_id), user_id, decision, direction, version_id,
                 json.dumps({"strategy": "Trend Pullback",
                             "score": f"{passed}/{total}"}),
                 json.dumps(confirmation_snap), json.dumps(risk_snap),
                 json.dumps(analysis_snap), ev["engine_version"]),
            ).fetchone()[0]
            cur.execute(
                "insert into decision_audit_logs (signal_id, engine_version,"
                " input_snapshot, decision, reasoning_snapshot)"
                " values (%s,%s,%s,%s,%s)",
                (str(signal_id), ev["engine_version"],
                 json.dumps({"symbol": symbol, "timeframe": timeframe,
                             "indicators": ev["indicators"],
                             "price_action": ev["price_action"],
                             "mtf": ev["mtf"]}),
                 decision, json.dumps({"state": ev["state"],
                                       "confirmations": ev["confirmations"],
                                       "missing": ev["missing_conditions"]})),
            )
        conn.commit()
    return {"signal_id": str(signal_id), "setup_id": str(setup_id),
            "state": ev["state"], "score": f"{passed}/{total}"}


def list_signals(user_id: str, symbol: str = "", limit: int = 20) -> list[dict]:
    """Recent signals with pair symbol (newest first)."""
    q = ("select s.id, cp.symbol, s.decision, s.direction, s.generated_at,"
         " s.confirmation_snapshot, s.status from signals s"
         " join setups st on st.id = s.setup_id"
         " join currency_pairs cp on cp.id = st.currency_pair_id"
         " where s.user_id=%s")
    args: list = [user_id]
    if symbol:
        q += " and cp.symbol=%s"
        args.append(symbol)
    q += " order by s.generated_at desc limit %s"
    args.append(limit)
    with connect() as conn:
        rows = conn.execute(q, args).fetchall()
    return [{"id": str(r[0]), "symbol": r[1], "decision": r[2],
             "direction": r[3], "generated_at": r[4].isoformat(),
             "confirmations": r[5].get("confirmations", []),
             "status": r[6]} for r in rows]
