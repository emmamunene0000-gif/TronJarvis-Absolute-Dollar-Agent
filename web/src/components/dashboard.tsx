import { useCallback, useEffect, useState } from "react";
import PriceChart from "./price-chart";

type Signal = { id?: number | string; signal: string; bias: "CALL" | "PUT"; symbol: string; tf: string; time: number; spot: number; confidence: number; fractal?: { sync_layers?: number; quality?: string }; setup?: { strike?: number; expiry_min?: number }; received_at?: string; narrative?: string };
type Risk = { state?: string; daily_pnl?: number; daily_trades?: number; win_rate?: number; consecutive_losses?: number; cooldown_active?: boolean; heat_level?: string };
type Status = { status: string; mode: string; active_signals: number; active_trades: number; total_trades: number; total_signals?: number; timestamp: string; risk?: Risk };
type Trade = { id?: number; contract_id?: string; signal_type?: string; bias?: string; stake?: number; result_status?: string; env?: string; timestamp?: string; result_pnl?: number };
type Candle = { time: number; open: number; high: number; low: number; close: number };
type DashboardPayload = { status: Status; signals: Signal[]; trades: Trade[]; candles: Candle[]; error?: string };

const empty: DashboardPayload = { status: { status: "connecting", mode: "DEMO", active_signals: 0, active_trades: 0, total_trades: 0, timestamp: "" }, signals: [], trades: [], candles: [] };
const api = (path: string) => `/api/backend/${path}`;

