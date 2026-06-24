# Absolute Dollar Intelligence — Risk & P&L Matrix Template
**ADSA v7.0 | Operator Risk Cheat Sheet System**
> This is a fill-in template, not a hardcoded cheat sheet. Values must be sourced directly from your MT5 Symbol Specification dialog to ensure accuracy per broker/account type.

---

## HOW TO GET YOUR REAL PIP VALUE FROM MT5

1. Open MT5 → Market Watch → Right-click your symbol → **Specification**
2. Note down:
   - **Contract Size** (e.g. 100 for XAUUSD, 100000 for GBPUSD)
   - **Tick Size** (smallest price movement, e.g. 0.01 for Gold)
   - **Tick Value** (dollar value of one tick at 1.0 lot, in account currency)
   - **Volume Min / Volume Max / Volume Step**
3. Calculate: `Pip Value per Lot = Tick Value / Tick Size × One Pip`

---

## THE MASTER FORMULA

```
Pip Value ($/lot) = Contract Size × Pip Size × Quote-to-USD Rate

Dollar P&L         = Price Move (pips) × Pip Value × Lot Size

Dollar Risk at SL  = SL Distance (pips) × Pip Value × Lot Size

Dollar Reward at TP = TP Distance (pips) × Pip Value × Lot Size

RR Ratio           = Dollar Reward / Dollar Risk

Required Lot Size  = Dollar Risk Target / (SL Distance × Pip Value)
```

> **Pip Size vs Tick Size:** A "pip" is the 4th decimal for forex (0.0001), 2nd decimal for gold (0.01), etc.
> On MT5, the *point* is the smallest tick. For a 5-digit forex broker, 1 pip = 10 points.

---

## SECTION A — XAUUSD (GOLD SPOT) — WORKED EXAMPLE

**MT5 Symbol Specification (Deriv):**
| Parameter | Value |
|-----------|-------|
| Contract Size | 100 troy oz |
| Pip / Point Size | 0.01 |
| Pip Value @ 1.0 lot | $1.00 per pip |
| Volume Min | 0.01 lot |
| Volume Step | 0.01 lot |

> Source your exact tick value from your MT5 spec. For Deriv: 1 lot × 100 oz × $0.01 = **$1.00/pip/lot**

### XAUUSD — Pip Value by Lot Size

| Lot Size | $/pip | $/point (0.01 move) |
|----------|-------|---------------------|
| 0.01     | $0.01 | $0.01 |
| 0.02     | $0.02 | $0.02 |
| 0.03     | $0.03 | $0.03 |
| 0.05     | $0.05 | $0.05 |
| 0.10     | $0.10 | $0.10 |
| 0.20     | $0.20 | $0.20 |
| 0.50     | $0.50 | $0.50 |
| 1.00     | $1.00 | $1.00 |

### XAUUSD — P&L Matrix (Price Move × Lot Size)

> XAUUSD moves are measured in POINTS (0.01 = 1 point). The agent labels them as "pts" in dashboard.
> A typical SL on M1/M5 is 30–80 points. TP1 at 1:1 matches the SL, TP3 at 2:1 doubles it.

| SL / Move (pts) | 0.01 lot | 0.05 lot | 0.10 lot | 0.20 lot | 0.50 lot |
|-----------------|----------|----------|----------|----------|----------|
| 10 pts          | $0.10    | $0.50    | $1.00    | $2.00    | $5.00    |
| 20 pts          | $0.20    | $1.00    | $2.00    | $4.00    | $10.00   |
| 30 pts          | $0.30    | $1.50    | $3.00    | $6.00    | $15.00   |
| 40 pts          | $0.40    | $2.00    | $4.00    | $8.00    | $20.00   |
| 50 pts          | $0.50    | $2.50    | $5.00    | $10.00   | $25.00   |
| 60 pts          | $0.60    | $3.00    | $6.00    | $12.00   | $30.00   |
| 80 pts          | $0.80    | $4.00    | $8.00    | $16.00   | $40.00   |
| 100 pts         | $1.00    | $5.00    | $10.00   | $20.00   | $50.00   |
| 150 pts         | $1.50    | $7.50    | $15.00   | $30.00   | $75.00   |
| 200 pts         | $2.00    | $10.00   | $20.00   | $40.00   | $100.00  |

