# Absolute Dollar Intelligence — Masterclass Framework
**ADSA v7.0 | Operator Training Programme**
*From Nairobi to the Global Markets — Augmented Intelligence for Consistent Traders*

---

## PROGRAMME OVERVIEW

The Absolute Dollar Masterclass is a 4-week structured training programme built around the ADSA v7.0 agent. The agent is a **decision support system** — an augmented intelligence that externalizes the analysis, not a black box. Operators who understand the framework trade with intelligence. Those who skip the foundation remain dependent on signals they cannot validate.

**Who this is for:** Beta operators, new community members, and anyone trading with Absolute Dollar Intelligence tools.

**Format:** Weekly masterclass sessions (operator-led study + live agent observation)

**Tools required:** TradingView (with ADSA v7.0 strategy), MT5 account (Deriv/Bybit), this masterclass guide, the Risk Cheat Sheet Template.

---

## PART 1 — THE PHILOSOPHY

### What the Agent Is

The Absolute Dollar Agent is a **glass box externalizing system** — every decision it makes is visible, labeled, and explainable. When it fires a signal, the HUD (dashboard) shows you exactly why:

- Which of the 4 fractal layers are aligned
- What the 5-layer AI narrative says about each timeframe
- Where the VWAP swing sits (bull/bear)
- What the Fibonacci trend and RSI momentum state is
- The exact SL, TP1, TP2, TP3 prices and their dollar values
- The minimum unit risk so you always know what you're risking

The agent does not trade for you. It maps the field and puts the intelligence in front of you. **You are the Master Control Operator.** The agent is your mission intelligence officer.

### What the Agent Is Not

- It is not a "VIP signals" service. You will always know WHY a signal was generated.
- It is not infallible. It has a SL Autopsy Engine for a reason — losses happen, and the agent explains them.
- It does not replace your understanding of price. The masterclass exists so you understand what price is doing independently of the agent.

### Absolute Dollar Trading Edge

Four years of intraday momentum trading has been codified into this system. The edge is:

1. **Fractal alignment**: Only trade when all 4 layers point the same direction
2. **VWAP momentum**: The swing VWAP tells you the path of least resistance
3. **3-TP progression**: Securing wins at TP1 (1:1) makes the system psychologically executable
4. **Glass box transparency**: Every signal has a reason. Every loss has an autopsy.

---

## PART 2 — THE TRADING PLAN (AGENT FRAMEWORK)

This section codifies the exact framework the agent uses to take positions. Operators must understand this to validate agent signals manually.

### The Architecture: TRIGGER → GATE → CONFIDENCE → EXECUTION

```
TRIGGER   →  ATM Bot (timing: when price momentum shifts)
GATE      →  Liquidity Trail direction (truth: which direction is allowed)
CONFLUENCE → MTF + Structure + RSI + VWAP + Fib + Volume Profile
CONFIDENCE → Score must exceed threshold (60% default = Moderate Claw Mode)
EXECUTION  → Only 4-layer aligned signals with passing confidence fire
```

The ATM Bot fires the WHEN. The 4-layer fractal determines the WHICH WAY. Confluence builds WHY. All three must agree before execution.

### Fractal 4-Layer Consensus

| Layer | Timeframe | Role | Name |
|-------|-----------|------|------|
| L1 Sovereign | Daily (D) | Macro veto — sets directional bias | Commander |
| L2 Anchor | H1 (60m) | Intraday commander | Anchor |
| L3 Filter | M15 (15m) | Tactical navigator | Navigator |
| L4 Exec | Current chart TF | Execution timing | Executor |

**Master Sync (highest quality signal):** All 4 layers aligned in the same direction.
- `FULLY ALIGNED: BULLISH (4-LAYER)` = best long signals
- `FULLY ALIGNED: BEARISH (4-LAYER)` = best short signals

**Counter-Trend (CT-L / CT-S):** L1 Sovereign opposes the signal. These are labeled on chart but require extra caution. Only trade with clear M15 tactical reason.

### Signal Quality Hierarchy

```
MASTER SYNC (4-layer)     → Highest confidence. Trade with full position.
3-layer alignment         → Good. Trade with standard position.
2-layer alignment         → Caution. Reduce size. Wait for better entry.
L4 PULLBACK signals       → WAIT. Exec layer must flip before entry.
STANDING ASIDE / SILENCE  → No trade. Admin override or no alignment.
```

