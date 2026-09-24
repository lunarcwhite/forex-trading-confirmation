"use client";
import { useEffect, useState } from "react";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8001";
const SYMS = ["EUR/USD", "GBP/USD", "USD/JPY", "XAU/USD"];
const TYPES = ["entry_zone", "confirmation", "setup_invalidated"];

export default function Alerts() {
  const [alerts, setAlerts] = useState(null);
  const [events, setEvents] = useState([]);
  const [sym, setSym] = useState(SYMS[0]);
  const [typ, setTyp] = useState(TYPES[0]);
  const [msg, setMsg] = useState("");

  const refresh = () => {
    fetch(`${API}/api/v1/alerts`).then((r) => r.json()).then((j) => setAlerts(j.alerts));
    fetch(`${API}/api/v1/alerts/events`).then((r) => r.json()).then((j) => setEvents(j.events));
  };
  useEffect(refresh, []);

  const create = () => {
    setMsg("");
    fetch(`${API}/api/v1/alerts`, {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ symbol: sym, alert_type: typ }),
    }).then((r) => {
      if (!r.ok) throw new Error("gagal membuat alert");
      setMsg("Alert dibuat.");
      refresh();
    }).catch((e) => setMsg(String(e)));
  };

  const evaluate = (s) => {
    setMsg("");
    fetch(`${API}/api/v1/alerts/evaluate`, {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ symbol: s }),
    }).then((r) => r.json()).then((j) => {
      setMsg(j.triggered.length ? `${j.triggered.length} alert terpicu.` : `Tidak ada picu (${j.state}).`);
      refresh();
    });
  };

  return (
    <div>
      <h1>Alerts <span className="muted">in-app</span></h1>
      <div className="card">
        <h3>Buat Alert</h3>
        <label>Pair <select value={sym} onChange={(e) => setSym(e.target.value)}>
          {SYMS.map((s) => <option key={s}>{s}</option>)}
        </select></label>{" "}
        <label>Jenis <select value={typ} onChange={(e) => setTyp(e.target.value)}>
          {TYPES.map((t) => <option key={t} value={t}>{t}</option>)}
        </select></label>{" "}
        <button onClick={create}>Create</button>
        {msg && <p className="muted">{msg}</p>}
      </div>
      <div className="card" style={{ marginTop: 12 }}>
        <h3>Aktif & Riwayat</h3>
        {!alerts ? <p className="muted">Loading…</p> : alerts.length === 0
          ? <p className="muted">Belum ada alert.</p> : (
          <table><thead><tr><th>Pair</th><th>Jenis</th><th>Aktif</th><th>Aksi</th></tr></thead>
          <tbody>{alerts.map((a) => (
            <tr key={a.id}>
              <td>{a.symbol}</td><td className="mono">{a.alert_type}</td>
              <td>{a.is_active ? "ya" : `terpicu ${a.triggered_at}`}</td>
              <td><button onClick={() => evaluate(a.symbol)}>Evaluate</button></td>
            </tr>))}</tbody></table>)}
      </div>
      <div className="card" style={{ marginTop: 12 }}>
        <h3>Events</h3>
        {events.length === 0 ? <p className="muted">Belum ada event.</p> : (
          <ul>{events.slice().reverse().map((e, i) => (
            <li key={i}>{e.triggered_at} — <strong>{e.payload.what}</strong> ({e.symbol})</li>))}</ul>)}
      </div>
    </div>
  );
}
