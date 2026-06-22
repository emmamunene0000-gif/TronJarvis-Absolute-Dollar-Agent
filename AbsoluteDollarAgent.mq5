//+------------------------------------------------------------------+
//|  ABSOLUTE DOLLAR AGENT — MT5 Execution Engine                   |
//|  © Absolute Dollar Intelligence 2026                            |
//+------------------------------------------------------------------+
//  Architecture (stripped to execution core):
//
//  OnTick()
//    │
//    ├─ [1] TRIGGER    CalcATMTrigger()    ATR trailing-stop crossover
//    │                 CalcSmartSignal()   RSI-momentum crossover (M5 confirm)
//    │
//    ├─ [2] GATE       CalcMTFTrails()     M15 + H1 trail direction lock
//    │                 trail_allows_long / trail_allows_short
//    │
//    ├─ [3] CONFLUENCE CalcConfidence()    6-factor weighted score → %
//    │                 GetClawThreshold()  CLAN mode → 40 / 60 / 80 %
//    │
//    └─ [4] EXECUTION  OpenTrade()         Platinum Risk: auto SL/TP sizing
//                      ManageTrade()       TP1 → TP2 → TP3 → Holder trail
//
//+------------------------------------------------------------------+
#property copyright "Absolute Dollar Intelligence 2026"
#property version   "1.00"
#include <Trade\Trade.mqh>

CTrade Trade;

// ══════════════════════════════════════════════════════════════════
// SECTION 1 — INPUTS
// ══════════════════════════════════════════════════════════════════

// ── ATM Bot ────────────────────────────────────────────────────────
input group            "ATM Bot"
input double           ATM_BuySens    = 3.5;    // Buy ATR multiplier
input int              ATM_BuyPeriod  = 2;      // Buy ATR period
input double           ATM_SellSens   = 3.5;    // Sell ATR multiplier
input int              ATM_SellPeriod = 2;      // Sell ATR period

// ── MTF Liquidity Trail ────────────────────────────────────────────
input group            "MTF Trail Gate"
input int              Trail_MA_Len   = 50;     // EMA length
input int              Trail_ATR_Len  = 14;     // ATR length
input double           Trail_ATR_Mult = 1.25;   // ATR distance multiplier

// ── CLAN Confidence Engine ─────────────────────────────────────────
input group            "Claw Confidence Engine"
input string           CLAN_Mode      = "Moderate"; // Conservative|Moderate|Aggressive|Custom
input int              CLAN_Custom    = 60;      // Custom threshold %
input double           W_MTF          = 1.5;     // MTF trail weight
input double           W_Struct       = 1.0;     // Structure bias weight
input double           W_RSI          = 1.0;     // RSI momentum weight
input double           W_VWAP         = 1.0;     // VWAP direction weight
input double           W_Fib          = 0.5;     // Fib trend weight (optional)
input double           W_VP           = 0.5;     // Value area weight (optional)
input bool             CLAN_UseFib    = false;   // Include Fib in score
input bool             CLAN_UseVP     = false;   // Include Value Area in score
input bool             CLAN_M5Confirm = true;    // Smart signals need M5 RSI agree

// ── Smart Signals ─────────────────────────────────────────────────
input group            "Smart Signals"
input bool             SmartSig_On    = true;    // Enable RSI-momentum entries
input int              RSI_Period     = 14;
input int              RSI_PosLevel   = 55;      // pmom: bull threshold
input int              RSI_NegLevel   = 50;      // nmom: bear threshold
input int              EMA_Fast       = 5;       // EMA for momentum slope

// ── Risk Management ───────────────────────────────────────────────
input group            "Risk Management"
input double           Risk_Dollars   = 15.0;   // $ risked per trade
input double           Risk_SL_ATRx   = 1.5;    // SL ATR buffer multiplier
input int              Risk_SwingBars = 5;       // Lookback for swing SL
input double           TP1_RR         = 1.0;    // TP1 risk:reward
input double           TP2_RR         = 1.5;    // TP2 risk:reward
input double           TP3_RR         = 2.0;    // TP3 risk:reward
input double           TP1_ClosePct   = 0.33;   // Close 33% at TP1
input double           TP2_ClosePct   = 0.50;   // Close 50% of remainder at TP2