export default function Dashboard() {
  const [data, setData] = useState<DashboardPayload>(empty);
  const [symbol, setSymbol] = useState("R_100");
  const [loading, setLoading] = useState(true);
  const refresh = useCallback(async () => {
    try {
      const [statusRes, signalsRes, tradesRes, candlesRes] = await Promise.all([
        fetch(api("status"), { cache: "no-store" }), fetch(api("signals?limit=100"), { cache: "no-store" }),
        fetch(api("trades?limit=100"), { cache: "no-store" }), fetch(api(`market/candles?symbol=${encodeURIComponent(symbol)}&tf=5&count=300`), { cache: "no-store" }),
      ]);
      if (!statusRes.ok || !signalsRes.ok || !tradesRes.ok) throw new Error("Backend dashboard API is unavailable");
      const [status, signals, trades] = await Promise.all([statusRes.json(), signalsRes.json(), tradesRes.json()]);
      const candles = candlesRes.ok ? await candlesRes.json() : [];
      setData({ status, signals, trades, candles: Array.isArray(candles) ? candles : [], error: candlesRes.ok ? undefined : "Market candle feed is not configured" });
    } catch (e) {
      setData(current => ({ ...current, error: e instanceof Error ? e.message : "Unable to connect to backend" }));
    } finally { setLoading(false); }
  }, [symbol]);

  useEffect(() => { void refresh(); const timer = window.setInterval(() => void refresh(), 15000); return () => window.clearInterval(timer); }, [refresh]);
  const latest = data.signals.slice(-8).reverse();
  const mode = data.status.mode || "DEMO";

  return <main className="shell">
    <header className="topbar">
      <a className="brand" href="#"><span className="brand-mark">T</span><span>TRON<span className="muted"> / </span>ADA<small>GLASSBOX TRADING CONSOLE</small></span></a>
      <div className="top-actions"><span className={`connection ${data.error ? "offline" : "online"}`}><i />{data.error ? "API DISCONNECTED" : "SYSTEM CONNECTED"}</span><span className="mode-badge">{mode} ACCOUNT</span><button className="icon-button" title="Refresh dashboard" onClick={() => void refresh()}>↻</button></div>
    </header>
    <section className="intro"><div><div className="eyebrow">CONTROL ROOM <span>—</span> {new Date().toLocaleDateString(undefined, { weekday: "short", day: "2-digit", month: "short", year: "numeric" })}</div><h1>Signal intelligence<span className="accent">, in full view.</span></h1><p>TRON detects. Absolute Dollar Agent classifies, explains, and guards every execution.</p></div><label className="symbol-picker">MARKET<select value={symbol} onChange={e => setSymbol(e.target.value)}><option>R_100</option><option>R_75</option><option>R_50</option><option>R_25</option><option>R_10</option></select></label></section>
    {data.error && <div className="notice"><strong>Connection notice</strong><span>{data.error}. This console never fabricates market or account data.</span></div>}
    <section className="metrics" aria-label="Account overview">
      <Metric label="SESSION STATUS" value={data.status.status.toUpperCase()} detail={loading ? "Connecting to API…" : "Backend heartbeat"} icon="◉" />
      <Metric label="OPEN POSITIONS" value={String(data.status.active_trades)} detail="Persisted unsettled trades" icon="⌁" />
      <Metric label="SIGNALS RECEIVED" value={String(data.status.total_signals ?? data.signals.length)} detail="Persisted TRON events" icon="⌖" />
      <Metric label="TRADING MODE" value={mode} detail={mode === "DEMO" ? "Deriv demo account" : "Real account · gated"} icon="◇" />
    </section>
    <section className="workbench">
      <div className="panel chart-panel"><div className="panel-head"><div><div className="eyebrow">PRICE ACTION</div><h2>{symbol}<span className="timeframe"> · 5m</span></h2></div><span className="chart-note">TRON signal markers · closed-bar events</span></div>
        <div className="chart-frame">{data.candles.length ? <PriceChart candles={data.candles} signals={data.signals.filter(s => s.symbol === symbol)} /> : <div className="chart-empty"><div className="empty-glyph">⌁</div><strong>Waiting for market candles</strong><span>Market history is fetched from Deriv's public feed. Provider errors are shown above; no sample values are used.</span></div>}</div>
        <div className="legend"><span><i className="bull-dot"/> CALL signal</span><span><i className="bear-dot"/> PUT signal</span><span className="chart-footnote">Markers are sourced from accepted TRON webhook events.</span></div>
      </div>
      <aside className="panel risk-panel"><div className="panel-head"><div><div className="eyebrow">SAFETY LAYER</div><h2>Risk governor</h2></div><span className="status-pill">{mode}</span></div>
        <div className="risk-summary"><span className="risk-orb">⌑</span><div><strong>{data.status.risk?.state ?? "Risk state unavailable"}</strong><small>Live state from the Python risk governor.</small></div></div>
        <RiskRow label="Manual approval" value="Required" good /><RiskRow label="Auto-execution" value="Backend controlled" /><RiskRow label="Daily P&L" value={data.status.risk?.daily_pnl == null ? "—" : `$${data.status.risk.daily_pnl.toFixed(2)}`} /><RiskRow label="Loss cooldown" value={data.status.risk?.cooldown_active ? "Active" : "Inactive"} /><RiskRow label="Heat" value={data.status.risk?.heat_level ?? "—"} /><div className="risk-disclaimer">Trading involves risk. Verify account mode, stake limits, and broker details before placing an order.</div>
        <button className="disabled-action" disabled title="Execution actions require authenticated, audited backend controls">WEB EXECUTION NOT ENABLED <span>↗</span></button>
      </aside>
    </section>
    <section className="lower-grid">
      <div className="panel signal-panel"><div className="panel-head"><div><div className="eyebrow">INCOMING INTELLIGENCE</div><h2>Recent TRON signals</h2></div><span className="count-badge">{data.signals.length} loaded</span></div>
        {latest.length ? <div className="table-wrap"><table><thead><tr><th>SIGNAL</th><th>MARKET</th><th>CONFIDENCE</th><th>SYNC</th><th>SPOT</th><th>TIME</th></tr></thead><tbody>{latest.map((s, i) => <tr key={String(s.id ?? `${s.time}-${i}`)}><td><span className={`direction-tag ${s.bias.toLowerCase()}`}>{s.bias}</span><strong>{s.signal}</strong></td><td>{s.symbol}<small>{s.tf}m</small></td><td><span className="confidence">{s.confidence}%</span></td><td>{s.fractal?.sync_layers ?? "—"}/4</td><td>{Number(s.spot).toLocaleString(undefined, { maximumFractionDigits: 2 })}</td><td>{s.received_at ? new Date(s.received_at).toLocaleTimeString() : "—"}</td></tr>)}</tbody></table></div> : <EmptyState title="No signal events yet" detail="Accepted webhook signals will appear here. Configure TradingView to POST to the TRON webhook." />}
      </div>
      <div className="panel positions-panel"><div className="panel-head"><div><div className="eyebrow">DERIV EXECUTION LEDGER</div><h2>Recent positions</h2></div><span className="count-badge">{data.trades.length}</span></div>
        {data.trades.length ? <div className="position-list">{data.trades.slice(-6).reverse().map((t, i) => <div className="position-row" key={`${t.contract_id ?? t.id ?? "trade"}-${i}`}><div className="position-symbol"><span className="position-icon">↗</span><div><strong>{t.signal_type ?? "Contract"}</strong><small>{t.contract_id ? `#${t.contract_id}` : "Contract ID unavailable"}</small></div></div><div className="position-meta"><strong>${Number(t.stake ?? 0).toFixed(2)}</strong><small>{t.env ?? mode} · {t.result_status ?? "PENDING"}</small></div></div>)}</div> : <EmptyState title="No executed positions" detail="Position state will populate after an order is confirmed and persisted." />}
      </div>
    </section>
    <footer><span>ABSOLUTE DOLLAR AGENT <b>·</b> GLASSBOX BY DESIGN</span><span>TRON signals only · no independent signal generation</span></footer>
  </main>;
}
function Metric({ label, value, detail, icon }: { label: string; value: string; detail: string; icon: string }) { return <article className="metric"><div className="metric-top"><span>{label}</span><i>{icon}</i></div><strong>{value}</strong><small>{detail}</small></article>; }
function RiskRow({ label, value, good = false }: { label: string; value: string; good?: boolean }) { return <div className="risk-row"><span>{label}</span><strong className={good ? "good" : ""}>{value}</strong></div>; }
function EmptyState({ title, detail }: { title: string; detail: string }) { return <div className="empty-state"><span className="empty-glyph">◌</span><strong>{title}</strong><small>{detail}</small></div>; }
