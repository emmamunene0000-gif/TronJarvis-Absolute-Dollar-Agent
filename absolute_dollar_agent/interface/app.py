"""Absolute Dollar Agent — web API."""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone

from fastapi import FastAPI, Header, HTTPException, Query, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field

from auth import require_api_key
from market_data import DerivMarketData

app = FastAPI(title="Absolute Dollar Agent", version="1.2.0")
templates = Jinja2Templates(directory="interface/templates")
market_data = DerivMarketData()


class ExecutionRequest(BaseModel):
    episode_id: int = Field(gt=0)
    style: str = Field(pattern=r"^(vanilla|rise_fall|multiplier)$")
    stake: float = Field(gt=0, le=5)
    mode: str = Field(pattern=r"^(paper|demo|live)$")


class RiskRequest(BaseModel):
    reason: str = Field(min_length=3, max_length=200)


def _agent(request: Request):
    agent = getattr(request.app.state, "agent", None)
    if agent is None:
        raise HTTPException(status_code=503, detail="Application services are not initialized")
    return agent


@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    return templates.TemplateResponse("dashboard.html", {"request": request, "app_name": "Absolute Dollar Agent", "version": "1.2.0"})


@app.get("/api/status")
async def api_status(request: Request):
    agent = _agent(request)
    trades = await agent.memory.get_recent_trades(limit=500)
    active = [trade for trade in trades if trade.get("result_status") == "PENDING"]
    return {"status": "running", "mode": agent.mode.upper(), "execution_mode": agent.execution_mode,
            "paper_balance": agent.paper.balance, "active_signals": await agent.memory.count_signals(),
            "active_trades": len(active), "total_trades": len(trades),
            "total_signals": await agent.memory.count_signals(), "risk": agent.governor.get_status(),
            "timestamp": datetime.now(timezone.utc).isoformat()}


@app.get("/api/signals")
async def api_signals(request: Request, limit: int = Query(default=100, ge=1, le=500)):
    return await _agent(request).memory.get_dashboard_signals(limit=limit)


@app.get("/api/trades")
async def api_trades(request: Request, limit: int = Query(default=100, ge=1, le=500)):
    return await _agent(request).memory.get_recent_trades(limit=limit)


@app.get("/api/active")
async def api_active(request: Request):
    agent = _agent(request)
    trades = await agent.memory.get_recent_trades(limit=500)
    return [trade for trade in trades if trade.get("result_status") == "PENDING"]


@app.get("/api/market/candles")
async def api_market_candles(symbol: str = Query(min_length=2, max_length=32, pattern=r"^[A-Z0-9_]+$"),
                             tf: str = Query(default="5", pattern=r"^(1|5|15|60|240)$"),
                             count: int = Query(default=300, ge=1, le=500)):
    allowed = set(os.getenv("ALLOWED_PAIRS", "R_10,R_25,R_50,R_75,R_100,1HZ10V,1HZ25V,1HZ50V,1HZ75V,1HZ100V").split(","))
    if symbol not in allowed:
        raise HTTPException(status_code=422, detail="Symbol is not enabled")
    try:
        return await market_data.candles(symbol, int(tf) * 60, count)
    except ValueError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@app.get("/api/health")
async def api_health(request: Request):
    return {"status": "ok" if getattr(request.app.state, "agent", None) else "starting"}


@app.post("/api/orders")
async def execute_order(payload: ExecutionRequest, request: Request,
                        x_api_key: str | None = Header(default=None),
                        idempotency_key: str | None = Header(default=None)):
    require_api_key(x_api_key)
    if not idempotency_key or len(idempotency_key) < 8:
        raise HTTPException(status_code=400, detail="Idempotency-Key header is required")
    agent = _agent(request)
    reserved = await agent.memory.reserve_request(idempotency_key, payload.episode_id, payload.style, payload.mode)
    if reserved["status"] == "COMPLETED" and reserved.get("contract_id"):
        return {"status": "idempotent_result", "contract_id": reserved["contract_id"]}

    try:
        if payload.mode == "paper":
            ticket = await agent.execute_paper(payload.episode_id, payload.style, payload.stake)
        elif payload.mode == "demo":
            row = await agent.memory.get_episode(payload.episode_id)
            if not row:
                raise HTTPException(status_code=404, detail="Signal episode not found")
            from tron.models import TronSignal
            signal = TronSignal(**json.loads(row["signal_json"]))
            ticket = await agent.execute_external(signal, payload.style, payload.stake, payload.episode_id, is_demo=True)
        else:
            if os.getenv("LIVE_EXECUTION_ENABLED", "false").lower() != "true":
                raise HTTPException(status_code=423, detail="Live execution is disabled")
            completed = await agent.memory.count_completed_trades("demo")
            if completed < agent.demo_trades_required:
                raise HTTPException(status_code=423, detail="Live gate requires 100 settled demo trades")
            row = await agent.memory.get_episode(payload.episode_id)
            if not row:
                raise HTTPException(status_code=404, detail="Signal episode not found")
            from tron.models import TronSignal
            signal = TronSignal(**json.loads(row["signal_json"]))
            ticket = await agent.execute_external(signal, payload.style, payload.stake, payload.episode_id, is_demo=False)
    except HTTPException:
        raise
    except (DerivError, ValueError) as exc:
        await agent.memory.complete_request(idempotency_key, "", "FAILED")
        raise HTTPException(status_code=400 if isinstance(exc, ValueError) else 502, detail=str(exc)) from exc

    contract_id = str(ticket.get("contract_id", ""))
    await agent.memory.complete_request(idempotency_key, contract_id)
    return {"status": "submitted", "contract_id": contract_id, "environment": ticket["env"]}


@app.post("/api/risk/override")
async def operator_override(payload: RiskRequest, request: Request,
                           x_api_key: str | None = Header(default=None)):
    require_api_key(x_api_key)
    if os.getenv("ALLOW_RISK_OVERRIDES", "false").lower() != "true":
        raise HTTPException(status_code=423, detail="Risk overrides are disabled")
    return _agent(request).governor.operator_override(payload.reason, operator_id="web-api")


@app.post("/api/reconcile")
async def reconciliation(request: Request, x_api_key: str | None = Header(default=None)):
    require_api_key(x_api_key)
    await _agent(request).reconcile_pending()
    return {"status": "reconciled", "timestamp": datetime.now(timezone.utc).isoformat()}
