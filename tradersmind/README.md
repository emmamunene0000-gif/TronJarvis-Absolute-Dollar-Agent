# 🤖 TradersMind
## Just a Really Very Intelligent Sidekick
### Trading Augmented Intelligence (DSS — Decision Support System)

---

## What This Is

TradersMind is the **execution arm** of TRON — your Pine Script glassbox signal generator. 

- **TRON** detects (math, instinct, zero hallucination)
- **TradersMind** executes (reason, memory, narrative, interface)
- **Risk Governor** protects (your money is the business)

TRON emits JSON webhooks. TradersMind receives, narrates, remembers, decides, and trades.

---

## Architecture

```
TRON (TradingView) → Webhook → TradersMind (Replit)
                                            │
    ┌───────────────┬───────────────┬───────┴───────┐
    ▼               ▼               ▼               ▼
 Webhook          Memory        Narrative          Risk
 Receiver        (SQLite)      Engine            Governor
    │               │               │               │
    └───────────────┴───────┬───────┴───────────────┘
                            ▼
                    Deriv Bridge
                    (WebSocket API)
                            │
                    ┌───────┴───────┐
                    ▼               ▼
               Telegram         Web Dashboard
               Mini App        (Real-time)
```

---

## Layers

| Layer | File | Purpose |
|-------|------|---------|
| **TRON** | `tron/` | Models, validator, webhook receiver |
| **Mind** | `mind/` | SQLite memory, narrative engine, KNN similarity |
| **Bridge** | `bridge/` | Deriv WebSocket client, contract mapper |
| **Governor** | `governor/` | Risk rules, stake sizing, cooldowns, limits |
| **Body** | `body/` | Telegram bot, signal cards, tap-to-execute |
| **Face** | `face/` | Web dashboard, TradingView embed, live P&L |

---

## Quick Start

### 1. Clone & Setup
```bash
git clone <repo>
cd tradersmind
pip install -r requirements.txt
cp .env.example .env
```

### 2. Configure `.env`
```env
TRADING_MODE=paper          # paper | demo | live
AUTO_EXECUTE=false          # NEVER true until 100 demo trades
WEBHOOK_SECRET=your_secret
TELEGRAM_BOT_TOKEN=your_token
TELEGRAM_CHAT_ID=your_chat_id
DERIV_APP_ID=your_app_id
DERIV_API_TOKEN=your_demo_token
```

### 3. Run
```bash
python main.py
```

### 4. Connect TRON (TradingView)
In TRON Pine Script alert:
- **Webhook URL**: `https://your-replit-url/webhook/tron`
- **Message**: `{{alert_message}}`

---

## Signal Flow

1. TRON detects signal → emits JSON webhook
2. TradersMind validates → stores in memory → generates narrative
3. Risk Governor checks limits → approves/rejects
4. If approved: broadcasts to Telegram + Web Dashboard
5. Operator taps **EXECUTE** (or auto-executes if enabled + high confidence)
6. Deriv Bridge fires contract → returns ticket
7. Live P&L streams to Telegram + Dashboard
8. Trade closes → result stored in episodic memory
9. Next signal: memory suggests stake adjustment based on similar history

---

## Risk Governor Rules (Hard-Coded)

| Rule | Default | Override? |
|------|---------|-----------|
| Max stake per trade | $5.00 | ❌ No |
| Daily loss limit | $50.00 | ⚠️ Logged override |
| Max consecutive losses | 3 | ⚠️ Logged override |
| Cooldown after 2 losses | 5 min | ❌ No |
| Min confidence for auto | 85% | ❌ No |
| Min sync layers for auto | 4/4 | ❌ No |
| Max 10% balance per trade | — | ❌ No |

---

## Trading Modes

| Mode | Description | Best For |
|------|-------------|----------|
| **Rise/Fall** | Direction + duration only | Quick scalps, high frequency |
| **Vanilla** | Strike + expiry + direction | Defined risk, higher payouts |
| **Multiplier** | Direction + leverage + SL/TP | Trend riding, compound gains |

---

## Episodic Memory Schema

Every trade stores:
- Full TRON context (fractal state, indicators, confidence)
- Execution details (stake, ticket, entry price)
- Result (P&L, win/loss, time to resolution)
- Feature vector for KNN similarity search

Queries supported:
- "Find similar setups" → KNN on indicator vector
- "H4 FLIP performance" → Filter by signal type
- "London session stats" → Group by hour
- "Streak detection" → Flag unstable regimes

---

## Narrative Engine (Zero LLM)

Template-based, deterministic storytelling:

> "SOVEREIGN CALL — H4 flipped BULL. All 4 layers aligned. Confidence 87%. Strike 314.50 ATM. Expiry 8m. Similar setups won 72% historically. Risk Governor approves max stake."

No hallucination. Every word traceable to TRON's JSON fields.

---

## Safety First

- **Default**: Paper trading + manual tap-to-execute
- **Auto-execute**: Requires `AUTO_EXECUTE=true` + confidence ≥85% + sync=4/4
- **Demo gate**: 100 demo trades required before live mode unlock
- **All overrides logged**: Operator can bypass, but every bypass is recorded

---

## Roadmap

- [x] v1.0: Webhook → Memory → Narrative → Telegram → Paper trades
- [ ] v1.1: Live Deriv execution + WebSocket P&L streaming
- [ ] v1.2: Web dashboard with real-time chart + stats
- [ ] v1.3: LightGBM predictive module + dynamic stake sizing
- [ ] v1.4: Multi-pair agent loader + portfolio heat map
- [ ] v1.5: Telegram Mini App (native buttons, no webview)

---

## License

MIT — Built for traders who think.

**TRON detects. TradersMind executes. Governor protects.**
