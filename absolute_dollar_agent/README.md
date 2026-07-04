# Absolute Dollar Agent
## Just a Really Very Intelligent Sidekick

This is the deployed tree. For the full spec — doctrine, webhook contract,
signal classification, routing matrix, risk rules, and verified build
status — see the root `README.md`. This file only covers running this tree.

---

## Layers

| Layer | Folder | Purpose |
|-------|--------|---------|
| **TRON** | `tron/` | Pydantic models (18-signal whitelist), validator, webhook receiver |
| **Mind** | `mind/` | Signal Router (classify + route), SQLite episodic memory, narrative engine |
| **Bridge** | `bridge/` | Deriv Bulk Purchase REST client, contract mapper |
| **Governor** | `governor/` | Sizing law + hard limits, cooldowns, live-mode gate |
| **Body** | `body/` | Telegram bot — tap-to-execute cards, live status/risk/history |
| **Interface** | `interface/` | Web interface (FastAPI + dashboard) |

---

## Run It

```bash
cd absolute_dollar_agent
pip install -r requirements.txt
cp .env.example .env
# fill in .env — see root README.md's Configuration section
python main.py
```

**Connect TRON (TradingView alert):**
- Webhook URL: `https://your-host/webhook/tron?key=your_secret`
- Message: `{{alert_message}}`
- Condition: Any alert() function call, frequency = Once Per Bar Close

**Telegram commands** (message your bot once to register as operator):
- `/status` — daily P&L, trades today, win rate, risk state, heat
- `/risk` — sizing band, hard limits, cooldown state, and the live-mode gate counter (`N/100 completed demo trades`)
- `/history` — last 10 executed trades

Tap cards only appear for EXECUTE-tier signals; CONTEXT-tier signals post
as plain informational messages with no buttons — that split is the point.

---

## Run the Tests

```bash
cd absolute_dollar_agent
pytest tests/ -v
```

32 tests covering the classifier, router, risk governor sizing/gates, and
the TRON payload models/validator.

---

## Known Gaps in This Tree

- `mind/similarity.py`'s KNN engine is instantiated but never called — the
  sizing law's edge signal comes from a simpler win-rate query today.
- `bridge/deriv_client.py` uses the Bulk Purchase REST endpoint, not a
  persistent WebSocket — no pre-quote, no balance lookup, no settlement
  polling. `contract_status()` raises rather than pretending to track a
  contract it structurally can't. Restoring full parity needs an
  OAuth2 + PKCE login upgrade.
- `interface/` is a session-stats dashboard with a generic TradingView
  embed, not a chart with TRON's signal markers overlaid on price.

Full detail on all of the above is in the root `README.md`.

---

## License

MIT.

**TRON detects. Absolute Dollar Agent executes. Governor protects.**
