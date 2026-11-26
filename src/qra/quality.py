"""Data-quality checks on long-format daily quotes.

Expected columns: trade_date, ticker, open, high, low, close, adj_close, volume.
Each check returns a DataFrame of offending rows (empty == pass), so callers
can both fail fast and show *which* rows broke the rule.
"""

from __future__ import annotations

import pandas as pd

KEY = ["trade_date", "ticker"]
REQUIRED = ["open", "high", "low", "close", "adj_close", "volume"]


def duplicate_keys(quotes: pd.DataFrame) -> pd.DataFrame:
    """Rows sharing (trade_date, ticker) with another row."""
    return quotes[quotes.duplicated(subset=KEY, keep=False)].sort_values(KEY)


def missing_values(quotes: pd.DataFrame) -> pd.DataFrame:
    cols = [c for c in REQUIRED if c in quotes.columns]
    return quotes[quotes[cols].isna().any(axis=1)]


def invalid_ohlc(quotes: pd.DataFrame) -> pd.DataFrame:
    """Non-positive prices, negative volume, or low/high not bracketing open/close.

    Only raw OHLC is compared: adj_close is on a different (dividend-adjusted)
    basis and may legitimately sit outside the raw low/high range.
    """
    q = quotes.dropna(subset=["open", "high", "low", "close"])
    bad = (
        (q[["open", "high", "low", "close"]] <= 0).any(axis=1)
        | (q["volume"] < 0)
        | (q["low"] > q[["open", "close"]].min(axis=1))
        | (q["high"] < q[["open", "close"]].max(axis=1))
    )
    return q[bad]


def incomplete_dates(quotes: pd.DataFrame, tickers: list[str]) -> pd.DataFrame:
    """Dates where at least one requested ticker has a row but another does not.

    Limitation: a date on which *every* ticker is missing never appears in the
    data, so it cannot be found here; that needs an exchange calendar.
    """
    present = quotes[quotes["ticker"].isin(tickers)]
    per_date = present.groupby("trade_date")["ticker"].apply(set)
    expected = set(tickers)
    gaps = per_date[per_date.apply(lambda s: s != expected)]
    return pd.DataFrame(
        {
            "trade_date": gaps.index,
            "missing_tickers": [sorted(expected - s) for s in gaps],
        }
    ).reset_index(drop=True)


def run_all(quotes: pd.DataFrame, tickers: list[str]) -> dict[str, pd.DataFrame]:
    """Run every check; returns only the checks that found problems."""
    results = {
        "duplicate_keys": duplicate_keys(quotes),
        "missing_values": missing_values(quotes),
        "invalid_ohlc": invalid_ohlc(quotes),
        "incomplete_dates": incomplete_dates(quotes, tickers),
    }
    return {name: df for name, df in results.items() if not df.empty}
