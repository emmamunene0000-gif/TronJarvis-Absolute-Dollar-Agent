"""
Unit tests for Risk Governor.
"""
import pytest
from governor.risk_engine import RiskGovernor, RiskProfile

class TestRiskGovernor:
    def test_approve_normal_trade(self):
        gov = RiskGovernor(RiskProfile(max_stake=5.0, daily_loss_limit=50.0))
        signal = {"confidence": 90, "fractal": {"sync_layers": 4}}

        approved, reason, stake = gov.check_pre_trade(signal, balance=1000.0, mode="auto")
        assert approved is True
        assert stake == 5.0

    def test_reject_low_confidence_auto(self):
        gov = RiskGovernor(RiskProfile(min_confidence_for_auto=85))
        signal = {"confidence": 60, "fractal": {"sync_layers": 4}}

        approved, reason, stake = gov.check_pre_trade(signal, balance=1000.0, mode="auto")
        assert approved is False
        assert "AUTO_CONF" in reason

    def test_daily_loss_limit(self):
        gov = RiskGovernor(RiskProfile(daily_loss_limit=50.0))
        gov.daily_pnl = -50.0

        signal = {"confidence": 95, "fractal": {"sync_layers": 4}}
        approved, reason, stake = gov.check_pre_trade(signal, balance=1000.0, mode="auto")
        assert approved is False
        assert "DAILY_LIMIT" in reason

    def test_consecutive_losses(self):
        gov = RiskGovernor(RiskProfile(max_consecutive_losses=3))
        gov.consecutive_losses = 3

        signal = {"confidence": 95, "fractal": {"sync_layers": 4}}
        approved, reason, stake = gov.check_pre_trade(signal, balance=1000.0, mode="manual")
        assert approved is False
        assert "STREAK_LIMIT" in reason

    def test_cooldown_active(self):
        from datetime import datetime, timedelta
        gov = RiskGovernor(RiskProfile(cooldown_minutes=5))
        gov.cooldown_until = datetime.utcnow() + timedelta(minutes=3)

        signal = {"confidence": 95, "fractal": {"sync_layers": 4}}
        approved, reason, stake = gov.check_pre_trade(signal, balance=1000.0, mode="manual")
        assert approved is False
        assert "COOLDOWN" in reason

    def test_record_win(self):
        gov = RiskGovernor()
        gov.record_trade(stake=5.0, result_pnl=7.5, signal_type="H4_FLIP_CALL")

        assert gov.daily_trades == 1
        assert gov.daily_wins == 1
        assert gov.consecutive_wins == 1
        assert gov.daily_pnl == 7.5

    def test_record_loss_triggers_cooldown(self):
        gov = RiskGovernor(RiskProfile(cooldown_minutes=5))
        gov.record_trade(stake=5.0, result_pnl=-5.0, signal_type="CALL_ENTRY")
        gov.record_trade(stake=5.0, result_pnl=-5.0, signal_type="CALL_ENTRY")

        assert gov.consecutive_losses == 2
        assert gov.cooldown_until is not None
