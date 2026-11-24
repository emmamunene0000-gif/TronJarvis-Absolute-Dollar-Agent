# Repository Runtime Synthesis and Safety Status

**Audit snapshot:** `3ade33a8cbdab7652b0e0d4d5475baad0258297e`  
**Audit date:** 24 November 2026  
**Branch at audit start:** `docs/runtime-synthesis-and-safety`  
**Review type:** Read-only source review. No source code was changed as part of the audit. The Python test suite, frontend typecheck/build, and an end-to-end Deriv Demo trade were not run.

> **Deployment status: NOT READY FOR LIVE TRADING.** This repository contains a TRON webhook-to-Deriv system and a Next.js dashboard foundation. It is not yet an independent TRON trading terminal, and the execution path has unresolved mode-routing, balance, persistence, and settlement safeguards.

## What this is

This is a TRON-to-Deriv trading system. The Pine Script indicator emits signals; a Python service receives and validates those signals, classifies and explains them, records them, applies risk checks, and can submit Deriv orders. A Next.js dashboard foundation presents status, candles, signals, risk information, and trade history.

**The Pine Script remains the signal source of truth.** The current system still depends on TradingView posting TRON JSON to `/webhook/tron`. There is no independent TypeScript TRON calculation engine in this snapshot. The frontend has a Deriv historical-candle endpoint, but that does not replace the Pine signal-generation and webhook path.

## Stack

- **Languages:** Python, TypeScript/JavaScript, HTML, CSS, and Pine Script
- **Backend:** FastAPI/Uvicorn
- **Frontend:** Next.js App Router
- **Notable libraries:** Pydantic, aiosqlite, `python-telegram-bot`, `httpx`, `websockets`, and `lightweight-charts`

## Repository organization

```text
TRON_Glassbox_SignalGenerator.pine  TradingView signal indicator
absolute_dollar_agent/
  main.py                           Signal-processing runtime and app assembly
  tron/                             Webhook receiver, validation, signal models
  mind/                             Signal routing, narration, SQLite ledger
  governor/                         Stake sizing and risk rules
  bridge/                           Deriv order client and contract mapping
  body/                             Telegram controls and status
  interface/                        FastAPI dashboard and API routes
  config/                           Router, narrative, and risk configuration
  tests/                            Python unit tests
  market_data.py                    Deriv historical candle retrieval
  paper_trading.py                  In-process paper-trading engine
web/
  src/app/                          Next.js pages and styles
  src/components/                   Dashboard and price chart
docs/                               Operator guides and app status notes
```

## Current signal and data flow

```text
TradingView / TRON Pine Script
          |
          | JSON webhook
          v
FastAPI /webhook/tron
          |
          v
Validation and signal queue
          |
          v
Classifier / Router / Narrative
          |
          v
SQLite episodic ledger
          |
          v
RiskGovernor
       /     \
      v       v
 Telegram   Execution API / Deriv Bridge
              |
              v
         Deriv order endpoint

Next.js dashboard ---> FastAPI API routes
                   ---> Deriv historical OHLC candles
```

The backend API currently includes status, signal, trade, active-position, market-candle, health, order, risk-override, and reconciliation routes. The market-candle endpoint requests historical OHLC candles from Deriv's public WebSocket API and closes the connection after each request. The dashboard refreshes its data on a polling interval. This is not yet a persistent streaming market-data service.

Deriv candles provide OHLC data. Do not infer or fabricate traded volume, volume profile, or VWAP inputs from these candles.

## Important gaps before live use

### 1. Execution mode is not authoritative end to end

- `execute_external()` accepts an `is_demo` argument but does not use it to select the Deriv account or environment.
- The Deriv bridge selects its endpoint from the `is_demo` value fixed when the bridge is constructed from `TRADING_MODE`.
- The order API separately accepts `paper`, `demo`, or `live` in the request body. Those request values do not reliably control the bridge environment.
- `EXECUTION_MODE` is parsed by the runtime, but other parts of the signal and execution pipeline still rely on `TRADING_MODE` and `AUTO_EXECUTE`.

A request labelled Demo can therefore reach the account environment configured on the shared bridge, rather than an environment selected and validated for that request. One authoritative server-side mode must govern every order path. A client request must never be able to override or mismatch the configured account environment.

### 2. Paper-mode startup still initializes broker and Telegram integrations

The runtime constructs `DerivBridge` unconditionally. Its constructor raises when the Deriv API token or account ID is missing. Startup also unconditionally calls the Deriv bridge and Telegram bot startup methods. The checked-in `.env.example` leaves the Deriv token, account ID, and Telegram token blank.

As a result, the documented expectation that Paper mode can run without broker access is not currently supported by the initialization path. Optional integrations need to be conditional on the selected mode and their credentials before Paper mode can be treated as broker-independent.

