import math

import pandas as pd
import pytest

from qra.metrics import (
    annualized_volatility,
    cumulative_return,
    max_drawdown,
    nav_series,
    performance_summary,
)

BASE = pd.Timestamp("2026-01-05")


def series(values, start="2026-01-06"):
    return pd.Series(values, index=pd.bdate_range(start, periods=len(values)), dtype=float)


def test_first_day_loss_counts_as_drawdown_from_initial_capital():
    # -10% then flat: both metrics are -10%. Dropping the base-date NAV of 1.0
    # would wrongly report a 0% drawdown.
    s = performance_summary(series([-0.10, 0.0]), BASE)
    assert s["cumulative_return"] == pytest.approx(-0.10)
    assert s["max_drawdown"] == pytest.approx(-0.10)


def test_cumulative_return_and_drawdown_differ_after_recovery():
    # -20% then +10%: 0.8 * 1.1 = 0.88 -> -12% total, but the trough was -20%.
    s = performance_summary(series([-0.20, 0.10]), BASE)
    assert s["cumulative_return"] == pytest.approx(-0.12)
    assert s["max_drawdown"] == pytest.approx(-0.20)


def test_price_path_100_90_99():
    prices = pd.Series([100.0, 90.0, 99.0], index=pd.to_datetime(["2025-02-03", "2025-02-04", "2025-02-05"]))
    r = prices.pct_change(fill_method=None).iloc[1:]
    s = performance_summary(r, prices.index[0])
    assert s["cumulative_return"] == pytest.approx(-0.01)
    assert s["max_drawdown"] == pytest.approx(-0.10)


def test_annualized_volatility_uses_sample_std():
    # mean 0, deviations +-1%: sample var = 2 * 0.0001 / (2 - 1) = 0.0002
    vol = annualized_volatility(series([0.01, -0.01]))
    assert vol == pytest.approx(math.sqrt(0.0002) * math.sqrt(252))


def test_nav_starts_at_one_on_base_date():
    nav = nav_series(series([0.05, -0.02]), BASE)
    assert nav.index[0] == BASE
    assert nav.iloc[0] == 1.0
    assert nav.iloc[-1] == pytest.approx(1.05 * 0.98)


def test_max_drawdown_is_zero_for_monotone_gains():
    assert max_drawdown(nav_series(series([0.01, 0.02]), BASE)) == 0.0


@pytest.mark.parametrize(
    "bad, match",
    [
        (pd.Series([0.01, float("nan")], index=pd.to_datetime(["2026-01-06", "2026-01-07"])), "missing"),
        (pd.Series([0.01, 0.02], index=pd.to_datetime(["2026-01-06", "2026-01-06"])), "duplicate"),
        (pd.Series([0.01, 0.02], index=pd.to_datetime(["2026-01-07", "2026-01-06"])), "sorted"),
    ],
)
def test_rejects_malformed_series(bad, match):
    with pytest.raises(ValueError, match=match):
        cumulative_return(bad)


def test_rejects_base_date_not_before_first_return():
    with pytest.raises(ValueError, match="base_date"):
        nav_series(series([0.01]), pd.Timestamp("2026-01-06"))
