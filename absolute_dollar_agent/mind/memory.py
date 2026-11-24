"""Episodic memory store — durable SQLite signal and execution ledger."""
import aiosqlite
import json
import numpy as np
from datetime import datetime
from typing import List, Optional, Dict, Any
from dataclasses import dataclass

DB_PATH = "absolute_dollar_agent.db"

@dataclass
class TradeEpisode:
    id: Optional[int] = None
    timestamp: str = ""
    signal_type: str = ""
    tier: str = "CONTEXT"
    bias: str = ""
    symbol: str = ""
    timeframe: str = ""
    confidence: int = 0
    sync_layers: int = 0
    regime_quality: str = ""
    rsi: float = 0.0
    vwap_state: str = ""
    fib_state: str = ""
    structure_bias: str = ""
    vp_position: str = ""
    atr: float = 0.0
    session_hour: int = 0
    strike: float = 0.0
    expiry_min: int = 0
    entry_price: float = 0.0
    stake: float = 0.0
    env: str = ""
    executed: bool = False
    contract_id: str = ""
    result_pnl: Optional[float] = None
    result_status: str = "PENDING"
    exit_price: Optional[float] = None
    exit_time: Optional[str] = None
    narrative: str = ""
    signal_json: str = "{}"

    def feature_vector(self) -> np.ndarray:
        return np.array([
            self.sync_layers / 4.0, self.confidence / 100.0, self.rsi / 100.0,
            1.0 if self.vwap_state == "BULL" else -1.0 if self.vwap_state == "BEAR" else 0.0,
            1.0 if self.fib_state == "BULL" else -1.0 if self.fib_state == "BEAR" else 0.0,
            1.0 if self.structure_bias in ["BULL", "BULL_BOS"] else -1.0,
            1.0 if self.vp_position == "ABOVE VAH" else -1.0 if self.vp_position == "BELOW VAL" else 0.0,
            self.atr, self.session_hour / 24.0,
        ])