// ══════════════════════════════════════════════════════════════════
// SECTION 2 — STATE
// ══════════════════════════════════════════════════════════════════

struct TrailState {
    double trail;
    int    trend;    // 1 = bullish, -1 = bearish
};

struct TradeState {
    bool   active;
    int    direction;       // 1 = long, -1 = short
    double entry;
    double sl;
    double tp1, tp2, tp3;
    double riskDist;
    double lotSize;
    ulong  ticket;
    bool   tp1Hit;
    bool   tp2Hit;
    bool   tp3Hit;
    double initialLots;
};

// Per-timeframe trail state
TrailState g_ltf, g_m15, g_h1;

// ATM Bot trail state
double g_atmTrailBuy  = 0.0;
double g_atmTrailSell = 0.0;

// RSI momentum state (persistent)
bool g_rsiPositive = false;
bool g_rsiNegative = false;

// VWAP swing direction
int g_vwapSwing = 0;   // 1 = bull, -1 = bear

// Structure bias from pivots
int g_structBias = 0;  // 1 = bull (HH/HL), -1 = bear (LL/LH)
double g_prevPivHigh = 0.0;
double g_prevPivLow  = 0.0;

// Fib trend
int g_fibTrend = 0;

// Value area (set externally or computed from VP logic)
double g_vahLevel = 0.0;
double g_valLevel = 0.0;

TradeState g_trade;
datetime   g_lastBarTime = 0;

// ══════════════════════════════════════════════════════════════════
// SECTION 3 — INIT / DEINIT
// ══════════════════════════════════════════════════════════════════

int OnInit() {
    ZeroMemory(g_trade);
    ZeroMemory(g_ltf);
    ZeroMemory(g_m15);
    ZeroMemory(g_h1);
    Trade.SetExpertMagicNumber(20260101);
    Trade.SetDeviationInPoints(20);
    return INIT_SUCCEEDED;
}

void OnDeinit(const int reason) {}

// ══════════════════════════════════════════════════════════════════
// SECTION 4 — MAIN LOOP  (the gate chain lives here)
// ══════════════════════════════════════════════════════════════════

void OnTick() {
    // Run once per confirmed bar
    datetime barTime = iTime(_Symbol, PERIOD_CURRENT, 0);
    if (barTime == g_lastBarTime) return;
    g_lastBarTime = barTime;

    // ── [1] TRIGGER LAYER ─────────────────────────────────────────
    bool atmBuy    = CalcATMTrigger(true);
    bool atmSell   = CalcATMTrigger(false);
    bool smartBuy  = SmartSig_On ? CalcSmartSignal(true)  : false;
    bool smartSell = SmartSig_On ? CalcSmartSignal(false) : false;

    bool anyBuyTrig  = atmBuy  || smartBuy;
    bool anySellTrig = atmSell || smartSell;

    if (!anyBuyTrig && !anySellTrig) {
        if (g_trade.active) ManageTrade();
        return;
    }

    // ── [2] GATE — MTF Trail Direction Lock ───────────────────────
    CalcMTFTrails();
    bool trailLong  = (g_ltf.trend == 1);
    bool trailShort = (g_ltf.trend == -1);

    bool gatedBuy  = anyBuyTrig  && trailLong;
    bool gatedSell = anySellTrig && trailShort;

    if (!gatedBuy && !gatedSell) {
        if (g_trade.active) ManageTrade();
        return;
    }

    // ── [3] GATE — Confidence Score ───────────────────────────────
    UpdateStructureBias();
    UpdateVWAPSwing();
    UpdateFibTrend();
    UpdateRSIMomentum();

    double bullConf = CalcConfidence(true);
    double bearConf = CalcConfidence(false);
    int    threshold = GetClawThreshold();

    bool confPassBuy  = gatedBuy  && (bullConf >= threshold);
    bool confPassSell = gatedSell && (bearConf >= threshold);

    // ── [4] EXECUTION ─────────────────────────────────────────────
    if (g_trade.active) {
        ManageTrade();
        return;   // one trade at a time
    }

    if (confPassBuy)
        OpenTrade(1, bullConf, threshold);
    else if (confPassSell)
        OpenTrade(-1, bearConf, threshold);
}

