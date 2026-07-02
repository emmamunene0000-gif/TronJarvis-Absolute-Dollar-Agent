# Absolute Dollar Intelligence — TRON / JARVIS

A glassbox trading system for Deriv. **TRON** detects on the price grid in Pine Script and emits nothing but signal. **JARVIS** receives, classifies, speaks, and executes — with a human tap today, autonomously later, always under a risk governor.

No blackbox. Every signal Jarvis acts on can be traced back to the exact TRON filters that fired.

## Architecture

```
TradingView (TRON, Premium)
        │  JSON webhook — engine: TRON_GBX_v3
        ▼
JARVIS (FastAPI)  →  SQLite Ledger (signals, trades, governor log)
        │
        ▼
Telegram — Jarvis's voice + Tap-to-Trade buttons
        │
        ▼
Deriv WebSocket API — Vanilla Options (primary) / Rise-Fall / Multipliers, demo or real
```

TRON has no idea what account it's trading, what already happened, or what a dollar is — it only reads price, one asset at a time, and says so. JARVIS is the only thing that knows about capital, risk, and history. That split is deliberate: it's what keeps TRON simple enough to trust and JARVIS smart enough to be worth building.

## What's in this repo

| Path | What it is |
|---|---|
| `TRON_Glassbox_SignalGenerator.pine` | TRON, v4.0 — the only Pine Script in this repo. Load this on TradingView. |
| `jarvis/` | JARVIS Phase 1 — FastAPI server, Deriv execution, Telegram tap-to-trade. See `jarvis/README.md` to run it. |
| `TRON_JARVIS/README.md` | The deep dive — signal hierarchy, how to act on every alert type, dashboard reference, operator masterclass. |

## Status

TRON's detection engine and Jarvis's execution twin are both built. What's not done yet is deploying Jarvis somewhere TradingView's webhook can reach it, and running it against a Deriv demo account long enough to trust it. See `TRON_JARVIS/README.md` → Build Sequence for the full phase-by-phase status.

## Quickstart

1. Load `TRON_Glassbox_SignalGenerator.pine` on a TradingView chart (Premium plan, for reliable webhooks).
2. Stand up Jarvis: follow `jarvis/README.md` (server, `.env`, the one TradingView alert you need).
3. Point the alert's webhook at your running Jarvis instance.
4. Start on `DERIV_ENV=demo`, `AUTO_TRADE=false` — tap-to-trade only until the ledger earns more.

## Broker & contracts

Deriv only. Vanilla Options is primary; Rise/Fall and Multipliers are both wired through the same execution pipeline. Multipliers cover the "perpetuals" use case, so there's no second exchange to integrate — one pipeline, one broker.
