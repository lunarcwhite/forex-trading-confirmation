"""Risk profiles store (Postgres). Spec: PRD.md 25, DATABASE.md 7.

Every user gets one idempotent 'Default' profile on first signal record.
Validation is deterministic: out-of-range values raise ValueError, never
silently clamped. Missing measurements stay SKIP in `check_limits` —
profiles only supply the *limits*, never fabricated measurements.
"""

from __future__ import annotations

DEFAULTS = {
    "name": "Default",
    "risk_per_trade_pct": 1.0,
    "max_daily_loss_pct": 5.0,
    "max_open_positions": 3,
    "max_exposure_pct": 20.0,
    "min_risk_reward": 2.0,
    "max_spread": 0.0005,
    "max_position_size": 5.0,
}

COLS = ("id", "user_id", "name", "risk_per_trade_pct", "max_daily_loss_pct",
        "max_open_positions", "max_exposure_pct", "min_risk_reward",
        "max_spread", "max_position_size", "created_at", "updated_at")


def validate(data: dict, partial: bool = False) -> dict:
    """Clean + range-check profile fields. Raises ValueError on violation."""
    out: dict = {}
    def need(key: str, default):
        if key in data and data[key] is not None:
            return data[key]
        if partial:
            return None
        return data.get(key, default)

    def num(key: str, lo: float, hi: float, default, integer: bool = False):
        v = need(key, default)
        if v is None:  # partial update skips this field
            return None
        try:
            f = float(v)
        except (TypeError, ValueError):
            raise ValueError(f"{key} must be a number")
        if integer:
            if int(f) != f:
                raise ValueError(f"{key} must be an integer")
            f = int(f)
        if not (lo <= f <= hi) if integer is False else not (lo <= f <= hi):
            raise ValueError(f"{key} out of range [{lo}, {hi}]")
        # strict >0 where lo==0 would allow 0; enforce documented bounds:
        return f

    name = data.get("name", DEFAULTS["name"] if not partial else None)
    if name is not None:
        name = str(name).strip()
        if not name or len(name) > 100:
            raise ValueError("name must be 1..100 chars")
        out["name"] = name
    elif not partial:
        out["name"] = DEFAULTS["name"]

    for key, lo, hi, dflt, integer in [
        ("risk_per_trade_pct", 0, 10, DEFAULTS["risk_per_trade_pct"], False),
        ("max_daily_loss_pct", 0, 100, DEFAULTS["max_daily_loss_pct"], False),
        ("max_open_positions", 1, 20, DEFAULTS["max_open_positions"], True),
        ("max_exposure_pct", 0, 100, DEFAULTS["max_exposure_pct"], False),
        ("min_risk_reward", 0.5, 10, DEFAULTS["min_risk_reward"], False),
        ("max_spread", 0, 1000, DEFAULTS["max_spread"], False),
        ("max_position_size", 0, 1000, DEFAULTS["max_position_size"], False),
    ]:
        v = num(key, lo, hi, data.get(key, dflt), integer)
        if v is None and partial:
            continue
        if v is not None and lo == 0 and v <= 0 and key not in ("max_spread",):
            raise ValueError(f"{key} must be > 0")
        if v is not None:
            out[key] = v
    return out


def _row_to_dict(r) -> dict:
    keys = ["id", "user_id", "name", "risk_per_trade_pct",
            "max_daily_loss_pct", "max_open_positions", "max_exposure_pct",
            "min_risk_reward", "max_spread", "max_position_size",
            "created_at", "updated_at"]
    d = dict(zip(keys, r))
    d["id"] = str(d["id"])
    d["user_id"] = str(d["user_id"])
    for k in ("risk_per_trade_pct", "max_daily_loss_pct", "max_exposure_pct",
              "min_risk_reward", "max_spread", "max_position_size"):
        d[k] = float(d[k]) if d[k] is not None else None
    d["max_open_positions"] = int(d["max_open_positions"])
    for k in ("created_at", "updated_at"):
        if d[k] is not None:
            d[k] = d[k].isoformat()
    return d


