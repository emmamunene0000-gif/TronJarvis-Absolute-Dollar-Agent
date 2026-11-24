"""Durable dashboard ledger tests."""
import asyncio
import json
from mind.memory import EpisodicMemory, TradeEpisode


def test_signal_ledger_persists_and_serializes_dashboard_signals(tmp_path):
    async def run():
        memory = EpisodicMemory(str(tmp_path / "ledger.sqlite"))
        await memory.init_db()
        signal = {"signal": "CALL_ENTRY", "bias": "CALL", "symbol": "R_100", "tf": "5", "time": 300000, "spot": 100.5, "confidence": 80}
        episode_id = await memory.store_signal(TradeEpisode(
            timestamp="2026-01-01T00:00:00", signal_type="CALL_ENTRY", tier="EXECUTE",
            bias="CALL", symbol="R_100", timeframe="5", confidence=80,
            narrative="test event", signal_json=json.dumps(signal),
        ))
        rows = await memory.get_dashboard_signals()
        assert rows[0]["id"] == episode_id
        assert rows[0]["signal"] == "CALL_ENTRY"
        assert await memory.count_signals() == 1
    asyncio.run(run())
