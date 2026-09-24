"use client";
import { useEffect, useState } from "react";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
const SYMS = ["EUR/USD", "GBP/USD", "USD/JPY", "XAU/USD"];

export default function Paper() {
  const [accounts, setAccounts] = useState([]);
  const [acc, setAcc] = useState("");
  const [positions, setPositions] = useState([]);
  const [trades, setTrades] = useState([]);
  const [name, setName] = useState("paper-1");
  const [form, setForm] = useState({ symbol: "EUR/USD", direction: "buy", lots: "0.01", entry: "", sl: "", tp: "" });

  const refresh = (id) => {
    if (!id) return;
    fetch(`${API}/api/v1/paper/positions?account_id=${id}`).then((r) => r.json()).then((j) => setPositions(j.positions));
    fetch(`${API}/api/v1/paper/trades?account_id=${id}`).then((r) => r.json()).then((j) => setTrades(j.trades));
  };
  useEffect(() => {
    fetch(`${API}/api/v1/paper/accounts`).then((r) => r.json()).then((j) => {
      setAccounts(j.accounts);
      if (j.accounts.length && !acc) { setAcc(j.accounts[0].id); refresh(j.accounts[0].id); }
    });
  }, []);
  useEffect(() => { refresh(acc); }, [acc]);

  const create = () => {
    fetch(`${API}/api/v1/paper/accounts`, { method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name, balance: 10000 }) })
      .then((r) => r.json()).then((a) => { setAccounts([...accounts, a]); setAcc(a.id); });
  };
  const loadSignal = () => {
    fetch(`${API}/api/v1/signals/latest?symbol=${encodeURIComponent(form.symbol)}`)
      .then((r) => r.json()).then((s) => {
        if (s.risk?.entry) setForm({ ...form, entry: s.risk.entry, sl: s.risk.stop_loss, tp: s.risk.take_profit });
      });
  };
  const order = () => {
    fetch(`${API}/api/v1/paper/orders`, { method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ account_id: acc, symbol: form.symbol, direction: form.direction,
        lots: parseFloat(form.lots), entry: parseFloat(form.entry),
        stop_loss: form.sl ? parseFloat(form.sl) : null,
        take_profit: form.tp ? parseFloat(form.tp) : null }) })
      .then(() => refresh(acc));
  };
  const close = (pid, exit) => {
    fetch(`${API}/api/v1/paper/positions/${pid}/close`, { method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ account_id: acc, exit: parseFloat(exit) }) })
      .then(() => refresh(acc));
  };

  return (
    <div>
      <h1>Paper Trading <span className="muted">SIMULATION</span></h1>
      <div className="card">
        <label>Account: <select value={acc} onChange={(e) => setAcc(e.target.value)}>
          {accounts.map((a) => <option key={a.id} value={a.id}>{a.name} — ${a.balance}</option>)}
        </select></label>{" "}
        <input value={name} onChange={(e) => setName(e.target.value)} size={10} />
        <button onClick={create}>New $10k account</button>
      </div>
      <div className="card" style={{ marginTop: 12 }}>
        <h3>New Order</h3>
        <label>Pair: <select value={form.symbol} onChange={(e) => setForm({ ...form, symbol: e.target.value })}>
          {SYMS.map((s) => <option key={s}>{s}</option>)}</select></label>{" "}
        <label>Dir: <select value={form.direction} onChange={(e) => setForm({ ...form, direction: e.target.value })}>
          <option>buy</option><option>sell</option></select></label>{" "}
        <label>Lots: <input value={form.lots} onChange={(e) => setForm({ ...form, lots: e.target.value })} size={5} /></label>{" "}
        <label>Entry: <input value={form.entry} onChange={(e) => setForm({ ...form, entry: e.target.value })} size={9} /></label>{" "}
        <label>SL: <input value={form.sl} onChange={(e) => setForm({ ...form, sl: e.target.value })} size={9} /></label>{" "}
        <label>TP: <input value={form.tp} onChange={(e) => setForm({ ...form, tp: e.target.value })} size={9} /></label>{" "}
        <button onClick={loadSignal}>Load signal</button> <button onClick={order}>Place (sim)</button>
      </div>
      <div className="card" style={{ marginTop: 12 }}>
        <h3>Open Positions</h3>
        <table><thead><tr><th>Pair</th><th>Dir</th><th>Lots</th><th>Entry</th><th>uPnL</th><th></th></tr></thead>
        <tbody>{positions.map((p) => <CloseRow key={p.id} p={p} onClose={close} />)}</tbody></table>
      </div>
      <div className="card" style={{ marginTop: 12 }}>
        <h3>Closed Trades</h3>
        <table><thead><tr><th>Pair</th><th>Entry</th><th>Exit</th><th>P/L</th><th>R</th><th>Result</th></tr></thead>
        <tbody>{trades.map((t) => (
          <tr key={t.id}><td>{t.symbol}</td><td className="mono">{t.entry}</td>
            <td className="mono">{t.exit}</td><td className="mono">{t.pnl}</td>
            <td className="mono">{t.r_multiple}</td><td>{t.result}</td></tr>))}</tbody></table>
      </div>
    </div>
  );
}

function CloseRow({ p, onClose }) {
  const [exit, setExit] = useState(p.entry);
  return (
    <tr><td>{p.symbol}</td><td>{p.direction}</td><td className="mono">{p.lots}</td>
      <td className="mono">{p.entry}</td><td className="mono">{p.unrealized_pnl}</td>
      <td><input value={exit} onChange={(e) => setExit(e.target.value)} size={9} />
        <button onClick={() => onClose(p.id, exit)}>Close</button></td></tr>
  );
}
