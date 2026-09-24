"""Run SQL migrations in order. Usage: DATABASE_URL=... python scripts/migrate.py"""

import glob
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from app.db import connect  # noqa: E402

ROOT = os.path.join(os.path.dirname(__file__), "..", "migrations")


def main() -> None:
    files = sorted(glob.glob(os.path.join(ROOT, "*.sql")))
    if not files:
        print("no migrations found")
        return
    with connect() as conn:
        with conn.cursor() as cur:
            for f in files:
                print(f"applying {os.path.basename(f)}...")
                cur.execute(open(f, encoding="utf-8").read())
        conn.commit()
    print(f"done: {len(files)} file(s)")


if __name__ == "__main__":
    main()
