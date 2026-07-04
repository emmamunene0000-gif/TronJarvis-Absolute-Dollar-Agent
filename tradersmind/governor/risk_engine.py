"""
Risk Governor — The Guard
Hard-coded rules. No override without explicit operator action.
"""
import os
from typing import Dict, Any, Tuple, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta

@dataclass
class RiskProfile:
    max_stake: float = 5.0
    daily_loss_limit: float = 50.0
    max_consecutive_losses: int = 3
    cooldown_minutes: int = 5
    heat_threshold_percent: float = 20.0
    min_confidence_for_auto: int = 85
    min_sync_layers_for_auto: int = 4

class RiskGovernor:
    """
    The Risk Governor enforces capital protection rules.
    It CAN be overridden by operator, but override is logged and flagged.
    """
    def __init__(self, profile: RiskProfile = None):
        self.profile = profile or RiskProfile()
        self.daily_pnl: float = 0.0
        self.daily_trades: int = 0
        self.daily_wins: int = 0
        self.daily_losses: int = 0
        self.consecutive_losses: int = 0
        self.consecutive_wins: int = 0
        self.last_trade_time: Optional[datetime] = None
        self.cooldown_until: Optional[datetime] = None
        self.total_staked_today: float = 0.0
        self.session_start: datetime = datetime.utcnow()
        self.overrides: list = []

    def check_pre_trade(self, signal: Dict[str, Any], 
                        balance: float,
                        mode: str = "manual") -> Tuple[bool, str, float]:
        """
        Pre-trade risk check.
        Returns: (approved, reason, adjusted_stake)
        """
        now = datetime.utcnow()

        # 1. Cooldown check
        if self.cooldown_until and now < self.cooldown_until:
            remaining = (self.cooldown_until - now).seconds // 60
            return False, f"COOLDOWN: {remaining} minutes remaining", 0.0

        # 2. Daily loss limit
        if self.daily_pnl <= -self.profile.daily_loss_limit:
            return False, "DAILY_LIMIT: Daily loss limit reached", 0.0

        # 3. Consecutive losses
        if self.consecutive_losses >= self.profile.max_consecutive_losses:
            return False, f"STREAK_LIMIT: {self.consecutive_losses} consecutive losses", 0.0

        # 4. Confidence gate (for auto-execute)
        conf = signal.get("confidence", 0)
        sync = signal.get("fractal", {}).get("sync_layers", 0)

        if mode == "auto":
            if conf < self.profile.min_confidence_for_auto:
                return False, f"AUTO_CONF: Confidence {conf}% < {self.profile.min_confidence_for_auto}%", 0.0
            if sync < self.profile.min_sync_layers_for_auto:
                return False, f"AUTO_SYNC: Sync {sync}/4 < {self.profile.min_sync_layers_for_auto}/4", 0.0

        # 5. Stake sizing
        base_stake = self.profile.max_stake

        # Kelly Criterion Lite adjustment
        if self.daily_trades > 0:
            win_rate = self.daily_wins / self.daily_trades
            if win_rate > 0.55:
                base_stake = min(base_stake * 1.2, balance * 0.05)  # Max 5% of balance
            elif win_rate < 0.4:
                base_stake = base_stake * 0.75

        # Heat check — reduce size if recent volatility high
        if abs(self.daily_pnl) > balance * (self.profile.heat_threshold_percent / 100):
            base_stake = base_stake * 0.5
            return True, "HEAT_REDUCED: High volatility detected, stake halved", base_stake

        # 6. Time between trades (anti-spam)
        if self.last_trade_time and (now - self.last_trade_time).seconds < 30:
            return False, "RATE_LIMIT: Minimum 30 seconds between trades", 0.0

        return True, "APPROVED", round(base_stake, 2)

    def record_trade(self, stake: float, result_pnl: float, 
                     signal_type: str, timestamp: datetime = None):
        """Record trade result for state tracking."""
        if timestamp is None:
            timestamp = datetime.utcnow()

        self.last_trade_time = timestamp
        self.daily_trades += 1
        self.total_staked_today += stake
        self.daily_pnl += result_pnl

        if result_pnl > 0:
            self.daily_wins += 1
            self.consecutive_wins += 1
            self.consecutive_losses = 0
        else:
            self.daily_losses += 1
            self.consecutive_losses += 1
            self.consecutive_wins = 0

            # Activate cooldown after loss
            if self.consecutive_losses >= 2:
                self.cooldown_until = timestamp + timedelta(minutes=self.profile.cooldown_minutes)

        # Reset daily stats if new day
        if timestamp.date() != self.session_start.date():
            self._reset_daily()

    def _reset_daily(self):
        self.daily_pnl = 0.0
        self.daily_trades = 0
        self.daily_wins = 0
        self.daily_losses = 0
        self.total_staked_today = 0.0
        self.consecutive_losses = 0
        self.consecutive_wins = 0
        self.session_start = datetime.utcnow()

    def get_status(self) -> Dict[str, Any]:
        """Current risk state for dashboard display."""
        now = datetime.utcnow()
        return {
            "state": "ACTIVE" if self.daily_pnl > -self.profile.daily_loss_limit else "PAUSED",
            "daily_pnl": round(self.daily_pnl, 2),
            "daily_trades": self.daily_trades,
            "win_rate": round(self.daily_wins / self.daily_trades * 100, 1) if self.daily_trades > 0 else 0,
            "consecutive_losses": self.consecutive_losses,
            "consecutive_wins": self.consecutive_wins,
            "cooldown_active": self.cooldown_until is not None and now < self.cooldown_until,
            "cooldown_remaining": max(0, (self.cooldown_until - now).seconds // 60) if self.cooldown_until else 0,
            "total_staked": round(self.total_staked_today, 2),
            "heat_level": "COOL" if abs(self.daily_pnl) < self.profile.daily_loss_limit * 0.3 else 
                         "WARM" if abs(self.daily_pnl) < self.profile.daily_loss_limit * 0.7 else "HOT"
        }

    def operator_override(self, reason: str) -> Dict[str, Any]:
        """
        Operator override — logs the override but allows trade.
        USE WITH CAUTION. This is your money.
        """
        override_record = {
            "timestamp": datetime.utcnow().isoformat(),
            "reason": reason,
            "daily_pnl_at_override": self.daily_pnl,
            "consecutive_losses_at_override": self.consecutive_losses
        }
        self.overrides.append(override_record)
        return {
            "status": "OVERRIDE_GRANTED",
            "warning": "OVERRIDE ACTIVE — Risk limits bypassed. Proceed with caution.",
            "record": override_record
        }
