"""Auth tests: hashing/JWT unit + live register/login (isolated user)."""

import os
import sys
import unittest
import uuid

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from app.auth import create_token, decode_token, hash_password, verify_password

HAS_DSN = bool(os.getenv("DATABASE_URL"))


class TestAuthUnit(unittest.TestCase):
    def test_password_roundtrip(self):
        h = hash_password("s3cret!")
        self.assertTrue(verify_password("s3cret!", h))
        self.assertFalse(verify_password("wrong", h))

    def test_token_roundtrip(self):
        t = create_token("u123")
        self.assertEqual(decode_token(t), "u123")
        self.assertIsNone(decode_token(t + "x"))


@unittest.skipUnless(HAS_DSN, "DATABASE_URL not set")
class TestAuthLive(unittest.TestCase):
    def test_register_login(self):
        from fastapi.testclient import TestClient

        from app.main import app

        client = TestClient(app)
        email = f"t_{uuid.uuid4().hex[:8]}@ex.com"
        r = client.post("/api/v1/auth/register",
                        json={"email": email, "password": "pw12345", "name": "T"})
        self.assertEqual(r.status_code, 200, r.text)
        uid = r.json()["user_id"]
        r2 = client.post("/api/v1/auth/login",
                         json={"email": email, "password": "pw12345"})
        self.assertEqual(r2.status_code, 200)
        me = client.get("/api/v1/auth/whoami",
                        params={"token": f"Bearer {r2.json()['token']}"})
        self.assertEqual(me.json()["user_id"], uid)
        # bad password rejected
        bad = client.post("/api/v1/auth/login",
                          json={"email": email, "password": "nope"})
        self.assertEqual(bad.status_code, 401)
        # cleanup
        from app.db import connect

        with connect() as c:
            c.execute("delete from users where email=%s", (email,))
            c.commit()


if __name__ == "__main__":
    unittest.main()
