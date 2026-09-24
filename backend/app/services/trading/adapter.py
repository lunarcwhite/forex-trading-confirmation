"""Broker boundary V4 (isolation only — no live orders in this slice).

ARCHITECTURE.md 26-27: live execution, if ever introduced, sits behind
explicit authorization and a broker adapter. Analytical agents (ai,
decision, analysis) must never import this package — enforced by
tests/test_broker_isolation.py via AST scan.
"""

from __future__ import annotations

import abc
import os


class BrokerAdapter(abc.ABC):
    """Minimal execution interface. Paper + future live brokers conform."""

    env: str = "UNKNOWN"

    @abc.abstractmethod
    def place_order(self, *args, **kwargs):
        raise NotImplementedError

    @abc.abstractmethod
    def cancel_order(self, *args, **kwargs):
        raise NotImplementedError

    @abc.abstractmethod
    def get_positions(self, *args, **kwargs):
        raise NotImplementedError

    @abc.abstractmethod
    def get_account(self, *args, **kwargs):
        raise NotImplementedError


class ExecutionDenied(RuntimeError):
    """Raised when live execution is attempted without explicit auth."""


def require_execution_auth(purpose: str, token: str | None) -> None:
    """Gate for any future live path. Denies unless ALL hold:

    - BROKER_LIVE_ENABLED=1 (default off)
    - EXECUTION_AUTH_TOKEN set and matched exactly
    - non-empty purpose string (audit trail)
    """
    if os.getenv("BROKER_LIVE_ENABLED", "") != "1":
        raise ExecutionDenied("live execution disabled (BROKER_LIVE_ENABLED!=1)")
    expected = os.getenv("EXECUTION_AUTH_TOKEN", "")
    if not expected or token != expected:
        raise ExecutionDenied("invalid execution auth token")
    if not (purpose or "").strip():
        raise ExecutionDenied("purpose required for audit")


class PaperBrokerAdapter(BrokerAdapter):
    """Adapter wrapper around the file-store PaperBroker (SIMULATION only)."""

    env = "SIMULATION"

    def __init__(self, paper):
        self._paper = paper

    def place_order(self, *args, **kwargs):
        return self._paper.place_order(*args, **kwargs)

    def cancel_order(self, position_id: str, account_id: str) -> dict:
        positions = self._paper.state.get("positions", {})
        pos = positions.get(position_id)
        if not pos or pos["account_id"] != account_id or pos["status"] != "open":
            raise KeyError("unknown position")
        pos["status"] = "cancelled"
        self._paper._save()
        return {"id": position_id, "status": "cancelled", "env": "SIMULATION"}

    def get_positions(self, account_id: str, mark=None):
        return self._paper.positions(account_id, mark)

    def get_account(self, account_id: str) -> dict:
        try:
            return self._paper.state["accounts"][account_id]
        except KeyError:
            raise KeyError("unknown account")
