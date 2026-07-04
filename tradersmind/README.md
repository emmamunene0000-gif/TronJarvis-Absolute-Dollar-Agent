# TradersMind
## Absolute Dollar Agent — Just a Really Very Intelligent Sidekick

This is the one deployed tree for ADA. See `/CLAUDE.md` §20–22 for the full
history of how it got here, including an earlier flat-layout build that
existed in parallel and was ported into this tree, then retired.

---

## What This Is

TradersMind is the **execution arm** of TRON — your Pine Script glassbox signal generator.

- **TRON** detects (math, instinct, zero hallucination)
- **TradersMind** classifies, narrates, remembers, sizes, and (if authorized) executes
- **Risk Governor** protects (your money is the business)

TRON emits JSON webhooks. TradersMind is the only thing that ever acts on them.

---

## Architecture

```
TRON (TradingView) → Webhook → TradersMind (Replit)
                                            │
              ┌──────────────┬─────────────┴──────────────┐
              ▼              ▼                             ▼
        tron/webhook    mind/router              mind/memory + narrative
        (validate)   (classify EXECUTE/          (episodic ledger,
                       CONTEXT + route            deterministic narrator)
                       to a contract style)
              │              │                             │
              └──────────────┴──────────┬──────────────────┘
                                         ▼
                              governor/risk_engine
                              (sizing law + hard limits)
                                         │
                                 ┌───────┴───────┐
                                 ▼               ▼
                          body/ (Telegram)  bridge/ (Deriv REST)
                          tap-to-execute    real order, demo or live
```

`face/` runs alongside as a read-only web dashboard.

---

## Layers

| Layer | File | Purpose |
|-------|------|---------|
| **TRON** | `tron/` | Pydantic models (18-signal whitelist), validator, webhook receiver |
| **Mind** | `mind/` | Signal Router (classify + route), SQLite episodic memory, narrative engine, KNN similarity module (see gap below) |
| **Bridge** | `bridge/` | Deriv Bulk Purchase REST client, contract mapper |
| **Governor** | `governor/` | Sizing law + hard limits, cooldowns, live-mode gate |
| **Body** | `body/` | Telegram bot — tap-to-execute cards, live status/risk/history |
| **Face** | `face/` | Web dashboard (TradingView embed, session stats) |

---

## Quick Start

### 1. Setup
```bash
cd tradersmind
pip install -r requirements.txt
cp .env.example .env
```

### 2. Configure `.env`
See `.env.example` for the full list. The essentials:
```env
TRADING_MODE=demo           # demo | live — there is no paper mode
AUTO_EXECUTE=false
WEBHOOK_SECRET=your_secret
TELEGRAM_BOT_TOKEN=your_token
TELEGRAM_CHAT_ID=your_chat_id
DERIV_APP_ID=your_app_id
DERIV_API_TOKEN=your_demo_token
DERIV_ACCOUNT_ID=your_deriv_account_id   # required by the Bulk Purchase endpoint
```

### 3. Run
```bash
python main.py
```

### 4. Connect TRON (TradingView)
- **Webhook URL**: `https://your-replit-url/webhook/tron?key=your_secret`
- **Message**: `{{alert_message}}`
- **Condition**: Any alert() function call, frequency = Once Per Bar Close

### 5. Telegram commands
Message your bot once to register as the operator, then:
- `/status` — daily P&L, trades today, win rate, risk state, heat
- `/risk` — sizing band, hard limits, cooldown state, and the
  live-mode gate counter (`N/100 completed demo trades`)
- `/history` — last 10 executed trades

Tap cards only appear for EXECUTE-tier signals; CONTEXT-tier signals post
as plain informational messages with no buttons — that split is the point.

---

## Signal Flow (§9)

1. TRON detects a signal on bar close → emits JSON webhook.
2. `tron/webhook.py` checks `?key=` and validates against the §6 schema.
3. `mind/router.py` classifies EXECUTE / CONTEXT / NOISE and, for EXECUTE
   signals, resolves which enabled contract style it auto-routes to.
4. `mind/narrative.py` generates a deterministic narrative; `mind/memory.py`
   logs the episode regardless of tier — CONTEXT signals included.
5. CONTEXT signals stop here — narrated and logged, never executed.
6. EXECUTE signals go through `governor/risk_engine.py`: hard limits first,
   then the $0.35–$1.00 sizing law scaled by confidence/edge.
7. Approved signals broadcast a tap card to Telegram. AUTO mode also fires
   automatically if confidence ≥85% and sync=4/4 (a hard gate, not a
   sizing input — anything below drops to TAP even with AUTO on).
