"""Generate one batch and keep its actual experimental design beside the CSV."""

import argparse
from copy import deepcopy
import json
from datetime import datetime, timezone
from pathlib import Path
import platform

import numpy as np


def validate_config(config):
    required = {"batch_id", "n", "seed", "slope", "intercept", "noise_std", "x_min", "x_max"}
    if not required <= config.keys():
        raise ValueError(f"missing configuration fields: {sorted(required - config.keys())}")
    if not isinstance(config["batch_id"], str) or not config["batch_id"].strip():
        raise ValueError("batch_id must be a nonempty label")
    if isinstance(config["n"], bool) or not isinstance(config["n"], int) or config["n"] < 2:
        raise ValueError("n must be an integer >= 2")
    if isinstance(config["seed"], bool) or not isinstance(config["seed"], int) or config["seed"] < 0:
        raise ValueError("seed must be a nonnegative integer")
    for field in ("slope", "intercept", "noise_std", "x_min", "x_max"):
        if isinstance(config[field], bool) or not np.isfinite(float(config[field])):
            raise ValueError(f"{field} must be finite")
    if config["noise_std"] < 0 or config["x_min"] >= config["x_max"]:
        raise ValueError("noise_std must be nonnegative and x_min < x_max")


def generate_data(config):
    """Return independent arrays; one RNG is created for this entire batch."""
    validate_config(config)
    x = np.linspace(config["x_min"], config["x_max"], config["n"])
    rng = np.random.default_rng(config["seed"])
    noise = rng.normal(0.0, config["noise_std"], config["n"])
    y = config["intercept"] + config["slope"] * x + noise
    return {"sample_id": np.arange(1, config["n"] + 1), "x": x, "y": y}


def write_batch(config, output_path):
    """Write CSV and a config snapshot. A changed config cannot change old metadata."""
    data = generate_data(config)
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    np.savetxt(output, np.column_stack(list(data.values())), delimiter=",",
               header="sample_id,x,y", comments="", fmt=["%d", "%.17g", "%.17g"])
    metadata = {
        "batch_id": config["batch_id"],
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "config": deepcopy(config),
        "python_version": platform.python_version(),
        "numpy_version": np.__version__,
        "source": {"kind": "simulation", "description": "Synthetic measurements generated locally."},
    }
    output.with_suffix(".meta.json").write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return metadata


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    config = json.loads(args.config.read_text(encoding="utf-8"))
    metadata = write_batch(config, args.out)
    print(f"batch={metadata['batch_id']} rows={config['n']} csv={args.out}")


if __name__ == "__main__":
    main()
