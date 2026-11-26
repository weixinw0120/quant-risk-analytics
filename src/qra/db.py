"""PostgreSQL access. Connection settings come from standard libpq environment
variables, so no credentials live in the code:

    PGHOST (default localhost), PGPORT (5432), PGDATABASE (quant_lab),
    PGUSER (postgres), PGPASSWORD (or a pgpass file).
"""

from __future__ import annotations

import os
from collections.abc import Iterable, Sequence
from pathlib import Path

import pandas as pd
import psycopg

SCHEMA_SQL = Path(__file__).resolve().parents[2] / "sql" / "schema.sql"

QUOTE_COLUMNS = [
    "trade_date", "ticker", "open", "high", "low", "close",
    "adj_close", "volume", "dividends", "stock_splits",
]

UPSERT_SQL = f"""
INSERT INTO daily_market_prices ({", ".join(QUOTE_COLUMNS)})
VALUES ({", ".join(["%s"] * len(QUOTE_COLUMNS))})
ON CONFLICT (trade_date, ticker) DO UPDATE SET
    {", ".join(f"{c} = EXCLUDED.{c}" for c in QUOTE_COLUMNS[2:])}
"""


def connect() -> psycopg.Connection:
    return psycopg.connect(
        host=os.getenv("PGHOST", "localhost"),
        port=os.getenv("PGPORT", "5432"),
        dbname=os.getenv("PGDATABASE", "quant_lab"),
        user=os.getenv("PGUSER", "postgres"),
    )


def init_schema(conn: psycopg.Connection) -> None:
    conn.execute(SCHEMA_SQL.read_text(encoding="utf-8"))


def upsert_quotes(conn: psycopg.Connection, rows: Iterable[Sequence]) -> int:
    """Insert or overwrite rows keyed by (trade_date, ticker). Re-running with
    the same rows leaves the table unchanged (idempotent)."""
    rows = list(rows)
    with conn.cursor() as cur:
        cur.executemany(UPSERT_SQL, rows)
    return len(rows)


def load_quotes(conn: psycopg.Connection, tickers: Sequence[str], start: str, end: str) -> pd.DataFrame:
    """Long-format quotes for tickers with start <= trade_date <= end."""
    cur = conn.execute(
        f"""
        SELECT {", ".join(QUOTE_COLUMNS)}
        FROM daily_market_prices
        WHERE ticker = ANY(%s) AND trade_date BETWEEN %s AND %s
        ORDER BY trade_date, ticker
        """,
        (list(tickers), start, end),
    )
    quotes = pd.DataFrame(cur.fetchall(), columns=QUOTE_COLUMNS)
    quotes["trade_date"] = pd.to_datetime(quotes["trade_date"])
    return quotes


def price_panel(quotes: pd.DataFrame, field: str = "adj_close") -> pd.DataFrame:
    """Wide dates x tickers panel. pivot() raises on duplicate keys, so run the
    quality checks first to get a readable error."""
    return (
        quotes.pivot(index="trade_date", columns="ticker", values=field)
        .sort_index()
        .astype(float)
    )
