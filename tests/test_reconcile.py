import pandas as pd

from qra.reconcile import reconcile_counts


def test_finding_missing_duplicates():
    source  = pd.DataFrame(
            {"trade_id": ["A", "B","C"], "amount": [65, 25,25]}
            
        )

    report  = pd.DataFrame(
            {"trade_id": ["A", "B","B"], "amount": [65, 25,25]}
            
        )


    diff = reconcile_counts(source,report,key = "trade_id")

    assert diff["trade_id"].tolist() == ["B","C"]
    assert diff["expected_count"].tolist() == [1,1]
    assert diff["actual_count"].tolist() == [2,0]

def test_rightone():
    source  = pd.DataFrame(
            {"trade_id": ["A", "B","C"], "amount": [40, 25,25]}
            
        )

    report  = pd.DataFrame(
            {"trade_id": ["A", "B","C"], "amount": [40, 25,25]}
            
        )


    diff = reconcile_counts(source,report,key = "trade_id")



    assert diff.empty