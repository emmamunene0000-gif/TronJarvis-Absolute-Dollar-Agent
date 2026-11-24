from paper_trading import PaperTradingEngine


def test_paper_trade_settles_against_observed_price_and_loses_stake():
    paper = PaperTradingEngine(100)
    ticket = paper.buy(7, "R_100", "CALL", 10, 5, 100, "rise_fall")
    result = paper.settle(ticket["contract_id"], 99)
    assert result["result_status"] == "LOSS"
    assert result["result_pnl"] == -10
    assert paper.balance == 90


def test_paper_trade_profit_uses_observed_price():
    paper = PaperTradingEngine(100)
    ticket = paper.buy(8, "R_100", "PUT", 10, 5, 100, "rise_fall")
    result = paper.settle(ticket["contract_id"], 99)
    assert result["result_status"] == "WIN"
    assert result["result_pnl"] == 8
    assert paper.balance == 98
