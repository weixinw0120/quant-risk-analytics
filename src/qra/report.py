"""Build the benchmark-vs-portfolio performance table from a price panel."""

from __future__ import annotations

from collections.abc import Mapping

import pandas as pd

from qra.metrics import performance_summary
from qra.portfolio import buy_and_hold_returns, rebalanced_returns, simple_returns


def performance_table(
    prices: pd.DataFrame,
    weights: Mapping[str, float],
    benchmark: str,
    expected_return_days: int | None = None,
) -> pd.DataFrame:
    """One row per strategy; columns are decimal metrics.

    The first row of ``prices`` is the base date (NAV = 1); returns start on the
    second row. ``expected_return_days`` guards against silently shortened
    windows, e.g. a trading day missing for every ticker.
    """
    base_date = prices.index[0]
    bench = simple_returns(prices[[benchmark]])[benchmark]
    if expected_return_days is not None and len(bench) != expected_return_days:
        raise ValueError(f"expected {expected_return_days} return days, got {len(bench)}")

    label = " / ".join(f"{w:.0%} {t}" for t, w in weights.items())
    series = {
        benchmark: bench,
        f"{label} (daily rebalance)": rebalanced_returns(prices, weights),
        f"{label} (buy and hold)": buy_and_hold_returns(prices, weights),
    }
    table = pd.DataFrame({name: performance_summary(r, base_date) for name, r in series.items()}).T
    table.index.name = "strategy"
    table.attrs.update(base_date=base_date, start=bench.index[0], end=bench.index[-1], days=len(bench))
    return table
