"""Performance metrics for a single daily simple-return series.

Conventions
-----------
* Returns are decimal simple returns (0.01 == 1%), indexed by trade date.
* The NAV starts at 1.0 on ``base_date`` (the last close *before* the first
  return). Including that starting point matters: a loss on the very first
  day is a drawdown from the initial capital.
* Volatility uses the sample standard deviation (ddof=1), annualised with
  sqrt(252).
* Drawdowns are reported as negative numbers.
"""

from __future__ import annotations

import math

import pandas as pd

TRADING_DAYS_PER_YEAR = 252


def validate_returns(returns: pd.Series, base_date: pd.Timestamp | None = None) -> None:
    """Raise ValueError if the series breaks the conventions above."""
    if returns.empty:
        raise ValueError("return series is empty")
    if returns.isna().any():
        bad = list(returns.index[returns.isna()])
        raise ValueError(f"return series has missing values on {bad}")
    if not returns.index.is_unique:
        dupes = list(returns.index[returns.index.duplicated()])
        raise ValueError(f"return series has duplicate dates {dupes}")
    if not returns.index.is_monotonic_increasing:
        raise ValueError("return series must be sorted by date ascending")
    if base_date is not None and pd.Timestamp(base_date) >= returns.index[0]:
        raise ValueError(
            f"base_date {base_date} must be earlier than the first return date {returns.index[0]}"
        )


def nav_series(returns: pd.Series, base_date: pd.Timestamp) -> pd.Series:
    """NAV path starting at 1.0 on base_date, compounded by the daily returns."""
    validate_returns(returns, base_date)
    growth = (1.0 + returns).cumprod()
    start = pd.Series([1.0], index=pd.DatetimeIndex([pd.Timestamp(base_date)]))
    nav = pd.concat([start, growth])
    nav.name = "nav"
    return nav


def cumulative_return(returns: pd.Series) -> float:
    validate_returns(returns)
    return float((1.0 + returns).prod() - 1.0)


def annualized_volatility(returns: pd.Series, periods_per_year: int = TRADING_DAYS_PER_YEAR) -> float:
    validate_returns(returns)
    if len(returns) < 2:
        raise ValueError("need at least two returns for a sample standard deviation")
    return float(returns.std(ddof=1) * math.sqrt(periods_per_year))


def max_drawdown(nav: pd.Series) -> float:
    """Largest peak-to-trough decline of a NAV path, as a negative decimal."""
    return float((nav / nav.cummax() - 1.0).min())


def performance_summary(returns: pd.Series, base_date: pd.Timestamp) -> dict[str, float]:
    nav = nav_series(returns, base_date)
    return {
        "cumulative_return": cumulative_return(returns),
        "annualized_volatility": annualized_volatility(returns),
        "max_drawdown": max_drawdown(nav),
    }
