-- One row per (trade_date, ticker). Raw OHLC and adj_close are on different
-- bases (adj_close is dividend/split adjusted), so only raw OHLC is range-checked.
CREATE TABLE IF NOT EXISTS daily_market_prices (
    trade_date    DATE             NOT NULL,
    ticker        TEXT             NOT NULL,
    open          DOUBLE PRECISION NOT NULL,
    high          DOUBLE PRECISION NOT NULL,
    low           DOUBLE PRECISION NOT NULL,
    close         DOUBLE PRECISION NOT NULL,
    adj_close     DOUBLE PRECISION,
    volume        BIGINT           NOT NULL,
    dividends     DOUBLE PRECISION,
    stock_splits  DOUBLE PRECISION,

    CONSTRAINT primary_composite_key PRIMARY KEY (trade_date, ticker),
    CONSTRAINT positive_open      CHECK (open > 0),
    CONSTRAINT positive_close     CHECK (close > 0),
    CONSTRAINT positive_high      CHECK (high > 0),
    CONSTRAINT positive_low       CHECK (low > 0),
    CONSTRAINT nonnegative_volume CHECK (volume >= 0),
    CONSTRAINT valid_low          CHECK (low <= open AND low <= close),
    CONSTRAINT valid_high         CHECK (high >= open AND high >= close)
);