// ══════════════════════════════════════════════════════════════════
// SECTION 5 — TRIGGER FUNCTIONS
// ══════════════════════════════════════════════════════════════════

// ATM Bot: vanilla ATR trailing stop — returns true on the crossover bar
bool CalcATMTrigger(bool isBuy) {
    double sens   = isBuy ? ATM_BuySens    : ATM_SellSens;
    int    period = isBuy ? ATM_BuyPeriod  : ATM_SellPeriod;

    double atr   = iATR(_Symbol, PERIOD_CURRENT, period, 1);
    double nLoss = sens * atr;
    double src   = iClose(_Symbol, PERIOD_CURRENT, 1);  // confirmed close
    double &trail = isBuy ? g_atmTrailBuy : g_atmTrailSell;

    if (trail == 0.0) {
        trail = isBuy ? src - nLoss : src + nLoss;
        return false;
    }

    double prev  = trail;
    double srcP  = iClose(_Symbol, PERIOD_CURRENT, 2);

    if (src > prev && srcP > prev)
        trail = MathMax(prev, src - nLoss);
    else if (src < prev && srcP < prev)
        trail = MathMin(prev, src + nLoss);
    else
        trail = src > prev ? src - nLoss : src + nLoss;

    if (isBuy)
        return (src > trail && srcP <= prev);   // price crossed above trail
    else
        return (src < trail && srcP >= prev);   // price crossed below trail
}

// Smart Signal: RSI momentum cross with optional M5 confirmation
bool CalcSmartSignal(bool isBull) {
    double rsi  = iRSI(_Symbol, PERIOD_CURRENT, RSI_Period, PRICE_CLOSE, 1);
    double rsiP = iRSI(_Symbol, PERIOD_CURRENT, RSI_Period, PRICE_CLOSE, 2);

    double ema1 = iMA(_Symbol, PERIOD_CURRENT, EMA_Fast, 0, MODE_EMA, PRICE_CLOSE, 1);
    double ema2 = iMA(_Symbol, PERIOD_CURRENT, EMA_Fast, 0, MODE_EMA, PRICE_CLOSE, 2);
    bool   slopeUp   = ema1 > ema2;
    bool   slopeDown = ema1 < ema2;

    bool m5Confirm = true;
    if (CLAN_M5Confirm) {
        double rsi_m5  = iRSI(_Symbol, PERIOD_M5, RSI_Period, PRICE_CLOSE, 1);
        double ema_m5a = iMA(_Symbol, PERIOD_M5, EMA_Fast, 0, MODE_EMA, PRICE_CLOSE, 1);
        double ema_m5b = iMA(_Symbol, PERIOD_M5, EMA_Fast, 0, MODE_EMA, PRICE_CLOSE, 2);
        m5Confirm = isBull
            ? (rsi_m5 > RSI_PosLevel && ema_m5a > ema_m5b)
            : (rsi_m5 < RSI_NegLevel && ema_m5a < ema_m5b);
    }

    if (isBull)
        return (rsiP < RSI_PosLevel && rsi >= RSI_PosLevel && slopeUp  && m5Confirm);
    else
        return (rsiP > RSI_NegLevel && rsi <= RSI_NegLevel && slopeDown && m5Confirm);
}

// ══════════════════════════════════════════════════════════════════
// SECTION 6 — GATE FUNCTIONS
// ══════════════════════════════════════════════════════════════════