def ensure_default(cur, user_id: str) -> dict:
    """Get-or-create the user's Default profile (idempotent, in-txn)."""
    row = cur.execute(
        "select id, user_id, name, risk_per_trade_pct, max_daily_loss_pct,"
        " max_open_positions, max_exposure_pct, min_risk_reward, max_spread,"
        " max_position_size, created_at, updated_at from risk_profiles"
        " where user_id=%s and name=%s",
        (user_id, DEFAULTS["name"]),
    ).fetchone()
    if row:
        return _row_to_dict(row)
    clean = validate({})
    row = cur.execute(
        "insert into risk_profiles (user_id, name, risk_per_trade_pct,"
        " max_daily_loss_pct, max_open_positions, max_exposure_pct,"
        " min_risk_reward, max_spread, max_position_size)"
        " values (%s,%s,%s,%s,%s,%s,%s,%s,%s) returning id, user_id, name,"
        " risk_per_trade_pct, max_daily_loss_pct, max_open_positions,"
        " max_exposure_pct, min_risk_reward, max_spread, max_position_size,"
        " created_at, updated_at",
        (user_id, clean["name"], clean["risk_per_trade_pct"],
         clean["max_daily_loss_pct"], clean["max_open_positions"],
         clean["max_exposure_pct"], clean["min_risk_reward"],
         clean["max_spread"], clean["max_position_size"]),
    ).fetchone()
    return _row_to_dict(row)


def list_profiles(user_id: str) -> list[dict]:
    from app.db import connect

    with connect() as conn:
        rows = conn.execute(
            "select id, user_id, name, risk_per_trade_pct, max_daily_loss_pct,"
            " max_open_positions, max_exposure_pct, min_risk_reward, max_spread,"
            " max_position_size, created_at, updated_at from risk_profiles"
            " where user_id=%s order by created_at",
            (user_id,),
        ).fetchall()
    return [_row_to_dict(r) for r in rows]


def get_profile(user_id: str, profile_id: str) -> dict:
    from app.db import connect

    with connect() as conn:
        row = conn.execute(
            "select id, user_id, name, risk_per_trade_pct, max_daily_loss_pct,"
            " max_open_positions, max_exposure_pct, min_risk_reward, max_spread,"
            " max_position_size, created_at, updated_at from risk_profiles"
            " where id=%s and user_id=%s",
            (profile_id, user_id),
        ).fetchone()
    if not row:
        raise LookupError("risk profile not found")
    return _row_to_dict(row)


def create_profile(user_id: str, data: dict) -> dict:
    from app.db import connect

    clean = validate(data)
    with connect() as conn:
        with conn.cursor() as cur:
            dup = cur.execute(
                "select id from risk_profiles where user_id=%s and name=%s",
                (user_id, clean["name"]),
            ).fetchone()
            if dup:
                raise ValueError(f"profile '{clean['name']}' already exists")
            row = cur.execute(
                "insert into risk_profiles (user_id, name, risk_per_trade_pct,"
                " max_daily_loss_pct, max_open_positions, max_exposure_pct,"
                " min_risk_reward, max_spread, max_position_size)"
                " values (%s,%s,%s,%s,%s,%s,%s,%s,%s) returning id, user_id, name,"
                " risk_per_trade_pct, max_daily_loss_pct, max_open_positions,"
                " max_exposure_pct, min_risk_reward, max_spread, max_position_size,"
                " created_at, updated_at",
                (user_id, clean["name"], clean["risk_per_trade_pct"],
                 clean["max_daily_loss_pct"], clean["max_open_positions"],
                 clean["max_exposure_pct"], clean["min_risk_reward"],
                 clean["max_spread"], clean["max_position_size"]),
            ).fetchone()
        conn.commit()
    return _row_to_dict(row)


def update_profile(user_id: str, profile_id: str, data: dict) -> dict:
    from app.db import connect

    clean = validate(data, partial=True)
    if not clean:
        raise ValueError("nothing to update")
    with connect() as conn:
        with conn.cursor() as cur:
            row = cur.execute(
                "select id from risk_profiles where id=%s and user_id=%s",
                (profile_id, user_id),
            ).fetchone()
            if not row:
                raise LookupError("risk profile not found")
            if "name" in clean:
                dup = cur.execute(
                    "select id from risk_profiles where user_id=%s and name=%s"
                    " and id<>%s",
                    (user_id, clean["name"], profile_id),
                ).fetchone()
                if dup:
                    raise ValueError(f"profile '{clean['name']}' already exists")
            # Build update dynamically but deterministically (sorted keys).
            keys = sorted(clean.keys())
            cur.execute(
                f"update risk_profiles set {', '.join(f'{k}=%s' for k in keys)},"
                " updated_at=now() where id=%s",
                ([clean[k] for k in keys] + [profile_id]),
            )
            out = cur.execute(
                "select id, user_id, name, risk_per_trade_pct, max_daily_loss_pct,"
                " max_open_positions, max_exposure_pct, min_risk_reward, max_spread,"
                " max_position_size, created_at, updated_at from risk_profiles"
                " where id=%s",
                (profile_id,),
            ).fetchone()
        conn.commit()
    return _row_to_dict(out)
