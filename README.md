# Absolute Dollar Agent
## Just a Really Very Intelligent Sidekick

A glassbox trading system for Deriv. **TRON** detects on the price grid in
Pine Script and emits nothing but signal. **Absolute Dollar Agent**
receives, classifies, narrates, remembers, sizes, and executes — a human
taps today, autonomy comes later, always under a risk governor.

Not a black-box AI trading bot. Every action Absolute Dollar Agent takes
must trace back to a named TRON field. If you can't point to the JSON field
that justified something, it shouldn't be on screen or in a trade.

---

## Repo Structure

```
TRON_Glassbox_SignalGenerator.pine   ← TRON, the Brain. Pine Script. Load on TradingView.
                                        Stateless, pure detection. Never modified by the
                                        backend build — a locked external dependency.

absolute_dollar_agent/                ← The Sidekick. One folder, the only deployed system.
├── tron/                              webhook receiver, 18-signal Pydantic models, validator
├── mind/                              classifier + router, episodic memory, narrative engine
├── governor/                          sizing law + hard risk limits, live-mode gate
├── bridge/                            Deriv execution client, contract mapper
├── body/                              Telegram — tap-to-execute, status/risk/history
├── interface/                         web interface (FastAPI + dashboard)
├── config/settings.yaml               narrative templates, risk band, router rules
├── tests/                             32 tests, all passing
├── .env.example                       every environment variable this build reads
└── README.md                          run instructions for this tree

docs/
└── TRON_ALERTS_GUIDE.md              ← operator's guide to reading TRON's alerts
                                        (signal hierarchy, masterclass, dashboard reference)

.mcp.json                             ← Deriv API MCP hub (dev-tool config, not deployed)
.replit                               ← points at absolute_dollar_agent/
README.md                             ← you are here — the single source of truth
```

One Pine file. One Python tree. One doctrine document. Nothing else.

---

## Architecture

```
TRON (TradingView, Pine Script) → Webhook → Absolute Dollar Agent (Replit)
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
                    Bulk Purchase REST
                             │
                     ┌───────┴───────┐
                     ▼               ▼
              Telegram (body/)   Web Interface (interface/)
              tap-to-execute     session stats + TradingView embed
```

**TRON = Brain.** Instinct, math, pure detection. Stateless.
**Absolute Dollar Agent = Sidekick.** Reason, memory, narrative, execution. Waits for TRON, then acts.
**RiskGovernor = the part whose business is making money**, not just enforcing limits.

> "TRON is TRON." The Sidekick never invents, re-scores, or overrides a signal — it classifies, narrates, sizes, and (if authorized) executes.

---

## Doctrine — Non-Negotiable Engineering Constraints

1. **The Sidekick never invents a signal.** All trade triggers originate from TRON's webhook. No independent technical analysis in the backend.
2. **Not "my Sidekick" — TRON's Sidekick.** The backend is an execution arm, not a second opinion.
3. **Load on the pair, then wait.** The agent does nothing until a TRON webhook arrives for that pair.
4. **Glass box, not black box.** Every action traces to a named TRON factor (`sync_layers=4`, `vwap=BULL`, `confidence=86`). No opaque "AI decided" messaging anywhere.
5. **Operator sets risk, RiskGovernor does the rest.** The operator picks a risk profile once; sizing and guardrails run autonomously from there.
6. **RiskGovernor sizes for edge — it is not a generic limit-checker.** Its job is to make money within hard limits, not just say no.
7. **Silence is a valid position.** No TRON trigger = no trade. That's an active "waiting for TRON" state, never a bug.
8. **Two trust levels, one engine.** TAP (decision-support) and AUTO (autonomous) share the same pipeline and differ only at the execution gate.
9. **No paper-trading mode, ever.** `TRADING_MODE` is `demo` or `live` only. Every trade, from day one, is a real order against a real Deriv account balance (virtual on demo, real on live).
10. **No LLM in the narrator**, no third-party trade-automation bots, Deriv API direct only.

---

## Configuration (`.env`)

See `absolute_dollar_agent/.env.example` for the complete, current list. The essentials:

```env
TRADING_MODE=demo           # demo | live — no paper mode exists
AUTO_EXECUTE=false          # requires the 100-demo-trade gate before flipping true
WEBHOOK_SECRET=your_secret
TELEGRAM_BOT_TOKEN=your_token
TELEGRAM_CHAT_ID=your_chat_id
DERIV_APP_ID=your_app_id
DERIV_API_TOKEN=your_demo_token
DERIV_ACCOUNT_ID=your_deriv_account_id   # required by the Bulk Purchase endpoint
```

`TRADING_MODE` has exactly two values. There is no `paper` value and no
paper-simulation code path.

---

## The Webhook Contract — Authoritative, Do Not Deviate

The *only* interface between TRON and Absolute Dollar Agent. TRON's live
Pine script already emits this schema field-for-field (`schema: 1`):

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

**Endpoint:** `POST /webhook/tron?key=SECRET` — always checked, no exceptions.
**TradingView alert config:** Condition = "Any alert() function call", Message = `{{alert_message}}`, Frequency = "Once Per Bar Close", Webhook URL = `https://your-replit-url/webhook/tron?key=SECRET`.

- `mode` is a single global tag from TRON's chart settings — the Router (not TRON) decides per-signal-type routing (see Routing Matrix below).
- All alerts fire once per bar close, non-repaint. Acted on closed-bar data only, never intrabar.
- Anything not matching this schema is rejected — never silently coerced.

---

## The 18 Signals — Classification (verified against `mind/router.py`)

**Classes:**
- **EXECUTE** — the agent may place a trade if its route-style is enabled.
- **CONTEXT** — never triggers an independent trade. Narrated and logged only.
- **NOISE** — dormant/duplicate, log only (unused today — all 18 signals map onto EXECUTE or CONTEXT; kept for a signal type TRON might add later).

| Signal(s) | Class | Fires when | Notes |
|---|---|---|---|
| `CALL_ENTRY` / `PUT_ENTRY` | EXECUTE | ATM crossover + trail align + confidence ≥ threshold + not deduped (3-bar window) | Workhorse entry; full strike/SL/TP payload |
| `CALL_CONTINUATION` / `PUT_CONTINUATION` | EXECUTE | Fresh RSI smart-momentum turn + trail align | No confidence gate, no dedup — re-fires as scale-in fuel. RiskGovernor caps stacking via cooldown + streak limits. |
| `H4_FLIP_CALL` / `H4_FLIP_PUT` | EXECUTE (priority 1) | H4 trail flip + trail align | No confidence gate — it IS the gate. Rare, sovereign event. |
| `MTF_FLIP_CALL` / `MTF_FLIP_PUT` | EXECUTE (priority 2) | M15 or H1 flip + trail align + conf pass | Suppressed if H4 flip fired same bar |
| `TRAIL_FLIP_CALL` / `TRAIL_FLIP_PUT` | EXECUTE (priority 3) | Chart trail flip + MTF support + conf pass | Suppressed if H4/MTF flip fired same bar |
| `SNIPER_CALL` / `SNIPER_PUT` | CONTEXT (dormant unless `show_zones` on) | Liquidity-zone retest + trail + conf pass | `show_zones` OFF by default in TRON |
| `CALL_ZONE_BREAK` / `PUT_ZONE_BREAK` | CONTEXT (dormant unless zones on) | Zone break + trail align, no conf gate | Stays CONTEXT permanently even if zones are enabled later — never an independent trade |
| `BULL_REGIME_SHIFT` / `BEAR_REGIME_SHIFT` | CONTEXT — primary exit signal | Trail/VWAP/Fib regime turn | Overlaps flips same bar — dedupe: flip = execute, shift = context/exit only |
| `BULL_BOS` / `BEAR_BOS` | CONTEXT — structure confirmation | Break of prior swing high/low with structure agreeing | Confidence modifier only |

Same-bar flip-priority suppression is enforced in code: a fired
`MTF_FLIP_*`/`TRAIL_FLIP_*` downgrades to CONTEXT if a higher-priority flip
(`H4_FLIP_*` > `MTF_FLIP_*` > `TRAIL_FLIP_*`) already fired for that symbol
on the same TRON bar.

