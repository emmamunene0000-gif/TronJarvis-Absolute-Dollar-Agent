# System Diagnostic — TRON / JARVIS

**Date:** 03 Jul 2026
**Purpose:** One document to read cold — what existed before this build session, what's actually live now, every bug that got found and fixed along the way, and what's genuinely left. Written so a future session (or a human) doesn't have to re-derive any of this from scratch.

---

## 1. What We Had

- One live Pine Script (`TRON_Glassbox_SignalGenerator.pine`, v4.0) — a single-asset, single-chart glassbox detection engine. Five-layer chain: TRIGGER → GATE → CONFLUENCE → CONFIDENCE → EXECUTION. Confirmed live and firing correctly on Volatility indices via screenshots throughout this session (CALL/PUT entries, trail flips, TP hits, PnL tracker).
- Alerts were **Telegram-native prose** — `tronAlert()` built a 20-line human-readable string. No machine-readable payload existed despite a code comment claiming "clean JSON signals."
- No execution layer at all. No Jarvis. Signals only ever reached a human via Telegram, manually acted on.
- Five redundant/legacy Pine files cluttering the repo, plus TradeSgnl/MQL5-era documents from an earlier, abandoned execution approach.

## 2. What We Built This Session

### Repo cleanup
Consolidated to one Pine Script, deleted four superseded versions and all TradeSgnl/MQL5-era legacy files. Root `README.md` and `TRON_JARVIS/README.md` rewritten to describe the system as it actually is, not as it was.

### TRON → JSON
`tronAlert()` (prose) replaced with `tronJSON()` (STEP 17), emitting a structured payload (`engine: TRON_GBX_v3`) carrying the full architecture state — fractal sync, confidence, structure/VWAP/fib/VP, setup math — on every signal. Humans no longer read raw TRON output directly; Jarvis is the only voice they hear now.

### JARVIS — built from nothing to a working execution twin
`jarvis/` — FastAPI server with:
- `parser.py` — validates TRON's JSON, classifies every signal into **EXECUTE** (tap-to-trade card) / **CONTEXT** (informational) / **NOISE** (ledger only, never spoken)
- `governor.py` — the risk constitution: stake cap → daily loss cap → max concurrent → auto-only gates (flag, signal whitelist, confidence floor ≥80%). Every refusal is logged and spoken.
- `voice.py` — Jarvis's plain-text signal cards, trade receipts, refusals, boot banner
- `deriv.py` — the Deriv execution client (see §4 — this went through a real architecture pivot mid-session)
- `telegram_bot.py` — tap-to-trade inline buttons for the operator, buttonless broadcast copy for the channel
- `db.py` — SQLite ledger: every signal, every trade, every governor veto
- `main.py` — the FastAPI spine: `POST /webhook/tron`, `GET /ledger/signals`, `GET /ledger/trades`

