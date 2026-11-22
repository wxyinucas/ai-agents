"""Command-line entry point for checking a local market CSV file."""

from __future__ import annotations

import argparse
from collections.abc import Sequence
from pathlib import Path
import sys

import pandas as pd


REQUIRED_COLUMNS = {"timestamp", "symbol", "close"}


def _report_failure(reason: str) -> int:
    print(f"reason={reason}")
    print("DATA_CHECK=FAIL")
    return 1


def _check_file(csv_path: Path, trace: bool = False) -> int:
    if trace:
        print(f"[trace] stage=entered path={csv_path}", file=sys.stderr)

    if not csv_path.is_file():
        return _report_failure(f"file not found: {csv_path}")

    try:
        prices = pd.read_csv(csv_path)
    except Exception as error:
        return _report_failure(f"could not read CSV: {error}")

    if trace:
        print(f"[trace] stage=loaded rows={len(prices)}", file=sys.stderr)

    missing_columns = sorted(REQUIRED_COLUMNS.difference(prices.columns))
    if missing_columns:
        return _report_failure(
            f"missing required columns: {','.join(missing_columns)}"
        )

    try:
        timestamps = pd.to_datetime(prices["timestamp"], errors="raise")
        symbols = sorted(prices["symbol"].astype(str).unique())
        start = timestamps.min().isoformat()
        end = timestamps.max().isoformat()
    except Exception as error:
        return _report_failure(f"invalid market data: {error}")

    print("execution_mode=fixture")
    print(f"symbols={','.join(symbols)}")
    print(f"rows={len(prices)}")
    print(f"start={start}")
    print(f"end={end}")
    print("DATA_CHECK=PASS")
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Report visible facts from a local market CSV fixture."
    )
    parser.add_argument("csv_path", type=Path, help="path to a local CSV file")
    parser.add_argument(
        "--trace", action="store_true", help="show two diagnostic steps on stderr"
    )
    arguments = parser.parse_args(argv)
    return _check_file(arguments.csv_path, arguments.trace)
