
import pandas as pd
import pandera.pandas as pa
from pandera.errors import SchemaErrors

QUOTES_SCHEMA = pa.DataFrameSchema(
    columns={
        "trade_date": pa.Column(pa.DateTime,coerce=True),                    
        "ticker": pa.Column(str, nullable=False),     
        "open": pa.Column(float, pa.Check.gt(0), nullable=False,coerce=True),     
        "high": pa.Column(float, pa.Check.gt(0), nullable=False,coerce=True),  
        "low": pa.Column(float, pa.Check.gt(0), nullable=False,coerce=True),  
        "close": pa.Column(float, pa.Check.gt(0), nullable=False,coerce=True), 
        "volume": pa.Column(int, pa.Check.ge(0), nullable=False,coerce=True),
        "adj_close": pa.Column(float, pa.Check.gt(0), nullable=False,coerce=True)

    },
    checks=[
        pa.Check(lambda df: df["high"] >= df[["open","close"]].max(axis = 1), name = "valid_high"),
        pa.Check(lambda df: df["low"] <=  df[["open","close"]].min(axis = 1), name = "valid_low"),      
    ],
    unique= ["trade_date","ticker"],
    strict=False   # 允许出现 schema 里没声明的列
)

def validate_quotes(quotes: pd.DataFrame) -> pd.DataFrame:
    '''
    pass if return empty dataframe 
    else return failures with [index,check]
    '''
    try:
        QUOTES_SCHEMA.validate(quotes,lazy=True)
    except SchemaErrors as e:
        failure = e.failure_cases
        failure = failure.reset_index(drop= True)
        failure = failure.drop_duplicates(subset = ["index","check"])
        failure = failure.sort_values(["index","check"])
        failure = failure[["index","check"]]
        failure = failure.reset_index(drop= True)
        return failure
    return pd.DataFrame()

if __name__ == "__main__":
    test = pd.DataFrame({
        "trade_date": ["2025-09-23","2025-09-23","2025-09-23","2025-09-24"],
        "ticker": ["SPY","QQQ", "SPY","SPY"],
        "open": [100, 50, 100,101],
        "high": [101, 49.5, 101,102],
        "low": [99, 48, 99,100],
        "close": [100.5, 49, 100.5,None],
        "volume": [1000, 500, 1000,-5],
        "adj_close":[100, 50, 100,101]
    }
    )

    failure = validate_quotes(test)
    print(failure)



