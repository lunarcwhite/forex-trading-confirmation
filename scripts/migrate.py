"""Run SQL migrations in order. Usage: DATABASE_URL=... python scripts/migrate.py

Idempotent: applied files are recorded in schema_migrations and skipped.
If the DB was migrated before tracking existed (legacy), already-applied
files are baselined instead of re-applied.
"""

import glob
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from app.db import connect  # noqa: E402

ROOT = os.path.join(os.path.dirname(__file__), "..", "migrations")

# Files whose effects are detectable without the tracking table:
# (filename, probe query returning truthy when already applied).
BASELINE_PROBES = {
    "001_phase1_mvp.sql": "select 1 from pg_tables where tablename='users'",
}


def main() -> None:
    files = sorted(glob.glob(os.path.join(ROOT, "*.sql")))
    if not files:
        print("no migrations found")
        return
    with connect() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "create table if not exists schema_migrations"
                " (filename text primary key, applied_at timestamptz default now())"
            )
            applied = {r[0] for r in cur.execute("select filename from schema_migrations")}
            for f in files:
                name = os.path.basename(f)
                if name in applied:
                    print(f"skip {name} (already applied)")
                    continue
                probe = BASELINE_PROBES.get(name)
                if probe and cur.execute(probe).fetchone():
                    print(f"baseline {name} (tables exist, recording without re-apply)")
                    cur.execute(
                        "insert into schema_migrations (filename) values (%s) on conflict do nothing",
                        (name,),
                    )
                    continue
                print(f"applying {name}...")
                cur.execute(open(f, encoding="utf-8").read())
                cur.execute(
                    "insert into schema_migrations (filename) values (%s) on conflict do nothing",
                    (name,),
                )
        conn.commit()
    print(f"done: {len(files)} file(s)")


if __name__ == "__main__":
    main()
