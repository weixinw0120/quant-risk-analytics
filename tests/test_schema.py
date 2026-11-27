import pandas as pd
import pytest

from qra.quality import invalid_ohlc
from qra.schema import validate_quotes

CLEAN  = pd.DataFrame(
{
        "trade_date": ["2025-09-23","2025-09-23"],
        "ticker": ["SPY","QQQ"],
        "open": [100, 50],
        "high": [101, 51],
        "low": [99, 48],
        "close": [100.5, 49],
        "volume": [1000, 500],
        "adj_close":[100, 50]


}

)
def help_change(df,index,column,value)-> pd.DataFrame:
    df = df.copy()
    df.iat[index, df.columns.get_loc(column)] = value
    return df

@pytest.mark.parametrize(
    "index,column,value,expected", 
    [(0,"close",None,[[0,"not_nullable"]]), 
     (0,"volume",-1,[[0,"greater_than_or_equal_to(0)"]]),
     (1,"ticker","SPY",[[ 0, "multiple_fields_uniqueness"],[1,"multiple_fields_uniqueness"]]),
     (1,"high",1,[[1,"valid_high"]]),
     (0,"low",1000,[[0,"valid_low"]])
    ])
def test_validate_quotes(index,column,value,expected):
    df = help_change(CLEAN,index,column,value)
    failure = validate_quotes(df)

    assert failure.values.tolist() == expected


def test_not_change():
    CLEAN_COPY= CLEAN.copy()
    failure = validate_quotes(CLEAN)
    assert CLEAN.equals(CLEAN_COPY)
    assert failure.empty

def test_same_as_invalid_ohlc():
    df = help_change(CLEAN,1,"high",1)
    failure = validate_quotes(df)
    failure_2 = invalid_ohlc(df)

    assert  failure["index"].values.tolist() == failure_2.index.tolist()