"""Turn a wide price panel (dates x tickers) into portfolio return series.

Two rebalancing conventions are supported, and they give different answers:

* ``rebalanced_returns``: weights are reset to target at every close, so each
  day's portfolio return is the weighted average of that day's asset returns.
* ``buy_and_hold_returns``: weights are set once at the base close and then
  drift with prices; the portfolio return on day t uses the weights from the
  close of day t-1.
"""

from __future__ import annotations

import math
from collections.abc import Mapping

import pandas as pd


def _check_prices(prices: pd.DataFrame) -> None:
    if prices.isna().any().any():
        missing = prices.index[prices.isna().any(axis=1)]
        raise ValueError(f"price panel has missing values on {list(missing)}")
    if not prices.index.is_unique or not prices.index.is_monotonic_increasing:
        raise ValueError("price panel index must be unique and sorted ascending")
    if (prices <= 0).any().any():
        raise ValueError("price panel has non-positive prices")


def _weight_vector(weights: Mapping[str, float], columns: pd.Index) -> pd.Series:
    w = pd.Series(weights, dtype=float)
    missing = set(w.index) - set(columns)
    if missing:
        raise ValueError(f"weights reference tickers not in prices: {sorted(missing)}")
    if not math.isclose(w.sum(), 1.0, abs_tol=1e-9):
        raise ValueError(f"weights must sum to 1, got {w.sum()}")
    return w


def simple_returns(prices: pd.DataFrame) -> pd.DataFrame:
    """Close-to-close simple returns. The first row (the base date) is dropped."""
    _check_prices(prices)
    return prices.pct_change(fill_method=None).iloc[1:]


def rebalanced_returns(prices: pd.DataFrame, weights: Mapping[str, float]) -> pd.Series:
    w = _weight_vector(weights, prices.columns)
    asset_returns = simple_returns(prices)[w.index]
    out = asset_returns.mul(w, axis=1).sum(axis=1)
    out.name = "rebalanced"
    return out


def buy_and_hold_returns(prices: pd.DataFrame, weights: Mapping[str, float]) -> pd.Series:
    w = _weight_vector(weights, prices.columns)
    _check_prices(prices)
    sub = prices[w.index]
    holdings_value = (sub / sub.iloc[0]).mul(w, axis=1).sum(axis=1)
    out = holdings_value.pct_change(fill_method=None).iloc[1:]
    out.name = "buy_and_hold"
    return out
