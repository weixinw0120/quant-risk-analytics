"""Download daily bars from Yahoo Finance and shape them into DB rows."""

from __future__ import annotations

import pandas as pd


def fetch_history(ticker: str, start: str, end: str) -> pd.DataFrame:
    """Raw and adjusted closes plus corporate actions. ``end`` is exclusive."""
    import yfinance as yf  # imported lazily so tests don't need network access

    return yf.Ticker(ticker).history(
        start=start, end=end, interval="1d", auto_adjust=False, actions=True
    )


def to_rows(history: pd.DataFrame, ticker: str) -> list[tuple]:
    """Convert a yfinance history frame to tuples in db.QUOTE_COLUMNS order."""
    if history.empty:
        raise ValueError(f"no rows downloaded for {ticker}")
    required = ["Open", "High", "Low", "Close", "Adj Close", "Volume", "Dividends", "Stock Splits"]
    missing = [c for c in required if c not in history.columns]
    if missing:
        raise ValueError(f"{ticker}: history is missing columns {missing}")
    rows = []
    for ts, r in history.iterrows():
        rows.append((
            pd.Timestamp(ts).date(), ticker,
            float(r["Open"]), float(r["High"]), float(r["Low"]), float(r["Close"]),
            float(r["Adj Close"]), int(r["Volume"]),
            float(r["Dividends"]), float(r["Stock Splits"]),
        ))
    return rows