---

## Routing Matrix (Locked — confirmed 2026-07-04)

| Trading style | Contract shape | Auto-routed EXECUTE signals |
|---|---|---|
| **Rise/Fall** | direction + expiry | `CALL_ENTRY` / `PUT_ENTRY`, `CALL_CONTINUATION` / `PUT_CONTINUATION`, `TRAIL_FLIP_*` |
| **Vanilla Options** | strike + expiry | `CALL_ENTRY` / `PUT_ENTRY`, `H4_FLIP_*`, `MTF_FLIP_*`, `TRAIL_FLIP_*` |
| **Multipliers** | direction + leverage + SL/TP | `CALL_ENTRY` / `PUT_ENTRY`, `H4_FLIP_*`, `MTF_FLIP_*`, `TRAIL_FLIP_*` |
| **Context (no trade)** | — | `SNIPER_*`, `ZONE_BREAK_*`, `REGIME_SHIFT_*`, `BOS_*` |

The operator enables one or more styles in `config/settings.yaml` →
`router.enabled_styles`. If a signal's best-fit style is disabled, it drops
to a TAP card instead of auto-executing — it is never silently skipped.

**How ties resolve when a signal fits more than one enabled style:**
`config/settings.yaml` → `router.style_priority` is a fixed ranked list
(default `vanilla > multiplier > rise_fall`) — the first enabled style in
that list wins the auto-route. This is what actually decides which
contract gets executed off a given TradingView alert: change
`enabled_styles`/`style_priority` and the exact same signal routes
differently, with no code change needed.

