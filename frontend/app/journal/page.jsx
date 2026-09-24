"use client";
import { useEffect, useState } from "react";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function Journal() {
  const [entries, setEntries] = useState([]);
  const [form, setForm] = useState({ trade_id: "", thesis: "", emotion: "", notes: "" });
  const refresh = () =>
    fetch(`${API}/api/v1/journal`).then((r) => r.json()).then((j) => setEntries(j.entries));
  useEffect(() => { refresh(); }, []);
  const add = () => {
    fetch(`${API}/api/v1/journal`, { method: "POST",
      headers: { "Content-Type": "application/json" }, body: JSON.stringify(form) })
      .then((r) => { if (r.ok) { setForm({ trade_id: "", thesis: "", emotion: "", notes: "" }); refresh(); } });
  };
  return (
    <div>
      <h1>Journal (V2)</h1>
      <div className="card">
        <h3>New Entry</h3>
        <label>Trade ID: <input value={form.trade_id} onChange={(e) => setForm({ ...form, trade_id: e.target.value })} size={10} /></label>{" "}
        <label>Thesis: <input value={form.thesis} onChange={(e) => setForm({ ...form, thesis: e.target.value })} size={20} /></label>{" "}
        <label>Emotion: <input value={form.emotion} onChange={(e) => setForm({ ...form, emotion: e.target.value })} size={10} /></label>{" "}
        <label>Notes: <input value={form.notes} onChange={(e) => setForm({ ...form, notes: e.target.value })} size={20} /></label>{" "}
        <button onClick={add}>Save</button>
      </div>
      <div className="card" style={{ marginTop: 12 }}>
        <table><thead><tr><th>Trade</th><th>Thesis</th><th>Emotion</th><th>Notes</th><th>Snapshot</th></tr></thead>
        <tbody>{entries.map((e) => (
          <tr key={e.id}><td className="mono">{e.trade_id}</td><td>{e.thesis}</td>
            <td>{e.emotion}</td><td>{e.notes}</td>
            <td className="mono muted">{JSON.stringify(e.decision_snapshot)}</td></tr>))}</tbody></table>
      </div>
    </div>
  );
}
