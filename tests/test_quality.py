import pandas as pd

from qra import quality


def quotes(rows):
    cols = ["trade_date", "ticker", "open", "high", "low", "close", "adj_close", "volume"]
    df = pd.DataFrame(rows, columns=cols)
    df["trade_date"] = pd.to_datetime(df["trade_date"])
    return df


CLEAN = [
    ("2025-09-16", "SPY", 100, 101, 99, 100.5, 100.0, 1000),
    ("2025-09-16", "QQQ", 200, 202, 198, 201.0, 200.0, 2000),
    ("2025-09-17", "SPY", 100, 101, 99, 100.0, 99.5, 1000),
    ("2025-09-17", "QQQ", 200, 202, 198, 199.0, 198.0, 2000),
]


def test_clean_data_passes_every_check():
    assert quality.run_all(quotes(CLEAN), ["SPY", "QQQ"]) == {}


def test_two_spy_rows_on_one_day_is_a_duplicate_and_hides_a_missing_qqq():
    # Row count per date is still 2, so a COUNT(*) = 2 check would pass.
    rows = CLEAN[:2] + [CLEAN[2], CLEAN[2]]
    issues = quality.run_all(quotes(rows), ["SPY", "QQQ"])
    assert len(issues["duplicate_keys"]) == 2
    gap = issues["incomplete_dates"]
    assert gap["trade_date"].tolist() == [pd.Timestamp("2025-09-17")]
    assert gap["missing_tickers"].tolist() == [["QQQ"]]


def test_low_above_close_is_invalid():
    rows = CLEAN.copy()
    rows[0] = ("2025-09-16", "SPY", 100, 101, 100.8, 100.5, 100.0, 1000)
    assert len(quality.invalid_ohlc(quotes(rows))) == 1


def test_adj_close_outside_raw_range_is_allowed():
    # adj_close is dividend-adjusted, so it can sit below the raw low.
    rows = CLEAN.copy()
    rows[0] = ("2025-09-16", "SPY", 100, 101, 99, 100.5, 95.0, 1000)
    assert quality.invalid_ohlc(quotes(rows)).empty


def test_missing_adj_close_is_reported():
    rows = CLEAN.copy()
    rows[1] = ("2025-09-16", "QQQ", 200, 202, 198, 201.0, None, 2000)
    assert len(quality.missing_values(quotes(rows))) == 1
