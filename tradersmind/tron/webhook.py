"""
FastAPI Webhook Endpoint for TRON
Receives, validates, queues, and broadcasts signals.
"""
from fastapi import APIRouter, Request, HTTPException, Header, Depends
from fastapi.responses import JSONResponse
from typing import Optional
import asyncio
import json
import os

from tron.models import SignalEnvelope
from tron.validator import TronValidator

router = APIRouter(prefix="/webhook", tags=["tron"])

# In-memory queue (production: use Redis or persistent queue)
signal_queue: asyncio.Queue = asyncio.Queue()

# Validator instance (singleton pattern in production)
_validator: Optional[TronValidator] = None

def get_validator() -> TronValidator:
    global _validator
    if _validator is None:
        _validator = TronValidator(
            webhook_secret=os.getenv("WEBHOOK_SECRET", "dev-secret"),
            allowed_pairs=os.getenv("ALLOWED_PAIRS", "R_10,R_25,R_50,R_75,R_100").split(","),
            allowed_timeframes=os.getenv("ALLOWED_TFS", "1,5,15,60,240").split(",")
        )
    return _validator

@router.post("/tron")
async def receive_tron_signal(
    request: Request,
    x_signature: Optional[str] = Header(None, alias="X-TRON-Signature"),
    validator: TronValidator = Depends(get_validator)
):
    """
    Primary endpoint for TRON Pine Script webhook.
    TradingView Alert Message: {{alert_message}}
    """
    body = await request.body()

    # Signature verification (optional in dev, required in prod)
    if os.getenv("VERIFY_SIGNATURE", "false").lower() == "true":
        if not x_signature or not validator.verify_signature(body, x_signature):
            raise HTTPException(status_code=401, detail="Invalid signature")

    try:
        raw = json.loads(body)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON")

    is_valid, envelope, error = validator.validate_payload(raw)

    if not is_valid or envelope is None:
        return JSONResponse(
            status_code=400,
            content={"status": "rejected", "reason": error}
        )

    # Queue for async processing (non-blocking response to TradingView)
    await signal_queue.put(envelope)

    return JSONResponse(
        status_code=200,
        content={
            "status": "accepted",
            "signal": envelope.payload.signal,
            "bias": envelope.payload.bias,
            "confidence": envelope.payload.confidence,
            "id": envelope.received_at.isoformat()
        }
    )

@router.get("/health")
async def webhook_health():
    return {"status": "alive", "queue_depth": signal_queue.qsize()}
