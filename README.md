# Absolute Dollar Agent (ADA)
## Just a Really Very Intelligent Sidekick

A glassbox trading system for Deriv. **TRON** detects on the price grid in
Pine Script and emits nothing but signal. **ADA** — codename `tradersmind/`
in this repo — receives, classifies, narrates, remembers, sizes, and
executes. A human taps today; autonomy comes later, always under a risk
governor.

No blackbox. Every action ADA takes traces back to a named TRON field.

---

## Repo Structure

```
TRON_Glassbox_SignalGenerator.pine   ← TRON, the Brain. Pine Script. Load on TradingView.
                                        Never modified by the backend build (locked doctrine).

tradersmind/                         ← ADA, the Sidekick. One folder, the only deployed system.
├── tron/                              webhook receiver, 18-signal models, validator
├── mind/                              classifier + router, episodic memory, narrative engine
├── governor/                          sizing law + hard risk limits, live-mode gate
├── bridge/                            Deriv execution client, contract mapper
├── body/                              Telegram — tap-to-execute, status/risk/history
├── face/                              web dashboard
├── config/settings.yaml               narrative templates, risk band, router rules
├── tests/                             31 tests, all passing
└── README.md                          run instructions + build status for this tree

docs/
└── TRON_ALERTS_GUIDE.md              ← operator's guide to reading TRON's alerts
                                        (signal hierarchy, masterclass, dashboard reference)

CLAUDE.md                             ← master build spec, doctrine, and the full
                                        verification/rebuild/purge/rebrand log (§20–23)
README.md                             ← you are here
```

One Pine file. One Python tree. One doctrine document. Nothing else.

---

## Status — verified against CLAUDE.md today, section by section

Nothing has placed a confirmed real order yet — that's what today's Replit
+ Telegram test is for. Everything below was checked against the actual
code in this repo just now, not assumed from memory.

### ✅ Built and verified (tests pass, or hand-verified against a mocked Deriv client)

| Spec section | What's confirmed working |
|---|---|
| §6 Webhook Contract | `POST /webhook/tron?key=SECRET` — exact match, always checked. Rejects malformed/unauthorized payloads. |
| §7 18-Signal Classification | `mind/router.py` classifies all 18 signal types EXECUTE/CONTEXT — 1:1 tested. Same-bar flip-priority suppression (H4 > MTF > TRAIL) enforced. |
| §8 Routing Matrix | All three flagged open decisions asked and answered (fixed style-priority list, zone breaks stay CONTEXT permanently, entries tap-executable to Rise/Fall as override). |
| §9 Signal Flow | Full pipeline wired: validate → classify → narrate → remember → size → route → tap or auto-execute → ledger. |
| §10 RiskGovernor | Sizing law ($0.35–$1.00 confidence-scaled) plus every hard limit ($5 ceiling, $50 daily loss, 3-loss streak, 5-min cooldown, 85%/4-sync auto-gate, 10%-of-balance cap). 100-demo-trade live-mode gate enforced at boot, not just documented — refuses to start in `live` below threshold. |
| §13 Narrative Engine | Template-based, zero LLM, all 18 signal types have a matching template (a real bug where this crashed on every non-SNIPER signal was found and fixed while verifying). |
| §14 Episodic Memory | SQLite ledger logs every signal (CONTEXT included), with `tier`/`env`/`executed`/`contract_id` columns to distinguish "signal seen" from "order placed." |
| §5/§18 No paper mode | `TRADING_MODE` is `demo`/`live` only, everywhere — confirmed via repo-wide search, zero `paper` branches remain. |
| §15 (partial) Risk panel | Telegram `/risk` now reports the live demo-trade counter (`N/100`) toward the live-mode gate — this was missing until today's pass. |

### ⚠️ Built but incomplete — don't mistake these for done

| What | The gap |
|---|---|
| §14 KNN similarity | `mind/similarity.py`'s `SimilarityEngine` is instantiated in `main.py` but **never called**. The sizing law's edge signal today comes from a simpler win-rate query (`get_stats_by_signal_type`), not true KNN feature-vector matching. |
| §16 Deriv Bridge | Bulk Purchase REST client is implemented and structurally matches the endpoint's real field names — but has **not** placed a real order in this session (no live credentials in this environment). Today's test is the first real check. |
| §15 Web dashboard | `face/` exists (session stats, live signal feed, TradingView embed) but is not the chart-centric UI with TRON markers overlaid on price that §15 specifies. |

### ❌ Not built — explicit gaps, not silent omissions

- Chart-centric UI with TRON signal markers on price (§15)
- Cross-signal confidence modifiers from CONTEXT signals onto a co-occurring EXECUTE signal (§7)
- LightGBM edge model (§14 — needs 50–70 logged episodes first, by design)
- OAuth2 + PKCE Deriv upgrade — balance checks, live quotes, settlement watching (§16)
- Multi-pair agent loader, Telegram Mini App (post-MVP roadmap, §17)

---

## Quickstart — for today's Replit + Telegram test

1. Load `TRON_Glassbox_SignalGenerator.pine` on a TradingView chart (Premium plan, for reliable webhooks).
2. On Replit: Secrets must match `tradersmind/.env.example` — notably `DERIV_ACCOUNT_ID`, which the real Bulk Purchase endpoint requires but wasn't in the original spec's env list.
3. Deploy (`.replit` already points at `tradersmind/`) and confirm the boot log shows `Mode: DEMO` and `Live-mode gate cleared` is **not** printed (you're not in live mode yet).
4. Point the TradingView alert webhook at `https://your-replit-url/webhook/tron?key=YOUR_SECRET`.
5. Message your Telegram bot once (registers you as the operator), then try `/status`, `/risk`, `/history` to confirm it's reading real state, not placeholders.
6. Wait for (or force) a TRON signal and confirm: CONTEXT-tier signals arrive with no buttons, EXECUTE-tier signals arrive with tap buttons, and a tap actually reaches Deriv.

## Broker & Contracts

Deriv only. Vanilla Options, Rise/Fall, and Multipliers all route through
the same Bulk Purchase REST client — one pipeline, one broker, no
third-party bots anywhere in the bridge.

## Where to Read Next

- **`CLAUDE.md`** — the master spec, doctrine, and the complete history of
  what was verified, rebuilt, purged, and rebranded (§20–23).
- **`tradersmind/README.md`** — how to run ADA, its architecture, and its
  own up-to-date built/not-built list.
- **`docs/TRON_ALERTS_GUIDE.md`** — what each TRON alert means and how to
  act on it, independent of whichever backend is deployed.
