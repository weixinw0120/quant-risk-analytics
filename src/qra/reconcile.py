"""Trade reconciliation: compare a source table against a downstream report.

W2 Day 4 · Lab B · Q3 — to be implemented by the author.
"""

from __future__ import annotations

import pandas as pd


def reconcile_counts(source: pd.DataFrame, report: pd.DataFrame, key: str = "trade_id") -> pd.DataFrame:
    """Return one row per key whose count differs between source and report.

    Expected output columns: key, expected_count, actual_count.
    An empty DataFrame means the two sides match row-for-row on ``key``.
    """

    source = source.groupby(key).size()
    
    source = source.rename("expected_count").reset_index()
    
    report = report.groupby(key).size()
    report = report.rename("actual_count").reset_index()

    merged = pd.merge(source,report,on = key,how= "outer")
    
    merged["actual_count"] = merged["actual_count"].fillna(0).astype(int)
    merged["expected_count"] = merged["expected_count"].fillna(0).astype(int)
    different = merged[merged["expected_count"] !=merged["actual_count"]]
    different = different.sort_values(key).reset_index(drop=True)

    

    return different
