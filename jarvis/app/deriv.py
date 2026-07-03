"""
JARVIS — Deriv Execution Hand.

FAST PATH (current): Deriv retired the legacy WebSocket API for this
account — confirmed via GET /trading/v1/options/legacy/migration-status
returning "complete". The new API's full single-account trading flow
(live quote before buy, balance checks, settlement watching) requires
interactive OAuth2 + PKCE login, which isn't wired up yet.

Until that lands, Jarvis buys through the Bulk Purchase REST endpoint,
which takes a Personal Access Token directly in the request body — no
OAuth, no browser redirect. Trade-off: direct buy only, no pre-quote,
no balance lookup, no contract-status polling.

  vanilla    -> VANILLALONGCALL / VANILLALONGPUT  (strike + expiry)
  rise_fall  -> CALL / PUT                        (direction + expiry)
  multiplier -> MULTUP / MULTDOWN                 (+ optional TP/SL)

TODO(oauth): once OAuth2+PKCE login is added, switch to the full
WebSocket flow (proposal -> buy -> proposal_open_contract) via an
OTP-authenticated connection to restore quotes, balance, and
settlement watching.
"""
import logging

import httpx

from . import config

log = logging.getLogger("jarvis.deriv")

CONTRACT_MAP = {
    ("vanilla", "CALL"): "VANILLALONGCALL",
    ("vanilla", "PUT"): "VANILLALONGPUT",
    ("rise_fall", "CALL"): "CALL",
    ("rise_fall", "PUT"): "PUT",
    ("multiplier", "CALL"): "MULTUP",
    ("multiplier", "PUT"): "MULTDOWN",
}


class DerivError(Exception):
    pass


class DerivClient:
    """Bulk Purchase REST client, single account entry per call."""

    def __init__(self, token: str | None = None, account_id: str | None = None):
        self.token = token or config.active_token()
        self.account_id = account_id or config.active_account_id()
        if not self.token:
            raise DerivError(f"No Deriv token configured for env '{config.DERIV_ENV}'")
        if not self.account_id:
            raise DerivError(
                f"No Deriv account id configured for env '{config.DERIV_ENV}' "
                f"(set DERIV_ACCOUNT_ID_{config.DERIV_ENV.upper()})")

    async def account_info(self) -> dict:
        """No OAuth yet, so no live balance call — just confirms config is present."""
        return {
            "loginid": self.account_id,
            "currency": "",
            "is_virtual": config.DERIV_ENV != "real",
            "balance": "n/a — bulk-purchase mode (OAuth not wired yet)",
        }

    def _build_contract_parameters(self, mode: str, bias: str, symbol: str,
                                   stake: float, expiry_min: int,
                                   strike: float | None,
                                   tp: float | None, sl: float | None) -> dict:
        ct = CONTRACT_MAP.get((mode, bias))
        if ct is None:
            raise DerivError(f"No contract mapping for mode={mode} bias={bias}")

        params: dict = {
            "contract_type": ct,
            "symbol": symbol,
            "amount": round(stake, 2),
        }

        if mode in ("vanilla", "rise_fall"):
            params["duration"] = max(1, int(expiry_min))
            params["duration_unit"] = "m"

        if mode == "vanilla":
            if strike is None:
                raise DerivError("vanilla mode requires a strike")
            params["barrier"] = str(strike)
        elif mode == "multiplier":
            params["multiplier"] = config.MULTIPLIER_DEFAULT
            limits = {}
            if tp is not None:
                limits["take_profit"] = round(abs(tp), 2)
            if sl is not None:
                limits["stop_loss"] = round(abs(sl), 2)
            if limits:
                params["limit_order"] = limits
        return params

    async def buy(self, mode: str, bias: str, symbol: str, stake: float,
                  expiry_min: int = 5, strike: float | None = None,
                  tp_amount: float | None = None, sl_amount: float | None = None) -> dict:
        """Bulk Purchase with a single account entry. Direct buy, no pre-quote."""
        contract_parameters = self._build_contract_parameters(
            mode, bias, symbol, stake, expiry_min, strike, tp_amount, sl_amount)

        env_path = "real" if config.DERIV_ENV == "real" else "demo"
        url = f"{config.DERIV_REST_BASE}/trading/v1/options/contracts/bulk-purchase/{env_path}"
        headers = {"Deriv-App-ID": config.DERIV_APP_ID, "Content-Type": "application/json"}
        body = {
            "contract_parameters": contract_parameters,
            "accounts": [{"token": self.token, "account_id": self.account_id}],
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
            "loginid": txn.get("account_id", self.account_id),
            "contract_id": txn.get("contract_id"),
            "buy_price": txn.get("buy_price"),
            "payout": None,
            "longcode": None,
            "ask_quote": None,
            "spot_at_buy": None,
        }

    async def contract_status(self, contract_id: int) -> dict:
        raise DerivError(
            "Settlement tracking needs the OAuth upgrade (not yet wired) — "
            "check the Deriv app for this contract's outcome.")
