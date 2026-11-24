"""Absolute Dollar Agent — dashboard API backed by persisted application state."""
from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Any

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from market_data import DerivMarketData

app = FastAPI(title="Absolute Dollar Agent", version="1.1.0")
templates = Jinja2Templates(directory="interface/templates")
market_data = DerivMarketData()


@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "app_name": "Absolute Dollar Agent",
        "version": "1.1.0",
    })


def _agent(request: Request):
    agent = getattr(request.app.state, "agent", None)
    if agent is None:
        raise HTTPException(status_code=503, detail="Application services are not initialized")
    return agent


@app.get("/api/status")
async def api_status(request: Request):
    agent = _agent(request)
    signals = await agent.memory.get_dashboard_signals(limit=100)
    trades = await agent.memory.get_recent_trades(limit=500)
    active = [trade for trade in trades if trade.get("result_status") == "PENDING"]
    return {
        "status": "running",
        "mode": agent.mode.upper(),
        "active_signals": len(signals),
        "active_trades": len(active),
        "total_trades": len(trades),
        "total_signals": await agent.memory.count_signals(),
        "risk": agent.governor.get_status(),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@app.get("/api/signals")
async def api_signals(request: Request, limit: int = Query(default=100, ge=1, le=500)):
    agent = _agent(request)
    return await agent.memory.get_dashboard_signals(limit=limit)


@app.get("/api/trades")
async def api_trades(request: Request, limit: int = Query(default=100, ge=1, le=500)):
    agent = _agent(request)
    return await agent.memory.get_recent_trades(limit=limit)


@app.get("/api/active")
async def api_active(request: Request):
    agent = _agent(request)
    trades = await agent.memory.get_recent_trades(limit=500)
    return [trade for trade in trades if trade.get("result_status") == "PENDING"]


@app.get("/api/market/candles")
async def api_market_candles(
    symbol: str = Query(min_length=2, max_length=32, pattern=r"^[A-Z0-9_]+$"),
    tf: str = Query(default="5", pattern=r"^(1|5|15|60|240)$"),
    count: int = Query(default=300, ge=1, le=500),
):
    allowed = set(os.getenv("ALLOWED_PAIRS", "R_10,R_25,R_50,R_75,R_100,1HZ10V,1HZ25V,1HZ50V,1HZ75V,1HZ100V").split(","))
    if symbol not in allowed:
        raise HTTPException(status_code=422, detail="Symbol is not enabled for this application")
    granularity = int(tf) * 60
    try:
        return await market_data.candles(symbol=symbol, granularity=granularity, count=count)
    except ValueError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@app.get("/api/health")
async def api_health(request: Request):
    return {"status": "ok" if getattr(request.app.state, "agent", None) else "starting"}
