"""
Unit tests for TRON layer.
"""
import pytest
import json
from tron.models import TronSignal, FractalState, CoreIndicators, SetupDetails
from tron.validator import TronValidator

class TestTronModels:
    def test_valid_signal(self):
        data = {
            "engine": "TRON_GBX_v3",
            "schema": 1,
            "signal": "H4_FLIP_CALL",
            "bias": "CALL",
            "mode": "vanilla",
            "symbol": "R_100",
            "tf": "5",
            "time": 1234567890,
            "spot": 314.50,
            "confidence": 87,
            "conf_bull": 87,
            "conf_bear": 0,
            "fractal": {
                "h4": "BULL", "h1": "BULL", "m15": "BULL", "m5": "BULL",
                "sync_layers": 4, "quality": "SOVEREIGN"
            },
            "core": {
                "structure": "BULL_BOS", "vwap": "BULL", "fib": "BULL",
                "vp": "ABOVE VAH", "rsi": 62.5, "spatial": "KEY_LEVEL"
            },
            "setup": {
                "strike": 314.50, "strike_mode": "ATM", "expiry_min": 8,
                "sl": 313.50, "tp1": 316.00, "tp2": 317.50, "tp3": 319.00,
                "rr": 1.5, "atr": 1.0, "iv_proxy": 0.124, "delta": 0.52,
                "regime_strength": 75, "regime_bars": 12
            }
        }
        signal = TronSignal(**data)
        assert signal.confidence == 87
        assert signal.fractal.sync_layers == 4
        assert signal.setup.strike == 314.50

    def test_invalid_signal_type(self):
        data = {
            "engine": "TRON_GBX_v3",
            "schema": 1,
            "signal": "INVALID_SIGNAL",
            "bias": "CALL",
            "mode": "vanilla",
            "symbol": "R_100",
            "tf": "5",
            "time": 1234567890,
            "spot": 314.50,
            "confidence": 50,
            "fractal": {"h4": "BULL", "h1": "BULL", "m15": "BULL", "m5": "BULL",
                       "sync_layers": 4, "quality": "SOVEREIGN"},
            "core": {"structure": "BULL", "vwap": "BULL", "fib": "BULL",
                    "vp": "ABOVE VAH", "rsi": 50, "spatial": "KEY_LEVEL"},
            "setup": {"strike": 314.50, "strike_mode": "ATM", "expiry_min": 5,
                     "sl": 313.50, "tp1": 316.00, "tp2": 317.50, "tp3": 319.00,
                     "rr": 1.5, "atr": 1.0, "iv_proxy": 0.1, "delta": 0.5,
                     "regime_strength": 50, "regime_bars": 5}
        }
        with pytest.raises(ValueError):
            TronSignal(**data)

class TestTronValidator:
    def test_validate_payload(self):
        validator = TronValidator(
            webhook_secret="test",
            allowed_pairs=["R_100", "R_50"],
            allowed_timeframes=["5", "15"]
        )

        valid_data = {
            "engine": "TRON_GBX_v3", "schema": 1, "signal": "H4_FLIP_CALL",
            "bias": "CALL", "mode": "vanilla", "symbol": "R_100",
            "tf": "5", "time": 1234567890, "spot": 314.50, "confidence": 87,
            "conf_bull": 87, "conf_bear": 0,
            "fractal": {"h4": "BULL", "h1": "BULL", "m15": "BULL", "m5": "BULL",
                       "sync_layers": 4, "quality": "SOVEREIGN"},
            "core": {"structure": "BULL_BOS", "vwap": "BULL", "fib": "BULL",
                    "vp": "ABOVE VAH", "rsi": 62.5, "spatial": "KEY_LEVEL"},
            "setup": {"strike": 314.50, "strike_mode": "ATM", "expiry_min": 8,
                     "sl": 313.50, "tp1": 316.00, "tp2": 317.50, "tp3": 319.00,
                     "rr": 1.5, "atr": 1.0, "iv_proxy": 0.124, "delta": 0.52,
                     "regime_strength": 75, "regime_bars": 12}
        }

        is_valid, envelope, error = validator.validate_payload(valid_data)
        assert is_valid is True
        assert envelope is not None
        assert envelope.payload.signal == "H4_FLIP_CALL"

    def test_reject_unknown_symbol(self):
        validator = TronValidator(
            webhook_secret="test",
            allowed_pairs=["R_100"],
            allowed_timeframes=["5"]
        )

        invalid_data = {
            "engine": "TRON_GBX_v3", "schema": 1, "signal": "CALL_ENTRY",
            "bias": "CALL", "mode": "vanilla", "symbol": "UNKNOWN",
            "tf": "5", "time": 1234567890, "spot": 100, "confidence": 50,
            "conf_bull": 50, "conf_bear": 0,
            "fractal": {"h4": "BULL", "h1": "NEUT", "m15": "BULL", "m5": "NEUT",
                       "sync_layers": 2, "quality": "MIXED"},
            "core": {"structure": "NEUT", "vwap": "BULL", "fib": "NEUT",
                    "vp": "IN VALUE", "rsi": 50, "spatial": "OPEN_SPACE"},
            "setup": {"strike": 100, "strike_mode": "ATM", "expiry_min": 5,
                     "sl": 99, "tp1": 101, "tp2": 102, "tp3": 103,
                     "rr": 1.0, "atr": 1.0, "iv_proxy": 0.1, "delta": 0.5,
                     "regime_strength": 30, "regime_bars": 3}
        }

        is_valid, envelope, error = validator.validate_payload(invalid_data)
        assert is_valid is False
        assert "not in allowed list" in error
