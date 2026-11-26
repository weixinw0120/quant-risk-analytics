import datetime as dt

import pandas as pd
import pytest

from qra.cli import main
from qra.db import QUOTE_COLUMNS
from qra.ingest import to_rows


def yf_frame():
    # yfinance returns a tz-aware index in exchange time.
    idx = pd.DatetimeIndex(["2025-03-21", "2025-03-24"]).tz_localize("America/New_York")
    return pd.DataFrame(
        {
            "Open": [560.0, 570.0], "High": [565.0, 575.0], "Low": [555.0, 568.0],
            "Close": [563.98, 574.08], "Adj Close": [557.0, 567.0],
            "Volume": [1_000_000, 900_000], "Dividends": [1.696, 0.0], "Stock Splits": [0.0, 0.0],
        },
        index=idx,
    )


def test_to_rows_matches_db_column_order():
    rows = to_rows(yf_frame(), "SPY")
    assert len(rows) == 2
    assert len(rows[0]) == len(QUOTE_COLUMNS)
    assert rows[0][:2] == (dt.date(2025, 3, 21), "SPY")
    assert rows[0][QUOTE_COLUMNS.index("dividends")] == pytest.approx(1.696)
    assert isinstance(rows[0][QUOTE_COLUMNS.index("volume")], int)


def test_to_rows_rejects_empty_download():
    with pytest.raises(ValueError, match="no rows"):
        to_rows(pd.DataFrame(), "SPY")


def test_demo_runs_offline(capsys):
    assert main(["demo"]) == 0
    out = capsys.readouterr().out
    assert "-1.00%" in out and "-10.00%" in out
