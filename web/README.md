# TRONJarvis Web Console

An App Router UI for the TRON / Absolute Dollar Agent stack. The existing Python service remains authoritative for signal validation, risk checks, the trade ledger, and execution. This UI is a read-only console in this first phase; execution controls stay locked until authenticated API execution and reconciliation are implemented and tested.

## Run locally

```bash
cd web
npm install
cp .env.example .env.local
npm run dev
```

The web app proxies `/api/backend/*` to `BACKEND_ORIGIN` (default `http://127.0.0.1:8080`). Run the Python service separately using `absolute_dollar_agent/README.md`.

## Chart data contract

The chart component accepts OHLC candles and overlays markers from TRON signal timestamps. The backend currently has no market-candle endpoint, so it displays an explicit unavailable state rather than invented/sample prices. Wire a Deriv market-data provider into `/api/market/candles` before enabling chart candles or marker placement. Signals require timestamps aligned to the candle timeframe.

## Safety

This frontend does not contain broker credentials and does not submit orders. Do not expose Deriv tokens in browser code. Do not enable live execution until order confirmation, authenticated operator controls, balance verification, durable settlement reconciliation, and duplicate-request protection are all in place.
