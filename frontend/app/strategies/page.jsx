"use client";
import { useState } from "react";
import { authHeaders } from "../login/page";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8001";
const FIELDS = ["ema_20", "ema_50", "ema_100", "ema_200", "rsi_14", "atr_14",
  "structure_bias", "risk_reward", "spread"];
const OPS = ["greater_than", "greater_than_or_equal", "less_than", "less_than_or_equal",
  "equal", "not_equal", "in", "between"];

export default function Builder() {
  const [name, setName] = useState("My Pullback");
  const [symbol, setSymbol] = useState("EUR/USD");
  const [rules, setRules] = useState([
    { rule_type: "trend", name: "EMA50>EMA200",
      condition: { field: "ema_50", operator: "greater_than", ref: "ema_200" }, required: true, weight: 1 },
    { rule_type: "momentum", name: "RSI>=50",
      condition: { field: "rsi_14", operator: "greater_than_or_equal", value: 50 }, required: true, weight: 1 },
  ]);
  const [out, setOut] = useState(null);
  const set = (i, patch) => setRules(rules.map((r, j) => (j === i ? { ...r, ...patch } : r)));
  const setCond = (i, patch) =>
    setRules(rules.map((r, j) => (j === i ? { ...r, condition: { ...r.condition, ...patch } } : r)));
  const add = () => setRules([...rules, { rule_type: "custom", name: "New rule",
    condition: { field: "rsi_14", operator: "greater_than", value: 50 }, required: true, weight: 1 }]);
  const preview = () => {
    fetch(`${API}/api/v1/strategies/evaluate`, { method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ rules, symbol, timeframe: "H1", direction: "buy" }) })
      .then((r) => r.json()).then(setOut);
  };
  const save = () => {
    fetch(`${API}/api/v1/strategies`, { method: "POST",
      headers: { "Content-Type": "application/json", ...authHeaders() },
      body: JSON.stringify({ name, direction: "buy", rules }) })
      .then((r) => r.json()).then((j) => alert(`Saved: ${j.id}`));
  };
  return (
    <div>
      <h1>Strategy Builder (V2)</h1>
      <label>Name: <input value={name} onChange={(e) => setName(e.target.value)} size={20} /></label>{" "}
      <label>Test pair: <select value={symbol} onChange={(e) => setSymbol(e.target.value)}>
        {["EUR/USD", "GBP/USD", "USD/JPY", "XAU/USD"].map((s) => <option key={s}>{s}</option>)}
      </select></label>
      {rules.map((r, i) => (
        <div className="card" key={i} style={{ marginTop: 8 }}>
          <input value={r.name} onChange={(e) => set(i, { name: e.target.value })} size={18} />{" "}
          <select value={r.condition.field} onChange={(e) => setCond(i, { field: e.target.value })}>
            {FIELDS.map((f) => <option key={f}>{f}</option>)}</select>{" "}
          <select value={r.condition.operator} onChange={(e) => setCond(i, { operator: e.target.value })}>
            {OPS.map((o) => <option key={o}>{o}</option>)}</select>{" "}
          <input value={r.condition.value ?? r.condition.ref ?? ""}
            onChange={(e) => {
              const v = e.target.value;
              setCond(i, isNaN(parseFloat(v)) || v === "" ? { value: v } : { value: parseFloat(v) });
            }} size={10} placeholder="value" />
          <label> <input type="checkbox" checked={r.required}
            onChange={(e) => set(i, { required: e.target.checked })} /> required</label>{" "}
          <button onClick={() => setRules(rules.filter((_, j) => j !== i))}>✕</button>
        </div>))}
      <p><button onClick={add}>+ Add rule</button>{" "}
        <button onClick={preview}>Preview vs {symbol}</button>{" "}
        <button onClick={save}>Save strategy</button></p>
      {out && (
        <div className="card">
          <p><span className={`badge ${out.decision}`}>{out.decision}</span></p>
          <table><tbody>
            {out.results.map((x, j) => <tr key={j}><td>{rules[j]?.name}</td><td>{x.result}</td></tr>)}
          </tbody></table>
        </div>)}
    </div>
  );
}
