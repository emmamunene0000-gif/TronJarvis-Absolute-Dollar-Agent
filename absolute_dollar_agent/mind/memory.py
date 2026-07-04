"""
Episodic Memory Store — SQLite
Every trade context, execution, and result is stored as a memory vector.
"""
import aiosqlite
import json
import numpy as np
from datetime import datetime
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, asdict

DB_PATH = "absolute_dollar_agent.db"

@dataclass
class TradeEpisode:
    id: Optional[int] = None
    timestamp: str = ""
    signal_type: str = ""
    tier: str = "CONTEXT"          # EXECUTE | CONTEXT | NOISE (mind/router.py)
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
    env: str = ""                  # demo | live | "" (not executed)
    executed: bool = False         # True once a real order was placed
    contract_id: str = ""
    result_pnl: Optional[float] = None
    result_status: str = "PENDING"  # PENDING, WIN, LOSS, EXPIRED
    exit_price: Optional[float] = None
    exit_time: Optional[str] = None
    narrative: str = ""
    signal_json: str = "{}"

    def feature_vector(self) -> np.ndarray:
        """Numerical vector for KNN similarity search."""
        return np.array([
            self.sync_layers / 4.0,
            self.confidence / 100.0,
            self.rsi / 100.0,
            1.0 if self.vwap_state == "BULL" else -1.0 if self.vwap_state == "BEAR" else 0.0,
            1.0 if self.fib_state == "BULL" else -1.0 if self.fib_state == "BEAR" else 0.0,
            1.0 if self.structure_bias in ["BULL", "BULL_BOS"] else -1.0,
            1.0 if self.vp_position == "ABOVE VAH" else -1.0 if self.vp_position == "BELOW VAL" else 0.0,
            self.atr,
            self.session_hour / 24.0
        ])

