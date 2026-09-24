"""Postgres connection helper. DSN only via DATABASE_URL env (never committed)."""

from __future__ import annotations

import os

import psycopg


def dsn() -> str:
    url = os.getenv("DATABASE_URL", "")
    if not url:
        raise RuntimeError("DATABASE_URL not set")
    return url


def connect():
    return psycopg.connect(dsn())