### 3. Account balance is not retrieved or reconciled

Risk checks in the signal and external execution paths use a hard-coded balance of `1000.0`. The current Deriv bridge does not implement a verified account-balance lookup. Sizing and risk decisions must use a fresh, authenticated balance for the selected account, with defined behavior when balance data is stale or unavailable.

### 4. Deriv settlement tracking is unimplemented

The bridge submits orders through the Bulk Purchase REST endpoint, but `contract_status()` explicitly raises because the required OAuth2/PKCE settlement-monitoring path is not implemented. The code does not yet demonstrate the full lifecycle from accepted order to confirmed settlement and ledger reconciliation.

The 100-settled-demo-trade gate must not be treated as a reliable live-safety gate until demo order settlement is actually obtained from Deriv, validated, persisted, and reconciled.

### 5. Paper settlement uses an unobserved exit price

The reconciliation loop currently sets the paper trade's exit price to its entry tick when the expiry time is reached. That is not an observed market price at expiry and cannot produce a valid simulation of the trade outcome. Paper settlement must use a recorded market quote at the defined expiry, with explicit tie and expiry rules.

### 6. Paper account state is held in memory

The paper engine's balance and open positions are in memory. A process restart can lose the state needed to reconcile pending paper trades, even when the SQLite ledger still records those trades. Paper balances, open positions, settlement inputs, and transaction history need durable persistence and restart recovery.

### 7. Order idempotency is incomplete

The order endpoint returns a cached result when a request is already marked `COMPLETED`. A request found in another state, including `PENDING`, can continue through order submission. Concurrent retries or a retry after an uncertain timeout could therefore submit a duplicate order.

The request lifecycle needs an atomic claim, explicit handling for in-progress requests, and recovery/reconciliation for an order whose submission outcome is unknown. An idempotency key must prevent duplicate execution, not merely cache successful responses.

### 8. Dashboard is a read-only foundation

- The visible web execution control is disabled.
- The empty-signal state still instructs the operator to configure the TradingView webhook.
- The dashboard polls the API and can display Deriv historical candles, but it is not yet a live streaming terminal.
- The dashboard component uses React hooks but does not currently declare the App Router `"use client"` directive. This is a likely build issue that needs confirmation through an actual Next.js build.
- The dashboard is not yet wired to a complete, audited execution-control workflow.

### 9. Documentation has drifted from implementation

The root README and web README contain older architecture and operating claims that conflict with newer code. The current `docs/COMPLETE_WEB_APP_STATUS.md` also says Paper mode has no broker access; that statement is contradicted by the unconditional Deriv bridge construction and startup path described above. Documentation should be reconciled after behavior is fixed and tested, rather than used as proof that the behavior already works.

## How to run it

The repository documentation gives these local commands for the backend:

```bash
cd absolute_dollar_agent
pip install -r requirements.txt
cp .env.example .env
python main.py
```

And for the frontend:

```bash
cd web
npm install
cp .env.example .env.local
npm run dev
```

These are repository-provided commands, **not a verified deployment recipe**. The backend requires valid runtime configuration; the current startup path also attempts to initialize Deriv and Telegram even when their credentials are blank. Operator endpoints require `WEB_API_KEY`. No successful clean-install startup or end-to-end trade is claimed here.

## Verification status

| Area | Status |
|---|---|
| Repository source inspection | Completed for the audit snapshot |
| Python test suite | Not run in this review |
| Frontend typecheck | Not run |
| Next.js production build | Not run |
| CI checks | No checks were reported for the audited main commit |
| End-to-end Deriv Demo order | Not run |
| Confirmed Deriv settlement and balance reconciliation | Not implemented in the inspected bridge |
| Live trading readiness | **Not ready** |

## Required gates before live use

1. Make execution mode authoritative and enforce it at startup, signal processing, Telegram execution, and HTTP API boundaries.
2. Separate Paper, Deriv Demo, and Live integrations so Paper can start without broker credentials and no request can cross account environments.
3. Implement authenticated account balance retrieval and reject execution when the selected account or balance cannot be verified.
4. Implement Deriv order lifecycle and settlement tracking, and reconcile real outcomes into durable storage.
5. Persist Paper account state and recover pending positions after restart; use observed expiry prices.
6. Make order idempotency atomic and safe for pending, concurrent, and uncertain requests.
7. Fix and verify the Next.js client component, wire the dashboard to supported endpoints, and keep execution controls disabled until the backend safety gates are complete.
8. Run Python tests, frontend typecheck/build, integration tests, and a controlled Deriv Demo lifecycle test. Record actual results rather than inferred pass status.
9. Reconcile the root README, web README, and status docs against the tested implementation.

**This document records the inspected repository state. It does not certify deployment readiness, authorize Live execution, or claim that any listed gap has been fixed.**