8. `bridge/deriv_client.py` places a real order against the Deriv demo or
   live balance via the Bulk Purchase REST endpoint, returns a contract ID.
9. Result settles → ledger updated → counts toward the 100-trade live gate.

---

## The Deriv Bridge — Honest Limitation

`bridge/deriv_client.py` does **not** implement the persistent WebSocket
bridge CLAUDE.md §1/§12 describe. Deriv retired the legacy WebSocket API for
this account (`GET /trading/v1/options/legacy/migration-status` → `"complete"`).
Every Personal Access Token fails `InvalidToken` against `wss://ws.derivws.com`
regardless of app_id. Instead, TradersMind buys through the **Bulk Purchase
REST endpoint** — direct buy, no pre-quote, no balance lookup, no settlement
polling. `contract_status()` raises rather than pretending to track a
contract it structurally can't. Restoring the full flow needs interactive
OAuth2 + PKCE login — tracked as future work, not part of this build.

---

## Risk Governor (§10)

**Sizing law** (what the Governor actually charges): stake is sized
dynamically between **$0.35 and $1.00**, scaled by confidence and, once
similar episodes exist, a historical win-rate edge signal from
`mind/memory.py`'s `get_stats_by_signal_type()` — a simple symbol+signal-type
query, not yet the KNN feature-vector matcher (see gap below).

**Hard limits** (never exceeded, nest around the sizing law):

| Rule | Default | Override? |
|------|---------|-----------|
| Max stake per trade | $5.00 | ❌ No |
| Daily loss limit | $50.00 | ⚠️ Logged override |
| Max consecutive losses | 3 | ⚠️ Logged override |
| Cooldown after 2 losses | 5 min | ❌ No |
| Min confidence for auto | 85% | ❌ No |
| Min sync layers for auto | 4/4 | ❌ No |
| Max 10% balance per trade | — | ❌ No |

**Live-mode gate**: `main.py` refuses to start with `TRADING_MODE=live`
until `mind/memory.py`'s ledger shows 100 completed (`WIN`/`LOSS`), actually
*executed* demo trades — not just signals seen. Hard gate, no override.

---

## Signal Classification (§7) — resolved against the prior build's disagreement

`mind/router.py` locks two calls this spec makes differently than the
earlier flat-layout tree it was ported from:
- `SNIPER_CALL`/`SNIPER_PUT` → **CONTEXT** (the prior build had these as EXECUTE)
- `BULL_BOS`/`BEAR_BOS` → **CONTEXT** (the prior build had these as NOISE)

Same-bar flip suppression is enforced: a fired `MTF_FLIP_*`/`TRAIL_FLIP_*`
downgrades to CONTEXT if a higher-priority flip (`H4_FLIP_*` > `MTF_FLIP_*`
> `TRAIL_FLIP_*`) already fired for that symbol on the same TRON bar.

---

## Routing Matrix (§8) — operator defaults locked

- `CALL_ENTRY`/`PUT_ENTRY` and the flip signals fit more than one enabled
  style (Vanilla/Multiplier, sometimes Rise/Fall too). `config/settings.yaml`
  → `router.style_priority` is a fixed ranked list; first enabled style
  wins. Default: `vanilla` > `multiplier` > `rise_fall`.
- `CALL_ZONE_BREAK`/`PUT_ZONE_BREAK` stay CONTEXT permanently, even if
  Liquidity Zones are enabled in TRON later — never an independent trade.
- `CALL_ENTRY`/`PUT_ENTRY` are also tap-executable to Rise/Fall as a manual
  override, even though the auto-router never picks it for them.

Change `router.enabled_styles` in `config/settings.yaml` to turn a trading
style on or off.

---

## What's Not Built Yet

Scoped out of this pass, tracked for later build-sequence phases (§17):
- Chart-centric UI with TRON signal markers overlaid on price (`face/`
  today is a session-stats panel + generic TradingView embed, not the
  glassbox chart §15 calls for).
- `mind/similarity.py`'s KNN engine (`SimilarityEngine.find_similar`,
  `TradeEpisode.feature_vector`) is instantiated in `main.py` but never
  called — the live pipeline's edge signal comes from a simpler win-rate
  query instead (§14's "Find similar setups → KNN" isn't wired in yet).
- Cross-signal confidence modifiers from CONTEXT signals onto a
  co-occurring EXECUTE signal (§7's "raises/lowers confidence" note).
- LightGBM edge model (needs 50–70 logged episodes first).
- OAuth2 + PKCE Deriv login (balance checks, live quotes, settlement
  watching).

---

## License

MIT.

**TRON detects. TradersMind executes. Governor protects.**
