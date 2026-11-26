"""Command-line entry point: ``qra <command> ...``"""

from __future__ import annotations

import argparse
import sys

import pandas as pd


def _weights(tickers: list[str], weights: list[float] | None) -> dict[str, float]:
    if weights is None:
        return {t: 1.0 / len(tickers) for t in tickers}
    if len(weights) != len(tickers):
        raise SystemExit("--weights must have one value per ticker")
    return dict(zip(tickers, weights))


def cmd_init_db(args: argparse.Namespace) -> int:
    from qra import db

    with db.connect() as conn:
        db.init_schema(conn)
    print("schema ready")
    return 0


def cmd_ingest(args: argparse.Namespace) -> int:
    from qra import db, ingest

    with db.connect() as conn:
        for t in args.tickers:
            rows = ingest.to_rows(ingest.fetch_history(t, args.start, args.end), t)
            n = db.upsert_quotes(conn, rows)
            print(f"{t}: upserted {n} rows")
    return 0


def cmd_check(args: argparse.Namespace) -> int:
    from qra import db, quality

    with db.connect() as conn:
        quotes = db.load_quotes(conn, args.tickers, args.start, args.end)
    issues = quality.run_all(quotes, args.tickers)
    print(f"checked {len(quotes)} rows for {args.tickers} {args.start}..{args.end}")
    for name, df in issues.items():
        print(f"\n[FAIL] {name}: {len(df)} row(s)\n{df.to_string(index=False)}")
    if not issues:
        print("all checks passed")
    return 1 if issues else 0


def cmd_report(args: argparse.Namespace) -> int:
    from qra import db, quality
    from qra.report import performance_table

    tickers = sorted(set(args.tickers) | {args.benchmark})
    with db.connect() as conn:
        quotes = db.load_quotes(conn, tickers, args.start, args.end)
    issues = quality.run_all(quotes, tickers)
    if issues:
        print(f"quality checks failed: {list(issues)}; run `qra check` for details", file=sys.stderr)
        return 1
    prices = db.price_panel(quotes)
    table = performance_table(prices, _weights(args.tickers, args.weights), args.benchmark, args.expected_days)
    a = table.attrs
    print(f"base {a['base_date']:%Y-%m-%d}; returns {a['start']:%Y-%m-%d}..{a['end']:%Y-%m-%d} ({a['days']} days)")
    print(table.to_string(float_format="{:.2%}".format))
    if args.csv:
        table.to_csv(args.csv)
        print(f"saved {args.csv}")
    return 0


def cmd_demo(args: argparse.Namespace) -> int:
    """Hand-checkable example: price 100 -> 90 -> 99 gives -1% total, -10% drawdown."""
    from qra.metrics import performance_summary

    prices = pd.Series([100.0, 90.0, 99.0], index=pd.to_datetime(["2025-02-03", "2025-02-04", "2025-02-05"]))
    r = prices.pct_change(fill_method=None).iloc[1:]
    print(pd.Series(performance_summary(r, prices.index[0])).to_string(float_format="{:.2%}".format))
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="qra", description="Quant strategy validation & risk analytics")
    sub = p.add_subparsers(dest="command", required=True)

    sub.add_parser("init-db", help="create tables if missing").set_defaults(func=cmd_init_db)
    sub.add_parser("demo", help="offline hand-checkable example").set_defaults(func=cmd_demo)

    def window(sp: argparse.ArgumentParser) -> None:
        sp.add_argument("--tickers", nargs="+", required=True)
        sp.add_argument("--start", required=True, help="YYYY-MM-DD")
        sp.add_argument("--end", required=True, help="YYYY-MM-DD")

    sp = sub.add_parser("ingest", help="download from Yahoo Finance and upsert (end is exclusive)")
    window(sp)
    sp.set_defaults(func=cmd_ingest)

    sp = sub.add_parser("check", help="run data-quality checks; exit 1 on failure")
    window(sp)
    sp.set_defaults(func=cmd_check)

    sp = sub.add_parser("report", help="benchmark vs portfolio performance table")
    window(sp)
    sp.add_argument("--weights", nargs="+", type=float, help="one per ticker; default equal weight")
    sp.add_argument("--benchmark", default="SPY")
    sp.add_argument("--expected-days", type=int, help="fail if the window has a different number of return days")
    sp.add_argument("--csv", help="also write the table to this CSV path")
    sp.set_defaults(func=cmd_report)
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
