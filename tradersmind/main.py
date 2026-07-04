"""
TradersMind — Main Orchestrator
Wires all layers: TRON → Mind → Bridge → Governor → Body
"""
import asyncio
import os
import json
from datetime import datetime
from dotenv import load_dotenv

from tron.models import SignalEnvelope
from tron.webhook import signal_queue
from mind.memory import EpisodicMemory, TradeEpisode
from mind.narrative import LogicTrace, NarrativeResult
from mind.similarity import SimilarityEngine
from bridge.deriv_client import DerivBridge, DerivConfig
from bridge.contract_mapper import ContractMapper, ContractParams
from governor.risk_engine import RiskGovernor, RiskProfile
from body.telegram_bot import TradersMindBot

# Load environment
load_dotenv()

class TradersMind:
    """
    The complete system. One instance per trading session.
    """
    def __init__(self):
        self.mode = os.getenv("TRADING_MODE", "paper")
        self.auto_execute = os.getenv("AUTO_EXECUTE", "false").lower() == "true"

        # Initialize all layers
        self.memory = EpisodicMemory()
        self.narrative = LogicTrace()
        self.similarity = SimilarityEngine(k=5)
        self.governor = RiskGovernor(RiskProfile(
            max_stake=float(os.getenv("MAX_STAKE_PER_TRADE", "5.0")),
            daily_loss_limit=float(os.getenv("DAILY_LOSS_LIMIT", "50.0")),
            max_consecutive_losses=int(os.getenv("MAX_CONSECUTIVE_LOSSES", "3")),
            cooldown_minutes=int(os.getenv("COOLDOWN_MINUTES_AFTER_LOSS", "5")),
            heat_threshold_percent=float(os.getenv("HEAT_THRESHOLD_PERCENT", "20.0"))
        ))
        self.deriv = DerivBridge(DerivConfig(
            app_id=os.getenv("DERIV_APP_ID", ""),
            api_token=os.getenv("DERIV_API_TOKEN", ""),
            is_demo=True
        ))
        self.telegram = TradersMindBot(
            token=os.getenv("TELEGRAM_BOT_TOKEN", ""),
            chat_id=os.getenv("TELEGRAM_CHAT_ID", "")
        )

        # Wire callbacks
        self.telegram.set_callbacks(
            on_execute=self.handle_telegram_execute,
            on_why=self.handle_telegram_why,
            on_history=self.handle_telegram_history
        )

        self._running = False

    async def start(self):
        """Start all services."""
        print("🤖 TradersMind initializing...")
        print(f"   Mode: {self.mode.upper()}")
        print(f"   Auto-execute: {self.auto_execute}")

        # Init database
        await self.memory.init_db()
        print("   ✅ Memory initialized")

        # Connect to Deriv (paper mode skips real connection)
        if self.mode != "paper":
            await self.deriv.connect()
            print("   ✅ Deriv connected")
        else:
            print("   📊 PAPER MODE — No real trades")

        # Start Telegram
        await self.telegram.start()
        print("   ✅ Telegram ready")

        # Start signal processor
        self._running = True
        asyncio.create_task(self._signal_processor())
        print("   ✅ Signal processor running")

        print("\n🚀 TradersMind is LIVE")
        print("   Waiting for TRON signals...")

    async def _signal_processor(self):
        """Background task: process signals from queue."""
        while self._running:
            try:
                envelope = await asyncio.wait_for(signal_queue.get(), timeout=1.0)
                await self._process_signal(envelope)
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                print(f"[Processor] Error: {e}")

    async def _process_signal(self, envelope: SignalEnvelope):
        """Process a single TRON signal end-to-end."""
        signal = envelope.payload
        sig_dict = signal.dict()

        print(f"\n📡 SIGNAL: {signal.signal} | {signal.bias} | {signal.confidence}%")

        # 1. Get similar history
        similar = await self.memory.get_similar_episodes(
            symbol=signal.symbol,
            signal_type=signal.signal,
            limit=5
        )

        # 2. Generate narrative
        stats = None
        if similar:
            stats = await self.memory.get_stats_by_signal_type(
                signal.symbol, signal.signal
            )

        narrative = self.narrative.generate(sig_dict, stats)
        print(f"   📝 {narrative.headline}")

        # 3. Risk check
        approved, reason, stake = self.governor.check_pre_trade(
            sig_dict, 
            balance=1000.0,  # Would fetch from Deriv
            mode="auto" if self.auto_execute else "manual"
        )

        if not approved:
            print(f"   🛡 REJECTED: {reason}")
            rejection = self.narrative.explain_rejection(reason.split(":")[0])
            await self.telegram.send_risk_alert("SIGNAL_BLOCKED", f"{reason}\n{rejection}")
            return

        print(f"   ✅ APPROVED: Stake ${stake}")

        # 4. Store episode (pre-execution)
        episode = TradeEpisode(
            timestamp=datetime.utcnow().isoformat(),
            signal_type=signal.signal,
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
            stake=stake,
            narrative=narrative.headline,
            signal_json=json.dumps(sig_dict)
        )

        episode_id = await self.memory.store_signal(episode)
        print(f"   💾 Stored as episode #{episode_id}")

        # 5. Broadcast to Telegram
        await self.telegram.send_signal(sig_dict, narrative.headline)

        # 6. Auto-execute or wait for tap
        if self.auto_execute and signal.confidence >= 85 and signal.fractal.sync_layers >= 4:
            print(f"   🤖 AUTO-EXECUTING...")
            await self._execute_trade(signal, stake, episode_id)
        else:
            print(f"   👆 Waiting for operator tap...")

    async def _execute_trade(self, signal, stake: float, episode_id: int):
        """Execute trade via Deriv bridge."""
        # Map to contract
        params = ContractMapper.map_signal(
            signal.dict(),
            mode=signal.mode,
            stake=stake
        )

        # Validate
        valid, error = ContractMapper.validate_params(params, balance=1000.0)
        if not valid:
            print(f"   ❌ Contract validation failed: {error}")
            return

        # Execute
        if self.mode == "paper":
            ticket = {
                "contract_id": f"PAPER_{episode_id}",
                "entry_tick": signal.spot,
                "buy_price": stake,
                "status": "PAPER",
                "signal": signal.signal
            }
        else:
            if params.contract_type == "rise_fall":
                ticket = await self.deriv.buy_rise_fall(
                    params.symbol, params.duration, params.duration_unit,
                    params.stake, params.direction
                )
            elif params.contract_type == "vanilla":
                ticket = await self.deriv.buy_vanilla(
                    params.symbol, params.strike, params.duration,
                    params.direction, params.stake
                )
            else:
                ticket = await self.deriv.buy_multiplier(
                    params.symbol, params.duration, params.direction,
                    params.stake, params.leverage, 
                    params.stop_loss_percent, params.take_profit_percent
                )

        print(f"   ✅ TICKET: #{ticket.get('contract_id', 'N/A')}")

        # Notify
        await self.telegram.send_execution_alert(ticket)

        # Record in governor
        self.governor.record_trade(stake=stake, result_pnl=0.0, 
                                    signal_type=signal.signal)

        # Update episode with ticket info
        # (In production, update when trade closes)

    async def handle_telegram_execute(self, signal: dict):
        """Callback when user taps EXECUTE in Telegram."""
        print(f"   👆 Operator executed: {signal.get('signal')}")
        # Re-process with manual override flag
        return "EXECUTED_MANUAL"

    async def handle_telegram_why(self, signal: dict):
        """Callback when user taps WHY?"""
        stats = await self.memory.get_stats_by_signal_type(
            signal.get("symbol", ""), signal.get("signal", "")
        )
        narrative = self.narrative.generate(signal, stats)
        return f"{narrative.confidence_breakdown}\n{narrative.recommendation}"

    async def handle_telegram_history(self):
        """Callback when user requests history."""
        return "History feature coming in v1.1"

    async def shutdown(self):
        self._running = False
        if self.mode != "paper":
            await self.deriv.disconnect()
        print("\n🛑 TradersMind shutdown complete")

# Entry point
if __name__ == "__main__":
    import uvicorn
    from fastapi import FastAPI
    from tron.webhook import router as tron_router
    from face.app import app as face_app

    # Combine routers
    app = FastAPI(title="TradersMind", version="1.0.0")
    app.include_router(tron_router)

    # Mount face app routes
    for route in face_app.routes:
        app.routes.append(route)

    mind = TradersMind()

    @app.on_event("startup")
    async def startup():
        await mind.start()

    @app.on_event("shutdown")
    async def shutdown():
        await mind.shutdown()

    port = int(os.getenv("WEBHOOK_PORT", "8080"))
    uvicorn.run(app, host="0.0.0.0", port=port)
