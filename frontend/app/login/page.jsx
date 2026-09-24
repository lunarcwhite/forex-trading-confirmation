"use client";
import { useState } from "react";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8001";

export function authHeaders() {
  if (typeof window === "undefined") return {};
  const t = localStorage.getItem("token");
  return t ? { Authorization: `Bearer ${t}` } : {};
}

export default function Login() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [name, setName] = useState("");
  const [msg, setMsg] = useState("");
  const go = (mode) => {
    fetch(`${API}/api/v1/auth/${mode}`, { method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password, name }) })
      .then(async (r) => {
        const j = await r.json();
        if (!r.ok) { setMsg(j.detail || "failed"); return; }
        localStorage.setItem("token", j.token);
        localStorage.setItem("user_id", j.user_id);
        window.location.href = "/";
      });
  };
  const out = () => { localStorage.removeItem("token"); localStorage.removeItem("user_id"); setMsg("logged out"); };
  return (
    <div>
      <h1>Login</h1>
      <div className="card">
        <label>Name: <input value={name} onChange={(e) => setName(e.target.value)} /></label><br /><br />
        <label>Email: <input value={email} onChange={(e) => setEmail(e.target.value)} /></label><br /><br />
        <label>Password: <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} /></label>
        <p><button onClick={() => go("register")}>Register</button>{" "}
          <button className="primary" onClick={() => go("login")}>Login</button>{" "}
          <button onClick={out}>Logout</button></p>
        {msg && <p className="muted">{msg}</p>}
        <p className="muted">Write endpoints (paper order, journal, builder save) butuh login.</p>
      </div>
    </div>
  );
}
