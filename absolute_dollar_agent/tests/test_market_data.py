from market_data import parse_candles


def test_parse_candles_sorts_and_normalizes_deriv_payload():
    parsed = parse_candles({"candles": [
        {"epoch": 120, "open": "2", "high": "4", "low": "1", "close": "3"},
        {"epoch": 60, "open": 1, "high": 2, "low": 0.5, "close": 1.5},
    ]})
    assert [row["time"] for row in parsed] == [60, 120]
    assert parsed[0]["close"] == 1.5


def test_parse_candles_rejects_bad_ohlc():
    try:
        parse_candles({"candles": [{"epoch": 1, "open": 5, "high": 4, "low": 1, "close": 3}]})
    except ValueError as error:
        assert "inconsistent" in str(error)
    else:
        raise AssertionError("Expected invalid OHLC candle to be rejected")


def test_parse_candles_surfaces_provider_error():
    try:
        parse_candles({"error": {"message": "Market is closed"}})
    except ValueError as error:
        assert "Market is closed" in str(error)
    else:
        raise AssertionError("Expected Deriv provider error to be surfaced")
