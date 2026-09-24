import "./globals.css";

export const metadata = { title: "Trading Decision Support - MVP" };

const MARKETS = ["EUR/USD", "GBP/USD", "USD/JPY", "XAU/USD"];

export default function RootLayout({ children }) {
  return (
    <html lang="id">
      <body>
        <div className="layout">
          <nav className="sidebar" aria-label="Navigasi utama">
            <span className="brand">Decision Support</span>
            <a href="/">Dashboard</a>
            <a href="/scanner">Scanner</a>
            <a href="/risk">Risk</a>
            <a href="/events">Events</a>
            <a href="/alerts">Alerts</a>
            <a href="/backtest">Backtest <span className="muted">V2</span></a>
            <a href="/paper">Paper <span className="muted">SIM</span></a>
            <a href="/journal">Journal <span className="muted">V2</span></a>
            <a href="/strategies">Builder <span className="muted">V2</span></a>
            <a href="/login">Login</a>
            <span className="nav-label muted">Markets:</span>
            {MARKETS.map((s) => (
              <a key={s} href={`/market/${encodeURIComponent(s)}`}>{s}</a>
            ))}
          </nav>
          <main className="main">{children}</main>
        </div>
      </body>
    </html>
  );
}
