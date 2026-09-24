"use client";
import { useEffect, useState } from "react";
import { authHeaders } from "../../login/page";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8001";
const TFS = ["M5", "M15", "H1", "H4", "D1"];

function Chart({ candles }) {
  const data = candles.slice(-60);
  const W = 640, H = 220, pad = 8;
  const hi = Math.max(...data.map((c) => c.high));
  const lo = Math.min(...data.map((c) => c.low));
  const span = hi - lo || 1;
  const y = (p) => pad + (1 - (p - lo) / span) * (H - 2 * pad);
  const w = W / data.length;
  return (
    <svg viewBox={`0 0 ${W} ${H}`} width="100%" role="img" aria-label="Grafik candlestick"
      style={{ background: "#0b0e14", borderRadius: 8 }}>
      {data.map((c, i) => {
        const up = c.close >= c.open;
        const col = up ? "#22c55e" : "#ef4444";
        const x = i * w + w / 2;
        const bw = Math.max(2, w * 0.6);
        return (
          <g key={i}>
            <line x1={x} x2={x} y1={y(c.high)} y2={y(c.low)} stroke={col} strokeWidth={1} />
            <rect x={x - bw / 2} y={y(Math.max(c.open, c.close))} width={bw}
              height={Math.max(1, Math.abs(y(c.open) - y(c.close)))} fill={col} />
          </g>
        );
      })}
    </svg>
  );
}

