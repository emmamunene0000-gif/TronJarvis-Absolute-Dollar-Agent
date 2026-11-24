## Stage 1 — live data and durable dashboard read models

- Added a bounded, public Deriv historical-candle adapter (no trading token is sent) and a validated candle API at `/api/market/candles`.
- Replaced dashboard API's process-local signal/trade view with SQLite-backed signal and trade reads, and exposed the current risk state.
- Updated the Next.js chart to consume the candle endpoint, map TRON millisecond timestamps to candle seconds, and skip markers that cannot be aligned to available bars. UI refresh is throttled to 15 seconds to avoid excessive market-data requests.
- Execution remains disabled in the web UI. Authenticated order APIs, real balance validation, persistent order events, settlement reconciliation, and Paper mode are subsequent stages; no claim of completion is made yet.

Verify locally:

```bash
cd absolute_dollar_agent
pip install -r requirements.txt
pytest -q
cd ../web
npm install
npm run typecheck
npm run build
```
