# Absolute Dollar Agent — TRON / TradersMind

A glassbox trading system for Deriv. **TRON** detects on the price grid in Pine Script and emits nothing but signal. **TradersMind** receives, classifies, narrates, remembers, and executes — with a human tap today, autonomously later, always under a risk governor.

No blackbox. Every signal TradersMind acts on can be traced back to the exact TRON filters that fired.

## Architecture

```
TradingView (TRON, Premium)
        │  JSON webhook — engine: TRON_GBX_v3
        ▼
TradersMind (FastAPI) → mind/router classifies EXECUTE/CONTEXT/NOISE
        │                → SQLite episodic memory (signals, trades, governor log)
        ▼
Telegram — tap-to-execute cards + status/risk/history
        │
        ▼
Deriv Bulk Purchase REST — Vanilla Options / Rise-Fall / Multipliers, demo or live
```

TRON has no idea what account it's trading, what already happened, or what a dollar is — it only reads price, one asset at a time, and says so. TradersMind is the only thing that knows about capital, risk, and history. That split is deliberate: it's what keeps TRON simple enough to trust and TradersMind smart enough to be worth building.

## What's in this repo

| Path | What it is |
|---|---|
| `TRON_Glassbox_SignalGenerator.pine` | TRON — the only Pine Script in this repo. Load this on TradingView. |
| `tradersmind/` | **The deployed system.** Layered `tron/mind/bridge/governor/body/face` build — see `tradersmind/README.md` to run it. `.replit` points here. |
| `TRON_JARVIS/README.md` | Operator's guide to TRON's alerts — signal hierarchy, how to read every alert type, dashboard reference. |
| `CLAUDE.md` | The master build spec and its verification/rebuild log — read this first. |

The earlier `jarvis/` build (flat layout, proved the Deriv Bulk Purchase execution path) has been purged — its classifier and Deriv-bridge logic was already ported into `tradersmind/` (see `CLAUDE.md` §21). It's still recoverable from git history if needed.

## Status

Nothing is live yet. TRON's detection engine is finished and unmodified. `tradersmind/` has the full pipeline (classify → narrate → remember → size → route) working end-to-end against a mocked Deriv client and passing its test suite, but has **not** placed a confirmed real order — that requires deploying it with real Deriv/Telegram credentials. See `CLAUDE.md` §21 for exactly what was rebuilt and what's still a known gap.

## Quickstart

1. Load `TRON_Glassbox_SignalGenerator.pine` on a TradingView chart (Premium plan, for reliable webhooks).
2. Stand up TradersMind: follow `tradersmind/README.md` (server, `.env`, the one TradingView alert you need).
3. Point the alert's webhook at your running instance: `https://your-host/webhook/tron?key=SECRET`.
4. Start on `TRADING_MODE=demo`, `AUTO_EXECUTE=false` — tap-to-trade only until the ledger earns more (100 completed demo trades before `live` unlocks at all).

## Broker & contracts

Deriv only. Vanilla Options is primary; Rise/Fall and Multipliers are both wired through the same execution pipeline. Multipliers cover the "perpetuals" use case, so there's no second exchange to integrate — one pipeline, one broker.