### Deployment
Live on Replit. `.replit` configured for a **Reserved VM** deployment (not Autoscale — Jarvis's Telegram polling loop and in-memory tap queue need a process that never spins to zero).

---

## 3. Bugs Found and Fixed, In Order

Documenting these because each one taught something that matters for next time:

1. **Pine compile error (CE10156)** — the JSON emitter's multi-line string concatenation (nested nested indentation, trailing `+` continuation) isn't valid Pine syntax. Apparently never actually compiled on TradingView before landing in the repo. Fixed by rebuilding it the way the original working `tronAlert()` was written: one JSON fragment per single-line string variable, concatenated on one final line.
2. **`.replit` missing a top-level `run` key** — the `[deployment]` block only applies when you click Publish. The interactive **Run** button needs its own `run =` line, which was missing, so Replit fell back to a bare `python jarvis/app/main.py` with no install step and no uvicorn → `ModuleNotFoundError: fastapi`.
3. **Stale Shell environment variables** — Replit shells snapshot Secrets at the moment they're opened. Every time a Secret changed, the already-open Shell kept using the old value. Cost significant time until isolated via `echo $VAR`. Lesson now baked into `jarvis/README.md`: always open a fresh Shell after changing a Secret.
4. **Wrong `DERIV_APP_ID` format** — `33ITk8ZVRVFVdr0pKmZ3z` (the OAuth-style id from the "App Builder" registration) caused an HTTP 401 at the WebSocket handshake when used the old legacy way. Swapping to the shared demo id `1089` got past the handshake, which is what exposed bug #5.
5. **The real root cause: Deriv retired the legacy API for this account.** `GET /trading/v1/options/legacy/migration-status` returned `"complete"`. Every `pat_` token — three different ones tested, both demo and real — failed `InvalidToken` against `wss://ws.derivws.com/websockets/v3` regardless of token or app_id, because that entire endpoint no longer authenticates for a migrated account. Confirmed independently via Deriv's own API Playground (same token, same rejection). This wasn't a bug in anything we wrote — the ground shifted under the integration mid-build.
6. **`"symbol"` vs `"underlying_symbol"`** — developers.deriv.com's own example for the Bulk Purchase endpoint shows `"symbol"` in `contract_parameters`; the live backend rejects it with `unknown field "symbol"` and wants `"underlying_symbol"` like the rest of the new API. Docs were wrong; fixed against the real error message from a live test call.
7. **Missing Secrets after a Replit session gap** — all Configurations values disappeared between sessions (cause unconfirmed — possibly a Replit-side reset tied to Configurations specifically, since they behave differently from Secrets). Rebuilt from records kept in this conversation; one demo token had to be regenerated since only its last 6 characters were ever recorded (by design, to avoid full exposure in chat).

---

## 4. The Deriv Integration — Current State and the Real Trade-off

Deriv's **legacy WebSocket API is dead for this account.** The **new API** has two paths:

| | OAuth2 + PKCE (full API) | Bulk Purchase REST (fast path — **what's live now**) |
|---|---|---|
| Auth | Interactive browser login → access token → OTP → WS URL | Personal Access Token, directly in the request body |
| Live quote before buy | Yes (`proposal` before `buy`) | No — direct buy only |
| Balance / portfolio check | Yes | No |
| Settlement watching (WIN/LOSS receipts) | Yes (`proposal_open_contract`, subscribable) | No — `_watch_contract` now sends one "can't track this yet" note and stops, instead of retrying 240 times against a call that can never succeed |
| Setup cost | Real: PKCE flow, callback route, token storage + refresh | Already done |

Jarvis ships today on the fast path. It can **buy** vanilla/rise-fall/multiplier contracts correctly (confirmed working after the `underlying_symbol` fix — verify one live test before trusting it unsupervised). It **cannot** check balance, get a quote first, or tell you WIN/LOSS without you checking the Deriv app yourself. Building the OAuth path is real work, tracked as **Phase 1.5** below.

---

## 5. What's Next — Priority Order

### 🔴 Watchlist / multi-asset scanning — flagged as key, elevated to top priority

**What it is:** today, Jarvis only ever reacts to whatever single chart TRON happens to be loaded on in TradingView. To have Jarvis "hunting" across a full watchlist (Volatility 10/25/75, Step Index, XAUUSD, GBPUSD, crypto perps — the "Red list" from the TradingView screenshots) the way NexTrader's UI implies, TRON's detection logic needs to run **server-side, independently, per symbol** — not just wait for whatever one TradingView chart happens to be open.

**Why it's genuinely hard, not just a config change:**
- TRON's edge is its Pine math — MTF trail, market structure, RSI momentum, VWAP regime, fib bands, volume profile, confidence scoring — all of it. To scan N symbols at once, that math has to exist a second time, in Python, running against Deriv's own candle/tick feed (`ticks_history`, `active_symbols`) instead of TradingView's.
- Two implementations of the same logic drift apart over time unless one is very deliberately kept in lockstep with the other. This is the real cost — not the code volume, the *maintenance discipline*.
- Per-symbol state (trail values, regime history, dedup) needs to live somewhere durable across restarts — the current SQLite ledger structure would need a companion table for this, separate from the signals/trades tables that exist today.
- API budget: Deriv's REST rate limit is 60 req/min per token — scanning many symbols on a tight loop needs to respect that, not poll-storm it.

**Recommended shape, when it's built:** a new module (e.g. `jarvis/app/watchlist.py`) that runs on a schedule (every N seconds per symbol), re-derives just the *entry-critical* subset of TRON's logic (trail direction, confidence score — not necessarily every visual/dashboard element), and feeds anything that crosses threshold into the **same** `parse → classify → route` pipeline Jarvis already has. Governor, Telegram, and the ledger don't need to change at all — they're already symbol-agnostic. Start with 2–3 symbols to prove the parity holds before widening to the full list.

**This is a real build, not a config flip — plan a dedicated session for it.**

### 🟠 Phase 1.5 — Deriv OAuth2 + PKCE (full API parity)
PKCE login flow + `/oauth/callback` route (redirect_uri already registered on the Deriv app) → token storage/refresh → swap `deriv.py` back to the OTP-authenticated WS flow for quotes, balance, and settlement watching.

### 🟡 Phase 2 — Jarvis's voice, deepened
- LLM-authored reasoning (Claude) in place of the deterministic templates in `voice.py` — including replacing the blank "Operator remarks" field (currently meant for the human to fill in by hand) with Jarvis's own generated commentary, grounded in TRON's real signal data. Explicitly deferred by you this session — noted here so it isn't lost.
- Telegram formatting pass — emojis are compatible with the current plain-text design (they're not markup), full Markdown/HTML is not (breaks the "reposts cleanly everywhere" guarantee) — a careful pass, not a rewrite.
- Telegram Mini App as the commercial skin, sitting on the `/ledger/signals` and `/ledger/trades` read API that already exists.

---

## 6. Before Trusting This Unsupervised

1. Confirm one real successful trade after the `underlying_symbol` fix (this was the immediate next step when this document was written).
2. Confirm the Replit app is on an actual **Reserved VM Deployment**, not just a Shell session — Shell sessions die when the browser tab closes.
3. Confirm the TradingView alert webhook points at the deployed `https://<name>.replit.app` URL, not `localhost`.
4. `STAKE_DEFAULT` and `AUTO_TRADE` are your call — the whitelist (`H4_FLIP_CALL/PUT`, `SNIPER_CALL/PUT`, ≥80% confidence) plus the daily loss cap are the existing safety rails regardless of what you set.
