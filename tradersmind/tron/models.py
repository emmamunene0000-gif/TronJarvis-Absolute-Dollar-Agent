"""
TRON Glassbox Signal Models
Pydantic validation for every JSON payload emitted by TRON Pine Script.
"""
from pydantic import BaseModel, Field, validator
from typing import Literal, Optional
from datetime import datetime

class FractalState(BaseModel):
    h4: Literal["BULL", "BEAR", "NEUT"] = "NEUT"
    h1: Literal["BULL", "BEAR", "NEUT"] = "NEUT"
    m15: Literal["BULL", "BEAR", "NEUT"] = "NEUT"
    m5: Literal["BULL", "BEAR", "NEUT"] = "NEUT"
    sync_layers: int = Field(..., ge=0, le=4)
    quality: Literal["OPPOSED", "MIXED", "ALIGNED", "SOVEREIGN"] = "MIXED"

class CoreIndicators(BaseModel):
    structure: str = "NEUT"
    vwap: Literal["BULL", "BEAR", "NEUT"] = "NEUT"
    fib: Literal["BULL", "BEAR", "NEUT"] = "NEUT"
    vp: str = "—"
    rsi: float = 50.0
    spatial: Literal["KEY_LEVEL", "OPEN_SPACE"] = "OPEN_SPACE"

class SetupDetails(BaseModel):
    strike: float
    strike_mode: Literal["ATM", "ITM", "OTM", "Dynamic"] = "ATM"
    expiry_min: int = Field(..., ge=1, le=60)
    sl: float
    tp1: float
    tp2: float
    tp3: float
    rr: float
    atr: float
    iv_proxy: float = 0.0
    delta: float = 0.5
    regime_strength: int = 0
    regime_bars: int = 0

class TronSignal(BaseModel):
    engine: str = "TRON_GBX_v3"
    schema: int = 1
    signal: str = Field(..., description="Signal classification: H4_FLIP_CALL, SNIPER_PUT, etc.")
    bias: Literal["CALL", "PUT"]
    mode: Literal["vanilla", "rise_fall", "multiplier"]
    symbol: str
    tf: str
    time: int
    spot: float
    confidence: int = Field(..., ge=0, le=100)
    conf_bull: int = 0
    conf_bear: int = 0
    fractal: FractalState
    core: CoreIndicators
    setup: SetupDetails

    @validator("signal")
    def validate_signal_type(cls, v):
        allowed = {
            "CALL_ENTRY", "PUT_ENTRY",
            "CALL_CONTINUATION", "PUT_CONTINUATION",
            "BULL_REGIME_SHIFT", "BEAR_REGIME_SHIFT",
            "BULL_BOS", "BEAR_BOS",
            "SNIPER_CALL", "SNIPER_PUT",
            "CALL_ZONE_BREAK", "PUT_ZONE_BREAK",
            "H4_FLIP_CALL", "H4_FLIP_PUT",
            "MTF_FLIP_CALL", "MTF_FLIP_PUT",
            "TRAIL_FLIP_CALL", "TRAIL_FLIP_PUT"
        }
        if v not in allowed:
            raise ValueError(f"Unknown signal type: {v}")
        return v

class SignalEnvelope(BaseModel):
    """Wrapper for webhook delivery with metadata."""
    payload: TronSignal
    received_at: datetime = Field(default_factory=datetime.utcnow)
    processed: bool = False
    executed: bool = False
    execution_error: Optional[str] = None
