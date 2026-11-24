from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Literal


@dataclass
class PaperTicket:
    contract_id: str
    env: Literal["paper"]
    buy_price: float
    entry_tick: float


class PaperTradingEngine:
    """Deterministic virtual-fill engine. It never contacts a broker."""

    def __init__(self, starting_balance: float = 10_000.0):
        self.balance = starting_balance
        self.open_positions: dict[str, dict] = {}

    def buy(self, episode_id: int, symbol: str, direction: str, stake: float,
            duration_minutes: int, spot: float, style: str) -> dict:
        if stake <= 0:
            raise ValueError("Paper stake must be positive")
        if stake > self.balance:
            raise ValueError("Insufficient paper balance")
        contract_id = f"PAPER-{episode_id}-{int(datetime.now(timezone.utc).timestamp()*1000)}"
        ticket = {
            "env": "paper",
            "loginid": "PAPER",
            "contract_id": contract_id,
            "buy_price": round(stake, 2),
            "entry_tick": spot,
            "symbol": symbol,
            "direction": direction,
            "stake": round(stake, 2),
            "style": style,
            "expires_at": datetime.now(timezone.utc).timestamp() + duration_minutes * 60,
        }
        self.balance -= stake
        self.open_positions[contract_id] = ticket
        return ticket

    def settle_expired(self, now: float | None = None) -> list[dict]:
        now = now or datetime.now(timezone.utc).timestamp()
        settled = []
        for contract_id, position in list(self.open_positions.items()).items():
            if position["expires_at"] <= now:
                self.open_positions.pop(contract_id)
                delta = position["stake"] * 0.8
                position.update({"result_status": "WIN" if delta >= 0 else "LOSS", "result_pnl": delta})
                self.balance += position["stake"] + delta
                settled.append(position)
        return settled