### XAUUSD — RR P&L Table (at 0.05 lot, agent default)

| SL (pts) | Risk ($) | TP1 1:1 ($) | TP2 1.5:1 ($) | TP3 2:1 ($) |
|----------|----------|-------------|----------------|--------------|
| 30 pts   | $1.50    | +$1.50      | +$2.25         | +$3.00       |
| 50 pts   | $2.50    | +$2.50      | +$3.75         | +$5.00       |
| 60 pts   | $3.00    | +$3.00      | +$4.50         | +$6.00       |
| 80 pts   | $4.00    | +$4.00      | +$6.00         | +$8.00       |
| 100 pts  | $5.00    | +$5.00      | +$7.50         | +$10.00      |
| 120 pts  | $6.00    | +$6.00      | +$9.00         | +$12.00      |

### XAUUSD — Required Lot Size for Dollar Risk Target

| Dollar Risk Target | SL 30pts | SL 50pts | SL 60pts | SL 80pts | SL 100pts |
|--------------------|----------|----------|----------|----------|-----------|
| $5 risk            | 0.17     | 0.10     | 0.08     | 0.06     | 0.05      |
| $10 risk           | 0.33     | 0.20     | 0.17     | 0.13     | 0.10      |
| $15 risk           | 0.50     | 0.30     | 0.25     | 0.19     | 0.15      |
| $20 risk           | 0.67     | 0.40     | 0.33     | 0.25     | 0.20      |
| $25 risk           | 0.83     | 0.50     | 0.42     | 0.31     | 0.25      |
| $50 risk           | 1.67     | 1.00     | 0.83     | 0.63     | 0.50      |

> Formula: Lot Size = Dollar Risk ÷ (SL pts × $1.00/pt/lot)

---

## SECTION B — GBPUSD — WORKED EXAMPLE

**MT5 Symbol Specification (Deriv / Standard Forex):**
| Parameter | Value |
|-----------|-------|
| Contract Size | 100,000 units |
| Pip Size | 0.0001 |
| Pip Value @ 1.0 lot | $10.00 per pip |
| Volume Min | 0.01 lot |
| Volume Step | 0.01 lot |

> GBPUSD is quoted vs USD, so pip value is fixed in USD: 100,000 × 0.0001 = $10.00/pip/lot

### GBPUSD — Pip Value by Lot Size

| Lot Size | $/pip | 10 pip move | 50 pip move |
|----------|-------|-------------|-------------|
| 0.01     | $0.10 | $1.00       | $5.00       |
| 0.02     | $0.20 | $2.00       | $10.00      |
| 0.03     | $0.30 | $3.00       | $15.00      |
| 0.05     | $0.50 | $5.00       | $25.00      |
| 0.10     | $1.00 | $10.00      | $50.00      |
| 0.20     | $2.00 | $20.00      | $100.00     |
| 0.50     | $5.00 | $50.00      | $250.00     |
| 1.00     | $10.00| $100.00     | $500.00     |

### GBPUSD — P&L Matrix (Price Move × Lot Size)

> GBPUSD moves measured in PIPS (0.0001 = 1 pip). M1/M5 SL typical range: 5–25 pips.

