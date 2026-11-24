"""Read-only Deriv market data using public historical candle requests.

This module never submits orders. Broker credentials are not required for candles;
DERIV_APP_ID is used only to identify the public API application.
"""
from __future__ import annotations

import json
import os
from typing import Any

import websockets

DEFAULT_APP_ID = "1089"
WS_BASE = "wss://ws.derivws.com/websockets/v3"
SUPPORTED_GRANULARITIES = {60, 300, 900, 3600, 14400}


def parse_candles(payload: dict[str, Any]) -> list[dict[str, int | float]]:
    """Normalize Deriv candle response; reject malformed/non-finite values."""
    error = payload.get("error")
    if error:
        raise ValueError(str(error.get("message", "Market data request failed")))
    candles = payload.get("candles")
    if not isinstance(candles, list):
        raise ValueError("Market data response did not contain candles")
    normalized = []
    for candle in candles:
        try:
            item = {
                "time": int(candle["epoch"]),
                "open": float(candle["open"]),
                "high": float(candle["high"]),
                "low": float(candle["low"]),
                "close": float(candle["close"]),
            }
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError("Market data response contained an invalid candle") from exc
        if not all(__import__("math").isfinite(item[key]) for key in ("open", "high", "low", "close")):
            raise ValueError("Market data response contained a non-finite candle")
        if item["high"] < max(item["open"], item["close"], item["low"]) or item["low"] > min(item["open"], item["close"], item["high"]):
            raise ValueError("Market data response contained inconsistent OHLC values")
        normalized.append(item)
    normalized.sort(key=lambda candle: candle["time"])
    return normalized


class DerivMarketData:
    """Fetch bounded historical OHLC candles from Deriv's public WS API."""

    def __init__(self, app_id: str | None = None):
        self.app_id = app_id or os.getenv("DERIV_APP_ID", DEFAULT_APP_ID)

    async def candles(self, symbol: str, granularity: int, count: int = 300) -> list[dict[str, int | float]]:
        if granularity not in SUPPORTED_GRANULARITIES:
            raise ValueError("Unsupported candle timeframe")
        if not 1 <= count <= 500:
            raise ValueError("Candle count must be between 1 and 500")
        uri = f"{WS_BASE}?app_id={self.app_id}"
        request = {
            "ticks_history": symbol,
            "adjust_start_time": 1,
            "count": count,
            "end": "latest",
            "granularity": granularity,
            "style": "candles",
        }
        try:
            async with websockets.connect(uri, open_timeout=8, close_timeout=2, ping_timeout=8) as socket:
                await socket.send(json.dumps(request))
                response = json.loads(await socket.recv())
        except (OSError, TimeoutError, websockets.WebSocketException, json.JSONDecodeError) as exc:
            raise RuntimeError("Deriv market data is temporarily unavailable") from exc
        return parse_candles(response)
