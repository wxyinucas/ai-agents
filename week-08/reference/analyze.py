"""Inspect a CSV, estimate a line from its values, and save named results."""

import argparse
import csv
import json
from pathlib import Path

import numpy as np


def load_data(path):
    with Path(path).open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        if not {"sample_id", "x", "y"} <= set(reader.fieldnames or []):
            raise ValueError("CSV must contain sample_id,x,y")
        rows = list(reader)
    if not rows:
        raise ValueError("CSV contains no observations")
    data = {
        "sample_id": np.array([int(row["sample_id"]) for row in rows]),
        "x": np.array([float(row["x"]) for row in rows]),
        "y": np.array([float(row["y"]) for row in rows]),
    }
    if not np.isfinite(data["x"]).all() or not np.isfinite(data["y"]).all():
        raise ValueError("this exercise requires finite x and y")
    if len(np.unique(data["sample_id"])) != len(rows):
        raise ValueError("sample_id must be unique within a batch")
    return data


def fit_line(x, y):
    """Ordinary least squares with an intercept; return (slope, intercept)."""
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    if x.ndim != 1 or y.ndim != 1 or x.size != y.size or x.size < 2:
        raise ValueError("x and y must be equal-length 1-D arrays with >= 2 observations")
    if not np.isfinite(x).all() or not np.isfinite(y).all():
        raise ValueError("x and y must be finite")
    centered_x = x - x.mean()
    denominator = np.dot(centered_x, centered_x)
    if denominator == 0:
        raise ValueError("x must not be constant")
    slope = float(np.dot(centered_x, y - y.mean()) / denominator)
    intercept = float(y.mean() - slope * x.mean())
    return slope, intercept


def _describe(values):
    return {
        "min": float(values.min()), "max": float(values.max()),
        "mean": float(values.mean()),
        "sample_std": float(values.std(ddof=1)) if len(values) > 1 else None,
    }


def analyze_file(input_path, prefix):
    """Analyze values, never substitute simulation parameters for fitted coefficients."""
    import matplotlib.pyplot as plt

    input_path, prefix = Path(input_path), Path(prefix)
    data = load_data(input_path)
    x, y = data["x"], data["y"]
    metadata_path = input_path.with_suffix(".meta.json")
    metadata = json.loads(metadata_path.read_text(encoding="utf-8")) if metadata_path.exists() else {}
    slope, intercept = fit_line(x, y)
    y_hat = intercept + slope * x
    residual = y - y_hat
    prefix.parent.mkdir(parents=True, exist_ok=True)
    fit_csv = Path(f"{prefix}-fit.csv")
    fit_plot, residual_plot = Path(f"{prefix}.png"), Path(f"{prefix}-residuals.png")
    summary = {
        "n": len(x), "slope": slope, "intercept": intercept,
        "input_path": str(input_path), "batch_id": metadata.get("batch_id", "unknown"),
        "source_kind": metadata.get("source", {}).get("kind", "unknown"),
        "fit_csv": str(fit_csv), "fit_plot": str(fit_plot),
        "residual_plot": str(residual_plot), "noise_plot": None,
        "data_stats": {"fields": list(data), "rows": len(x), "unique_ids": len(x),
                       "missing_count": 0, "x": _describe(x), "y": _describe(y)},
        "residual_mean": float(residual.mean()),
    }
    with fit_csv.open("w", encoding="utf-8", newline="") as handle:
        fields = ["n", "slope", "intercept", "input_path", "batch_id", "source_kind"]
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerow({key: summary[key] for key in fields})
    order = np.argsort(x)
    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.scatter(x, y, alpha=0.7, label="observations")
    ax.plot(x[order], y_hat[order], color="#5e33bf", label="OLS fit")
    ax.set(xlabel="x", ylabel="y", title=f"Batch: {summary['batch_id']}")
    ax.legend()
    fig.tight_layout()
    fig.savefig(fit_plot, dpi=160)
    plt.close(fig)
    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.scatter(x, residual, alpha=0.7)
    ax.axhline(0, color="#5e33bf")
    ax.set(xlabel="x", ylabel="residual", title="Residuals use fitted coefficients")
    fig.tight_layout()
    fig.savefig(residual_plot, dpi=160)
    plt.close(fig)
    config = metadata.get("config")
    if config is not None and {"slope", "intercept"} <= config.keys():
        noise = y - (config["intercept"] + config["slope"] * x)
        noise_plot = Path(f"{prefix}-noise.png")
        summary["noise_stats"] = _describe(noise)
        summary["noise_plot"] = str(noise_plot)
        fig, ax = plt.subplots(figsize=(8, 4.5))
        ax.hist(noise, bins="auto", color="#5e33bf", alpha=0.8)
        ax.set(xlabel="noise", ylabel="count", title="Noise uses known generation parameters")
        fig.tight_layout()
        fig.savefig(noise_plot, dpi=160)
        plt.close(fig)
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--prefix", type=Path, required=True)
    args = parser.parse_args()
    analyze_file(args.input, args.prefix)


if __name__ == "__main__":
    main()