| SL / Move (pips) | 0.01 lot | 0.05 lot | 0.10 lot | 0.20 lot |
|------------------|----------|----------|----------|----------|
| 5 pips           | $0.50    | $2.50    | $5.00    | $10.00   |
| 8 pips           | $0.80    | $4.00    | $8.00    | $16.00   |
| 10 pips          | $1.00    | $5.00    | $10.00   | $20.00   |
| 15 pips          | $1.50    | $7.50    | $15.00   | $30.00   |
| 20 pips          | $2.00    | $10.00   | $20.00   | $40.00   |
| 25 pips          | $2.50    | $12.50   | $25.00   | $50.00   |
| 30 pips          | $3.00    | $15.00   | $30.00   | $60.00   |
| 50 pips          | $5.00    | $25.00   | $50.00   | $100.00  |

### GBPUSD — RR P&L Table (at 0.05 lot, agent default)

| SL (pips) | Risk ($) | TP1 1:1 ($) | TP2 1.5:1 ($) | TP3 2:1 ($) |
|-----------|----------|-------------|----------------|--------------|
| 5 pips    | $2.50    | +$2.50      | +$3.75         | +$5.00       |
| 8 pips    | $4.00    | +$4.00      | +$6.00         | +$8.00       |
| 10 pips   | $5.00    | +$5.00      | +$7.50         | +$10.00      |
| 15 pips   | $7.50    | +$7.50      | +$11.25        | +$15.00      |
| 20 pips   | $10.00   | +$10.00     | +$15.00        | +$20.00      |

### GBPUSD — Required Lot Size for Dollar Risk Target

| Dollar Risk Target | SL 5 pips | SL 10 pips | SL 15 pips | SL 20 pips |
|--------------------|-----------|------------|------------|------------|
| $5 risk            | 1.00      | 0.50       | 0.33       | 0.25       |
| $10 risk           | 2.00      | 1.00       | 0.67       | 0.50       |
| $15 risk           | 3.00      | 1.50       | 1.00       | 0.75       |
| $20 risk           | 4.00      | 2.00       | 1.33       | 1.00       |
| $25 risk           | 5.00      | 2.50       | 1.67       | 1.25       |

> Formula: Lot Size = Dollar Risk ÷ (SL pips × $10.00/pip/lot)

---

## SECTION C — FILL-IN TEMPLATE (All Other Assets)

Use this section for every asset on your watchlist. Pull specs from MT5 Specification dialog.

### Asset: _____________________

| Parameter | Value (from MT5 Spec) |
|-----------|----------------------|
| Asset Name | |
| Contract Size | |
| Tick / Point Size | |
| Tick Value (at 1.0 lot) | $ |
| Pip Size (= how many ticks) | |
| **Pip Value @ 1.0 lot** | **$** |
| Min Volume (lot) | |
| Max Volume (lot) | |
| Volume Step | |
| Typical SL range (pips/pts) | |

### Pip Value Table (fill in):

| Lot Size | Pip Value ($/pip) |
|----------|-------------------|
| Min lot  |                   |
| 2× min   |                   |
| 5× min   |                   |
| 10× min  |                   |
| 0.10     |                   |
| 0.50     |                   |
| 1.00     |                   |

### RR P&L Table (fill in at your standard lot size):

My standard lot size: _______

| SL (pips) | Risk ($) | TP1 1:1 ($) | TP2 1.5:1 ($) | TP3 2:1 ($) |
|-----------|----------|-------------|----------------|--------------|
|           |          |             |                |              |
|           |          |             |                |              |
|           |          |             |                |              |

---

## SECTION D — DERIV SYNTHETIC INDICES REFERENCE

> Deriv synthetic indices have unique contract specs. Always verify at: deriv.com/trading-specifications#derived-indices

### How to Calculate Synthetic Index Pip Value

1. Go to MT5 → Symbol Spec OR check Deriv trading specs page
2. Find: Contract Size, Tick Size, Tick Value
3. Apply: `Pip Value = (Tick Value / Tick Size) × Pip Size`

### Known Lot Sizes from Operator Syntax File

| Asset | Standard Lot Used | Notes |
|-------|-------------------|-------|
| Volatility 10 Index | 1.0 lot | Low volatility, tighter SL possible |
| Volatility 25 Index | 0.5 lot | Medium volatility |
| Volatility 75 Index | 0.1 lot | High volatility, wider SL required |

