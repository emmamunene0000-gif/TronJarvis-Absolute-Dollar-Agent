## Complete web app runtime

The FastAPI process now owns the `AbsoluteDollarAgent` runtime, initializes SQLite, attaches it to `app.state.agent`, serves the webhook and `/api` routes, and starts paper/execution reconciliation.

Paper mode has no broker access. Deriv demo/live execution remains governed by environment flags, operator API key, risk governor, and the 100 settled demo-trade gate. The UI must send an `Idempotency-Key` header for order requests.