// Computes EMA+ATR trail for one timeframe, returns trend direction
TrailState CalcOneTFTrail(ENUM_TIMEFRAMES tf) {
    double ma   = iMA(_Symbol, tf, Trail_MA_Len, 0, MODE_EMA, PRICE_CLOSE, 1);
    double atr  = iATR(_Symbol, tf, Trail_ATR_Len, 1);
    double src  = iClose(_Symbol, tf, 1);
    double rawUp = ma - atr * Trail_ATR_Mult;
    double rawDn = ma + atr * Trail_ATR_Mult;

    // Retrieve state for this TF
    TrailState &state = (tf == PERIOD_CURRENT) ? g_ltf :
                        (tf == PERIOD_M15)     ? g_m15 : g_h1;

    if (state.trail == 0.0) {
        state.trend = src > ma ? 1 : -1;
        state.trail = state.trend == 1 ? rawUp : rawDn;
        return state;
    }

    double prev = state.trail;
    if (state.trend == 1) {
        state.trail = MathMax(rawUp, prev);
        if (src < state.trail) {
            state.trend = -1;
            state.trail = rawDn;
        }
    } else {
        state.trail = MathMin(rawDn, prev);
        if (src > state.trail) {
            state.trend = 1;
            state.trail = rawUp;
        }
    }
    return state;
}

void CalcMTFTrails() {
    CalcOneTFTrail(PERIOD_CURRENT);
    CalcOneTFTrail(PERIOD_M15);
    CalcOneTFTrail(PERIOD_H1);
}

// ══════════════════════════════════════════════════════════════════
// SECTION 7 — CONFLUENCE INPUTS (state update helpers)
// ══════════════════════════════════════════════════════════════════

void UpdateRSIMomentum() {
    double rsi  = iRSI(_Symbol, PERIOD_CURRENT, RSI_Period, PRICE_CLOSE, 1);
    double rsiP = iRSI(_Symbol, PERIOD_CURRENT, RSI_Period, PRICE_CLOSE, 2);
    double ema1 = iMA(_Symbol, PERIOD_CURRENT, EMA_Fast, 0, MODE_EMA, PRICE_CLOSE, 1);
    double ema2 = iMA(_Symbol, PERIOD_CURRENT, EMA_Fast, 0, MODE_EMA, PRICE_CLOSE, 2);

    if (rsi > RSI_PosLevel && ema1 > ema2) { g_rsiPositive = true;  g_rsiNegative = false; }
    if (rsi < RSI_NegLevel && ema1 < ema2) { g_rsiPositive = false; g_rsiNegative = true;  }
}

void UpdateVWAPSwing() {
    // Simplified: use 50-bar highest/lowest to determine swing direction
    // In a full build this would match the Pine adaptive VWAP anchor logic
    int prd = 100;
    double hh = iHighest(_Symbol, PERIOD_CURRENT, MODE_HIGH, prd, 1);
    double ll = iLowest(_Symbol,  PERIOD_CURRENT, MODE_LOW,  prd, 1);
    double src = iClose(_Symbol, PERIOD_CURRENT, 1);
    // If price is in upper half of the range → bullish swing
    double mid = (hh + ll) / 2.0;
    g_vwapSwing = src >= mid ? 1 : -1;
}

void UpdateStructureBias() {
    // Pivot-based HH/HL (bull) vs LL/LH (bear)
    int    swSz = 25;
    double ph = iHigh(_Symbol, PERIOD_CURRENT, iHighest(_Symbol, PERIOD_CURRENT, MODE_HIGH, swSz*2+1, swSz));
    double pl = iLow (_Symbol, PERIOD_CURRENT, iLowest (_Symbol, PERIOD_CURRENT, MODE_LOW,  swSz*2+1, swSz));

    if (ph > 0 && ph != g_prevPivHigh) {
        g_structBias  = (g_prevPivHigh == 0.0 || ph >= g_prevPivHigh) ? 1 : -1;
        g_prevPivHigh = ph;
    }
    if (pl > 0 && pl != g_prevPivLow) {
        if (g_prevPivLow == 0.0 || pl >= g_prevPivLow) {
            if (g_structBias != -1) g_structBias = 1;
        } else {
            g_structBias = -1;
        }
        g_prevPivLow = pl;
    }
}