export default function MarketDetail({ params }) {
  const symbol = decodeURIComponent(params.symbol);
  const [tf, setTf] = useState("H1");
  const [an, setAn] = useState(null);
  const [sig, setSig] = useState(null);
  const [candles, setCandles] = useState(null);
  const [err, setErr] = useState("");
  const [bal, setBal] = useState("1000");
  const [riskPct, setRiskPct] = useState("1");
  const [pos, setPos] = useState(null);
  const [ai, setAi] = useState(null);
  const [recMsg, setRecMsg] = useState("");
  const [recents, setRecents] = useState([]);

  useEffect(() => {
    setAn(null); setSig(null); setCandles(null); setErr(""); setPos(null); setAi(null);
    Promise.all([
      fetch(`${API}/api/v1/analysis?symbol=${encodeURIComponent(symbol)}&timeframe=${tf}`).then((r) => {
        if (!r.ok) throw new Error(r.statusText); return r.json();
      }),
      fetch(`${API}/api/v1/signals/latest?symbol=${encodeURIComponent(symbol)}`).then((r) => r.json()),
      fetch(`${API}/api/v1/candles?symbol=${encodeURIComponent(symbol)}&timeframe=${tf}&limit=120`).then((r) => r.json()),
      fetch(`${API}/api/v1/ai/explain?symbol=${encodeURIComponent(symbol)}`).then((r) => r.json()).catch(() => null),
    ]).then(([a, s, c, e]) => { setAn(a); setSig(s); setCandles(c.candles); setAi(e); })
      .catch(() => setErr("Data market tak tersedia. Pastikan backend :8001 jalan, lalu muat ulang."));
    loadRecents();
  }, [symbol, tf]);

  const calc = () => {
    if (!sig?.risk?.stop_loss) return;
    fetch(`${API}/api/v1/risk/validate`, {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        balance: parseFloat(bal), risk_pct: parseFloat(riskPct),
        entry: sig.risk.entry, stop_loss: sig.risk.stop_loss,
        take_profit: sig.risk.take_profit, pair: symbol,
      }),
    }).then((r) => r.json()).then(setPos);
  };

  const loadRecents = () => {
    fetch(`${API}/api/v1/signals?symbol=${encodeURIComponent(symbol)}&limit=5`,
      { headers: authHeaders() })
      .then((r) => (r.ok ? r.json() : Promise.reject(r.status)))
      .then((j) => setRecents(j.signals))
      .catch(() => setRecents([]));
  };

  const NEXT = { generated: ["active", "expired"],
    active: ["executed", "ignored", "expired", "invalidated"] };

  const move = (id, st) => {
    fetch(`${API}/api/v1/signals/${id}/status`, {
      method: "POST", headers: { "Content-Type": "application/json", ...authHeaders() },
      body: JSON.stringify({ status: st }),
    }).then(() => loadRecents());
  };

  const record = () => {
    setRecMsg("");
    fetch(`${API}/api/v1/signals`, {
      method: "POST", headers: { "Content-Type": "application/json", ...authHeaders() },
      body: JSON.stringify({ symbol }),
    }).then(async (r) => {
      const j = await r.json();
      if (r.status === 401) { setRecMsg("Login dulu untuk merekam keputusan."); return; }
      if (!r.ok) { setRecMsg(j.detail || "gagal merekam"); return; }
      setRecMsg(`Terekam: ${j.state} (${j.score})`);
      loadRecents();
    }).catch((e) => setRecMsg(String(e)));
  };

  if (err) return <div><h1>{symbol}</h1><p className="empty">{err}</p></div>;
  if (!an || !sig || !candles) return <div><h1>{symbol}</h1><p className="muted">Memuat analisis…</p></div>;
  const passed = new Set(sig.confirmations);
  const total = sig.confirmations.length + sig.missing_conditions.length;
  const f5 = (n) => (typeof n === "number" ? n.toFixed(5) : "n/a");
  return (
    <div>
      <h1>{symbol} <span className="muted mono">{f5(an.indicators.ema_50)}</span></h1>
      <div className="seg" role="group" aria-label="Timeframe">
        {TFS.map((t) => (
          <button key={t} onClick={() => setTf(t)} aria-current={t === tf}>{t}</button>))}
      </div>
      <span className="muted"> · source: {an.source}</span>
      <div className={`card decision ${sig.state}`} style={{ marginTop: 12 }}>
        <span className={`badge ${sig.state}`}>{sig.state}</span>{" "}
        <span className="muted">{an.bias} bias · {passed.size}/{total} konfirmasi · news {sig.news?.state || "OFF"}</span>
        <p>{sig.state === "ENTER" ? "Seluruh kondisi mandatory terpenuhi."
          : sig.state === "WAIT" ? `Menunggu: ${sig.missing_conditions.join(", ")}`
          : `Batal: ${(sig.invalidations || []).join(", ") || sig.missing_conditions.join(", ")}`}</p>
        <button className="primary" onClick={record}>Record decision</button>
        {recMsg && <p className="muted">{recMsg}</p>}
      </div>
      <div className="card"><h3>Chart ({tf})</h3><Chart candles={candles} /></div>
      {an.mtf?.biases && (
        <div className="card">
          <h3>MTF Analysis <span className="muted">· {an.mtf.alignment}</span></h3>
          <div className="tbl-wrap"><table><tbody>
            {["D1", "H4", "H1", "M15", "M5"].map((t) => (
              <tr key={t}><td>{t}</td><td>{an.mtf.biases[t] ?? "n/a"}</td>
                <td>{an.mtf.biases[t] === "bullish" ? "✓" : an.mtf.biases[t] === "bearish" ? "✕" : "○"}</td></tr>))}
          </tbody></table></div>
        </div>)}
      <div className="grid2">
        <div className="card">
          <h3>Confirmation Matrix</h3>
          <table><tbody>
            {[...sig.confirmations.map((c) => [c, true]),
              ...sig.missing_conditions.map((c) => [c, false])].map(([c, ok]) => (
              <tr key={c}><td>{c}</td>
                <td><span className={`bar${ok ? "" : " missing"}`}><span style={{ width: ok ? "100%" : "25%" }} /></span></td>
                <td>{ok ? "✓" : "○"}</td></tr>))}
          </tbody></table>
          <h4>Mengapa {sig.state}?</h4>
          {sig.missing_conditions.length === 0
            ? <p>Seluruh kondisi mandatory terpenuhi.</p>
            : <ul>{sig.missing_conditions.map((m) => <li key={m}>{m}</li>)}</ul>}
        </div>
        <div className="card">
          <h3>Trade Plan (ATR-based)</h3>
          <p className="mono">Entry zone {f5(sig.entry_zone.min)} - {f5(sig.entry_zone.max)} <span className="muted">({sig.entry_zone.source})</span></p>
          <p className="mono">Entry {f5(sig.risk.entry)}</p>
          <p className="mono">SL {f5(sig.risk.stop_loss)}</p>
          <p className="mono">TP {f5(sig.risk.take_profit)}</p>
          <p className="mono">R:R {sig.risk.risk_reward?.toFixed?.(2)}</p>
          <h4>Position Size</h4>
          <label>Balance <input value={bal} onChange={(e) => setBal(e.target.value)} size={8} /></label>{" "}
          <label>Risk % <input value={riskPct} onChange={(e) => setRiskPct(e.target.value)} size={4} /></label>{" "}
          <button onClick={calc}>Calculate</button>
          {pos && !pos.lots && <p>{JSON.stringify(pos)}</p>}
          {pos?.lots !== undefined && (
            <><p className="mono">Risk ${pos.risk_amount} · {pos.sl_pips?.toFixed?.(1)} pips · <strong>{pos.lots} lot</strong> · {pos.status}</p>
              {pos.failures?.length > 0 && (
                <ul>{pos.failures.map((f) => <li key={f}>✕ {f}</li>)}</ul>)}
              {pos.rules?.filter((r) => r.result === "SKIP").length > 0 && (
                <p className="muted">Skipped: {pos.rules.filter((r) => r.result === "SKIP").map((r) => r.rule).join(", ")} (tanpa pengukuran)</p>)}
            </>)}
        </div>
      </div>
      <div className="card">
        <h3>AI Analyst</h3>
        {!ai ? <p className="muted">Memuat penjelasan…</p> : (
          <>
            <p><strong>{ai.headline}</strong></p>
            <p>{ai.summary}</p>
            {ai.confirmed?.length > 0 && (
              <><h4>Terkonfirmasi ({ai.score})</h4>
              <ul>{ai.confirmed.map((c, i) => <li key={i}>✓ {c}</li>)}</ul></>)}
            {ai.missing?.length > 0 && (
              <><h4>Belum terpenuhi</h4>
              <ul>{ai.missing.map((m, i) => <li key={i}>○ {m}</li>)}</ul></>)}
            {ai.what_needs_to_happen?.length > 0 && (
              <><h4>Agar entry valid</h4>
              <ol>{ai.what_needs_to_happen.map((w, i) => <li key={i}>{w}</li>)}</ol></>)}
            {ai.invalidations?.length > 0 && (
              <><h4>Setup batal jika</h4>
              <ul>{ai.invalidations.map((v, i) => <li key={i}>✕ {v}</li>)}</ul></>)}
            <p className="muted">{ai.risk_note}</p>
            {ai.mtf_note && <p className="muted">{ai.mtf_note}</p>}
            <p className="muted">{ai.news_note}</p>
            <p className="muted">{ai.uncertainty}</p>
          </>
        )}
      </div>
      <div className="card">
        <h3>Recorded Signals</h3>
        {recents.length === 0
          ? <p className="empty">Belum ada. <span className="act">Login lalu Record decision.</span></p>
          : <ul>{recents.map((s) => (
            <li key={s.id} className="mono">{s.generated_at} · {s.decision} {s.direction} [{s.status}]
              {(NEXT[s.status] || []).map((n) => (
                <button key={n} onClick={() => move(s.id, n)}
                  style={{ marginLeft: 6, padding: "2px 8px" }}>{n}</button>))}</li>))}</ul>}
      </div>
    </div>
  );
}
