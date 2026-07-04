"""
Deriv WebSocket API Bridge
Direct API — no XML bots. Real-time ticks, execution, P&L streaming.
"""
import asyncio
import json
import websockets
from typing import Callable, Optional, Dict, Any
from dataclasses import dataclass
import os

@dataclass
class DerivConfig:
    app_id: str
    api_token: str
    endpoint: str = "wss://ws.derivws.com/websockets/v3"
    is_demo: bool = True

class DerivBridge:
    """
    WebSocket client for Deriv API.
    Handles: auth, contract buy, price subscription, P&L streaming.
    """
    def __init__(self, config: DerivConfig):
        self.config = config
        self.ws: Optional[websockets.WebSocketClientProtocol] = None
        self.authenticated = False
        self.balance: float = 0.0
        self.active_tickets: Dict[str, Dict[str, Any]] = {}
        self.callbacks: Dict[str, Callable] = {}
        self._req_id = 0
        self._running = False

    def _next_req_id(self) -> str:
        self._req_id += 1
        return str(self._req_id)

    async def connect(self):
        """Establish WebSocket connection and authenticate."""
        self.ws = await websockets.connect(f"{self.config.endpoint}?app_id={self.config.app_id}")
        self._running = True

        # Authenticate
        auth_msg = {
            "authorize": self.config.api_token,
            "req_id": self._next_req_id()
        }
        await self.ws.send(json.dumps(auth_msg))

        # Start listener
        asyncio.create_task(self._listen())

        # Wait for auth response
        for _ in range(10):
            if self.authenticated:
                break
            await asyncio.sleep(0.5)

        if not self.authenticated:
            raise ConnectionError("Deriv auth failed")

        print(f"[DerivBridge] Connected. Demo={self.config.is_demo}")

    async def _listen(self):
        """Background listener for all WebSocket messages."""
        while self._running and self.ws:
            try:
                msg = await self.ws.recv()
                data = json.loads(msg)
                await self._handle_message(data)
            except Exception as e:
                print(f"[DerivBridge] Listen error: {e}")
                await asyncio.sleep(1)

    async def _handle_message(self, data: Dict[str, Any]):
        """Route incoming messages to appropriate handlers."""
        if "authorize" in data:
            self.authenticated = True
            self.balance = data["authorize"].get("balance", 0)
            print(f"[DerivBridge] Auth OK. Balance: {self.balance}")

        elif "buy" in data:
            ticket = data["buy"]
            contract_id = ticket.get("contract_id")
            self.active_tickets[contract_id] = {
                "entry": ticket.get("entry_tick"),
                "stake": ticket.get("buy_price"),
                "contract_id": contract_id,
                "status": "OPEN"
            }
            if "on_buy" in self.callbacks:
                await self.callbacks["on_buy"](ticket)

        elif "proposal_open_contract" in data:
            contract = data["proposal_open_contract"]
            cid = contract.get("contract_id")
            if cid in self.active_tickets:
                self.active_tickets[cid]["current_profit"] = contract.get("profit", 0)
                self.active_tickets[cid]["current_spot"] = contract.get("current_spot", 0)
                self.active_tickets[cid]["status"] = contract.get("status", "OPEN")

                if "on_tick" in self.callbacks:
                    await self.callbacks["on_tick"](contract)

        elif "balance" in data:
            self.balance = data["balance"].get("balance", self.balance)

        elif "error" in data:
            print(f"[DerivBridge] API Error: {data['error']}")
            if "on_error" in self.callbacks:
                await self.callbacks["on_error"](data["error"])

    async def buy_rise_fall(self, symbol: str, duration: int, duration_unit: str,
                            stake: float, direction: str) -> Dict[str, Any]:
        """
        Buy Rise/Fall contract.
        direction: "CALL" or "PUT"
        """
        if not self.authenticated:
            raise RuntimeError("Not connected to Deriv")

        # Map symbol to Deriv format
        deriv_symbol = symbol  # e.g., "R_100" for Volatility 100

        proposal = {
            "proposal": 1,
            "amount": stake,
            "basis": "stake",
            "contract_type": "CALL" if direction == "CALL" else "PUT",
            "currency": "USD",
            "duration": duration,
            "duration_unit": duration_unit,
            "symbol": deriv_symbol,
            "req_id": self._next_req_id()
        }

        await self.ws.send(json.dumps(proposal))

        # Wait for proposal response (simplified — in production, parse properly)
        await asyncio.sleep(0.5)

        # For paper trading mode, return mock
        if os.getenv("TRADING_MODE", "paper") == "paper":
            return {
                "contract_id": f"PAPER_{self._next_req_id()}",
                "entry_tick": 0,
                "buy_price": stake,
                "status": "PAPER"
            }

        # Real execution
        buy_msg = {
            "buy": "proposal_id_here",  # Would extract from proposal response
            "price": stake,
            "req_id": self._next_req_id()
        }
        await self.ws.send(json.dumps(buy_msg))

        return {"status": "pending", "contract_id": "pending"}

    async def buy_vanilla(self, symbol: str, strike: float, expiry: int,
                          direction: str, stake: float) -> Dict[str, Any]:
        """
        Buy Vanilla Options contract.
        """
        if os.getenv("TRADING_MODE", "paper") == "paper":
            return {
                "contract_id": f"PAPER_VAN_{self._next_req_id()}",
                "entry_tick": strike,
                "buy_price": stake,
                "status": "PAPER",
                "strike": strike,
                "expiry_min": expiry
            }

        # Real vanilla execution (Deriv API specifics)
        proposal = {
            "proposal": 1,
            "amount": stake,
            "basis": "stake",
            "contract_type": "CALL" if direction == "CALL" else "PUT",
            "currency": "USD",
            "symbol": symbol,
            "barrier": strike,
            "date_expiry": expiry,  # Unix timestamp
            "req_id": self._next_req_id()
        }
        await self.ws.send(json.dumps(proposal))
        return {"status": "pending"}

    async def buy_multiplier(self, symbol: str, duration: int, direction: str,
                             stake: float, multiplier: int, 
                             stop_loss: float, take_profit: float) -> Dict[str, Any]:
        """
        Buy Multiplier contract.
        """
        if os.getenv("TRADING_MODE", "paper") == "paper":
            return {
                "contract_id": f"PAPER_MULT_{self._next_req_id()}",
                "entry_tick": 0,
                "buy_price": stake,
                "status": "PAPER",
                "multiplier": multiplier
            }

        # Real multiplier execution
        proposal = {
            "proposal": 1,
            "amount": stake,
            "basis": "stake",
            "contract_type": "MULTUP" if direction == "CALL" else "MULTDOWN",
            "currency": "USD",
            "duration": duration,
            "duration_unit": "m",
            "symbol": symbol,
            "multiplier": multiplier,
            "stop_loss": stop_loss,
            "take_profit": take_profit,
            "req_id": self._next_req_id()
        }
        await self.ws.send(json.dumps(proposal))
        return {"status": "pending"}

    async def subscribe_to_contract(self, contract_id: str):
        """Subscribe to live P&L updates for a contract."""
        msg = {
            "proposal_open_contract": 1,
            "contract_id": contract_id,
            "subscribe": 1,
            "req_id": self._next_req_id()
        }
        await self.ws.send(json.dumps(msg))

    async def get_balance(self) -> float:
        """Request current balance."""
        msg = {
            "balance": 1,
            "req_id": self._next_req_id()
        }
        await self.ws.send(json.dumps(msg))
        return self.balance

    async def disconnect(self):
        self._running = False
        if self.ws:
            await self.ws.close()
