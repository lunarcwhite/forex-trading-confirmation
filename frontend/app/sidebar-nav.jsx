"use client";
import { usePathname } from "next/navigation";

const MARKETS = [
  { symbol: "EUR/USD", label: "EUR / USD" },
  { symbol: "GBP/USD", label: "GBP / USD" },
  { symbol: "USD/JPY", label: "USD / JPY" },
  { symbol: "XAU/USD", label: "Gold (XAU)" },
];

export default function SidebarNav() {
  const pathname = usePathname();

  const isCurrent = (path) => {
    if (path === "/" && pathname === "/") return true;
    if (path !== "/" && pathname.startsWith(path)) return true;
    return false;
  };

  return (
    <nav className="sidebar" aria-label="Navigasi Workstation">
      <div className="nav-group-title">Intelligence</div>
      <a href="/" className={isCurrent("/") ? "active" : ""}>
        <svg className="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <rect x="3" y="3" width="7" height="7" rx="1" />
          <rect x="14" y="3" width="7" height="7" rx="1" />
          <rect x="14" y="14" width="7" height="7" rx="1" />
          <rect x="3" y="14" width="7" height="7" rx="1" />
        </svg>
        <span>Dashboard</span>
      </a>

      <a href="/scanner" className={isCurrent("/scanner") ? "active" : ""}>
        <svg className="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <circle cx="12" cy="12" r="9" />
          <path d="M12 3v18M3 12h18" />
          <circle cx="12" cy="12" r="4" />
        </svg>
        <span>Scanner</span>
        <span className="tag-pill">LIVE</span>
      </a>

      <a href="/alerts" className={isCurrent("/alerts") ? "active" : ""}>
        <svg className="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9" />
          <path d="M13.73 21a2 2 0 0 1-3.46 0" />
        </svg>
        <span>Alerts</span>
      </a>

      <div className="nav-group-title">Markets</div>
      {MARKETS.map((m) => {
        const link = `/market/${encodeURIComponent(m.symbol)}`;
        const active = isCurrent(link);
        return (
          <a key={m.symbol} href={link} className={active ? "active" : ""}>
            <svg className="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <line x1="12" y1="2" x2="12" y2="22" />
              <rect x="9" y="6" width="6" height="12" rx="1" fill={active ? "currentColor" : "none"} />
            </svg>
            <span className="mono" style={{ fontSize: "0.82rem" }}>{m.label}</span>
          </a>
        );
      })}

      <div className="nav-group-title">Execution & Risk</div>
      <a href="/risk" className={isCurrent("/risk") ? "active" : ""}>
        <svg className="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
        </svg>
        <span>Risk Engine</span>
      </a>

      <a href="/paper" className={isCurrent("/paper") ? "active" : ""}>
        <svg className="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <line x1="12" y1="1" x2="12" y2="23" />
          <path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6" />
        </svg>
        <span>Paper Sim</span>
        <span className="tag-pill">SIM</span>
      </a>

      <a href="/events" className={isCurrent("/events") ? "active" : ""}>
        <svg className="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <rect x="3" y="4" width="18" height="18" rx="2" ry="2" />
          <line x1="16" y1="2" x2="16" y2="6" />
          <line x1="8" y1="2" x2="8" y2="6" />
          <line x1="3" y1="10" x2="21" y2="10" />
        </svg>
        <span>Events Calendar</span>
      </a>

      <div className="nav-group-title">Lab & Records</div>
      <a href="/journal" className={isCurrent("/journal") ? "active" : ""}>
        <svg className="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20" />
          <path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z" />
        </svg>
        <span>Trade Journal</span>
      </a>

      <a href="/strategies" className={isCurrent("/strategies") ? "active" : ""}>
        <svg className="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <line x1="4" y1="21" x2="4" y2="14" />
          <line x1="4" y1="10" x2="4" y2="3" />
          <line x1="12" y1="21" x2="12" y2="12" />
          <line x1="12" y1="8" x2="12" y2="3" />
          <line x1="20" y1="21" x2="20" y2="16" />
          <line x1="20" y1="12" x2="20" y2="3" />
          <line x1="1" y1="14" x2="7" y2="14" />
          <line x1="9" y1="8" x2="15" y2="8" />
          <line x1="17" y1="16" x2="23" y2="16" />
        </svg>
        <span>Strategy Builder</span>
      </a>

      <a href="/backtest" className={isCurrent("/backtest") ? "active" : ""}>
        <svg className="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <polygon points="13 19 22 12 13 5 13 19" />
          <polygon points="2 19 11 12 2 5 2 19" />
        </svg>
        <span>Backtesting</span>
      </a>

      <div className="sidebar-footer">
        <a href="/login" className={isCurrent("/login") ? "active" : ""}>
          <svg className="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M15 3h4a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2h-4" />
            <polyline points="10 17 15 12 10 7" />
            <line x1="15" y1="12" x2="3" y2="12" />
          </svg>
          <span>Account Login</span>
        </a>
      </div>
    </nav>
  );
}