### The ATM Bot (Trigger Engine)

The ATM Bot uses an ATR-based trailing stop system:
- **Long trigger:** Price crosses above the buy trail (trail_buy) on a confirmed bar
- **Short trigger:** Price crosses below the sell trail (trail_sell) on a confirmed bar
- **Regime filter:** If RSI is bearish, long triggers are rejected (shown as X marks on chart)
- **VWAP filter (optional):** Additional confirmation that VWAP swing matches direction

### RSI Momentum State

| RSI State | Condition | Direction Allowed |
|-----------|-----------|-------------------|
| Positive (Bull) | RSI > 55, EMA rising | Long signals pass |
| Negative (Bear) | RSI < 50, EMA falling | Short signals pass |
| Neutral | Between zones | Signals filtered out |

### VWAP Swing (The Truth Line)

The Adaptive VWAP tracks the dominant swing direction:
- **BULL label on chart:** VWAP anchored from most recent swing low — bullish path
- **BEAR label on chart:** VWAP anchored from most recent swing high — bearish path

On M1: Use swing period 100. On M5: Use swing period 50.

Price above VWAP in a bull swing = in the trade. Price below VWAP in a bear swing = in the trade. Price crossing VWAP against trend = warning.

### Premium, Discount, Equilibrium

The agent plots these zones based on the current VWAP swing range:
- **Premium zone (top 25%):** Overpriced relative to VWAP anchor — short bias, or TP zone for longs
- **Equilibrium (middle 50%):** Fair value — most contested area
- **Discount zone (bottom 25%):** Underpriced relative to VWAP anchor — long bias, or TP zone for shorts

For intraday momentum: enter from discount (long) or premium (short), target the opposing zone.

### Trade Progression Engine (3-TP System)

| Level | RR | % of Position | Notes |
|-------|----|---------------|-------|
| TP1 | 1:1 | 33% closed | Secures first profit, psychological lock-in |
| TP2 | 1.5:1 | 50% of remainder | Second partial, trades funded |
| TP3 | 2:1 | Remaining | Trail in Holder Mode |

**Holder Mode (post-TP3):** The remaining position is trailed using either:
- **Structural trail:** Pivot low (long) or pivot high (short) — price must break structure to exit
- **VWAP trail:** Position stays open as long as VWAP remains favorable

### SL Autopsy Engine

When a stop loss is hit, the agent generates a contextual explanation:
- What the regime state was at entry
- Whether the Sovereign layer was counter-trend
- Whether RSI momentum failed after entry
- Whether VWAP crossed against the trade

This is the glass box at work. Every loss teaches you something. Log the autopsy.

---

## PART 3 — MULTI-TIMEFRAME ANALYSIS (TOP-DOWN)

The operator conducts this analysis **before market open** (recommended: 05:30–06:00 UTC, before Asia close).

### The Daily Candle Framework

The daily candle = 1 unit of the market's intent. On H1, 24 candles fill that unit. On H4, 6 candles. On M15, 96 candles. Understanding where you are in the daily development cycle is critical.

```
ASIA SESSION    → Price discovery, range formation, liquidity sweep
LONDON SESSION  → Primary trend initiation, breakouts
NEW YORK SESSION → Continuation or reversal, high volume
```

Use ICT Killzones & Pivots indicator as a session awareness supplement. The agent dashboard also shows session context in the Core Signals block.

### H1 — Intraday Map (Sovereign Anchor Layer)

**What to look for:**
- Current VWAP swing direction (BULL / BEAR label)
- Structure: is price making HH/HL (bull) or LH/LL (bear)?
- Premium / Discount / Equilibrium — where is price within the H1 range?
- Previous Day High (PDH) / Previous Day Low (PDL) — is price above or below?
- Value Area: VAH, VAL, POC from H1 volume profile
- ATR reading — what is the average range for this asset today?

**Dashboard read on H1:**
Check the 5-Layer AI Narrative block:
```
D  (Sovereign)  → Your L1 directional bias
H4 (Anchor)     → Confirms or disagrees with daily
H1              → Your intraday map layer
M15             → Tactical field
M5              → Entry alignment
```

### M15 — Tactical Battlefield (Navigator Layer)

