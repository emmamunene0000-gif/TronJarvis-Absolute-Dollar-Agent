"""
Deriv Execution Bridge — Bulk Purchase REST fast path.

CLAUDE.md §1/§12 call for a persistent WebSocket bridge. That's not what
this file implements, on purpose: Deriv retired the legacy WebSocket API
(wss://ws.derivws.com) for migrated accounts — confirmed via
GET /trading/v1/options/legacy/migration-status returning "complete" (see
SYSTEM_DIAGNOSTIC.md §4). Every Personal Access Token fails InvalidToken
against that endpoint regardless of app_id, for this account. This is the
same fast-path pivot jarvis/app/deriv.py already made and proved against
the live API.

Trade-off, same as jarvis: direct buy only via Bulk Purchase REST — no
pre-quote, no balance lookup, no settlement-watching subscription. Restoring
those needs interactive OAuth2 + PKCE login (tracked as future work, not
part of this pass) and would swap this module back to a WebSocket flow.

  vanilla    -> VANILLALONGCALL / VANILLALONGPUT  (strike + expiry)
  rise_fall  -> CALL / PUT                        (direction + expiry)
  multiplier -> MULTUP / MULTDOWN                  (+ optional TP/SL)
"""
import logging
from dataclasses import dataclass
from typing import Any, Optional

import httpx

log = logging.getLogger("tradersmind.bridge")

CONTRACT_MAP = {
    ("vanilla", "CALL"): "VANILLALONGCALL",
    ("vanilla", "PUT"): "VANILLALONGPUT",
    ("rise_fall", "CALL"): "CALL",
    ("rise_fall", "PUT"): "PUT",
    ("multiplier", "CALL"): "MULTUP",
    ("multiplier", "PUT"): "MULTDOWN",
}

DERIV_REST_BASE = "https://api.derivws.com"


@dataclass
class DerivConfig:
    app_id: str
    api_token: str
    account_id: str
    is_demo: bool = True


class DerivError(Exception):
    pass


class DerivBridge:
    """Bulk Purchase REST client, single account entry per call."""

    def __init__(self, config: DerivConfig):
        self.config = config
        if not self.config.api_token:
            raise DerivError("No Deriv API token configured")
        if not self.config.account_id:
            raise DerivError(
                "No Deriv account id configured (Bulk Purchase requires it "
                "alongside the token — see DERIV_ACCOUNT_ID in .env.example)")

    async def connect(self):
        """No persistent connection in the REST fast path — this just
        confirms config is present. Kept for interface parity with the
        WebSocket bridge this replaces."""
        log.info("[DerivBridge] Ready. Demo=%s account=%s",
                  self.config.is_demo, self.config.account_id)

    async def disconnect(self):
        pass

    def _build_contract_parameters(self, mode: str, direction: str, symbol: str,
                                    stake: float, expiry_min: Optional[int] = None,
                                    strike: Optional[float] = None,
                                    tp_amount: Optional[float] = None,
                                    sl_amount: Optional[float] = None,
                                    multiplier: int = 100) -> dict:
        ct = CONTRACT_MAP.get((mode, direction))
        if ct is None:
            raise DerivError(f"No contract mapping for mode={mode} direction={direction}")

        params: dict[str, Any] = {
            "contract_type": ct,
            "underlying_symbol": symbol,
            "amount": round(stake, 2),
        }

        if mode in ("vanilla", "rise_fall"):
            params["duration"] = max(1, int(expiry_min or 5))
            params["duration_unit"] = "m"

        if mode == "vanilla":
            if strike is None:
                raise DerivError("vanilla mode requires a strike")
            params["barrier"] = str(strike)
        elif mode == "multiplier":
            params["multiplier"] = multiplier
            limits = {}
            if tp_amount is not None:
                limits["take_profit"] = round(abs(tp_amount), 2)
            if sl_amount is not None:
                limits["stop_loss"] = round(abs(sl_amount), 2)
            if limits:
                params["limit_order"] = limits

        return params

    async def _buy(self, mode: str, direction: str, symbol: str, stake: float,
                    expiry_min: Optional[int] = None, strike: Optional[float] = None,
                    tp_amount: Optional[float] = None, sl_amount: Optional[float] = None,
                    multiplier: int = 100) -> dict:
        """Bulk Purchase with a single account entry. Direct buy, no pre-quote."""
        contract_parameters = self._build_contract_parameters(
            mode, direction, symbol, stake, expiry_min, strike,
            tp_amount, sl_amount, multiplier)

        env_path = "demo" if self.config.is_demo else "real"
        url = f"{DERIV_REST_BASE}/trading/v1/options/contracts/bulk-purchase/{env_path}"
        headers = {"Deriv-App-ID": self.config.app_id, "Content-Type": "application/json"}
        body = {
            "contract_parameters": contract_parameters,
            "accounts": [{"token": self.config.api_token, "account_id": self.config.account_id}],
        }

        async with httpx.AsyncClient(timeout=20) as http:
            resp = await http.post(url, headers=headers, json=body)

        try:
            payload = resp.json()
        except ValueError:
            raise DerivError(f"Non-JSON response ({resp.status_code}): {resp.text[:200]}")

        if resp.status_code >= 400:
            raise DerivError(f"HTTP {resp.status_code}: {payload}")

        txns = payload.get("data", {}).get("transactions", [])
        if not txns:
            raise DerivError(f"No transaction in response: {payload}")

        txn = txns[0]
        if "error" in txn:
            raise DerivError(txn["error"].get("message", str(txn["error"])))

        return {
            "env": env_path,
            "loginid": txn.get("account_id", self.config.account_id),
            "contract_id": txn.get("contract_id"),
            "buy_price": txn.get("buy_price"),
            "payout": None,
            "entry_tick": None,
        }

    async def buy_rise_fall(self, symbol: str, expiry_min: int, direction: str,
                            stake: float) -> dict:
        return await self._buy("rise_fall", direction, symbol, stake, expiry_min=expiry_min)

    async def buy_vanilla(self, symbol: str, strike: float, expiry_min: int,
                          direction: str, stake: float) -> dict:
        return await self._buy("vanilla", direction, symbol, stake,
                                expiry_min=expiry_min, strike=strike)

    async def buy_multiplier(self, symbol: str, direction: str, stake: float,
                             multiplier: int, tp_amount: Optional[float] = None,
                             sl_amount: Optional[float] = None) -> dict:
        return await self._buy("multiplier", direction, symbol, stake,
                                tp_amount=tp_amount, sl_amount=sl_amount,
                                multiplier=multiplier)

    async def contract_status(self, contract_id: int) -> dict:
        """Settlement watching needs the OAuth upgrade (proposal_open_contract
        subscription) — the Bulk Purchase fast path can't poll this. Honest
        failure instead of pretending to track it."""
        raise DerivError(
            "Settlement tracking needs the OAuth2+PKCE upgrade (not yet "
            "wired) — check the Deriv app for this contract's outcome.")