void UpdateFibTrend() {
    // Double-smoothed EMA (basis of Fib bands) — slope = Fib trend
    int    len = 200;
    double ema1 = iMA(_Symbol, PERIOD_CURRENT, len,   0, MODE_EMA, PRICE_CLOSE, 1);
    double ema1p= iMA(_Symbol, PERIOD_CURRENT, len,   0, MODE_EMA, PRICE_CLOSE, 2);
    g_fibTrend = ema1 > ema1p ? 1 : ema1 < ema1p ? -1 : g_fibTrend;
}

// ══════════════════════════════════════════════════════════════════
// SECTION 8 — CONFIDENCE ENGINE
// ══════════════════════════════════════════════════════════════════

double CalcConfidence(bool isBull) {
    bool mtfFull    = isBull ? (g_m15.trend == 1  && g_h1.trend == 1)  : (g_m15.trend == -1 && g_h1.trend == -1);
    bool mtfPartial = isBull ? (g_m15.trend == 1  || g_h1.trend == 1)  : (g_m15.trend == -1 || g_h1.trend == -1);
    bool structPass = isBull ? (g_structBias == 1)  : (g_structBias == -1);
    bool rsiPass    = isBull ? g_rsiPositive        : g_rsiNegative;
    bool vwapPass   = isBull ? (g_vwapSwing == 1)   : (g_vwapSwing == -1);
    bool fibPass    = isBull ? (g_fibTrend == 1)     : (g_fibTrend == -1);
    bool vpPass     = isBull
        ? (g_valLevel > 0.0 && iClose(_Symbol, PERIOD_CURRENT, 1) > g_valLevel)
        : (g_vahLevel > 0.0 && iClose(_Symbol, PERIOD_CURRENT, 1) < g_vahLevel);

    double score = 0.0;
    double maxScore = 0.0;

    // MTF (partial alignment gets 40% credit)
    score    += mtfFull ? W_MTF : mtfPartial ? W_MTF * 0.4 : 0.0;
    maxScore += W_MTF;

    // Structure
    score    += structPass ? W_Struct : 0.0;
    maxScore += W_Struct;

    // RSI
    score    += rsiPass ? W_RSI : 0.0;
    maxScore += W_RSI;

    // VWAP
    score    += vwapPass ? W_VWAP : 0.0;
    maxScore += W_VWAP;

    // Fib (optional)
    if (CLAN_UseFib) {
        score    += fibPass ? W_Fib : 0.0;
        maxScore += W_Fib;
    }

    // Value Area (optional)
    if (CLAN_UseVP) {
        score    += vpPass ? W_VP : 0.0;
        maxScore += W_VP;
    }

    return maxScore > 0.0 ? (score / maxScore) * 100.0 : 0.0;
}

int GetClawThreshold() {
    if (CLAN_Mode == "Conservative") return 80;
    if (CLAN_Mode == "Aggressive")   return 40;
    if (CLAN_Mode == "Custom")       return CLAN_Custom;
    return 60;  // Moderate (default)
}

// ══════════════════════════════════════════════════════════════════
// SECTION 9 — EXECUTION ENGINE (Platinum Risk Model)
// ══════════════════════════════════════════════════════════════════

