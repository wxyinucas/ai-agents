"""Fetch one local batch through the official CLI, or replay a labelled fixture."""

import argparse
import csv
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import subprocess
import sys

from checks import FIELDS, validate_bars


def batch_path(name):
    """Keep a batch inside this project's data directory."""
    if not name or name in {".", ".."} or "/" in name or "\\" in name:
        raise ValueError("batch must be one directory name")
    return Path("data") / name


def utc_now():
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def cli_failure(completed):
    """Summarize an error without exposing full output or successful data."""
    for stream in (completed.stderr, completed.stdout):
        try:
            error = json.loads(stream).get("error", {})
            if isinstance(error, dict) and error:
                code = error.get("code", "unknown")
                message = error.get("message", "request failed")
                return f"Longbridge request failed: code={code}; message={message}"
        except (ValueError, AttributeError):
            pass
    return "Longbridge request failed; inspect the CLI error privately"


def write_batch(destination, raw_text, rows, metadata):
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.mkdir(exist_ok=False)
    created = []
    try:
        raw_path = destination / "raw.json"
        with raw_path.open("x", encoding="utf-8") as stream:
            created.append(raw_path)
            stream.write(raw_text.rstrip() + "\n")
        csv_path = destination / "bars.csv"
        with csv_path.open("x", newline="", encoding="utf-8") as stream:
            created.append(csv_path)
            writer = csv.DictWriter(stream, fieldnames=FIELDS)
            writer.writeheader()
            writer.writerows(rows)
        metadata_path = destination / "metadata.json"
        with metadata_path.open("x", encoding="utf-8") as stream:
            created.append(metadata_path)
            json.dump(metadata, stream, ensure_ascii=False, indent=2)
            stream.write("\n")
    except Exception:
        # Only remove files created by this operation, never an older batch.
        for path in reversed(created):
            path.unlink()
        try:
            destination.rmdir()
        except OSError:
            pass
        raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--batch", required=True)
    parser.add_argument("--count", type=int, default=100)
    parser.add_argument("--input", type=Path, help="read a synthetic fixture instead of contacting Longbridge")
    args = parser.parse_args()
    try:
        destination = batch_path(args.batch)
        # Check this before subprocess.run: an existing batch must not cause a request.
        if destination.exists() or destination.is_symlink():
            raise ValueError(f"batch already exists: {args.batch}")
        if args.input is not None:
            raw_text = args.input.read_text(encoding="utf-8")
            metadata = {
                "batch_id": args.batch,
                "source": "fixture",
                "input_file": str(args.input.resolve()),
                "processed_at_utc": utc_now(),
            }
        else:
            if not 1 <= args.count <= 1000:
                raise ValueError("count must be between 1 and 1000")
            command = [
                "longbridge", "kline", "AAPL.US", "--period", "day",
                "--count", str(args.count), "--adjust", "none",
                "--session", "intraday", "--format", "json",
            ]
            environment = os.environ.copy()
            environment["LONGBRIDGE_REGION"] = "global"
            completed = subprocess.run(
                command, env=environment, stdin=subprocess.DEVNULL,
                capture_output=True, text=True, timeout=35,
            )
            if completed.returncode != 0:
                raise ValueError(cli_failure(completed))
            raw_text = completed.stdout
            metadata = {
                "batch_id": args.batch,
                "source": "longbridge",
                "request": {
                    "symbol": "AAPL.US", "period": "day", "count": args.count,
                    "adjust": "none", "session": "intraday", "format": "json",
                    "region": "global",
                },
                "fetched_at_utc": utc_now(),
            }
        raw_rows = json.loads(raw_text)
        rows = validate_bars(raw_rows)
        metadata.update({
            "actual_rows": len(rows),
            "first_time": rows[0]["time"],
            "last_time": rows[-1]["time"],
            "sorted_by_time": True,
        })
        write_batch(destination, raw_text, rows, metadata)
        print(f"batch={args.batch} source={metadata['source']} rows={len(rows)}")
        print(f"saved={destination}")
        if args.input is None and len(rows) != args.count:
            print(f"requested={args.count}; actual={len(rows)}; do not invent missing rows")
        return 0
    except (ValueError, OSError, subprocess.SubprocessError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
