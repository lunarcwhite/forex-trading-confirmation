"""Rule engine. Spec: ARCHITECTURE.md sections 14-15."""

from __future__ import annotations

HARD_TYPES = {"risk", "spread", "news"}


def evaluate_condition(
    field_value, operator: str, value=None, ref=None
) -> str:
    if field_value is None:
        return "NOT_READY"
    v = ref if ref is not None else value
    try:
        if operator == "equal":
            return "PASS" if field_value == v else "FAIL"
        if operator == "not_equal":
            return "PASS" if field_value != v else "FAIL"
        if operator == "greater_than":
            return "PASS" if field_value > v else "FAIL"
        if operator == "greater_than_or_equal":
            return "PASS" if field_value >= v else "FAIL"
        if operator == "less_than":
            return "PASS" if field_value < v else "FAIL"
        if operator == "less_than_or_equal":
            return "PASS" if field_value <= v else "FAIL"
        if operator == "in":
            return "PASS" if field_value in v else "FAIL"
        if operator == "not_in":
            return "PASS" if field_value not in v else "FAIL"
        if operator == "between":
            return "PASS" if v[0] <= field_value <= v[1] else "FAIL"
    except TypeError:
        return "FAIL"
    return "NOT_APPLICABLE"


def aggregate(
    results: list[tuple[str, str, bool]],
    direction: str = "buy",
    structure_bias: str = "neutral",
    structure_strong: bool = False,
) -> str:
    """results: (rule_type, result, required)."""
    for t, r, _ in results:
        if t in HARD_TYPES and r == "FAIL":
            return "NO_TRADE"
    if structure_strong and (
        (direction == "buy" and structure_bias == "bearish")
        or (direction == "sell" and structure_bias == "bullish")
    ):
        return "NO_TRADE"
    if any(r in ("FAIL", "NOT_READY") and req for _, r, req in results):
        return "WAIT"
    return "ENTER"