class EpisodicMemory:
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path

    async def init_db(self):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS episodes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, timestamp TEXT NOT NULL,
                    signal_type TEXT NOT NULL, tier TEXT NOT NULL DEFAULT 'CONTEXT',
                    bias TEXT NOT NULL, symbol TEXT NOT NULL, timeframe TEXT NOT NULL,
                    confidence INTEGER, sync_layers INTEGER, regime_quality TEXT,
                    rsi REAL, vwap_state TEXT, fib_state TEXT, structure_bias TEXT,
                    vp_position TEXT, atr REAL, session_hour INTEGER, strike REAL,
                    expiry_min INTEGER, entry_price REAL, stake REAL,
                    env TEXT NOT NULL DEFAULT '', executed INTEGER NOT NULL DEFAULT 0,
                    contract_id TEXT NOT NULL DEFAULT '', result_pnl REAL,
                    result_status TEXT DEFAULT 'PENDING', exit_price REAL, exit_time TEXT,
                    narrative TEXT, signal_json TEXT
                )
            """)
            await db.execute("CREATE INDEX IF NOT EXISTS idx_signal_type ON episodes(signal_type)")
            await db.execute("CREATE INDEX IF NOT EXISTS idx_symbol ON episodes(symbol)")
            await db.execute("CREATE INDEX IF NOT EXISTS idx_result ON episodes(result_status)")
            await db.execute("CREATE INDEX IF NOT EXISTS idx_contract ON episodes(contract_id)")
            await db.execute("""
                CREATE TABLE IF NOT EXISTS operator_requests (
                    idempotency_key TEXT PRIMARY KEY,
                    episode_id INTEGER NOT NULL,
                    style TEXT NOT NULL,
                    env TEXT NOT NULL,
                    contract_id TEXT,
                    status TEXT NOT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """)
            await db.commit()

    async def reserve_request(self, idempotency_key: str, episode_id: int, style: str, env: str) -> dict:
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            now = datetime.utcnow().isoformat()
            existing = await db.execute("SELECT * FROM operator_requests WHERE idempotency_key = ?", (idempotency_key,))
            row = await existing.fetchone()
            if row:
                return dict(row)
            await db.execute("INSERT INTO operator_requests (idempotency_key, episode_id, style, env, contract_id, status, created_at, updated_at) VALUES (?, ?, ?, ?, '', 'PENDING', ?, ?)", (idempotency_key, episode_id, style, env, now, now))
            await db.commit()
            return {"idempotency_key": idempotency_key, "episode_id": episode_id, "style": style, "env": env, "contract_id": "", "status": "PENDING", "created_at": now, "updated_at": now}

    async def complete_request(self, idempotency_key: str, contract_id: str, status: str = "COMPLETED"):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("UPDATE operator_requests SET contract_id = ?, status = ?, updated_at = ? WHERE idempotency_key = ?", (contract_id, status, datetime.utcnow().isoformat(), idempotency_key))
            await db.commit()

    async def store_signal(self, episode: TradeEpisode) -> int:
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("""
                INSERT INTO episodes (timestamp, signal_type, tier, bias, symbol, timeframe,
                    confidence, sync_layers, regime_quality, rsi, vwap_state, fib_state,
                    structure_bias, vp_position, atr, session_hour, strike, expiry_min,
                    entry_price, stake, env, executed, contract_id, result_pnl,
                    result_status, exit_price, exit_time, narrative, signal_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                episode.timestamp, episode.signal_type, episode.tier, episode.bias,
                episode.symbol, episode.timeframe, episode.confidence, episode.sync_layers,
                episode.regime_quality, episode.rsi, episode.vwap_state, episode.fib_state,
                episode.structure_bias, episode.vp_position, episode.atr, episode.session_hour,
                episode.strike, episode.expiry_min, episode.entry_price, episode.stake,
                episode.env, int(episode.executed), episode.contract_id, episode.result_pnl,
                episode.result_status, episode.exit_price, episode.exit_time,
                episode.narrative, episode.signal_json,
            ))
            await db.commit()
            return int(cursor.lastrowid)

    async def mark_executed(self, episode_id: int, env: str, contract_id: str):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("UPDATE episodes SET executed = 1, env = ?, contract_id = ? WHERE id = ?", (env, contract_id, episode_id))
            await db.commit()

    async def update_result(self, episode_id: int, pnl: float, status: str, exit_price: float, exit_time: str):
        if status not in {"WIN", "LOSS", "EXPIRED"}:
            raise ValueError("Invalid settlement status")
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("UPDATE episodes SET result_pnl = ?, result_status = ?, exit_price = ?, exit_time = ? WHERE id = ?", (pnl, status, exit_price, exit_time, episode_id))
            await db.commit()

    async def count_signals(self) -> int:
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("SELECT COUNT(*) FROM episodes")
            row = await cursor.fetchone()
            return int(row[0] if row else 0)

    async def get_dashboard_signals(self, limit: int = 100) -> List[Dict[str, Any]]:
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("SELECT id, timestamp, narrative, signal_json FROM episodes ORDER BY id DESC LIMIT ?", (max(1, min(limit, 500)),))
            rows = await cursor.fetchall()
        signals = []
        for row in rows:
            try:
                signal = json.loads(row["signal_json"] or "{}")
            except (json.JSONDecodeError, TypeError):
                continue
            signals.append({**signal, "id": row["id"], "received_at": row["timestamp"], "narrative": row["narrative"]})
        return list(reversed(signals))

    async def count_completed_trades(self, env: str = "demo") -> int:
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("SELECT COUNT(*) FROM episodes WHERE executed = 1 AND env = ? AND result_status IN ('WIN', 'LOSS')", (env,))
            row = await cursor.fetchone()
            return int(row[0] if row else 0)

    async def recent_signals_same_bar(self, symbol: str, bar_time: int) -> List[str]:
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("SELECT signal_json FROM episodes WHERE symbol = ? AND json_extract(signal_json, '$.time') = ?", (symbol, bar_time))
            rows = await cursor.fetchall()
            out = []
            for (raw,) in rows:
                try:
                    out.append(json.loads(raw).get("signal", ""))
                except (json.JSONDecodeError, AttributeError):
                    continue
            return out

    async def get_episode(self, episode_id: int) -> Optional[Dict[str, Any]]:
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("SELECT * FROM episodes WHERE id = ?", (episode_id,))
            row = await cursor.fetchone()
            return dict(row) if row else None

    async def get_recent_trades(self, limit: int = 10) -> List[Dict[str, Any]]:
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("SELECT * FROM episodes WHERE executed = 1 ORDER BY timestamp DESC LIMIT ?", (max(1, min(limit, 500)),))
            return [dict(row) for row in await cursor.fetchall()]

    async def get_similar_episodes(self, symbol: str, signal_type: str, limit: int = 5) -> List[TradeEpisode]:
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("SELECT * FROM episodes WHERE symbol = ? AND signal_type = ? AND result_status != 'PENDING' ORDER BY timestamp DESC LIMIT ?", (symbol, signal_type, limit))
            return [TradeEpisode(**dict(row)) for row in await cursor.fetchall()]

    async def get_stats_by_signal_type(self, symbol: str, signal_type: str) -> Dict[str, Any]:
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("SELECT result_status, result_pnl FROM episodes WHERE symbol = ? AND signal_type = ? AND result_status != 'PENDING' ORDER BY timestamp DESC LIMIT 50", (symbol, signal_type))
            rows = await cursor.fetchall()
        if not rows:
            return {"total": 0, "wins": 0, "losses": 0, "win_rate": 0, "avg_pnl": 0, "streak": 0}
        wins = sum(1 for row in rows if row[0] == "WIN")
        losses = sum(1 for row in rows if row[0] == "LOSS")
        pnls = [row[1] for row in rows if row[1] is not None]
        streak = 0
        for row in rows:
            if row[0] == "WIN": streak = streak + 1 if streak >= 0 else 1
            elif row[0] == "LOSS": streak = streak - 1 if streak <= 0 else -1
            else: break
        total = wins + losses
        return {"total": total, "wins": wins, "losses": losses, "win_rate": round(wins / total * 100, 1) if total else 0, "avg_pnl": round(float(np.mean(pnls)), 2) if pnls else 0, "streak": streak}

    async def get_daily_stats(self, symbol: str, date: str) -> Dict[str, Any]:
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("SELECT result_status, result_pnl FROM episodes WHERE symbol = ? AND date(timestamp) = ? AND result_status != 'PENDING'", (symbol, date))
            rows = await cursor.fetchall()
        wins = sum(1 for row in rows if row[0] == "WIN")
        losses = sum(1 for row in rows if row[0] == "LOSS")
        pnls = [row[1] for row in rows if row[1] is not None]
        return {"date": date, "trades": len(rows), "wins": wins, "losses": losses, "win_rate": round(wins / len(rows) * 100, 1) if rows else 0, "net_pnl": round(sum(pnls), 2) if pnls else 0}
