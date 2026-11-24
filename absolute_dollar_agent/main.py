"""Absolute Dollar Agent — application runtime."""
from __future__ import annotations

import asyncio
import json
import logging
import os
from datetime import datetime

import yaml
from dotenv import load_dotenv

from tron.models import SignalEnvelope, TronSignal
from tron.webhook import signal_queue, router as tron_router
from mind.memory import EpisodicMemory, TradeEpisode
from mind.narrative import LogicTrace
from mind import router as signal_router
from bridge.deriv_client import DerivBridge, DerivConfig, DerivError
from bridge.contract_mapper import ContractMapper
from governor.risk_engine import RiskGovernor, RiskProfile, can_unlock_live_mode
from body.telegram_bot import AbsoluteDollarAgentBot
from paper_trading import PaperTradingEngine
from interface.app import app

load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")
log = logging.getLogger("absolute_dollar_agent.main")
VALID_TRADING_MODES = {"demo", "live"}


def _load_settings() -> dict:
    path = os.path.join(os.path.dirname(__file__), "config", "settings.yaml")
    if os.path.exists(path):
        with open(path) as handle:
            return yaml.safe_load(handle) or {}
    return {}


class AbsoluteDollarAgent:
    def __init__(self):
        settings = _load_settings()
        router_cfg = settings.get("router", {})
        risk_cfg = settings.get("risk", {})
        gov_cfg = settings.get("governor", {})

        mode = os.getenv("TRADING_MODE", "demo").lower()
        if mode not in VALID_TRADING_MODES:
            mode = "demo"
        self.mode = mode
        self.execution_mode = os.getenv("EXECUTION_MODE", "paper").lower()
        if self.execution_mode not in {"paper", "demo", "live"}:
            self.execution_mode = "paper"
        self.auto_execute = os.getenv("AUTO_EXECUTE", "false").lower() == "true"
        self.enabled_styles = set(router_cfg.get("enabled_styles", ["vanilla", "multiplier", "rise_fall"]))
        self.style_priority = router_cfg.get("style_priority", ["vanilla", "multiplier", "rise_fall"])
        self.demo_trades_required = int(gov_cfg.get("demo_trades_required_for_live", 100))

        self.memory = EpisodicMemory(os.getenv("DATABASE_PATH", "absolute_dollar_agent.db"))
        self.narrative = LogicTrace()
        self.governor = RiskGovernor(RiskProfile(
            min_stake=float(os.getenv("MIN_STAKE", risk_cfg.get("min_stake", 0.35))),
            max_dynamic_stake=float(os.getenv("MAX_DYNAMIC_STAKE", risk_cfg.get("max_dynamic_stake", 1.0))),
            max_stake=float(os.getenv("MAX_STAKE_PER_TRADE", risk_cfg.get("max_stake", 5.0))),
            daily_loss_limit=float(os.getenv("DAILY_LOSS_LIMIT", "50.0")),
            max_consecutive_losses=int(os.getenv("MAX_CONSECUTIVE_LOSSES", "3")),
            cooldown_minutes=int(os.getenv("COOLDOWN_MINUTES_AFTER_LOSS", "5")),
            heat_threshold_percent=float(os.getenv("HEAT_THRESHOLD_PERCENT", "20.0")),
        ))
        self.deriv = DerivBridge(DerivConfig(
            app_id=os.getenv("DERIV_APP_ID", "1089"),
            api_token=os.getenv("DERIV_API_TOKEN", ""),
            account_id=os.getenv("DERIV_ACCOUNT_ID", ""),
            is_demo=(self.mode == "demo"),
        ))
        self.paper = PaperTradingEngine(float(os.getenv("PAPER_STARTING_BALANCE", "10000")))
        self.telegram = AbsoluteDollarAgentBot(
            token=os.getenv("TELEGRAM_BOT_TOKEN", ""), chat_id=os.getenv("TELEGRAM_CHAT_ID", ""),
            governor=self.governor, memory=self.memory, demo_trades_required=self.demo_trades_required,
        )
        self.telegram.set_callbacks(
            on_execute=self.handle_telegram_execute,
            on_why=self.handle_telegram_why,
            on_history=self.handle_telegram_history,
        )
        self._running = False

    async def start(self):
        await self.memory.init_db()
        if self.mode == "live":
            completed = await self.memory.count_completed_trades("demo")
            if not can_unlock_live_mode(completed, self.demo_trades_required):
                raise SystemExit(f"LIVE MODE REFUSED: {completed}/{self.demo_trades_required} settled demo trades")
        await self.deriv.connect()
        await self.telegram.start()
        self._running = True
        asyncio.create_task(self._signal_processor())
        asyncio.create_task(self._reconciliation_loop())

    async def shutdown(self):
        self._running = False
        await self.deriv.disconnect()
        await self.telegram.stop()

    async def _signal_processor(self):
        while self._running:
            try:
                envelope = await asyncio.wait_for(signal_queue.get(), timeout=1.0)
                await self._process_signal(envelope)
            except asyncio.TimeoutError:
                continue
            except Exception:
                log.exception("Signal processor error")

    async def _process_signal(self, envelope: SignalEnvelope):
        signal = envelope.payload
        sig_dict = signal.dict()
        tier = signal_router.classify(signal.signal)
        same_bar = await self.memory.recent_signals_same_bar(signal.symbol, signal.time)
        if signal_router.suppressed_by_higher_priority_flip(signal.signal, same_bar):
            tier = signal_router.TIER_CONTEXT

        stats = await self.memory.get_stats_by_signal_type(signal.symbol, signal.signal)
        narrative = self.narrative.generate(sig_dict, stats if stats.get("total") else None)
        episode = TradeEpisode(
            timestamp=datetime.utcnow().isoformat(), signal_type=signal.signal, tier=tier,
            bias=signal.bias, symbol=signal.symbol, timeframe=signal.tf,
            confidence=signal.confidence, sync_layers=signal.fractal.sync_layers,
            regime_quality=signal.fractal.quality, rsi=signal.core.rsi,
            vwap_state=signal.core.vwap, fib_state=signal.core.fib,
            structure_bias=signal.core.structure, vp_position=signal.core.vp,
            atr=signal.setup.atr, session_hour=datetime.utcnow().hour,
            strike=signal.setup.strike, expiry_min=signal.setup.expiry_min,
            entry_price=signal.spot, stake=0.0, narrative=narrative.headline,
            signal_json=json.dumps(sig_dict),
        )
        episode_id = await self.memory.store_signal(episode)

        if tier != signal_router.TIER_EXECUTE:
            await self.telegram.send_context_card(sig_dict, narrative.headline)
            return

        decision = signal_router.route(signal.signal, self.enabled_styles, self.style_priority)
        edge = (stats["win_rate"] / 100) if stats.get("total") else None
        approved, reason, stake = self.governor.check_pre_trade(
            sig_dict, balance=1000.0,
            mode="auto" if (self.auto_execute and decision.auto_style) else "manual",
            edge_win_rate=edge,
        )
        if not approved:
            await self.telegram.send_risk_alert("SIGNAL_BLOCKED", reason)
            return

        await self.telegram.send_signal_card(sig_dict, narrative.headline, episode_id, decision.tap_styles, stake)
        if self.auto_execute and decision.auto_style and signal.confidence >= 85 and signal.fractal.sync_layers >= 4:
            await self.execute_external(signal, decision.auto_style, stake, episode_id, is_demo=(self.mode == "demo"))

    async def execute_external(self, signal: TronSignal, style: str, stake: float, episode_id: int, is_demo: bool):
        params = ContractMapper.map_signal(signal.dict(), mode=style, stake=stake)
        valid, error = ContractMapper.validate_params(params, balance=1000.0)
        if not valid:
            raise DerivError(error)
        if params.contract_type == "rise_fall":
            ticket = await self.deriv.buy_rise_fall(params.symbol, params.duration, params.direction, params.stake)
        elif params.contract_type == "vanilla":
            ticket = await self.deriv.buy_vanilla(params.symbol, params.strike, params.duration, params.direction, params.stake)
        else:
            rr = signal.setup.rr or 1.5
            ticket = await self.deriv.buy_multiplier(params.symbol, params.direction, params.stake,
                                                      params.leverage, tp_amount=params.stake * rr,
                                                      sl_amount=params.stake)
        await self.memory.mark_executed(episode_id, ticket["env"], str(ticket.get("contract_id", "")), stake)
        return ticket

    async def execute_paper(self, episode_id: int, style: str, stake: float):
        row = await self.memory.get_episode(episode_id)
        if not row:
            raise ValueError("Signal episode not found")
        signal = TronSignal(**json.loads(row["signal_json"]))
        approved, reason, approved_stake = self.governor.check_pre_trade(signal.dict(), balance=self.paper.balance,
                                                                          mode="manual")
        if not approved:
            raise ValueError(reason)
        ticket = self.paper.buy(episode_id, signal.symbol, signal.bias, min(stake, approved_stake),
                                signal.setup.expiry_min, signal.spot, style)
        await self.memory.mark_executed(episode_id, "paper", str(ticket["contract_id"]), float(ticket["stake"]))
        return ticket

    async def reconcile_pending(self):
        trades = await self.memory.get_recent_trades(limit=500)
        now = datetime.utcnow().timestamp()
        for trade in trades:
            if trade.get("env") == "paper" and trade.get("result_status") == "PENDING":
                contract = self.paper.open_positions.get(str(trade.get("contract_id", "")))
                if contract and contract["expires_at"] <= now:
                    exit_price = contract["entry_tick"]
                    settled = self.paper.settle(str(trade["contract_id"]), exit_price)
                    await self.memory.update_result(int(trade["id"]), float(settled["result_pnl"]),
                                                    settled["result_status"], exit_price,
                                                    settled["exit_time"])

    async def _reconciliation_loop(self):
        while self._running:
            await asyncio.sleep(30)
            await self.reconcile_pending()

    async def handle_telegram_execute(self, episode_id: int, style: str, stake: float):
        row = await self.memory.get_episode(episode_id)
        if not row:
            return "Signal expired — not in the ledger."
        signal = TronSignal(**json.loads(row["signal_json"]))
        await self.execute_external(signal, style, stake, episode_id, is_demo=(self.mode == "demo"))
        return f"{style} submitted"

    async def handle_telegram_why(self, episode_id: int, signal: dict):
        stats = await self.memory.get_stats_by_signal_type(signal.get("symbol", ""), signal.get("signal", ""))
        narrative = self.narrative.generate(signal, stats if stats.get("total") else None)
        return f"{narrative.confidence_breakdown}\n{narrative.recommendation}\n{narrative.risk_note}"

    async def handle_telegram_history(self):
        trades = await self.memory.get_recent_trades(limit=10)
        return "\n".join(f"{t['signal_type']} ${float(t.get('stake') or 0):.2f} {t['result_status']}" for t in trades) if trades else "No executed trades yet."


agent = AbsoluteDollarAgent()
app.state.agent = agent
app.include_router(tron_router)


@app.on_event("startup")
async def startup():
    await agent.start()


@app.on_event("shutdown")
async def shutdown():
    await agent.shutdown()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("WEBHOOK_PORT", "8080")))