**What to look for:**
- CHoCH (Change of Character) — first structural shift, early warning
- BOS (Break of Structure) — confirmed structural break
- Swing High / Swing Low — strong vs weak
- BSL (Buy-Side Liquidity) — equal highs, previous swing highs
- SSL (Sell-Side Liquidity) — equal lows, previous swing lows
- PDL (Previous Day Low) / PDH (Previous Day High)
- VAH / VAL / POC from daily volume profile at M15 view

**The tactical question on M15:** Has price swept liquidity and is now showing a CHoCH in my direction? That CHoCH is the structural evidence that smart money has repositioned.

### M5 — Execution Preparation Layer

**What to look for:**
- VWAP alignment with H1 direction (swing period: 50)
- Core signals in dashboard: ATM, VWAP, Fib Trend, RSI, MACD
- Supply zone / Demand zone labels from agent
- Agent sync phase: is it saying FULLY ALIGNED or waiting?
- Current active trade setup (if any) — check the Trade Setup block

**The M5 question:** Is the agent showing an active or pending setup? Is the Fractal 4-Layer sync phase aligned with my H1 read?

### M1 — Entry Precision Layer

**What to look for on M1:**
- Core signals from dashboard (ATM direction, RSI state)
- VWAP swing direction (period: 100 on M1)
- Entry label from agent (Long Entry / Short Entry)
- Confirmation of CHoCH from M15 replicated at M1 level
- Current SL/TP levels as shown in Trade Setup block

**The M1 question:** Has the agent fired a signal? Does it match my H1 map and M15 structure read? If yes → execute. If no → wait.

---

## WEEK 1 — RISK MANAGEMENT FOUNDATION

### Module 1.1 — Understanding Pip Value and Lot Size

**Learning objective:** Operator can calculate dollar risk for any trade on any asset before entering.

**Exercise:**
1. Open MT5 → Symbol Specification for XAUUSD
2. Note Contract Size, Tick Size, Tick Value
3. Fill in the XAUUSD section of the Risk Cheat Sheet Template
4. Answer: If I risk 0.05 lots with a 60-point SL on XAUUSD, what is my dollar risk?
5. Answer: What lot size do I need to risk exactly $10 with a 50-point SL on XAUUSD?

**Answer guide (XAUUSD at $1/pt/lot):**
- 0.05 lots × 60 pts × $1/pt/lot = **$3.00 risk**
- $10 ÷ (50 pts × $1/pt/lot) = **0.20 lots**

### Module 1.2 — The 3-TP System in Dollar Terms

**Exercise:** Given the following agent signal, calculate the full dollar outcome:

> XAUUSD Long | Entry: 3,980 | SL: 3,960 | TP1: 4,000 | TP2: 4,010 | TP3: 4,020 | Lot: 0.10

```
SL Distance:  3,980 - 3,960 = 20 points  → Risk = 20 × $1 × 0.10 = $2.00
TP1 Distance: 4,000 - 3,980 = 20 points  → Reward = 20 × $1 × 0.10 × 0.33 = $0.66 (1:1, 33%)
TP2 Distance: 4,010 - 3,980 = 30 points  → On 50% of remaining = $0.50 × 0.50 = $0.67 (1.5:1)  
TP3 Distance: 4,020 - 3,980 = 40 points  → On final runner = $0.40 × remaining lots (2:1)
```

Operators complete this exercise for GBPUSD, Volatility 75, and their primary traded assets.

### Module 1.3 — Account Risk % Reality Check

**Exercise:** With a $100 account and a $3.00 trade risk, what % of account is at risk?
- $3.00 / $100 = 3% risk per trade

**Exercise:** With a 10K prop challenge account and $15 risk, what % per trade?
- $15 / $10,000 = 0.15% per trade — very conservative, excellent for prop

**Key rule:** On small accounts ($50–$100), never risk more than 5% per trade. Use minimum lot and verify dollar risk against the cheat sheet before every trade.

---

## WEEK 2 — READING THE AGENT DASHBOARD (HUD MASTERY)

### Module 2.1 — The Dashboard Anatomy

The agent dashboard has six main blocks:

```
┌─────────────────────────────────────┐
│ AUTO / Sovereign: BEAR/BULL         │ ← Admin + Sovereign state
│ Score: -11/15 | Public: SANITIZED   │ ← Confidence score + broadcast mode
├─────────────────────────────────────┤
│ FRACTAL 4-LAYER SYNC                │ ← Sync phase label (the key read)
│ L1/L2/L3/L4 status + L4 PULLBACK   │
├─────────────────────────────────────┤
│ CORE SIGNALS                        │ ← Asset, price, ATR, session
│ NY SESSION | ATR | Daily Context    │ ← ATM, VWAP, Fib, RSI, MACD state
├─────────────────────────────────────┤
│ 5-LAYER AI NARRATIVE                │ ← Tree view: D / H4 / H1 / M15 / M5
│ Each layer: Regime / VWAP / Fib     │
│ / RSI state                         │
├─────────────────────────────────────┤
│ AGENT ADVICE                        │ ← Plain English trade bias
├─────────────────────────────────────┤
│ LIQUIDITY                           │ ← Near swing high/low context
│ Buy-side / Sell-side levels         │
├─────────────────────────────────────┤
│ TRADE SETUP                         │ ← Active trade details
│ Phase, ID, Direction, Risk          │ ← Entry, SL, TP1, TP2, TP3
│ Live P&L, VWAP Trail, Peak          │
├─────────────────────────────────────┤
│ TODAY                               │ ← Daily performance summary
│ Sigs / WR / PF / Net pts / Report   │
└─────────────────────────────────────┘
```

### Module 2.2 — Reading the Fractal Sync Phase

This is the single most important line on the dashboard. Operator must be able to read this instantly.

| Sync Phase Label | Meaning | Action |
|-----------------|---------|--------|
| FULLY ALIGNED: BULLISH (4-LAYER) | All 4 layers bull | Take long signals |
| FULLY ALIGNED: BEARISH (4-LAYER) | All 4 layers bear | Take short signals |
| L4 PULLBACK — Wait for Exec Bear Flip | L1–L3 bear, L4 pulling back | Wait. Don't jump early. |
| L4 PULLBACK — Wait for Exec Bull Flip | L1–L3 bull, L4 pulling back | Wait. The dip is not an entry yet. |
| L3 PULLBACK — Wait for Filter Bear Flip | L1–L2 bear, M15 not yet | Wait for M15 to flip |
| L2 PULLBACK — Wait for Anchor Bear Flip | L1 bear, H1 not yet | Early in the setup |
| SOVEREIGN NEUTRAL | Daily is flat | Stand aside or reduce size |

### Module 2.3 — The 5-Layer AI Narrative Tree

Each row in the narrative follows this structure:

```
[Layer] (Regime) → Regime :Direction V.WAP :Direction Fib Trend :Direction RSI :Direction
```

Example read:
```
H1 (Anchor) ●
Regime :Short V.WAP :Bear Fib Trend :Bear RSI :Bear    ← Full bear alignment on H1
```

If H1, M15, and M5 all show `:Bear RSI :Bear` → extremely high confluence for shorts. If RSI shows `:Neut` on any layer → that layer is undecided, reduce confidence.

### Module 2.4 — Trade Setup Block Walkthrough

When an active trade is running, the Trade Setup block shows:

```
Phase: TP3 HIT — HOLDER MODE    ← Trade progression phase
ID: ATM-20260624-1527-BUY-26    ← Unique trade identifier
Dir: LONG                        ← Direction
Min-Unit Risk: -$6.07 | Variable: $15 → 2.472 Units
Entry: 3981.89  SL: 3975.82 (60.7 pts)
TP1: 3987.96 ✓  (60.7 pts)    ← Checked = already hit
TP2: 3990.99 ✓  (91 pts)
TP3: 3994.03 ✓  (121.4 pts)   ← TP3 hit = now in Holder Mode
VWAP Trail: 3994.37
Peak: 209.7 pts
```

Operator reads this in 10 seconds: Long trade, all TPs hit, trailing at 3994.37. Peak unrealized was 209.7 points.

---

## WEEK 3 — MULTI-TIMEFRAME ANALYSIS IN PRACTICE

### Module 3.1 — The Pre-Session Ritual (05:30–06:30 UTC)

Before Asia close / London open, complete this checklist:

**Step 1 — H1 Map (5 minutes)**
- [ ] What is the Sovereign (Daily) direction? Check dashboard L1 label.
- [ ] Where is price relative to PDH / PDL? Dashboard shows: Above PDH / Below PDL / Inside Daily Range
- [ ] What is the H1 VWAP swing direction? (BULL/BEAR label on H1 chart)
- [ ] Is H1 in premium, discount, or equilibrium?
- [ ] What is today's ATR? (Shows in Core Signals block)

