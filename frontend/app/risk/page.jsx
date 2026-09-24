"use client";
import { useEffect, useState } from "react";
import { authHeaders } from "../login/page";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

const FIELDS = [
  ["risk_per_trade_pct", "Risk/trade %"],
  ["max_daily_loss_pct", "Max daily loss %"],
  ["max_open_positions", "Max open positions"],
  ["max_exposure_pct", "Max exposure %"],
  ["min_risk_reward", "Min R:R"],
  ["max_spread", "Max spread"],
  ["max_position_size", "Max lots"],
];

const DEFAULT_FORM = {
  name: "Default", risk_per_trade_pct: "1", max_daily_loss_pct: "5",
  max_open_positions: "3", max_exposure_pct: "20", min_risk_reward: "2",
  max_spread: "0.0005", max_position_size: "5",
};

function toPayload(f) {
  const p = { name: f.name };
  for (const [k] of FIELDS) p[k] = parseFloat(f[k]);
  return p;
}

export default function Risk() {
  const [profiles, setProfiles] = useState(null);
  const [err, setErr] = useState("");
  const [form, setForm] = useState(DEFAULT_FORM);
  const [msg, setMsg] = useState("");
  const [editing, setEditing] = useState(null);
  const [sigId, setSigId] = useState("");
  const [checks, setChecks] = useState(null);

  const load = () => {
    setErr("");
    fetch(`${API}/api/v1/risk/profiles`, { headers: authHeaders() })
      .then(async (r) => {
        if (r.status === 401) throw new Error("Login dulu untuk kelola risk profiles.");
        if (r.status === 503) throw new Error("Butuh DATABASE_URL di backend.");
        if (!r.ok) throw new Error((await r.json()).detail || "gagal memuat");
        return r.json();
      })
      .then((j) => setProfiles(j.profiles))
      .catch((e) => { setProfiles([]); setErr(String(e.message || e)); });
  };

  useEffect(load, []);

  const save = (isNew) => {
    setMsg("");
    const url = isNew ? `${API}/api/v1/risk/profiles`
      : `${API}/api/v1/risk/profiles/${editing}`;
    fetch(url, {
      method: isNew ? "POST" : "PUT",
      headers: { "Content-Type": "application/json", ...authHeaders() },
      body: JSON.stringify(toPayload(form)),
    }).then(async (r) => {
      const j = await r.json();
      if (!r.ok) { setMsg(j.detail || "gagal menyimpan"); return; }
      setMsg(isNew ? `Tersimpan: ${j.name}` : `Updated: ${j.name}`);
      setEditing(null); setForm(DEFAULT_FORM); load();
    }).catch((e) => setMsg(String(e)));
  };

  const startEdit = (p) => {
    setEditing(p.id);
    const f = { name: p.name };
    for (const [k] of FIELDS) f[k] = String(p[k]);
    setForm(f);
  };

  const viewChecks = () => {
    if (!sigId) return;
    fetch(`${API}/api/v1/risk/checks?signal_id=${encodeURIComponent(sigId)}`,
      { headers: authHeaders() })
      .then(async (r) => {
        const j = await r.json();
        if (!r.ok) throw new Error(j.detail || "gagal");
        setChecks(j.checks);
      })
      .catch((e) => setChecks({ error: String(e.message || e) }));
  };

  if (profiles === null) return <div><h1>Risk</h1><p className="muted">Loading…</p></div>;
  return (
    <div>
      <h1>Risk Profiles</h1>
      <p className="muted">Batas risk tersimpan di PG · setiap Record decision menulis 1 baris risk_checks · tanpa pengukuran = SKIP, bukan lolos diam-diam.</p>
      {err && <p>{err}</p>}
      <div className="card">
        <h3>Profiles ({profiles.length})</h3>
        {profiles.length === 0
          ? <p className="muted">Belum ada — Record 1 signal untuk bootstrap Default, atau buat di bawah.</p>
          : <table><thead><tr><th>Name</th><th>Risk%</th><th>Min R:R</th><th>MaxPos</th><th>Status</th></tr></thead>
            <tbody>{profiles.map((p) => (
              <tr key={p.id}><td>{p.name}</td><td>{p.risk_per_trade_pct}</td>
                <td>{p.min_risk_reward}</td><td>{p.max_open_positions}</td>
                <td><button onClick={() => startEdit(p)}>Edit</button></td></tr>))}
            </tbody></table>}
      </div>
      <div className="card" style={{ marginTop: 12 }}>
        <h3>{editing ? "Edit profile" : "New profile"}</h3>
        <label>Name <input value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} /></label>
        <div style={{ display: "flex", gap: 12, flexWrap: "wrap", marginTop: 8 }}>
          {FIELDS.map(([k, label]) => (
            <label key={k}>{label}<br />
              <input value={form[k]} size={8}
                onChange={(e) => setForm({ ...form, [k]: e.target.value })} /></label>
          ))}
        </div>
        <p>
          <button onClick={() => save(!editing)}>{editing ? "Update" : "Create"}</button>{" "}
          {editing && <button onClick={() => { setEditing(null); setForm(DEFAULT_FORM); }}>Cancel</button>}
        </p>
        {msg && <p className="muted">{msg}</p>}
      </div>
      <div className="card" style={{ marginTop: 12 }}>
        <h3>Stored risk_checks</h3>
        <p className="muted">Setiap signal tercatat punya 1 baris risk_checks (setup → risk_checks → signal). Masukkan signal_id untuk melihat.</p>
        <input value={sigId} onChange={(e) => setSigId(e.target.value)}
          placeholder="signal_id" size={40} />{" "}
        <button onClick={viewChecks}>View</button>
        {checks && (checks.error
          ? <p>{checks.error}</p>
          : checks.length === 0
            ? <p className="muted">Tidak ada baris.</p>
            : <table><thead><tr><th>Status</th><th>R:R</th><th>Failures</th><th>Profile</th></tr></thead>
              <tbody>{checks.map((c) => (
                <tr key={c.id}><td>{c.status}</td><td>{c.risk_reward ?? "—"}</td>
                  <td>{(c.failures || []).join(", ") || "—"}</td>
                  <td className="mono">{c.risk_profile_id.slice(0, 8)}</td></tr>))}
              </tbody></table>)}
      </div>
    </div>
  );
}
