"""
Unit tests for Risk Governor.
"""
import pytest
from governor.risk_engine import RiskGovernor, RiskProfile, can_unlock_live_mode


class TestRiskGovernor:
    def test_approve_normal_trade_sizes_within_band(self):
        gov = RiskGovernor(RiskProfile(min_stake=0.35, max_dynamic_stake=1.00, max_stake=5.0))
        signal = {"confidence": 90, "fractal": {"sync_layers": 4}}

        approved, reason, stake = gov.check_pre_trade(signal, balance=1000.0, mode="auto")
        assert approved is True
        assert 0.35 <= stake <= 1.00

    def test_higher_confidence_sizes_larger_within_band(self):
        gov_low = RiskGovernor(RiskProfile())
        gov_high = RiskGovernor(RiskProfile())

        _, _, stake_low = gov_low.check_pre_trade(
            {"confidence": 50, "fractal": {"sync_layers": 2}}, balance=1000.0, mode="manual")
        _, _, stake_high = gov_high.check_pre_trade(
            {"confidence": 100, "fractal": {"sync_layers": 4}}, balance=1000.0, mode="manual")

        assert stake_high > stake_low

    def test_stake_never_exceeds_hard_ceiling(self):
        gov = RiskGovernor(RiskProfile(min_stake=0.35, max_dynamic_stake=1.00, max_stake=5.0))
        signal = {"confidence": 100, "fractal": {"sync_layers": 4}}

        approved, reason, stake = gov.check_pre_trade(signal, balance=1000.0, mode="manual")
        assert approved is True
        assert stake <= 5.0

    def test_reject_low_confidence_auto(self):
        gov = RiskGovernor(RiskProfile(min_confidence_for_auto=85))
        signal = {"confidence": 60, "fractal": {"sync_layers": 4}}

        approved, reason, stake = gov.check_pre_trade(signal, balance=1000.0, mode="auto")
        assert approved is False
        assert "AUTO_CONF" in reason

    def test_reject_low_sync_auto(self):
        gov = RiskGovernor(RiskProfile(min_sync_layers_for_auto=4))
        signal = {"confidence": 95, "fractal": {"sync_layers": 3}}

        approved, reason, stake = gov.check_pre_trade(signal, balance=1000.0, mode="auto")
        assert approved is False
        assert "AUTO_SYNC" in reason

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
        gov.record_trade(stake=0.75, result_pnl=1.10, signal_type="H4_FLIP_CALL")

        assert gov.daily_trades == 1
        assert gov.daily_wins == 1
        assert gov.consecutive_wins == 1
        assert gov.daily_pnl == 1.10

    def test_record_loss_triggers_cooldown(self):
        gov = RiskGovernor(RiskProfile(cooldown_minutes=5))
        gov.record_trade(stake=0.75, result_pnl=-0.75, signal_type="CALL_ENTRY")
        gov.record_trade(stake=0.75, result_pnl=-0.75, signal_type="CALL_ENTRY")

        assert gov.consecutive_losses == 2
        assert gov.cooldown_until is not None

    def test_operator_override_logs_operator_id(self):
        gov = RiskGovernor()
        result = gov.operator_override("manual review", operator_id="op-42")

        assert result["status"] == "OVERRIDE_GRANTED"
        assert gov.overrides[0]["operator_id"] == "op-42"


class TestLiveModeGate:
    def test_refuses_below_threshold(self):
        assert can_unlock_live_mode(99, required=100) is False

    def test_unlocks_at_threshold(self):
        assert can_unlock_live_mode(100, required=100) is True

    def test_unlocks_above_threshold(self):
        assert can_unlock_live_mode(150, required=100) is True
