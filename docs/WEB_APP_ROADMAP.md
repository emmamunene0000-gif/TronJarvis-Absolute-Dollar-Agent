## Current build status

The web-console branch includes a Next.js dashboard foundation, Deriv historical candles, SQLite-backed signal/trade read models, and early operator-request/paper abstractions. The following items are **not yet production-complete**: end-to-end authenticated order controls, real Deriv balance verification, reliable settlement/restart reconciliation, a persistent paper ledger, complete front-end controls/tests, and verified CI/deployment. Do not enable unattended or live execution based on the dashboard scaffold alone.

The original signal doctrine remains authoritative: TRON emits signals; the application may classify, explain, size and execute them but must not synthesize signals.
