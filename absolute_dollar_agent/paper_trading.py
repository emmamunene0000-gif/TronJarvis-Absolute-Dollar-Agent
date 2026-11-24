from __future__ import annotations

from datetime import datetime, timezone


class PaperTradingEngine:
    """Paper positions use observed market prices; this engine never calls a broker."""
    def __init__(self, starting_balance: float = 10_000.0):
        if starting_balance <= 0:
            raise ValueError("Starting paper balance must be positive")
        self.starting_balance = starting_balance
        self.balance = starting_balance
        self.open_positions: dict[str, dict] = {}

    def buy(self, episode_id: int, symbol: str, direction: str, stake: float,
            duration_minutes: int, spot: float, style: str) -> dict:
        if stake <= 0 or stake > self.balance:
            raise ValueError("Paper stake is outside the available paper balance")
        if direction not in {"CALL", "PUT"} or spot <= 0 or duration_minutes < 1:
            raise ValueError("Invalid paper contract parameters")
        contract_id = f"PAPER-{episode_id}-{int(datetime.now(timezone.utc).timestamp() * 1000)}"
        ticket = {"env": "paper", "loginid": "PAPER", "contract_id": contract_id,
                  "buy_price": round(stake, 2), "entry_tick": spot, "symbol": symbol,
                  "direction": direction, "stake": round(stake, 2), "style": style,
                  "expires_at": datetime.now(timezone.utc).timestamp() + duration_minutes * 60,
                  "result_status": "PENDING"}
        self.balance -= stake
        self.open_positions[contract_id] = ticket
        return ticket

    def settle(self, contract_id: str, exit_price: float, payout_multiplier: float = 0.8) -> dict:
        """Settle on an observed exit quote; no synthetic win or price generation."""
        position = self.open_positions.pop(contract_id, None)
        if position is None:
            raise KeyError("Unknown paper contract")
        if exit_price <= 0 or payout_multiplier < 0:
            self.open_positions[contract_id] = position
            raise ValueError("Invalid settlement inputs")
        won = (exit_price > position["entry_tick"] if position["direction"] == "CALL"
               else exit_price < position["entry_tick"])
        pnl = round(position["stake"] * payout_multiplier, 2) if won else -position["stake"]
        position.update({"exit_price": exit_price, "result_pnl": pnl,
                         "result_status": "WIN" if won else "LOSS",
                         "exit_time": datetime.now(timezone.utc).isoformat()})
        self.balance += position["stake"] + pnl
        return position
