# ADA — Absolute Dollar Agent (a.k.a. TradersMind) — Master Build Spec for Claude Code

**Version:** July 4th ClaudeMD (2026-07-04)
**Status:** Single reconciled source of truth for this repo. Read in full before writing code in `tron/`, `mind/`, `bridge/`, `governor/`, `body/`, or `face/`. See the repo-verification note appended at the end of this file for what has already been checked against the codebase as of this date.

**Working name:** ADA / TradersMind — "Just a Really Very Intelligent Sidekick."
**What this document is:** the single reconciled source of truth, merging the doctrine/architecture brief with the project README. It replaces both. Before writing any code, **verify this document against whatever already exists in the repo** — confirm what's actually built vs. what's spec-only, and flag any mismatch instead of silently building around it.

Every claim below is one of three things: a **fact** (from TRON's Pine source), a **locked decision** (from the operator), or a flagged **open decision**. Don't blur those categories, don't invent a fourth, and don't add features not named here.

---

## 0. Message to the engineer (you)

You're being handed a fully mapped trading system. The brain (TRON, Pine Script v3.0) is finished. Your job is to build its execution arm and its home: a backend that receives TRON's signals, a glassbox interactive interface where the operator watches TRON think, and a bridge that fires trades on Deriv.

**This is not a black-box AI trading bot.** Every pixel on screen must be explainable by a named TRON field. If you can't point to the JSON field that justified something on screen, it shouldn't be there.

**This is an MVP going live this week, on free-tier infrastructure, with real demo-account execution from day one.** There is no paper-trading mode in this build — remove any assumption of one. The safety gate is a **demo-account trade count**, not a paper-simulation layer (see §10). Replit and Deriv affiliate upgrades happen after this week's deployment, not before.

Read the whole spec before writing code. Where it says "locked," build exactly that. Where it says "open decision," stop and ask.

---

## 1. Architecture — One Diagram, One Line

```
TRON (TradingView, Pine Script) → Webhook → ADA Backend (Replit)
                                                    │
    ┌───────────────┬───────────────┬───────────────┴───────────────┐
    ▼               ▼               ▼                               ▼
 Webhook          Episodic       Narrative                    RiskGovernor
 Receiver         Memory         Engine                       (sizing + limits)
 (tron/)          (mind/)        (mind/, zero LLM)             (governor/)
    │               │               │                               │
    └───────────────┴───────┬───────┴───────────────────────────────┘
                             ▼
                      Deriv Bridge (bridge/)
                      persistent WebSocket
                             │
                     ┌───────┴───────┐
                     ▼               ▼
              Telegram (body/)   Web App / Face (face/)
              tap-to-execute     chart + console + risk panel
```

**TRON = Brain.** Instinct, math, pure detection. Stateless. Never modified by this build.
**ADA/TradersMind = Sidekick.** Reason, memory, narrative, execution. Waits for TRON, then acts.
**RiskGovernor = the part whose business is making money**, not just enforcing limits.

> "TRON is TRON." The Sidekick never invents, re-scores, or overrides a signal — it classifies, narrates, sizes, and (if authorized) executes.

---

## 2. Doctrine — Non-Negotiable Engineering Constraints

1. **The Sidekick never invents a signal.** All trade triggers originate from TRON's webhook. No independent technical analysis in the backend.
2. **Not "my Jarvis" — TRON's Jarvis.** The backend is an execution arm, not a second opinion.
3. **Load on the pair, then wait.** The agent is instantiated per traded pair and does nothing until a TRON webhook arrives for that pair.
4. **Glass box, not black box.** Every action traces to a named TRON factor (`sync_layers=4`, `vwap=BULL`, `confidence=86`). No opaque "AI decided" messaging anywhere.
5. **Operator sets risk, RiskGovernor does the rest.** The operator picks a risk profile once; sizing and guardrails run autonomously from there.
6. **RiskGovernor sizes for edge — it is not a generic limit-checker.** Its job is to make money within hard limits, not just say no.
7. **Silence is a valid position.** No TRON trigger = no trade. Narrate this as an active "waiting for TRON" state, never as a bug.
8. **Two trust levels, one engine.** TAP (decision-support) and AUTO (autonomous) share the same pipeline and differ only at the execution gate.

---

## 3. Verification Checklist — What We Have vs. What We Need vs. Cost

**Claude Code: confirm each "HAVE" line actually exists in the repo/environment before assuming it. Confirm each "NEED" line is genuinely missing before building it again.**

### ✓ HAVE (assets in hand today)
- TRON GLASSBOX v3.0 (Pine Script) — complete, emits 18-type JSON webhook on bar close. **Do not modify its detection logic.**
- Webhook emitter already inside TRON — the Brain→Sidekick contract already exists (§6). Build the receiver to match it, not the reverse.
- TradingView Premium — paid, required tier for `alert()`-based webhooks.
- Replit account — **free tier only**, no paid plan yet.
- Deriv account — **demo account**, no live money yet.
- Telegram channel — companion broadcast surface, not the primary UI.
- This document — the locked architecture doctrine.

### ⬚ NEED (to build)
- ADA backend on Replit (FastAPI): webhook receiver, parser/classifier, narrator, episodic memory, RiskGovernor, signal router, Deriv bridge.
- Web app face: chart-centric UI with TRON's signals overlaid on price, console, signal stream, risk panel.
- Deriv WebSocket bridge: demo-account connection, contract mapping, order placement, live P&L streaming, reconnect/resync logic (no Reserved VM yet — see §12).
- Signal Router: signal-type → contract-style, per operator-enabled trading styles.
- Episodic Memory DB (SQLite) + KNN similarity search. LightGBM edge model comes later, once ~50–70 episodes are logged.
- Telegram companion: tap-to-trade stream (TAP mode) + executed-trade alerts (AUTO mode).

### $ Cost Map

**This week (MVP launch):**

| Item | Cost |
|---|---|
| TradingView Premium | Paid (sunk) |
| Replit | Free tier |
| Deriv API | Free (demo account) |
| Telegram Bot | Free |
| SQLite + LightGBM | Free (open-source) |
| Narrative engine | $0 — template-based, zero LLM |
| **MVP recurring total** | **$0** beyond the sunk TradingView subscription |

**After launch (once Replit + Deriv affiliate relationships are active):**

| Item | Cost |
|---|---|
| Replit Core | ~$20–25/mo |
| Replit Reserved VM (24/7 socket) | ~$10–25/mo |
| Domain | ~$10–15/yr |
| **Post-launch realistic recurring** | **~$32–50/mo + ~$12/yr domain**, offset by affiliate revenue |

---

## 4. Repo Layers

| Layer | Folder | Purpose |
|---|---|---|
| **TRON** | `tron/` | Models, payload validator, webhook receiver |
| **Mind** | `mind/` | SQLite episodic memory, narrative engine, KNN similarity |
| **Bridge** | `bridge/` | Deriv WebSocket client, contract mapper, reconnect/resync logic |
| **Governor** | `governor/` | Risk rules, stake sizing, cooldowns, limits |
| **Body** | `body/` | Telegram bot, signal cards, tap-to-execute |
| **Face** | `face/` | Web app: chart, console, signal stream, risk panel |

---

## 5. Configuration (`.env`)

```env
TRADING_MODE=demo           # demo | live — NO paper mode
AUTO_EXECUTE=false          # requires demo-trade gate (§10) before flipping true
WEBHOOK_SECRET=your_secret
TELEGRAM_BOT_TOKEN=your_token
TELEGRAM_CHAT_ID=your_chat_id
DERIV_APP_ID=your_app_id
DERIV_API_TOKEN=your_demo_token
```

`TRADING_MODE` has exactly two values: `demo` and `live`. There is no `paper` value and no paper-simulation code path — every trade, from day one, is a real order against the Deriv demo account's virtual balance. Do not build a simulated fill engine.

---

## 6. The Webhook Contract — Authoritative, Do Not Deviate

The *only* interface between TRON and ADA. Build the receiver to this schema exactly (`schema: 1`):

```json
{
  "engine": "TRON_GBX_v3",
  "schema": 1,
  "signal": "H4_FLIP_CALL",
  "bias": "CALL",
  "mode": "vanilla",
  "symbol": "R_100",
  "tf": "5",
  "time": 1735900000000,
  "spot": 4908.12,
  "confidence": 86,
  "conf_bull": 86,
  "conf_bear": 14,
  "fractal": {
    "h4": "BULL", "h1": "BULL", "m15": "BULL", "m5": "BULL",
    "sync_layers": 4, "quality": "SOVEREIGN"
  },
  "core": {
    "structure": "BULL_BOS", "vwap": "BULL", "fib": "BULL",
    "vp": "ABOVE VAH", "rsi": 62.3, "spatial": "KEY_LEVEL"
  },
  "setup": {
    "strike": 4908.12, "strike_mode": "ATM", "expiry_min": 3,
    "sl": 4902.0, "tp1": 4914.0, "tp2": 4920.0, "tp3": 4928.0,
    "rr": 1.5, "atr": 4.1, "iv_proxy": 0.32, "delta": 0.55,
    "regime_strength": 78, "regime_bars": 12
  }
}
```

**Endpoint:** `POST /webhook/tron?key=SECRET`
**TradingView alert config:** Condition = "Any alert() function call", Message = `{{alert_message}}`, Webhook URL = `https://your-replit-url/webhook/tron?key=SECRET`

Implementation notes:
- `mode` is a single global tag from TRON's chart settings — the Router (not TRON) decides per-signal-type routing (§8).
- All alerts fire once per bar close, non-repaint. Act on closed-bar data only, never intrabar.
- Reject anything not matching this schema — don't silently coerce bad payloads.

---

## 7. The 18 Signals — Classification

**Classes:**
- **EXECUTE** — the agent may place a trade if its route-style is enabled.
- **CONTEXT** — never triggers an independent trade. Either raises/lowers confidence on a co-occurring EXECUTE signal, or triggers exit/reduce logic on an open position.
- **NOISE** — dormant/duplicate. Log only.

| Signal(s) | Class | Fires when | Notes |
|---|---|---|---|
| `CALL_ENTRY` / `PUT_ENTRY` | EXECUTE | ATM crossover + trail align + confidence ≥ threshold + not deduped (3-bar window) | Workhorse entry; full strike/SL/TP payload |
| `CALL_CONTINUATION` / `PUT_CONTINUATION` | EXECUTE | Fresh RSI smart-momentum turn + trail align | No confidence gate, no dedup — re-fires as scale-in fuel. RiskGovernor must cap stacking. |
| `H4_FLIP_CALL` / `H4_FLIP_PUT` | EXECUTE (priority 1) | H4 trail flip + trail align | No confidence gate — it IS the gate. Rare, sovereign event. |
| `MTF_FLIP_CALL` / `MTF_FLIP_PUT` | EXECUTE (priority 2) | M15 or H1 flip + trail align + conf pass | Suppressed if H4 flip fired same bar |
| `TRAIL_FLIP_CALL` / `TRAIL_FLIP_PUT` | EXECUTE (priority 3) | Chart trail flip + MTF support + conf pass | Suppressed if H4/MTF flip fired same bar |
| `SNIPER_CALL` / `SNIPER_PUT` | CONTEXT (dormant unless `show_zones` on) | Liquidity-zone retest + trail + conf pass | `show_zones` OFF by default in TRON |
| `CALL_ZONE_BREAK` / `PUT_ZONE_BREAK` | CONTEXT (dormant unless zones on) | Zone break + trail align, no conf gate | Same dormancy caveat |
| `BULL_REGIME_SHIFT` / `BEAR_REGIME_SHIFT` | CONTEXT — primary exit signal | Trail/VWAP/Fib regime turn | Overlaps flips same bar — dedupe: flip = execute, shift = context/exit only |
| `BULL_BOS` / `BEAR_BOS` | CONTEXT — structure confirmation | Break of prior swing high/low with structure agreeing | Confidence modifier only |

---

## 8. Routing Matrix (Locked)

| Trading style | Contract shape | Routed EXECUTE signals |
|---|---|---|
| **Rise/Fall** | direction + expiry | `CALL_CONTINUATION` / `PUT_CONTINUATION`, `TRAIL_FLIP_*` |
| **Vanilla Options** | strike + expiry | `CALL_ENTRY` / `PUT_ENTRY`, `H4_FLIP_*`, `MTF_FLIP_*`, `TRAIL_FLIP_*` |
| **Multipliers** | direction + leverage + SL/TP | `CALL_ENTRY` / `PUT_ENTRY`, `H4_FLIP_*`, `MTF_FLIP_*`, `TRAIL_FLIP_*` |
| **Context (no trade)** | — | `SNIPER_*`, `ZONE_BREAK_*`, `REGIME_SHIFT_*`, `BOS_*` |

Operator enables one or more styles. If a signal's best-fit style is disabled, it drops to a TAP card instead of auto-executing.

**⚠ Open decisions — surface to the operator before wiring, don't resolve silently:**
1. When `CALL_ENTRY`/`PUT_ENTRY` or a flip fits both Vanilla and Multipliers (both enabled) — fixed operator default, or agent picks by conviction (`regime_strength`/confidence)?
2. If Liquidity Zones are later enabled, do `ZONE_BREAK` signals become Rise/Fall executes, or stay CONTEXT permanently?
3. Should `CALL_ENTRY`/`PUT_ENTRY` also be tap-executable to Rise/Fall, or Vanilla+Multipliers only?

---

## 9. Signal Flow — End to End

1. TRON detects a signal on bar close → emits JSON webhook.
2. `tron/` receives, validates against §6's schema, queues it.
3. `mind/` classifies EXECUTE/CONTEXT/NOISE (§7), stores full context in episodic memory, generates a plain-English narrative (§13).
4. `governor/` checks limits (§10) → approves or rejects.
5. If approved: broadcast to Telegram (`body/`) + Web App (`face/`).
6. **TAP mode:** operator taps EXECUTE. **AUTO mode:** fires automatically if it clears the auto-execute gate (§10).
7. `bridge/` maps the signal to a Deriv contract (§8/§11) and fires it — returns a ticket ID and entry price.
8. Live P&L streams to Telegram + Web App.
9. On close: result stored in episodic memory.
10. Next matching signal: memory suggests a stake adjustment based on similar historical setups (once enough episodes exist — §14).

---

## 10. RiskGovernor — Reconciled Rules

The Governor's default sizing law (per doctrine §2.6) and its hard safety ceiling are two different things — they don't conflict, they nest. Build both:

**Sizing law (the Governor's actual behavior):**
- Stake per trade is sized dynamically between **$0.35 and $1.00**, scaled by TRON's grade/confidence and the memory-model's edge signal once available. This is the Governor "doing its job" — sizing for edge, not just picking a flat number.

**Hard limits (never exceeded, regardless of sizing law output):**

| Rule | Default | Override? |
|---|---|---|
| Max stake per trade | $5.00 (hard ceiling above the sizing law) | ❌ No |
| Daily loss limit | $50.00 | ⚠️ Logged override only |
| Max consecutive losses | 3 | ⚠️ Logged override only |
| Cooldown after 2 losses | 5 min | ❌ No |
| Min confidence for AUTO-execute | 85% | ❌ No |
| Min sync layers for AUTO-execute | 4/4 (SOVEREIGN) | ❌ No |
| Max % of balance per trade | 10% | ❌ No |

**Auto-execute gate, explicitly:** a signal only fires automatically in AUTO mode if confidence ≥ 85% **and** `sync_layers` = 4/4. Anything below that threshold drops to a TAP card even with AUTO mode on — it is not auto-fired at a smaller size. This is a hard gate, not a sizing input.

**Demo-trade safety gate (replaces any notion of "paper mode"):** `TRADING_MODE=live` cannot be unlocked until **100 completed demo-account trades** are logged in episodic memory. This is a real-order count against Deriv's demo balance, not a simulated trade count. All manual overrides of any rule above are logged with operator ID and timestamp — never silently bypassed.

Silence (no trade) always comes from TRON not triggering — never from the Governor vetoing a live signal that passed its gates.

---

## 11. Trading Modes

| Mode | Description | Best for |
|---|---|---|
| **Rise/Fall** | Direction + duration only | Quick scalps, high frequency |
| **Vanilla** | Strike + expiry + direction | Defined risk, higher payouts |
| **Multiplier** | Direction + leverage + SL/TP | Trend riding, compound gains |

---

## 12. Backend Modules (map directly to repo layers in §4)

1. **Webhook Receiver** (`tron/`) — validates schema, rejects malformed payloads, queues for processing.
2. **Parser/Classifier** (`tron/` or `mind/`) — sorts each signal per §7.
3. **Narrative Engine** (`mind/`) — template-based, zero LLM (§13).
4. **Signal Router** (`mind/` or its own module) — applies §8's matrix.
5. **Episodic Memory + KNN** (`mind/`) — SQLite ledger, similarity search (§14).
6. **RiskGovernor** (`governor/`) — sizing + hard limits (§10).
7. **Deriv Bridge** (`bridge/`) — persistent WebSocket, contract mapping, order placement, live P&L, **reconnect/resync logic that reconciles against Deriv's actual open-position state on reconnect** (no Reserved VM yet, so this must not silently assume nothing happened mid-drop).
8. **Telegram Body** (`body/`) — tap-to-execute cards, executed-trade alerts.
9. **Web Face** (`face/`) — see §15.

Direct Deriv API only — no third-party XML bots anywhere in the bridge.

---

## 13. Narrative Engine — Zero LLM

Template-based, deterministic. Every word traceable to a TRON JSON field:

> "SOVEREIGN CALL — H4 flipped BULL. All 4 layers aligned. Confidence 87%. Strike 314.50 ATM. Expiry 8m. Similar setups won 72% historically. Risk Governor approves max stake."

No LLM call in this path unless explicitly requested by the operator later.

---

## 14. Episodic Memory

Every trade stores:
- Full TRON context (fractal state, indicators, confidence, `setup` block)
- Execution details (stake, ticket ID, entry price)
- Result (P&L, win/loss, time to resolution)
- Feature vector for KNN similarity search

Supported queries:
- "Find similar setups" → KNN on the indicator feature vector
- "H4 FLIP performance" → filter by signal type
- "Session stats" → group by hour/session
- "Streak detection" → flag unstable regimes

LightGBM edge model trains on this ledger once ~50–70 episodes exist. Output is a **risk adjustment suggestion only** ("this setup won 70% last time → size up" / "lost 3/5 → lower multiplier") — it never generates a new signal.

---

## 15. Web App — ADA's Own Interactive Home for TRON

Not a signal card-feed with a chart bolted on — the chart is the home screen, and the console, signal stream, and risk panel live around it.

- **The chart is the centerpiece.** Renders from the Deriv tick stream and overlays TRON's signal markers directly on price — flips, entries, regime shifts, SL/TP levels. One canvas showing price action and TRON's reasoning together. A card feed with no chart underneath does not satisfy this spec.
- **Mode switch:** TAP vs AUTO, same engine underneath.
- **Instrument loader:** load the agent onto the traded pair; explicit "awaiting TRON" idle state until a signal lands.
- **Signal stream (TAP mode):** live cards docked alongside the chart — type, bias, confidence %, fractal N/4, strike/expiry/RR, narrative. Actions: `[TAP EXECUTE]` `[WHY?]` `[HISTORY]`. Each card traceable to its chart marker.
- **Auto Trader:** TRON triggers → Governor clears the gate (§10) → **the agent places the trade** → shows as an executed alert.
- **Conversational glass-box log:** narrates TRON's reasoning in real time; answers "why?", "find similar", "how am I doing?"
- **Live console:** open tickets, live P&L, time-to-expiry, SL/TP distance, manual close, ~1s refresh.
- **Dashboard:** today's P&L, win-rate by signal type, session insight from memory.
- **Risk control panel:** risk profile, default stake range, TAP/AUTO toggle, loss limit, win targets, Deriv account link, live demo-trade counter toward the 100-trade gate.

---

## 16. Deriv Integration

- **Markets:** Volatility Indices (10/25/50/75/100, incl. 1s variants, 24/7), Step Indices, Crash/Boom, Jump, and related synthetic families.
- **Contract types:** Rise/Fall, Multipliers, Vanilla Options — one WebSocket covers all three.
- **Honest technical flag:** synthetics have no order book, so technical patterns are "coincidental" per Deriv's own docs (except Range Break). TRON's price-based layers are unaffected; its volume-derived layers (Volume Profile, VWAP) lean on synthetic volume — a weighting note for the edge model, not a reason to change TRON.
- **Rollout:** demo account first — verify buy execution, P&L math, sub-500ms execution for all three contract types. Live money and affiliate-attributed OAuth come after this week's MVP is proven, not as part of this build.

---

## 17. Build Sequence

- **A.** Deriv WebSocket bridge against the demo account — prove buy + live P&L for Rise/Fall, Multiplier, Vanilla.
- **B.** Webhook receiver + parser — ingest real TRON JSON, classify EXECUTE/CONTEXT/NOISE.
- **C.** RiskGovernor v0 (sizing + hard limits) + manual TAP execution end-to-end.
- **D.** Web app v0 — chart with TRON overlays, instrument loader, signal stream, live console.
- **E.** Episodic memory logging — start banking toward the 50–70 episodes the edge model needs, and toward the 100-trade live-mode gate.
- **F.** AUTO mode + Telegram companion stream.
- **G.** LightGBM edge model once the ledger is deep enough — last brick, not first.

**Definition of done for Phase A:** a working demo-account flow that places a trade of each contract type, confirms the ticket, and streams live P&L to a bare console — before any UI polish.

**Roadmap beyond MVP:** live Deriv execution hardening → LightGBM predictive module → multi-pair agent loader → Telegram Mini App (native buttons, no webview).

---

## 18. Guardrails for the Build Itself

- Never modify TRON's Pine logic — it's a locked external dependency.
- Never add a signal type not listed in §7.
- No LLM in the narrator unless explicitly requested later.
- No XML bots or third-party trade automation layers — Deriv API direct only.
- No paper-trading mode, no simulated fill engine — demo account only, real orders, real virtual balance.
- Treat the §8 open decisions as blocking — ask before wiring that part of the router.
- Every trade must be traceable, in the UI, to the exact TRON field(s) that caused it.
- Every manual override of a RiskGovernor rule must be logged, never silent.

---

## 19. Quick Start

```bash
git clone <repo>
cd tradersmind
pip install -r requirements.txt
cp .env.example .env
# edit .env per §5
python main.py
```

Connect TRON (TradingView alert): Webhook URL `https://your-replit-url/webhook/tron?key=SECRET`, Message `{{alert_message}}`.

---

## License

MIT.

**TRON detects. TradersMind executes. Governor protects.**

---

## 20. Repo-Verification Note (added 2026-07-04, do not treat as spec — treat as findings)

This section is not part of the locked doctrine above. It is the record of comparing §0–§19 against the actual code in this repo as of 2026-07-04, per §0's instruction to verify before building. Read it before touching `tradersmind/` or `jarvis/`.

**The repo currently contains two parallel, non-identical implementations, and neither one matches this spec exactly:**

1. **`jarvis/`** — the deployed system. Flat `app/` layout (not the `tron/mind/bridge/governor/body/face` layering in §4). Already live on Replit (Reserved VM per `.replit`), already executes real Deriv demo trades via the Bulk Purchase REST fast path (`jarvis/app/deriv.py`), already has a working EXECUTE/CONTEXT/NOISE classifier (`jarvis/app/parser.py`), Telegram tap-to-trade, and a SQLite ledger. No paper mode anywhere. No web face/chart UI at all (Telegram-only). Its Deriv integration is REST bulk-purchase, not the persistent WebSocket bridge §1/§12 call for, because Deriv retired the legacy WebSocket API for this account (documented in `SYSTEM_DIAGNOSTIC.md` §4).

2. **`tradersmind/`** — a separate, newly-added scaffold matching this spec's exact folder names (`tron/`, `mind/`, `bridge/`, `governor/`, `body/`, `face/`) and matching its narrative templates and risk defaults almost verbatim. Not deployed (no `.replit` entry, `.replit` still points at `jarvis/`). Has a real web dashboard (`face/`) that `jarvis/` lacks. But it diverges from this spec in ways that need an explicit decision before either building on it or discarding it in favor of `jarvis/`:
   - **Paper mode is baked in throughout** (`main.py`, `bridge/deriv_client.py`, `face/app.py`, `body/telegram_bot.py`, its own `README.md`) — `TRADING_MODE` defaults to `"paper"` and every buy method has a paper branch. §5/§18 explicitly forbid this.
   - **No signal classifier or router exists.** `main.py`'s `_process_signal` runs every incoming signal — including CONTEXT-class ones (`SNIPER_*`, `*_ZONE_BREAK`, `*_REGIME_SHIFT`, `*_BOS`) — through the same risk-check → auto-execute path as EXECUTE signals. §7's EXECUTE/CONTEXT/NOISE split and §8's Routing Matrix are not implemented anywhere in this tree.
   - **`bridge/deriv_client.py` targets the legacy WebSocket endpoint** (`wss://ws.derivws.com/websockets/v3`, `authorize`/`proposal`/`buy` messages) that `SYSTEM_DIAGNOSTIC.md` confirms is dead for this Deriv account. Its "real execution" branches are stubs (`# Would extract from proposal response`, returns `{"status": "pending"}"`) — none of the three contract-buy methods would actually complete a trade against this account today.
   - **Governor sizing law doesn't match §10.** `governor/risk_engine.py` sizes from a flat `max_stake` ($5 default) adjusted ±20–25% by same-day win rate — not the $0.35–$1.00 confidence/edge-scaled law §10 specifies. The $5/$50/3-loss/5-min-cooldown/85%/4-of-4/10%-of-balance hard limits are otherwise correctly implemented.
   - **Webhook auth differs from §6.** `tron/webhook.py` accepts `POST /webhook/tron` with an optional `X-TRON-Signature` HMAC header, gated by `VERIFY_SIGNATURE` (defaults `false` — open by default). §6 specifies `POST /webhook/tron?key=SECRET`. `jarvis/`'s webhook already does match §6 exactly (`?key=` query param, always checked).
   - `tron/models.py`'s 18-signal whitelist matches §7's list exactly (verified 1:1).

3. **The live Pine source (`TRON_Glassbox_SignalGenerator.pine`, `//@version=6`, "TRON — GLASSBOX SIGNAL GENERATOR") already emits the §6 schema field-for-field** (`engine`, `schema`, `signal`, `bias`, `mode`, `symbol`, `tf`, `time`, `spot`, `confidence`, `conf_bull`, `conf_bear`, `fractal{}`, `core{}`, `setup{}`) via `tronJSON()` at STEP 17. This part of the spec needs no reconciliation — the contract is real and already live.

4. **One doctrine disagreement between this spec and the already-shipped classifier:** `jarvis/app/parser.py` classifies `SNIPER_CALL`/`SNIPER_PUT` as `EXECUTE` (and auto-whitelists them), while this spec's §7 classifies Sniper signals as **CONTEXT**, dormant unless `show_zones` is on. Whichever implementation is carried forward needs this resolved explicitly, not inherited by default.

**None of the above was fixed as part of writing this file — this is the verification record called for in §0, surfaced for an explicit decision on which tree (`jarvis/` hardened to match §4's layering, or `tradersmind/` fixed to drop paper mode + add the router + swap to the REST bridge) becomes the one deployed system before wiring the TradingView MVP alert.**
