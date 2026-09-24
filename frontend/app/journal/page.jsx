"use client";
import { useEffect, useState } from "react";
import { authHeaders } from "../login/page";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8001";

export default function Journal() {
  const [entries, setEntries] = useState([]);
  const [store, setStore] = useState("pg");
  const [form, setForm] = useState({ trade_id: "", signal_id: "", thesis: "", emotion: "", lesson: "", notes: "" });
  const [msg, setMsg] = useState("");
  const refresh = () =>
    fetch(`${API}/api/v1/journal`, { headers: authHeaders() })
      .then((r) => r.json())
      .then((j) => { setEntries(j.entries || []); setStore(j.store || "?"); });
  useEffect(() => { refresh(); }, []);
  const add = () => {
    setMsg("");
    fetch(`${API}/api/v1/journal`, { method: "POST",
      headers: { "Content-Type": "application/json", ...authHeaders() }, body: JSON.stringify(form) })
      .then(async (r) => {
        const j = await r.json();
        if (r.status === 401) { setMsg("Login dulu untuk menulis journal."); return; }
        if (!r.ok) { setMsg(j.detail || "gagal menyimpan"); return; }
        setForm({ trade_id: "", signal_id: "", thesis: "", emotion: "", lesson: "", notes: "" });
        refresh();
      });
  };
  const set = (k) => (e) => setForm({ ...form, [k]: e.target.value });
  return (
    <div>
      <h1>Journal <span className="muted">· {store === "pg" ? "Postgres" : "file-store"}</span></h1>
      <p className="muted page-sub">Snapshot keputusan di-resolve server-side dari signal milikmu, tidak bisa dikarang client.</p>
      <div className="card">
        <h3>New Entry</h3>
        <label>Trade ID (paper): <input value={form.trade_id} onChange={set("trade_id")} size={10} /></label>{" "}
        <label>Signal ID (PG): <input value={form.signal_id} onChange={set("signal_id")} size={32} /></label>
        <br /><br />
        <label>Thesis: <input value={form.thesis} onChange={set("thesis")} size={24} /></label>{" "}
        <label>Emotion: <input value={form.emotion} onChange={set("emotion")} size={10} /></label>{" "}
        <label>Lesson: <input value={form.lesson} onChange={set("lesson")} size={20} /></label>{" "}
        <label>Notes: <input value={form.notes} onChange={set("notes")} size={20} /></label>{" "}
        <button className="primary" onClick={add}>Save entry</button>
        {msg && <p className="muted">{msg}</p>}
      </div>
      <div className="card" style={{ marginTop: 12 }}>
        <table><thead><tr><th>Trade</th><th>Signal</th><th>Thesis</th><th>Emotion</th><th>Snapshot</th></tr></thead>
        <tbody>{entries.map((e) => (
          <tr key={e.id}><td className="mono">{e.trade_id || "n/a"}</td>
            <td className="mono">{e.signal_id ? e.signal_id.slice(0, 8) : "n/a"}</td>
            <td>{e.thesis}</td><td>{e.emotion}</td>
            <td className="mono muted">{JSON.stringify(e.decision_snapshot).slice(0, 80)}</td></tr>))}</tbody></table>
        {entries.length === 0 && <p className="muted">Belum ada entry (login untuk PG).</p>}
      </div>
    </div>
  );
}
