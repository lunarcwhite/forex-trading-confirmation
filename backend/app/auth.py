"""Minimal HS256 JWT + PBKDF2 passwords (stdlib only). Secret via SECRET_KEY env."""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import secrets
import time


def _secret() -> str:
    s = os.getenv("SECRET_KEY", "")
    if not s:
        s = "dev-insecure-change-me"
    return s


def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 200_000)
    return f"pbkdf2$200000${salt}${dk.hex()}"


def verify_password(password: str, stored: str) -> bool:
    try:
        _, iters, salt, hexdk = stored.split("$")
        dk = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), int(iters))
        return hmac.compare_digest(dk.hex(), hexdk)
    except (ValueError, AttributeError):
        return False


def _b64(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def create_token(user_id: str, ttl: int = 86400) -> str:
    header = _b64(json.dumps({"alg": "HS256", "typ": "JWT"}).encode())
    payload = _b64(json.dumps({"sub": user_id, "exp": int(time.time()) + ttl}).encode())
    sig = _b64(hmac.new(_secret().encode(), f"{header}.{payload}".encode(), hashlib.sha256).digest())
    return f"{header}.{payload}.{sig}"


def decode_token(token: str) -> str | None:
    """Returns user_id or None."""
    try:
        header, payload, sig = token.split(".")
        expect = _b64(hmac.new(_secret().encode(), f"{header}.{payload}".encode(), hashlib.sha256).digest())
        if not hmac.compare_digest(expect, sig):
            return None
        body = json.loads(base64.urlsafe_b64decode(payload + "=="))
        if body.get("exp", 0) < time.time():
            return None
        return body.get("sub")
    except (ValueError, KeyError):
        return None