> For each synthetic index, complete a Section C template using the Deriv specifications page.
> Never guess pip values for synthetics — the contract math differs from forex.

---

## SECTION E — ACCOUNT SIZING & RISK FRAMEWORK

### Risk Per Trade Formula

```
% Risk per Trade = (Dollar Risk) / (Account Balance) × 100

For a $100 account risking $5:   5 / 100 × 100 = 5% risk per trade
For a $100 account risking $10:  10 / 100 × 100 = 10% risk per trade
For a $10,000 challenge risking $15: 15 / 10,000 × 100 = 0.15% risk per trade
```

### Agent Default Risk Settings (ADSA v7.0)

| Setting | Value | Description |
|---------|-------|-------------|
| Risk Per Trade | $15 | Variable position sizing engine |
| SL Buffer | 1.5× ATR | Auto SL placement |
| TP1 | 1:1 RR | 33% closed |
| TP2 | 1.5:1 RR | 50% of remaining |
| TP3 | 2:1 RR | Remaining / Holder Mode |

### Live Account ($50–$100) Risk Guide

| Account Size | Conservative (1%) | Moderate (3%) | Agent Default ($15) |
|--------------|-------------------|---------------|---------------------|
| $50          | $0.50/trade       | $1.50/trade   | 30% risk — too high |
| $100         | $1.00/trade       | $3.00/trade   | 15% risk — high |
| $200         | $2.00/trade       | $6.00/trade   | 7.5% risk |
| $500         | $5.00/trade       | $15.00/trade  | 3% risk — standard |
| $1,000       | $10.00/trade      | $30.00/trade  | 1.5% risk |

> For small live accounts ($50–$100), use the minimum lot on each asset and calculate your actual dollar risk using Section A/B tables above. Scale risk to your account, not the agent's default.

### 1Step 10K Prop Firm Risk Guide

| Challenge Phase | Max Daily Loss | Recommended Risk/Trade | Max Lot (XAUUSD) |
|----------------|----------------|------------------------|------------------|
| Phase 1 (10K)  | ~$500 (5%)     | $15–$50/trade          | 0.15–0.50        |
| Phase 2 (10K)  | ~$500 (5%)     | $10–$30/trade          | 0.10–0.30        |

---

## SECTION F — QUICK REFERENCE CARD

### The 60-Second Pre-Trade Risk Check

Before entering any trade signaled by the agent:

1. **What is my SL in pips/points?** (Read from agent dashboard → Trade Setup section)
2. **What is the pip value for this asset at my lot size?** (Reference your cheat sheet)
3. **Dollar Risk = SL × Pip Value × Lot Size** → Is this within my risk budget?
4. **What are my 3 TPs in dollar terms?** → TP1, TP2, TP3 = 1:1, 1.5:1, 2:1 of risk
5. **Is this worth taking?** Only trade when dollar risk is acceptable AND agent gives FULLY ALIGNED signal

### Minimum Risk Reference (at minimum lot size)

| Asset | Min Lot | $/pip at min lot | Risk @ 50pt SL | Risk @ 100pt SL |
|-------|---------|------------------|----------------|-----------------|
| XAUUSD | 0.01 | $0.01/pt | $0.50 | $1.00 |
| GBPUSD | 0.01 | $0.10/pip | $0.50 (5 pip SL) | $1.00 (10 pip SL) |
| V75 Index | (fill from spec) | (fill) | (fill) | (fill) |
| V25 Index | (fill from spec) | (fill) | (fill) | (fill) |
| V10 Index | (fill from spec) | (fill) | (fill) | (fill) |

---

*Absolute Dollar Intelligence © 2026 | ADSA v7.0 | Risk Cheat Sheet Template v1.0*
*Not financial advice. All values must be verified against your MT5 broker specification.*