**Step 2 — M15 Structure Read (5 minutes)**
- [ ] Mark key swing highs and swing lows (strong vs weak)
- [ ] Is there a recent CHoCH? In which direction?
- [ ] Where is BSL (equal highs / previous swing highs)?
- [ ] Where is SSL (equal lows / previous swing lows)?
- [ ] What does the M15 layer show in the AI narrative tree?

**Step 3 — Agent Sync Phase (2 minutes)**
- [ ] What phase is the agent showing? (Dashboard top section)
- [ ] Is it FULLY ALIGNED, PULLBACK waiting, or NEUTRAL?
- [ ] If PULLBACK — note what needs to flip for alignment

**Step 4 — Risk Calibration (3 minutes)**
- [ ] What is the current ATR? (Determines approximate SL size)
- [ ] For that SL size, what is my dollar risk at my intended lot size? (Use cheat sheet)
- [ ] Is that dollar risk within my account risk budget for today?

### Module 3.2 — Identifying the VWAP Swing Play

The VWAP swing is the intraday trade thesis. Every valid long or short has a VWAP reason.

**Long thesis (bullish VWAP swing):**
- VWAP is anchored from a swing low (BULL label visible)
- Price is in discount zone (below VWAP or at equilibrium)
- RSI is positive or turning positive
- H1 narrative shows Long V.WAP and Bull RSI
- M15 shows CHoCH from a low, with a higher low forming

**Short thesis (bearish VWAP swing):**
- VWAP is anchored from a swing high (BEAR label visible)
- Price is in premium zone (above VWAP or at equilibrium)
- RSI is negative or turning negative
- H1 narrative shows Short V.WAP and Bear RSI
- M15 shows CHoCH from a high, with a lower high forming

### Module 3.3 — Counting H4 Candles in the Day

```
Daily candle = 6 H4 candles
The session cycle (Asia → London → NY) maps to:
  Asia:    H4 candle 1–2 (overnight accumulation)
  London:  H4 candle 3–4 (primary trend move)
  NY:      H4 candle 5–6 (continuation or reversal)
```

When you are in London open (H4 candle 3), the M15 has already produced 4 candles (1 per 15 min × 4 = 1 hour). On M1, London has produced 60 candles. This awareness lets you judge: is this early in the move, or late?

### Module 3.4 — Session Awareness with ICT Killzones

Use ICT Killzones & Pivots as a complement to the agent dashboard.

| Session | UTC Time | What to Watch |
|---------|----------|---------------|
| Asia (Tokyo) | 00:00–09:00 | Range formation, liquidity build |
| London Open | 07:00–10:00 | Primary breakout zone, CHoCH candidates |
| NY Open | 13:00–16:00 | Volume spike, continuation or reversal |
| London Close | 16:00–17:00 | Potential reversal setups |
| NY PM | 18:00–22:00 | Lower volume, trend continuation |

---

## WEEK 4 — EXECUTION, TRADE MANAGEMENT & FILTERS

### Module 4.1 — The Entry Confluence Checklist

Before executing any signal, confirm these manually:

**MINIMUM requirement (agent must show):**
- [ ] Fractal 4-Layer Sync Phase: FULLY ALIGNED (4-layer) or at minimum 3-layer
- [ ] ATM signal fired (Long Entry or Short Entry label on chart)
- [ ] RSI state matches direction (Bull for long, Bear for short)
- [ ] VWAP swing matches direction

**PREFERRED additional confluence:**
- [ ] M15 shows CHoCH in direction of trade
- [ ] Entry is from discount zone (long) or premium zone (short)
- [ ] Volume Profile: price above VAL (long) or below VAH (short)
- [ ] Fib trend in agreement
- [ ] Session: London or NY open (not Asia flatline)

**Counter-signal killers (do not trade if any present):**
- [ ] Agent says SOVEREIGN NEUTRAL or STANDING ASIDE
- [ ] Sync phase shows PULLBACK (wait for it to flip)
- [ ] RSI is neutral (not bull or bear confirmed)
- [ ] ATR is very low (asset is ranging, low momentum)
- [ ] You are in a ranging consolidation visible on H1

### Module 4.2 — Trade Execution via TradeSgnl Handshake

When trading automatically via TradeSgnl EA:

**The alert message format (from June TradeSgnl Syntax):**
```
LICENSE_ID,XAUUSD,buy,vol_dollar={{risk}},sl_price={{sl}},tp1_price={{tp1}},pct1=0.33,tp2_price={{tp2}},pct2=0.50,tp3_price={{tp3}},exent=1
```

Key parameters:
- `vol_dollar` = dollar risk amount (agent calculates position size from this)
- `sl_price` = exact SL price (not pips — exact price)
- `pct1=0.33` = 33% of position closes at TP1
- `pct2=0.50` = 50% of remaining closes at TP2
- `exent=1` = exit entire remaining position at TP3

For manual fixed lot override (used on specific synthetic indices):
```
vol_lots=0.05
```

**TradeSgnl Handshake verification:** After every executed trade, verify in MT5 that:
- Order opened at correct price
- SL and TPs are set correctly
- Lot size matches expected calculation from risk cheat sheet

### Module 4.3 — Managing Trades in Progress

**Phase: ENTRY ACTIVE**
- Trade is open, none of the TPs hit yet
- Watch: Is price respecting the VWAP trail? Is structure holding?
- Only manual exit if: clear reversal signal on M5 AND agent switches to opposite direction

**Phase: TP1 HIT**
- 33% secured. Trade is now "funded" — you are trading with profit
- Remaining position: SL stays at original level until TP2
- Begin watching for TP2 levels

**Phase: TP2 HIT**
- 50% of remainder secured. Runner active.
- SL can be moved to break-even or to just below TP1 level
- Runner now in "free trade" territory

**Phase: TP3 HIT — HOLDER MODE**
- All TPs hit. Runner continues with trailing stop
- Structural trail: trail stop below last confirmed pivot low (long) or above last pivot high (short)
- VWAP trail: position exits when VWAP crosses against the trade
- This is where the "Peak" points in dashboard show the maximum unrealized gain

### Module 4.4 — Filtering Low-Probability Setups

**Ranging Market Filter:**

Signs that an asset is ranging (avoid fresh signals):
- ATR is significantly below its average (dashboard shows low ATR reading)
- Price is bouncing between two levels without a new HH/HL or LL/LH pattern
- Volume profile shows a very wide, flat distribution (no clear POC direction)
- H1 VWAP is flat (not clearly angled up or down)
- 5-Layer AI Narrative shows mixed readings (some layers Bull, some Bear, some Neutral)

**What to do in ranging markets:**
- Reduce lot size by 50%
- Only trade at the extremes of the range (demand zone for long, supply zone for short)
- Wait for the range break with a strong BOS candle before resuming normal size

**Low ATR Filter:**

If ATR is below 30% of its recent average:
- Expected move is compressed
- SL may be tight but TP targets are also close → poor RR potential
- Signal may fire but the move won't follow through
- Action: Pass on this trade, wait for ATR expansion

**Counter-Trend Warning (CT-L / CT-S labels):**
- These are signals that go against the Sovereign (Daily) layer
- They can work but have lower win rate
- Only trade CT signals with reduced size (50% of normal lot)
- Require extra M15 confluence: confirmed CHoCH, clear liquidity swept above/below

---

## PART 4 — AUTOMATION TIER vs MANUAL TIER

### Tier 1: Manual Operators (All Beta Operators — Weeks 1–4)

- Use the agent as an intelligence overlay on TradingView
- Read the dashboard and conduct top-down analysis yourself
- Execute trades manually on MT5 using risk cheat sheet
- Log every trade with: asset, direction, entry, SL, TP1/2/3, dollar risk, dollar P&L, sync phase at entry, dashboard screenshot

### Tier 2: Semi-Automated Operators (TradingView + TradeSgnl Basic)

- Agent fires alerts → TradeSgnl EA places trades on MT5
- Operator monitors dashboard, can manually close or adjust
- Still requires: pre-session analysis, understanding sync phase, awareness of active trades

### Tier 3: Master Control Operator (TradingView Premium + TradeSgnl Advanced)

- Full automation: alert → EA → MT5 execution with all TPs and partial exits
- Operator role: strategic oversight, watchlist management, override authority
- Required competency: Must have completed Weeks 1–4 and can execute the top-down analysis manually without the agent
- Access: Invite only via Absolute Dollar Intelligence

---

## PART 5 — PERFORMANCE TRACKING