**Locked decisions, confirmed against the code:**
- `CALL_ENTRY`/`PUT_ENTRY` auto-route to Rise/Fall, Vanilla, or Multiplier — whichever enabled style ranks highest in `style_priority`. (Earlier drafts of this doc had Rise/Fall as tap-only for entries; that's superseded — entries are a first-class auto-route candidate for all three styles now.)
- `CALL_ZONE_BREAK`/`PUT_ZONE_BREAK` stay CONTEXT permanently, even if Liquidity Zones are enabled in TRON later — never an independent trade.

---

## Signal Flow — End to End

1. TRON detects a signal on bar close → emits JSON webhook.
2. `tron/webhook.py` checks `?key=` and validates against the schema above; malformed or unauthorized payloads are rejected, not coerced.
3. `mind/router.py` classifies EXECUTE/CONTEXT/NOISE and, for EXECUTE signals, resolves which enabled contract style it auto-routes to.
4. `mind/narrative.py` generates a deterministic narrative; `mind/memory.py` logs the episode regardless of tier — CONTEXT signals included.
5. CONTEXT signals stop here — narrated and logged, never executed.
6. EXECUTE signals go through `governor/risk_engine.py`: hard limits first, then the $0.35–$1.00 sizing law scaled by confidence/edge.
7. Approved signals broadcast a tap card to Telegram. AUTO mode also fires automatically if confidence ≥85% and sync=4/4 — a hard gate, not a sizing input; anything below drops to TAP even with AUTO on.
8. `bridge/deriv_client.py` places a real order against the Deriv demo or live balance via the Bulk Purchase REST endpoint, returns a contract ID.
9. Result settles → ledger updated → counts toward the 100-trade live-mode gate.

---

## RiskGovernor — Reconciled Rules

The sizing law and the hard safety ceiling are two different things — they
don't conflict, they nest.

**Sizing law (the Governor's actual behavior):** stake is sized dynamically
between **$0.35 and $1.00**, scaled by TRON's confidence and, once similar
episodes exist, a historical win-rate edge signal.

**Hard limits (never exceeded, regardless of sizing law output):**

| Rule | Default | Override? |
|---|---|---|
| Max stake per trade | $5.00 | ❌ No |
| Daily loss limit | $50.00 | ⚠️ Logged override only |
| Max consecutive losses | 3 | ⚠️ Logged override only |
| Cooldown after 2 losses | 5 min | ❌ No |
| Min confidence for AUTO-execute | 85% | ❌ No |
| Min sync layers for AUTO-execute | 4/4 (SOVEREIGN) | ❌ No |
| Max % of balance per trade | 10% | ❌ No |

**Auto-execute gate, explicitly:** a signal only fires automatically in AUTO
mode if confidence ≥ 85% **and** `sync_layers` = 4/4. Anything below drops
to a TAP card even with AUTO mode on — never auto-fired at a smaller size.

**Demo-trade safety gate:** `TRADING_MODE=live` cannot be unlocked until
**100 completed demo-account trades** are logged in episodic memory —
enforced at boot (`main.py` refuses to start otherwise), not just
documented. This is a real-order count against Deriv's demo balance, never
a simulated one. All manual overrides are logged with operator ID and
timestamp — never silently bypassed.

Silence (no trade) always comes from TRON not triggering — never from the
Governor vetoing a live signal that already passed its gates.

---

## Trading Modes

| Mode | Description | Best for |
|---|---|---|
| **Rise/Fall** | Direction + duration only | Quick scalps, high frequency |
| **Vanilla** | Strike + expiry + direction | Defined risk, higher payouts |
| **Multiplier** | Direction + leverage + SL/TP | Trend riding, compound gains |

---

## Backend Modules

1. **Webhook Receiver** (`tron/`) — validates schema, rejects malformed payloads, queues for processing.
2. **Classifier + Router** (`mind/router.py`) — sorts each signal per the classification table and applies the Routing Matrix.
3. **Narrative Engine** (`mind/narrative.py`) — template-based, zero LLM.
4. **Episodic Memory** (`mind/memory.py`) — SQLite ledger; `mind/similarity.py` holds a KNN engine not yet wired into the live pipeline (see Known Gaps).
5. **RiskGovernor** (`governor/risk_engine.py`) — sizing + hard limits + live-mode gate.
6. **Deriv Bridge** (`bridge/deriv_client.py`) — Bulk Purchase REST client, contract mapping, order placement.
7. **Telegram Body** (`body/telegram_bot.py`) — tap-to-execute cards, `/status` `/risk` `/history`.
8. **Web Interface** (`interface/`) — session-stats dashboard, TradingView embed.

Direct Deriv API only — no third-party bots anywhere in the bridge.

---

## Narrative Engine — Zero LLM

Template-based, deterministic. Every word traceable to a TRON JSON field:

> "SOVEREIGN CALL — H4 flipped BULL. All 4 layers aligned. Confidence 87%. Strike 314.50 ATM. Expiry 8m. Similar setups won 72% historically. Risk Governor approves max stake."

No LLM call in this path unless explicitly requested later.

---

## Episodic Memory

Every signal stores full TRON context (fractal state, indicators,
confidence, `setup` block), a `tier` (EXECUTE/CONTEXT), and — once a trade
is actually placed — execution details (stake, contract ID, env) and result
(P&L, WIN/LOSS, settlement time).

Supported queries today: recent episodes by symbol+signal-type, win-rate
stats by signal type, daily stats, recent executed trades, and same-bar
signal lookups (for flip-priority suppression). A LightGBM edge model is
intended once 50–70 episodes exist — not started, by design (needs the
data first).

---

## Deriv Integration

- **Markets:** Volatility Indices (10/25/50/75/100, incl. 1s variants, 24/7), Step Indices, Crash/Boom, and related synthetic families.
- **Contract types:** Rise/Fall, Multipliers, Vanilla Options — one client covers all three.
- **Execution path:** Deriv retired the legacy WebSocket API for migrated accounts. Absolute Dollar Agent buys through the **Bulk Purchase REST endpoint** — direct buy, no pre-quote, no balance lookup, no settlement-polling subscription. Restoring those needs an OAuth2 + PKCE login upgrade (not built — see Known Gaps).
- **Honest technical note:** synthetics have no order book, so technical patterns are "coincidental" per Deriv's own docs (except Range Break). TRON's price-based layers are unaffected; its volume-derived layers lean on synthetic volume.

---

## Build Status — verified against the code, not assumed

### ✅ Built and verified (32 tests pass; hand-verified against a mocked Deriv client)

- Webhook auth and schema validation exactly as specified above.
- Full 18-signal classification, 1:1 tested, including the two resolutions against an earlier build that disagreed (SNIPER → CONTEXT, BOS → CONTEXT).
- Routing Matrix with the confirmed entry-auto-routing rule and same-bar flip suppression.
- Full pipeline wired: validate → classify → narrate → remember → size → route → tap or auto-execute → ledger.
- RiskGovernor sizing law + every hard limit + the 100-demo-trade live-mode gate, enforced at boot.
- Narrative engine covers all 18 signal types (a bug that crashed every non-SNIPER signal was found and fixed while verifying).
- No paper mode anywhere — confirmed via repo-wide search.
- Telegram `/risk` reports the live demo-trade counter (`N/100`) toward the live-mode gate.
- Full app assembly (`main.py`'s FastAPI + interface routes) boots cleanly — a crash bug (a `StaticFiles` mount pointing at a directory that doesn't exist) was found and fixed while verifying.

### ⚠️ Built but incomplete

- **KNN similarity** (`mind/similarity.py`) is instantiated but never called. The sizing law's edge signal today comes from a simpler win-rate query, not true KNN feature-vector matching.
- **Deriv Bridge** is implemented and structurally correct but has not placed a real order yet — that's what today's deployment test is for.
- **Web interface** (`interface/`) has session stats, a live signal feed, and a TradingView embed, but is not the chart-centric UI with TRON markers overlaid on price described in earlier planning.

### ❌ Not built — explicit gaps

- Chart-centric UI with TRON signal markers on price.
- Cross-signal confidence modifiers from CONTEXT signals onto a co-occurring EXECUTE signal.
- LightGBM edge model (needs 50–70 logged episodes first, by design).
- OAuth2 + PKCE Deriv upgrade — balance checks, live quotes, settlement watching.
- Multi-pair agent loader, Telegram Mini App (post-MVP roadmap).

---

## Guardrails for the Build Itself

- Never modify TRON's Pine logic — it's a locked external dependency.
- Never add a signal type not listed above.
- No LLM in the narrator unless explicitly requested later.
- No third-party trade-automation bots — Deriv API direct only.
- No paper-trading mode, no simulated fill engine — demo account only, real orders, real virtual balance.
- Every trade must be traceable, in the UI, to the exact TRON field(s) that caused it.
- Every manual override of a RiskGovernor rule must be logged, never silent.

---

## Quickstart — Deploying and Testing

1. Load `TRON_Glassbox_SignalGenerator.pine` on a TradingView chart (Premium plan, for reliable webhooks).
2. `cd absolute_dollar_agent && pip install -r requirements.txt && cp .env.example .env`, then fill in `.env` per the Configuration section above.
3. On Replit: Secrets must match `.env.example` — notably `DERIV_ACCOUNT_ID`, which the Bulk Purchase endpoint requires. `.replit` already points at `absolute_dollar_agent/`.
4. Deploy and confirm the boot log shows `Mode: DEMO` and does **not** print `Live-mode gate cleared` (you're not in live mode yet).
5. Point the TradingView alert webhook at `https://your-replit-url/webhook/tron?key=YOUR_SECRET`.
6. Message your Telegram bot once (registers you as the operator), then try `/status`, `/risk`, `/history` to confirm it reads real state, not placeholders.
7. Wait for (or force) a TRON signal and confirm: CONTEXT-tier signals arrive with no buttons, EXECUTE-tier signals arrive with tap buttons, and a tap actually reaches Deriv.

## Broker & Contracts

Deriv only. Vanilla Options, Rise/Fall, and Multipliers all route through
the same Bulk Purchase REST client — one pipeline, one broker.

## Where to Read Next

- **`absolute_dollar_agent/README.md`** — how to run this tree day to day.
- **`docs/TRON_ALERTS_GUIDE.md`** — what each TRON alert means and how to act on it.

## License

MIT.

**TRON detects. Absolute Dollar Agent executes. Governor protects.**