void OpenTrade(int direction, double confPct, int threshold) {
    double entry = iClose(_Symbol, PERIOD_CURRENT, 1);  // confirmed close
    double atr   = iATR(_Symbol, PERIOD_CURRENT, 14, 1);
    double ema21 = iMA(_Symbol, PERIOD_CURRENT, 21, 0, MODE_EMA, PRICE_CLOSE, 1);

    // ── Platinum Risk Model ─────────────────────────────────────────
    // SL: swing extreme ± ATR buffer (mirrors Pine Script logic)
    double sl, riskDist;
    if (direction == 1) {
        double swingLow = iLow(_Symbol, PERIOD_CURRENT,
                               iLowest(_Symbol, PERIOD_CURRENT, MODE_LOW, Risk_SwingBars, 1));
        sl = MathMax(ema21, swingLow) - atr * Risk_SL_ATRx;
        if (sl >= entry) sl = entry - atr * 1.5;   // fallback if SL would be above entry
        riskDist = entry - sl;
    } else {
        double swingHigh = iHigh(_Symbol, PERIOD_CURRENT,
                                 iHighest(_Symbol, PERIOD_CURRENT, MODE_HIGH, Risk_SwingBars, 1));
        sl = MathMin(ema21, swingHigh) + atr * Risk_SL_ATRx;
        if (sl <= entry) sl = entry + atr * 1.5;
        riskDist = sl - entry;
    }

    // TP levels at RR multiples of risk distance
    double tp1 = direction == 1 ? entry + riskDist * TP1_RR : entry - riskDist * TP1_RR;
    double tp2 = direction == 1 ? entry + riskDist * TP2_RR : entry - riskDist * TP2_RR;
    double tp3 = direction == 1 ? entry + riskDist * TP3_RR : entry - riskDist * TP3_RR;

    // Position size: risk dollars ÷ (dist × contract notional)
    double lots = CalcLotSize(riskDist);
    if (lots <= 0.0) return;

    // ── Send Order ──────────────────────────────────────────────────
    bool ok;
    if (direction == 1)
        ok = Trade.Buy(lots, _Symbol, 0, sl, tp3, "ADA-LONG");
    else
        ok = Trade.Sell(lots, _Symbol, 0, sl, tp3, "ADA-SHORT");

    if (!ok) return;

    // ── Lock state ──────────────────────────────────────────────────
    g_trade.active      = true;
    g_trade.direction   = direction;
    g_trade.entry       = entry;
    g_trade.sl          = sl;
    g_trade.tp1         = tp1;
    g_trade.tp2         = tp2;
    g_trade.tp3         = tp3;
    g_trade.riskDist    = riskDist;
    g_trade.lotSize     = lots;
    g_trade.ticket      = Trade.ResultOrder();
    g_trade.tp1Hit      = false;
    g_trade.tp2Hit      = false;
    g_trade.tp3Hit      = false;
    g_trade.initialLots = lots;

    PrintFormat("[ADA] ENTRY %s | Entry=%.5f SL=%.5f TP1=%.5f TP2=%.5f TP3=%.5f | Lots=%.4f | Conf=%.0f%% (need %d%%)",
        direction == 1 ? "LONG" : "SHORT",
        entry, sl, tp1, tp2, tp3, lots, confPct, threshold);
}

// ══════════════════════════════════════════════════════════════════
// SECTION 10 — TRADE MANAGEMENT  (TP1 → TP2 → TP3 → Holder Mode)
// ══════════════════════════════════════════════════════════════════

