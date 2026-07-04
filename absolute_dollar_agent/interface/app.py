"""
Absolute Dollar Agent — Web Interface
Lightweight, real-time, embedded TradingView chart.
"""
import os
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
import json
import asyncio
from typing import Dict, List, Any
from datetime import datetime

app = FastAPI(title="Absolute Dollar Agent", version="1.0.0")
templates = Jinja2Templates(directory="interface/templates")

# In-memory state (production: Redis)
active_signals: List[Dict[str, Any]] = []
trade_history: List[Dict[str, Any]] = []
active_tickets: Dict[str, Dict[str, Any]] = {}
ws_connections: List[WebSocket] = []

@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "app_name": "Absolute Dollar Agent",
        "version": "1.0.0"
    })

@app.get("/api/status")
async def api_status():
    return {
        "status": "running",
        "mode": os.getenv("TRADING_MODE", "demo").upper(),
        "active_signals": len(active_signals),
        "active_trades": len(active_tickets),
        "total_trades": len(trade_history),
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/api/signals")
async def api_signals():
    return active_signals[-20:]  # Last 20

@app.get("/api/trades")
async def api_trades():
    return trade_history[-50:]  # Last 50

@app.get("/api/active")
async def api_active():
    return active_tickets

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    ws_connections.append(websocket)
    try:
        while True:
            # Send current state every second
            await websocket.send_json({
                "type": "heartbeat",
                "active_signals": active_signals[-5:],
                "active_trades": list(active_tickets.values()),
                "timestamp": datetime.utcnow().isoformat()
            })
            await asyncio.sleep(1)
    except WebSocketDisconnect:
        ws_connections.remove(websocket)

async def broadcast_update(data: Dict[str, Any]):
    """Broadcast to all connected WebSocket clients."""
    dead = []
    for ws in ws_connections:
        try:
            await ws.send_json(data)
        except:
            dead.append(ws)
    for ws in dead:
        ws_connections.remove(ws)

def add_signal(signal: Dict[str, Any]):
    active_signals.append({
        **signal,
        "received_at": datetime.utcnow().isoformat()
    })
    # Keep only last 100
    if len(active_signals) > 100:
        active_signals.pop(0)

def add_trade(trade: Dict[str, Any]):
    trade_history.append({
        **trade,
        "timestamp": datetime.utcnow().isoformat()
    })

def update_ticket(ticket_id: str, update: Dict[str, Any]):
    if ticket_id in active_tickets:
        active_tickets[ticket_id].update(update)
    else:
        active_tickets[ticket_id] = update
