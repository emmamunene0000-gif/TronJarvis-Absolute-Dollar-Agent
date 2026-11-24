"""Unit coverage for corrected durable episode and idempotency tables."""
import asyncio
import json
from mind.memory import EpisodicMemory, TradeEpisode


def test_init_and_reserve_idempotent_request(tmp_path):
    async def run():
        memory = EpisodicMemory(str(tmp_path / "ledger.sqlite"))
        await memory.init_db()
        first = await memory.reserve_request("request-key-0001", 1, "vanilla", "paper")
        second = await memory.reserve_request("request-key-0001", 1, "vanilla", "paper")
        assert first["status"] == "PENDING"
        assert second["idempotency_key"] == first["idempotency_key"]
        await memory.complete_request("request-key-0001", "PAPER-1", "COMPLETED")
        third = await memory.reserve_request("request-key-0001", 1, "vanilla", "paper")
        assert third["status"] == "COMPLETED"
        assert third["contract_id"] == "PAPER-1"
    asyncio.run(run())


def test_persisted_signal_read_model(tmp_path):
    async def run():
        memory = EpisodicMemory(str(tmp_path / "ledger.sqlite"))
        await memory.init_db()
        payload = {"signal": "CALL_ENTRY", "bias": "CALL", "symbol": "R_100", "tf": "5", "time": 300000, "spot": 100.1, "confidence": 80}
        episode_id = await memory.store_signal(TradeEpisode(timestamp="2026-01-01T00:00:00", signal_type="CALL_ENTRY", tier="EXECUTE", bias="CALL", symbol="R_100", timeframe="5", confidence=80, signal_json=json.dumps(payload)))
        result = await memory.get_dashboard_signals()
        assert result[0]["id"] == episode_id
        assert result[0]["signal"] == "CALL_ENTRY"
    asyncio.run(run())