void ManageTrade() {
    if (!g_trade.active) return;

    double price = iClose(_Symbol, PERIOD_CURRENT, 1);
    bool   isLong = (g_trade.direction == 1);

    // ── TP1: close 33%, move SL to breakeven ────────────────────────
    if (!g_trade.tp1Hit) {
        bool tp1Reached = isLong ? price >= g_trade.tp1 : price <= g_trade.tp1;
        if (tp1Reached) {
            double closeVol = NormalizeDouble(g_trade.initialLots * TP1_ClosePct, 2);
            if (closeVol >= SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MIN))
                Trade.PositionClosePartial(g_trade.ticket, closeVol);
            // Move SL to breakeven
            Trade.PositionModify(g_trade.ticket, g_trade.entry, g_trade.tp3);
            g_trade.sl    = g_trade.entry;
            g_trade.tp1Hit = true;
            PrintFormat("[ADA] TP1 HIT — SL moved to breakeven (%.5f)", g_trade.entry);
        }
        return;
    }

    // ── TP2: close 50% of remainder ─────────────────────────────────
    if (!g_trade.tp2Hit) {
        bool tp2Reached = isLong ? price >= g_trade.tp2 : price <= g_trade.tp2;
        if (tp2Reached) {
            double closeVol = NormalizeDouble(g_trade.initialLots * (1.0 - TP1_ClosePct) * TP2_ClosePct, 2);
            if (closeVol >= SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MIN))
                Trade.PositionClosePartial(g_trade.ticket, closeVol);
            g_trade.tp2Hit = true;
            PrintFormat("[ADA] TP2 HIT — Runner active to TP3 (%.5f)", g_trade.tp3);
        }
        return;
    }

    // ── TP3 + Holder Mode: trail the runner ─────────────────────────
    if (!g_trade.tp3Hit) {
        bool tp3Reached = isLong ? price >= g_trade.tp3 : price <= g_trade.tp3;
        if (tp3Reached) {
            // Switch to structural trail — use the liquidity trail as the stop
            double newSL = isLong ? g_ltf.trail : g_ltf.trail;
            if (isLong  && newSL > g_trade.sl)
                Trade.PositionModify(g_trade.ticket, newSL, 0);
            if (!isLong && newSL < g_trade.sl)
                Trade.PositionModify(g_trade.ticket, newSL, 0);
            g_trade.sl    = newSL;
            g_trade.tp3Hit = true;
            PrintFormat("[ADA] TP3 HIT — Holder Mode active, trailing at %.5f", newSL);
        }
    } else {
        // Holder Mode: keep trailing with the LTF trail
        double trailSL = g_ltf.trail;
        bool   trailMoved = isLong
            ? (trailSL > g_trade.sl)
            : (trailSL < g_trade.sl);
        if (trailMoved) {
            Trade.PositionModify(g_trade.ticket, trailSL, 0);
            g_trade.sl = trailSL;
        }

        // Holder exit: price crosses back through trail
        bool trailExit = isLong ? price < trailSL : price > trailSL;
        if (trailExit) {
            Trade.PositionClose(g_trade.ticket);
            ZeroMemory(g_trade);
            g_trade.active = false;
            Print("[ADA] HOLDER EXIT — trail broken");
        }
    }
}

// ══════════════════════════════════════════════════════════════════
// SECTION 11 — RISK UTILITIES
// ══════════════════════════════════════════════════════════════════

double CalcLotSize(double slDist) {
    // Mirrors Pine Script Platinum Risk Model asset router
    double notional;
    string symType = SymbolInfoString(_Symbol, SYMBOL_DESCRIPTION);
    long category  = SymbolInfoInteger(_Symbol, SYMBOL_TRADE_CALC_MODE);

    switch ((int)category) {
        case SYMBOL_CALC_MODE_FOREX:
            notional = 100000.0; break;
        case SYMBOL_CALC_MODE_CFD:
        case SYMBOL_CALC_MODE_FUTURES:
            notional = SymbolInfoDouble(_Symbol, SYMBOL_TRADE_CONTRACT_SIZE); break;
        default:
            notional = SymbolInfoDouble(_Symbol, SYMBOL_TRADE_CONTRACT_SIZE);
            if (notional == 0.0) notional = 1.0;
    }

    double lots = notional > 0.0 ? Risk_Dollars / (slDist * notional) : 0.0;

    // Clamp to broker limits
    double minLot  = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MIN);
    double maxLot  = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MAX);
    double stepLot = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_STEP);

    lots = MathFloor(lots / stepLot) * stepLot;
    return MathMax(minLot, MathMin(maxLot, lots));
}

// ══════════════════════════════════════════════════════════════════
// END — AbsoluteDollarAgent.mq5
// ══════════════════════════════════════════════════════════════════
