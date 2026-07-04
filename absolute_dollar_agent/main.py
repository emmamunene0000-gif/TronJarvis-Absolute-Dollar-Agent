"""
Absolute Dollar Agent — Main Orchestrator
Wires all layers: TRON -> Mind (classify/route/narrate/remember) -> Governor -> Bridge/Body

No paper mode anywhere in this file (CLAUDE.md §5/§18) — TRADING_MODE is
demo or live, both real orders against Deriv, differing only in which
account balance they touch.
"""
import asyncio
import json
import logging
import os
from datetime import datetime

import yaml
from dotenv import load_dotenv

from tron.models import SignalEnvelope
from tron.webhook import signal_queue
from mind.memory import EpisodicMemory, TradeEpisode
from mind.narrative import LogicTrace
from mind.similarity import SimilarityEngine
from mind import router as signal_router
from bridge.deriv_client import DerivBridge, DerivConfig, DerivError
from bridge.contract_mapper import ContractMapper
from governor.risk_engine import RiskGovernor, RiskProfile, can_unlock_live_mode
from body.telegram_bot import AbsoluteDollarAgentBot

load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")
log = logging.getLogger("absolute_dollar_agent.main")

VALID_TRADING_MODES = {"demo", "live"}


def _load_settings() -> dict:
    path = os.path.join(os.path.dirname(__file__), "config", "settings.yaml")
    if os.path.exists(path):
        with open(path) as f:
            return yaml.safe_load(f) or {}
    return {}


