## Web app foundation

A Next.js App Router dashboard is being developed under `web/`. It currently consumes the existing Python status, signal, and trade endpoints through a rewrite proxy and presents explicit empty states when the backend or market candle provider is unavailable. The chart renderer is wired for real OHLC candles plus signal markers; no sample market data is shown.

Execution controls remain disabled in the web client. Backend authentication, demo order confirmation, persistent order reconciliation, and settlement data must be completed and tested before enabling an order UI. The Pine Script remains the signal source of truth while any PineTS migration is validated for parity.

Start the frontend with `cd web && npm install && npm run dev`; run the Python backend separately as documented in `absolute_dollar_agent/README.md`.
