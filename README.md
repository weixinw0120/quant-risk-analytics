# Quant Strategy Validation & Risk Analytics

A small, reproducible pipeline that loads daily ETF prices into PostgreSQL, checks data quality, and produces a benchmark-vs-portfolio performance table. Every metric is covered by hand-checkable unit tests.

```
Yahoo Finance ──ingest──▶ PostgreSQL (daily_market_prices) ──check──▶ quality report
                                   │
                                   └──report──▶ price panel ─▶ portfolio returns ─▶ metrics table
```

## Quick start

Requires Python ≥ 3.11 and a reachable PostgreSQL. Connection settings come from the standard libpq variables. The defaults are `localhost:5432`, database `quant_lab`, and user `postgres`. The password comes from `PGPASSWORD` or a pgpass file, never from the code.

```powershell
pip install -e ".[dev]"
pytest -q                      # offline, no database needed
qra demo                       # 100 -> 90 -> 99: cumulative -1.00%, max drawdown -10.00%

$env:PGPASSWORD = "<your password>"
qra init-db
qra ingest --tickers SPY QQQ --start 2025-01-01 --end 2026-01-01   # end is exclusive; safe to re-run
qra check  --tickers SPY QQQ --start 2025-01-01 --end 2025-12-31   # exit code 1 on any failure
qra report --tickers SPY QQQ --weights 0.5 0.5 --benchmark SPY `
           --start 2025-09-15 --end 2025-12-31 --expected-days 75
```

## Methodology

| Item | Convention |
|---|---|
| Price | `adj_close` (split and dividend adjusted). Raw OHLC is used only for range checks, because the two are on different bases. |
| Window | The first price date is the **base date** with NAV = 1. Returns start on the next trading day. |
| Returns | Close-to-close simple returns, in decimals. |
| Daily rebalance | Weights reset to target at every close. The portfolio return is the weighted average of that day's asset returns. |
| Buy and hold | Weights are set at the base close and then drift with prices. |
| Volatility | Sample standard deviation (ddof = 1) × √252. |
| Max drawdown | Minimum of NAV / running peak − 1. The base-date NAV is included, so a first-day loss counts. |
| Costs, risk-free rate | Both zero in this version. |

## Data-quality checks (`qra check`)

| Check | Catches |
|---|---|
| `duplicate_keys` | Two rows for the same (date, ticker). Example: two SPY rows on one day, which still passes a naive `COUNT(*) = 2` per date. |
| `missing_values` | Nulls in price or volume columns. |
| `invalid_ohlc` | Non-positive prices, negative volume, or low/high that do not bracket open/close. |
| `incomplete_dates` | Dates where some requested tickers have a row and others do not. |

**Known limitation:** a trading day that is missing for *every* ticker is invisible to these checks. `report --expected-days` guards a fixed window against that. A proper fix needs an exchange calendar (planned).

## Results (local data)

Window: base 2025-09-15, 75 return days from 2025-09-16 to 2025-12-31. All quality checks passed.

| Strategy | Cumulative return | Annualized vol | Max drawdown |
|---|---:|---:|---:|
| SPY | 3.77% | 11.88% | −5.07% |
| 50% SPY / 50% QQQ, daily rebalance | 3.94% | 14.19% | −6.48% |
| 50% SPY / 50% QQQ, buy and hold | 3.92% | 14.21% | −6.50% |

**Verification.**
- The SPY and daily-rebalance rows match the earlier v0.1 script run on the same data, figure by figure.
- The buy-and-hold cumulative return matches a separate calculation from start and end prices: $100 grows to $103.924866.

Buy and hold is slightly more volatile here. QQQ outperformed over the window, so its weight drifted above 50%, and QQQ is the more volatile asset.

Regenerate the table with the `qra report` command above.

## Layout

```
src/qra/
  metrics.py    NAV, cumulative return, annualized volatility, max drawdown
  portfolio.py  simple returns, daily-rebalance and buy-and-hold portfolios
  quality.py    data-quality checks on long-format quotes
  db.py         connection, schema, idempotent upsert, loaders
  ingest.py     Yahoo Finance download -> DB rows
  report.py     performance table
  cli.py        `qra` command
sql/schema.sql  table definition with primary key and price constraints
tests/          offline unit tests (pytest)
```

## Roadmap

- [ ] Trade reconciliation module: source vs report, by ID, count and amount
- [ ] Cross-check metrics against `empyrical-reloaded` / `pyfolio-reloaded`
- [ ] Exchange-calendar coverage check
- [ ] Docker Compose (PostgreSQL + app) for one-command reproduction
- [ ] Block-bootstrap confidence interval for the mean daily excess return
