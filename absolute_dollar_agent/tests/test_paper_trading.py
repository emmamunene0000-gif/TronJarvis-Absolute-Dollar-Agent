"""Tests for runtime wiring and paper mode."""
import os
from paper_trading import PaperTradingEngine


def test_paper_stake_and_settlement():
    engine = PaperTradingEngine(100)
    ticket = engine.buy(1, "R_100", "CALL", 10, 5, 100, "rise_fall")
    settled = engine.settle(ticket["contract_id"], 99)
    assert settled["result_status"] == "LOSS"
    assert engine.balance == 90


def test_paper_win_from_observed_price():
    engine = PaperTradingEngine(100)
    ticket = engine.buy(2, "R_100", "PUT", 10, 5, 100, "rise_fall")
    settled = engine.settle(ticket["contract_id"], 99)
    assert settled["result_status"] == "WIN"
    assert settled["result_pnl"] == 8