class EpisodicMemory:
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path

    async def init_db(self):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS episodes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    signal_type TEXT NOT NULL,
                    tier TEXT NOT NULL DEFAULT 'CONTEXT',
                    bias TEXT NOT NULL,
                    symbol TEXT NOT NULL,
                    timeframe TEXT NOT NULL,
                    confidence INTEGER,
                    sync_layers INTEGER,
                    regime_quality TEXT,
                    rsi REAL,
                    vwap_state TEXT,
                    fib_state TEXT,
                    structure_bias TEXT,
                    vp_position TEXT,
                    atr REAL,
                    session_hour INTEGER,
                    strike REAL,
                    expiry_min INTEGER,
                    entry_price REAL,
                    stake REAL,
                    env TEXT NOT NULL DEFAULT '',
                    executed INTEGER NOT NULL DEFAULT 0,
                    contract_id TEXT NOT NULL DEFAULT '',
                    result_pnl REAL,
                    result_status TEXT,
                    exit_price REAL,
                    exit_time TEXT,
                    narrative TEXT,
                    signal_json TEXT
                )
            """)
            await db.execute("""
                CREATE INDEX IF NOT EXISTS idx_signal_type ON episodes(signal_type)
            """)
            await db.execute("""
                CREATE INDEX IF NOT EXISTS idx_symbol ON episodes(symbol)
            """)
            await db.execute("""
                CREATE INDEX IF NOT EXISTS idx_result ON episodes(result_status)
            """)
            await db.commit()

    async def store_signal(self, episode: TradeEpisode) -> int:
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("""
                INSERT INTO episodes (
                    timestamp, signal_type, tier, bias, symbol, timeframe, confidence,
                    sync_layers, regime_quality, rsi, vwap_state, fib_state,
                    structure_bias, vp_position, atr, session_hour, strike,
                    expiry_min, entry_price, stake, env, executed, contract_id,
                    result_pnl, result_status, exit_price, exit_time, narrative, signal_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                episode.timestamp, episode.signal_type, episode.tier, episode.bias,
                episode.symbol, episode.timeframe, episode.confidence, episode.sync_layers,
                episode.regime_quality, episode.rsi, episode.vwap_state,
                episode.fib_state, episode.structure_bias, episode.vp_position,
                episode.atr, episode.session_hour, episode.strike, episode.expiry_min,
                episode.entry_price, episode.stake, episode.env, int(episode.executed),
                episode.contract_id, episode.result_pnl,
                episode.result_status, episode.exit_price, episode.exit_time,
                episode.narrative, episode.signal_json
            ))
            await db.commit()
            return cursor.lastrowid

    async def mark_executed(self, episode_id: int, env: str, contract_id: str):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                UPDATE episodes SET executed = 1, env = ?, contract_id = ?
                WHERE id = ?
            """, (env, contract_id, episode_id))
            await db.commit()

    async def update_result(self, episode_id: int, pnl: float, status: str,
                           exit_price: float, exit_time: str):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                UPDATE episodes
                SET result_pnl = ?, result_status = ?, exit_price = ?, exit_time = ?
                WHERE id = ?
            """, (pnl, status, exit_price, exit_time, episode_id))
            await db.commit()

    async def count_completed_trades(self, env: str = "demo") -> int:
        """§10 demo-trade safety gate: count of real orders placed against
        `env` that have settled (WIN/LOSS), not just signals seen."""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("""
                SELECT COUNT(*) FROM episodes
                WHERE executed = 1 AND env = ? AND result_status IN ('WIN', 'LOSS')
            """, (env,))
            row = await cursor.fetchone()
            return row[0] if row else 0

    async def recent_signals_same_bar(self, symbol: str, bar_time: int) -> List[str]:
        """Every signal_type already logged for this symbol at this exact
        TRON bar timestamp — used for same-bar flip-priority suppression."""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("""
                SELECT signal_json FROM episodes
                WHERE symbol = ? AND json_extract(signal_json, '$.time') = ?
            """, (symbol, bar_time))
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
        """Last N *executed* trades — for the /history glassbox read."""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("""
                SELECT * FROM episodes WHERE executed = 1
                ORDER BY timestamp DESC LIMIT ?
            """, (limit,))
            rows = await cursor.fetchall()
            return [dict(r) for r in rows]

    async def get_similar_episodes(self, symbol: str, signal_type: str,
                                    limit: int = 5) -> List[TradeEpisode]:
        """Get recent similar episodes by symbol and signal type."""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("""
                SELECT * FROM episodes 
                WHERE symbol = ? AND signal_type = ? AND result_status != 'PENDING'
                ORDER BY timestamp DESC
                LIMIT ?
            """, (symbol, signal_type, limit))
            rows = await cursor.fetchall()
            return [TradeEpisode(**dict(row)) for row in rows]

    async def get_stats_by_signal_type(self, symbol: str, 
                                        signal_type: str) -> Dict[str, Any]:
        """Win rate, avg P&L, streak info for a specific signal type."""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("""
                SELECT result_status, result_pnl FROM episodes
                WHERE symbol = ? AND signal_type = ? AND result_status != 'PENDING'
                ORDER BY timestamp DESC
                LIMIT 50
            """, (symbol, signal_type))
            rows = await cursor.fetchall()

            if not rows:
                return {"total": 0, "wins": 0, "losses": 0, "win_rate": 0, "avg_pnl": 0, "streak": 0}

            wins = sum(1 for r in rows if r[0] == "WIN")
            losses = sum(1 for r in rows if r[0] == "LOSS")
            total = wins + losses
            pnls = [r[1] for r in rows if r[1] is not None]

            # Streak calculation
            streak = 0
            for r in rows:
                if r[0] == "WIN":
                    streak = streak + 1 if streak >= 0 else 1
                elif r[0] == "LOSS":
                    streak = streak - 1 if streak <= 0 else -1
                else:
                    break

            return {
                "total": total,
                "wins": wins,
                "losses": losses,
                "win_rate": round(wins / total * 100, 1) if total > 0 else 0,
                "avg_pnl": round(np.mean(pnls), 2) if pnls else 0,
                "streak": streak
            }

    async def get_daily_stats(self, symbol: str, date: str) -> Dict[str, Any]:
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("""
                SELECT result_status, result_pnl FROM episodes
                WHERE symbol = ? AND date(timestamp) = ? AND result_status != 'PENDING'
            """, (symbol, date))
            rows = await cursor.fetchall()

            wins = sum(1 for r in rows if r[0] == "WIN")
            losses = sum(1 for r in rows if r[0] == "LOSS")
            pnls = [r[1] for r in rows if r[1] is not None]

            return {
                "date": date,
                "trades": len(rows),
                "wins": wins,
                "losses": losses,
                "win_rate": round(wins / len(rows) * 100, 1) if rows else 0,
                "net_pnl": round(sum(pnls), 2) if pnls else 0
            }