class AbsoluteDollarAgent:
    """The complete system. One instance per trading session."""

    def __init__(self):
        settings = _load_settings()
        router_cfg = settings.get("router", {})
        risk_cfg = settings.get("risk", {})
        gov_cfg = settings.get("governor", {})

        mode = os.getenv("TRADING_MODE", "demo").lower()
        if mode not in VALID_TRADING_MODES:
            log.warning("Invalid TRADING_MODE=%r — no paper mode exists (CLAUDE.md §5). "
                        "Falling back to demo.", mode)
            mode = "demo"
        self.mode = mode
        self.auto_execute = os.getenv("AUTO_EXECUTE", "false").lower() == "true"

        self.enabled_styles = set(router_cfg.get("enabled_styles", ["vanilla", "multiplier", "rise_fall"]))
        self.style_priority = router_cfg.get("style_priority", ["vanilla", "multiplier", "rise_fall"])
        self.demo_trades_required = int(gov_cfg.get("demo_trades_required_for_live", 100))

        self.memory = EpisodicMemory()
        self.narrative = LogicTrace()
        self.similarity = SimilarityEngine(k=5)
        self.governor = RiskGovernor(RiskProfile(
            min_stake=float(os.getenv("MIN_STAKE", risk_cfg.get("min_stake", 0.35))),
            max_dynamic_stake=float(os.getenv("MAX_DYNAMIC_STAKE", risk_cfg.get("max_dynamic_stake", 1.00))),
            max_stake=float(os.getenv("MAX_STAKE_PER_TRADE", risk_cfg.get("max_stake", 5.0))),
            daily_loss_limit=float(os.getenv("DAILY_LOSS_LIMIT", "50.0")),
            max_consecutive_losses=int(os.getenv("MAX_CONSECUTIVE_LOSSES", "3")),
            cooldown_minutes=int(os.getenv("COOLDOWN_MINUTES_AFTER_LOSS", "5")),
            heat_threshold_percent=float(os.getenv("HEAT_THRESHOLD_PERCENT", "20.0")),
        ))
        self.deriv = DerivBridge(DerivConfig(
            app_id=os.getenv("DERIV_APP_ID", ""),
            api_token=os.getenv("DERIV_API_TOKEN", ""),
            account_id=os.getenv("DERIV_ACCOUNT_ID", ""),
            is_demo=(self.mode == "demo"),
        ))
        self.telegram = AbsoluteDollarAgentBot(
            token=os.getenv("TELEGRAM_BOT_TOKEN", ""),
            chat_id=os.getenv("TELEGRAM_CHAT_ID", ""),
            governor=self.governor,
            memory=self.memory,
            demo_trades_required=self.demo_trades_required,
        )
        self.telegram.set_callbacks(
            on_execute=self.handle_telegram_execute,
            on_why=self.handle_telegram_why,
            on_history=self.handle_telegram_history,
        )

        self._running = False

    async def start(self):
        print("Absolute Dollar Agent initializing...")
        print(f"   Mode: {self.mode.upper()}")
        print(f"   Auto-execute: {self.auto_execute}")

        await self.memory.init_db()
        print("   Memory initialized")

        if self.mode == "live":
            completed = await self.memory.count_completed_trades(env="demo")
            if not can_unlock_live_mode(completed, self.demo_trades_required):
                raise SystemExit(
                    f"LIVE MODE REFUSED: {completed}/{self.demo_trades_required} completed "
                    f"demo trades logged. The §10 gate is hard, no override. "
                    f"Run TRADING_MODE=demo until the ledger earns it."
                )
            print(f"   Live-mode gate cleared ({completed}/{self.demo_trades_required} demo trades)")

        await self.deriv.connect()
        print(f"   Deriv bridge ready ({self.mode})")

        await self.telegram.start()
        print("   Telegram ready")

        self._running = True
        asyncio.create_task(self._signal_processor())
        print("   Signal processor running")
        print("\nAbsolute Dollar Agent is LIVE — waiting for TRON signals...")

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
        """Process a single TRON signal end-to-end (§9)."""
        signal = envelope.payload
        sig_dict = signal.dict()
        tier = signal_router.classify(signal.signal)

        print(f"\nSIGNAL: {signal.signal} | {signal.bias} | {signal.confidence}% | tier={tier}")

        # Same-bar flip-priority suppression (§7): a lower-tier flip is
        # downgraded to context-only if a higher-tier flip already fired
        # for this symbol on this exact TRON bar.
        same_bar = await self.memory.recent_signals_same_bar(signal.symbol, signal.time)
        if signal_router.suppressed_by_higher_priority_flip(signal.signal, same_bar):
            tier = signal_router.TIER_CONTEXT
            print("   Downgraded to CONTEXT — higher-priority flip already fired this bar")

        similar = await self.memory.get_similar_episodes(
            symbol=signal.symbol, signal_type=signal.signal, limit=5
        )
        stats = await self.memory.get_stats_by_signal_type(signal.symbol, signal.signal) if similar else None
        narrative = self.narrative.generate(sig_dict, stats)
        print(f"   {narrative.headline}")

        # Every signal is logged — CONTEXT included. Glass box means the
        # ledger is the product, not just the trades.
        episode = TradeEpisode(
            timestamp=datetime.utcnow().isoformat(),
            signal_type=signal.signal,
            tier=tier,
            bias=signal.bias,
            symbol=signal.symbol,
            timeframe=signal.tf,
            confidence=signal.confidence,
            sync_layers=signal.fractal.sync_layers,
            regime_quality=signal.fractal.quality,
            rsi=signal.core.rsi,
            vwap_state=signal.core.vwap,
            fib_state=signal.core.fib,
            structure_bias=signal.core.structure,
            vp_position=signal.core.vp,
            atr=signal.setup.atr,
            session_hour=datetime.utcnow().hour,
            strike=signal.setup.strike,
            expiry_min=signal.setup.expiry_min,
            entry_price=signal.spot,
            stake=0.0,
            narrative=narrative.headline,
            signal_json=json.dumps(sig_dict),
        )
        episode_id = await self.memory.store_signal(episode)
        print(f"   Stored as episode #{episode_id} (tier={tier})")

        if tier != signal_router.TIER_EXECUTE:
            # CONTEXT/NOISE never triggers an independent trade (§2.1, §7).
            await self.telegram.send_context_card(sig_dict, narrative.headline)
            return

        decision = signal_router.route(signal.signal, self.enabled_styles, self.style_priority)
        edge_win_rate = (stats["win_rate"] / 100) if stats and stats.get("total", 0) > 0 else None

        approved, reason, stake = self.governor.check_pre_trade(
            sig_dict, balance=1000.0,  # real balance calls need the OAuth upgrade — see bridge/deriv_client.py
            mode="auto" if (self.auto_execute and decision.auto_style) else "manual",
            edge_win_rate=edge_win_rate,
        )

        if not approved:
            print(f"   REJECTED: {reason}")
            rejection = self.narrative.explain_rejection(reason.split(":")[0])
            await self.telegram.send_risk_alert("SIGNAL_BLOCKED", f"{reason}\n{rejection}")
            return

        print(f"   APPROVED: Stake ${stake}")
        await self.telegram.send_signal_card(sig_dict, narrative.headline, episode_id,
                                             decision.tap_styles, stake)

        # Auto-execute only when AUTO_EXECUTE is on, a style auto-routed, and
        # the hard gate clears — otherwise it's a TAP card, never a smaller
        # auto-fire (§10 is explicit: this is a gate, not a sizing input).
        if (self.auto_execute and decision.auto_style
                and signal.confidence >= 85 and signal.fractal.sync_layers >= 4):
            print(f"   AUTO-EXECUTING via {decision.auto_style}...")
            await self._execute_trade(signal, decision.auto_style, stake, episode_id)
        else:
            print("   Waiting for operator tap...")

    async def _execute_trade(self, signal, style: str, stake: float, episode_id: int):
        """Execute trade via Deriv bridge — a real order against demo or live balance."""
        params = ContractMapper.map_signal(signal.dict(), mode=style, stake=stake)

        valid, error = ContractMapper.validate_params(params, balance=1000.0)
        if not valid:
            print(f"   Contract validation failed: {error}")
            await self.telegram.send_risk_alert("CONTRACT_INVALID", error)
            return

        try:
            if params.contract_type == "rise_fall":
                ticket = await self.deriv.buy_rise_fall(
                    params.symbol, params.duration, params.direction, params.stake
                )
            elif params.contract_type == "vanilla":
                ticket = await self.deriv.buy_vanilla(
                    params.symbol, params.strike, params.duration, params.direction, params.stake
                )
            else:
                rr = signal.setup.rr or 1.5
                ticket = await self.deriv.buy_multiplier(
                    params.symbol, params.direction, params.stake,
                    params.leverage, tp_amount=stake * rr, sl_amount=stake,
                )
        except DerivError as e:
            print(f"   Deriv execution failed: {e}")
            await self.telegram.send_risk_alert("EXECUTION_FAULT", str(e))
            return

        print(f"   TICKET: #{ticket.get('contract_id', 'N/A')}")
        await self.memory.mark_executed(episode_id, ticket["env"], str(ticket.get("contract_id", "")))
        await self.telegram.send_execution_alert(ticket, signal.signal, stake)
        self.governor.record_trade(stake=stake, result_pnl=0.0, signal_type=signal.signal)

    async def handle_telegram_execute(self, episode_id: int, style: str, stake: float) -> str:
        """Callback when the operator taps a style button in Telegram."""
        from tron.models import TronSignal

        row = await self.memory.get_episode(episode_id)
        if row is None:
            return "Signal expired — not in the ledger."
        signal = TronSignal(**json.loads(row["signal_json"]))
        await self._execute_trade(signal, style, stake, episode_id)
        return f"{style} @ ${stake:.2f} submitted"

    async def handle_telegram_why(self, episode_id: int, signal: dict) -> str:
        stats = await self.memory.get_stats_by_signal_type(
            signal.get("symbol", ""), signal.get("signal", "")
        )
        narrative = self.narrative.generate(signal, stats)
        return f"{narrative.confidence_breakdown}\n{narrative.recommendation}\n{narrative.risk_note}"

    async def handle_telegram_history(self) -> str:
        trades = await self.memory.get_recent_trades(limit=10)
        if not trades:
            return "No executed trades yet."
        return "\n".join(
            f"{t['signal_type']} {t['bias']} | ${t['stake']:.2f} | {t['result_status']}"
            for t in trades
        )

    async def shutdown(self):
        self._running = False
        await self.deriv.disconnect()
        await self.telegram.stop()
        print("\nAbsolute Dollar Agent shutdown complete")


# Entry point
if __name__ == "__main__":
    import uvicorn
    from fastapi import FastAPI
    from tron.webhook import router as tron_router
    from interface.app import app as interface_app

    app = FastAPI(title="Absolute Dollar Agent", version="1.0.0")
    app.include_router(tron_router)
    for route in interface_app.routes:
        app.routes.append(route)

    agent = AbsoluteDollarAgent()

    @app.on_event("startup")
    async def startup():
        await agent.start()

    @app.on_event("shutdown")
    async def shutdown():
        await agent.shutdown()

    port = int(os.getenv("WEBHOOK_PORT", "8080"))
    uvicorn.run(app, host="0.0.0.0", port=port)
