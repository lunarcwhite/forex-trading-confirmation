"""Risk hard filters. Spec: PRD.md 25, ARCHITECTURE.md 16, CALCULATIONS.md 10.1.

Every limit is optional: a rule without both measurement and configured
maximum is SKIPped (reported, never silently passed as safe). Any FAIL
rule → overall status fail. Mirrors `risk_checks.failures` shape.
"""

from __future__ import annotations

SKIP = "SKIP"


def check_limits(
    *,
    risk_reward: float | None = None,
    min_rr: float = 2.0,
    spread: float | None = None,
    max_spread: float | None = None,
    lots: float | None = None,
    max_lots: float | None = None,
    exposure_pct: float | None = None,
    max_exposure_pct: float | None = None,
    open_positions: int | None = None,
    max_open_positions: int | None = None,
    daily_loss_pct: float | None = None,
    max_daily_loss_pct: float | None = None,
) -> dict:
    rules: list[dict] = []

    def add(name: str, result: str, detail: str = "") -> None:
        rules.append({"rule": name, "result": result, "detail": detail})

    if risk_reward is None or risk_reward + 1e-9 < min_rr:
        add("min_rr", "FAIL", f"R:R {risk_reward} < 1:{min_rr}")
    else:
        add("min_rr", "PASS", f"R:R 1:{risk_reward:.2f}")
    if spread is None or max_spread is None:
        add("max_spread", SKIP, "no spread feed (MVP)")
    elif spread > max_spread:
        add("max_spread", "FAIL", f"spread {spread} > {max_spread}")
    else:
        add("max_spread", "PASS", f"spread {spread}")
    if lots is not None and max_lots is not None and lots > max_lots:
        add("max_position_size", "FAIL", f"{lots} lot > max {max_lots}")
    else:
        add("max_position_size", SKIP if lots is None or max_lots is None else "PASS",
            f"{lots} lot" if lots is not None else "unmeasured")
    if exposure_pct is None or max_exposure_pct is None:
        add("max_exposure", SKIP, "exposure unmeasured")
    elif exposure_pct > max_exposure_pct:
        add("max_exposure", "FAIL", f"{exposure_pct}% > {max_exposure_pct}%")
    else:
        add("max_exposure", "PASS", f"{exposure_pct}%")
    if open_positions is None or max_open_positions is None:
        add("max_open_positions", SKIP, "position count unmeasured")
    elif open_positions >= max_open_positions:
        add("max_open_positions", "FAIL",
            f"{open_positions} >= max {max_open_positions}")
    else:
        add("max_open_positions", "PASS", f"{open_positions} open")
    if daily_loss_pct is None or max_daily_loss_pct is None:
        add("max_daily_loss", SKIP, "daily P/L unmeasured")
    elif daily_loss_pct >= max_daily_loss_pct:
        add("max_daily_loss", "FAIL",
            f"loss {daily_loss_pct}% >= max {max_daily_loss_pct}%")
    else:
        add("max_daily_loss", "PASS", f"loss {daily_loss_pct}%")

    failures = [r["rule"] for r in rules if r["result"] == "FAIL"]
    return {"status": "fail" if failures else "pass",
            "failures": failures, "rules": rules}
