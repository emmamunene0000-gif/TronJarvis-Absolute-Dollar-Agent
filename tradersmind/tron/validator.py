"""
TRON Payload Validator & Gatekeeper
Ensures only clean, expected signals enter the system.
"""
import json
import hmac
import hashlib
from typing import Optional, Tuple
from tron.models import TronSignal, SignalEnvelope

class TronValidator:
    def __init__(self, webhook_secret: str, allowed_pairs: list, allowed_timeframes: list):
        self.secret = webhook_secret
        self.allowed_pairs = set(allowed_pairs)
        self.allowed_tfs = set(allowed_timeframes)

    def verify_signature(self, body: bytes, signature: str) -> bool:
        """Verify HMAC-SHA256 signature from TradingView webhook."""
        expected = hmac.new(
            self.secret.encode(),
            body,
            hashlib.sha256
        ).hexdigest()
        return hmac.compare_digest(expected, signature)

    def validate_payload(self, raw_json: dict) -> Tuple[bool, Optional[SignalEnvelope], str]:
        """
        Returns: (is_valid, envelope, error_message)
        """
        try:
            # Schema version check
            if raw_json.get("schema", 0) != 1:
                return False, None, f"Unsupported schema version: {raw_json.get('schema')}"

            # Engine check
            if not raw_json.get("engine", "").startswith("TRON"):
                return False, None, f"Unknown engine: {raw_json.get('engine')}"

            # Symbol whitelist
            sym = raw_json.get("symbol", "")
            if sym not in self.allowed_pairs:
                return False, None, f"Symbol {sym} not in allowed list"

            # Timeframe whitelist
            tf = raw_json.get("tf", "")
            if tf not in self.allowed_tfs:
                return False, None, f"Timeframe {tf} not allowed"

            # Pydantic validation (strict)
            signal = TronSignal(**raw_json)
            envelope = SignalEnvelope(payload=signal)
            return True, envelope, "OK"

        except Exception as e:
            return False, None, f"Validation error: {str(e)}"
