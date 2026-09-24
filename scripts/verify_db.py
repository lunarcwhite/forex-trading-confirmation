"""Verify migration: table count + seed. Reads DATABASE_URL env."""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from app.db import connect

with connect() as c:
    rows = c.execute(
        "select tablename from pg_tables where schemaname='public' order by 1"
    ).fetchall()
    print(len(rows), "tables")
    print(sorted(r[0] for r in rows))
    print(c.execute("select symbol from currency_pairs order by 1").fetchall())
