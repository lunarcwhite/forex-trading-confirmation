"use client";
import { useEffect, useState } from "react";
import { authHeaders } from "../login/page";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8001";
const SAMPLE = "currency,event_name,impact,scheduled_at,source,external_id\nUSD,US CPI,high,2026-10-01T12:30:00+00:00,csv,cpi-oct\nEUR,ECB Rate,medium,2026-10-02T12:15:00+00:00,csv,ecb-oct";

export default function Events() {
  const [events, setEvents] = useState([]);
  const [src, setSrc] = useState(null);
  const [ccy, setCcy] = useState("");
  const [csv, setCsv] = useState(SAMPLE);
  const [msg, setMsg] = useState("");
  const [man, setMan] = useState({ currency: "USD", event_name: "", impact: "high", scheduled_at: "" });

  const load = () => {
    fetch(`${API}/api/v1/events/source`).then((r) => (r.ok ? r.json() : null)).then(setSrc);
    fetch(`${API}/api/v1/events${ccy ? `?currency=${encodeURIComponent(ccy)}` : ""}`)
      .then((r) => (r.ok ? r.json() : Promise.reject(r.statusText)))
      .then((j) => setEvents(j.events))
      .catch(() => setEvents([]));
  };
  useEffect(load, []);

  const doImport = () => {
    setMsg("");
    fetch(`${API}/api/v1/events/import`, { method: "POST",
      headers: { "Content-Type": "application/json", ...authHeaders() },
      body: JSON.stringify({ csv }) })
      .then(async (r) => {
        const j = await r.json();
        if (r.status === 401) { setMsg("Login dulu untuk import."); return; }
        if (!r.ok) { setMsg(j.detail || "import gagal"); return; }
        setMsg(`Inserted ${j.inserted}, skipped ${j.skipped}` +
          (j.errors?.length ? `, errors: ${j.errors.join("; ")}` : ""));
        load();
      });
  };

  const addManual = () => {
    setMsg("");
    fetch(`${API}/api/v1/events`, { method: "POST",
      headers: { "Content-Type": "application/json", ...authHeaders() },
      body: JSON.stringify({ ...man, source: "manual" }) })
      .then(async (r) => {
        const j = await r.json();
        if (!r.ok) { setMsg(j.detail || "gagal"); return; }
        setMsg(`Terekam: ${j.event_name}`);
        setMan({ ...man, event_name: "", scheduled_at: "" });
        load();
      });
  };

  return (
    <div>
      <h1>Economic Calendar <span className="muted">V2</span></h1>
      <p className="muted page-sub">
        Source: {src ? `${src.configured_source} (rows: ${(src.row_sources || []).join(", ") || "none"})` : "memuat…"} ·
        HIGH ±[-15min,+60min] menuju ELEVATED lalu NO_TRADE · tanpa baris/unreachable menuju OFF (tak mengasumsikan aman).
      </p>
      <div className="card">
        <h3>Upcoming</h3>
        <input value={ccy} onChange={(e) => setCcy(e.target.value)} placeholder="filter currency" size={8} />{" "}
        <button onClick={load}>Terapkan filter</button>
        <table><thead><tr><th>When (UTC)</th><th>Ccy</th><th>Event</th><th>Impact</th><th>Source</th></tr></thead>
        <tbody>{events.map((e) => (
          <tr key={e.id}><td className="mono">{e.scheduled_at}</td><td>{e.currency}</td>
            <td>{e.event_name}</td><td>{e.impact}</td><td className="muted">{e.source}</td></tr>))}</tbody></table>
        {events.length === 0 && <p className="empty">Tidak ada event (filter OFF, bukan berarti aman).</p>}
      </div>
      <div className="card" style={{ marginTop: 12 }}>
        <h3>CSV Import (login)</h3>
        <textarea value={csv} onChange={(e) => setCsv(e.target.value)} rows={5} cols={90} />
        <p><button className="primary" onClick={doImport}>Import CSV</button></p>
        {msg && <p className="muted">{msg}</p>}
      </div>
      <div className="card" style={{ marginTop: 12 }}>
        <h3>Manual Input (login)</h3>
        <label>Ccy <input value={man.currency} onChange={(e) => setMan({ ...man, currency: e.target.value })} size={4} /></label>{" "}
        <label>Event <input value={man.event_name} onChange={(e) => setMan({ ...man, event_name: e.target.value })} size={20} /></label>{" "}
        <label>Impact <select value={man.impact} onChange={(e) => setMan({ ...man, impact: e.target.value })}>
          <option>high</option><option>medium</option><option>low</option></select></label>{" "}
        <label>At (ISO) <input value={man.scheduled_at} onChange={(e) => setMan({ ...man, scheduled_at: e.target.value })} size={28} placeholder="2026-10-01T12:30:00+00:00" /></label>{" "}
        <button className="primary" onClick={addManual}>Save event</button>
      </div>
    </div>
  );
}
