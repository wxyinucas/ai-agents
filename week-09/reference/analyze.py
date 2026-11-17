"""Analyze an existing local CSV batch without making network requests."""

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
from matplotlib.ticker import PercentFormatter
import pandas as pd

from checks import validate_bars
from fetch_batch import batch_path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--batch", required=True)
    parser.add_argument("--tail", type=int)
    args = parser.parse_args()
    try:
        if args.tail is not None and args.tail <= 0:
            raise ValueError("tail must be positive")
        input_path = batch_path(args.batch) / "bars.csv"
        metadata_path = input_path.with_name("metadata.json")
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        if metadata.get("source") not in {"fixture", "longbridge"}:
            raise ValueError("batch metadata needs a known source")
        frame = pd.read_csv(input_path)
        rows = validate_bars(frame.to_dict(orient="records"))
        frame = pd.DataFrame(rows)
        # Compute before selecting the display window: its first row may have a predecessor.
        frame["change"] = frame["close"].div(frame["close"].shift(1)).sub(1)
        visible = frame if args.tail is None else frame.tail(args.tail)
        output = Path("outputs") / args.batch
        if args.tail is not None:
            output = output / f"tail-{args.tail}"
        output.mkdir(parents=True, exist_ok=True)
        visible[["time", "close", "change"]].to_csv(
            output / "analysis.csv", index=False, float_format="%.15g",
        )
        dates = pd.to_datetime(visible["time"], utc=True)
        figure, axes = plt.subplots(2, 1, sharex=True, figsize=(10, 6), constrained_layout=True)
        axes[0].plot(dates, visible["close"], marker="o", color="#5e33bf")
        axes[0].set_ylabel("Close")
        axes[0].set_title(f"{args.batch} | source={metadata['source']}")
        axes[1].plot(dates, visible["change"], marker="o", color="#291344")
        axes[1].axhline(0, color="#777777", linewidth=0.8)
        axes[1].set_ylabel("Price change")
        axes[1].yaxis.set_major_formatter(PercentFormatter(1))
        axes[1].set_xlabel("Trading date")
        # Daily observations need date labels, rather than repeated half-day ticks.
        tick_dates = dates.iloc[::max(1, (len(dates) + 5) // 6)].tolist()
        if tick_dates[-1] != dates.iloc[-1]:
            tick_dates.append(dates.iloc[-1])
        axes[1].set_xticks(tick_dates)
        axes[1].xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d", tz=timezone.utc))
        for axis in axes:
            axis.grid(alpha=0.2)
        figure.autofmt_xdate()
        figure.savefig(output / "figure.png", dpi=160)
        plt.close(figure)
        result_metadata = {
            "input_file": str(input_path.resolve()),
            "input_batch": args.batch,
            "source": metadata["source"],
            "analyzed_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "parameters": {"tail": args.tail, "change": "close/previous_close-1"},
            "input_rows": len(frame),
            "displayed_rows": len(visible),
            "first_time": visible.iloc[0]["time"],
            "last_time": visible.iloc[-1]["time"],
        }
        (output / "analysis.meta.json").write_text(
            json.dumps(result_metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8",
        )
        print(f"input={input_path} rows={len(frame)} displayed={len(visible)}")
        print(f"saved={output}")
        return 0
    except (ValueError, OSError, KeyError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
