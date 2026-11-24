from __future__ import annotations

import os
import secrets
from fastapi import Header, HTTPException


def require_api_key(x_api_key: str | None = None) -> None:
    """Protect operator endpoints. The key is only checked server-side."""
    configured = os.getenv("WEB_API_KEY", "").strip()
    if not configured:
        raise HTTPException(
            status_code=503,
            detail="Web API operator authentication is not configured",
        )
    if not secrets.compare_digest(x_api_key or "", configured):
        raise HTTPException(status_code=401, detail="Invalid or missing web API key")
