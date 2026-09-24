"""Auto-load repo-root .env (if present) for local runs. No secrets here."""

from __future__ import annotations

import os

try:
    from dotenv import find_dotenv, load_dotenv

    load_dotenv(find_dotenv(usecwd=True) or os.path.join(os.getcwd(), ".env"))
except ImportError:
    pass