### Daily Log Template

| Field | Entry |
|-------|-------|
| Date | |
| Asset | |
| Trade ID | |
| Direction | |
| Sync Phase at Entry | |
| Layer Alignment (1/2/3/4) | |
| Session (Asia/London/NY) | |
| Entry Price | |
| SL Price | |
| SL in pips/pts | |
| Lot Size | |
| Dollar Risk | |
| TP1 Price / Hit? | |
| TP2 Price / Hit? | |
| TP3 Price / Hit? | |
| Final P&L (pts) | |
| Final P&L ($) | |
| Notes / Autopsy | |

### Weekly Review Questions

1. What was my win rate this week? How does it compare to the agent's displayed WR?
2. Which sync phase produced the most wins? (4-layer, 3-layer, or counter-trend?)
3. What was my average RR on completed trades?
4. Were there any trades I took that the agent did not signal? Result?
5. Were there any agent signals I passed on? What happened after?
6. What was my worst loss? What does the SL autopsy show?
7. Am I respecting the dollar risk limit per trade consistently?

---

## APPENDIX A — QUICK REFERENCE CARD

### Agent Dashboard Read Sequence (30 seconds)

```
1. Top line → Sovereign direction (BULL/BEAR/NEUT)
2. Sync phase → FULLY ALIGNED / PULLBACK / NEUTRAL
3. Score block → How many layers are aligned (-15 to +15)
4. Core signals → ATM direction, VWAP, Fib, RSI, MACD state
5. 5-Layer narrative → D / H4 / H1 / M15 / M5 all pointing same way?
6. Agent Advice → Plain English summary
7. Trade Setup → Is there an active trade? What phase?
8. TODAY block → Daily performance context
```

### Entry Decision Tree

```
Is Sync Phase FULLY ALIGNED?
  YES → Is RSI in momentum (bull or bear)?
          YES → Is VWAP swing matching direction?
                  YES → Is entry in discount (long) or premium (short)?
                          YES → CHECK RISK (SL × pip value × lot = $ within budget?)
                                  YES → EXECUTE
                                  NO  → Reduce lot size, re-check
                          NO  → WAIT for price to pull back
                  NO  → WAIT for VWAP to confirm
          NO  → WAIT for RSI regime to establish
  NO  → Is it a 3-layer alignment with clear reason for 4th layer lag?
          YES → Trade with 50% size only
          NO  → DO NOT TRADE
```

### Common Dashboard Signal Combinations (High Confidence)

**Best Long Setup:**
- Sovereign: BULL | Sync: FULLY ALIGNED BULLISH
- 5-Layer all showing: `:Long V.WAP :Bull RSI :Bull`
- Price in discount zone
- M15 CHoCH to the upside visible
- Session: London or NY open

**Best Short Setup:**
- Sovereign: BEAR | Sync: FULLY ALIGNED BEARISH
- 5-Layer all showing: `:Short V.WAP :Bear RSI :Bear`
- Price in premium zone
- M15 CHoCH to the downside visible
- Session: London or NY open

---

## APPENDIX B — GLOSSARY

| Term | Definition |
|------|------------|
| CHoCH | Change of Character — first structural break against the prior trend, early warning |
| BOS | Break of Structure — confirmed structural continuation |
| BSL | Buy-Side Liquidity — resting orders above swing highs (target for shorts) |
| SSL | Sell-Side Liquidity — resting orders below swing lows (target for longs) |
| PDH/PDL | Previous Day High / Previous Day Low — key daily reference levels |
| VAH/VAL/POC | Value Area High / Low / Point of Control — volume profile levels |
| Holder Mode | Post-TP3 trailing mechanism for the remaining position runner |
| CT-L / CT-S | Counter-Trend Long / Short — trade against the Sovereign layer |
| ATR | Average True Range — measures asset volatility (SL buffer multiplier) |
| VWAP Swing | Volume-weighted average price anchored to the most recent swing high or low |
| Master Sync | All 4 fractal layers aligned — highest confidence signal state |
| Glass Box | The agent's principle of transparent, explainable decision-making |
| Absolute Dollar | Risk expressed in real dollar amounts, not just percentages |

---

*Absolute Dollar Intelligence © 2026 | ADSA v7.0 | Masterclass Framework v1.0*
*Built in Nairobi. Traded globally. Not financial advice.*
