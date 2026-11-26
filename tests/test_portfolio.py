import pandas as pd
import pytest

from qra.portfolio import buy_and_hold_returns, rebalanced_returns, simple_returns
from qra.report import performance_table

# SPY flat; QQQ +20% then -10%. Start 50/50 on the base close.
PRICES = pd.DataFrame(
    {"SPY": [100.0, 100.0, 100.0], "QQQ": [100.0, 120.0, 108.0]},
    index=pd.to_datetime(["2025-09-15", "2025-09-16", "2025-09-17"]),
)
W = {"SPY": 0.5, "QQQ": 0.5}


def test_daily_rebalance():
    r = rebalanced_returns(PRICES, W)
    assert list(r) == pytest.approx([0.10, -0.05])
    assert (1 + r).prod() - 1 == pytest.approx(0.045)  # 1.10 * 0.95


def test_buy_and_hold_uses_drifted_weights():
    # Day 2 opens with 50 SPY + 60 QQQ = 110, QQQ weight 54.5%; ends 50 + 54 = 104.
    r = buy_and_hold_returns(PRICES, W)
    assert r.iloc[1] == pytest.approx(104 / 110 - 1)
    assert (1 + r).prod() - 1 == pytest.approx(0.04)


def test_rebalance_and_buy_and_hold_differ_once_weights_drift():
    assert rebalanced_returns(PRICES, W).iloc[1] != pytest.approx(buy_and_hold_returns(PRICES, W).iloc[1])


def test_simple_returns_drop_base_row():
    r = simple_returns(PRICES)
    assert r.index[0] == pd.Timestamp("2025-09-16")
    assert len(r) == len(PRICES) - 1


def test_missing_price_is_rejected_not_skipped():
    # pandas' sum(axis=1) would silently treat a NaN return as 0.
    bad = PRICES.copy()
    bad.loc["2025-09-16", "QQQ"] = float("nan")
    with pytest.raises(ValueError, match="missing"):
        rebalanced_returns(bad, W)


def test_weights_must_sum_to_one():
    with pytest.raises(ValueError, match="sum to 1"):
        rebalanced_returns(PRICES, {"SPY": 0.5, "QQQ": 0.6})


def test_performance_table_shape_and_window_guard():
    table = performance_table(PRICES, W, "SPY", expected_return_days=2)
    assert table.shape == (3, 3)
    assert table.loc["SPY", "cumulative_return"] == 0.0
    with pytest.raises(ValueError, match="expected 75"):
        performance_table(PRICES, W, "SPY", expected_return_days=75)
