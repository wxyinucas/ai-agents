"""Read the teacher's W8 PostgreSQL dataset and export CSV plus public provenance."""

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import sys

import numpy as np


def export_dataset(conn, dataset, output_path):
    """Read two fixed course tables; never retrieve credentials or true parameters."""
    if dataset not in {"calibration", "application"}:
        raise ValueError("dataset must be calibration or application")
    with conn.cursor() as cur:
        cur.execute("SELECT batch_id,generated_at FROM w08_demo.batches WHERE dataset=%s", (dataset,))
        batch = cur.fetchone()
        if batch is None:
            raise ValueError("course dataset is not prepared")
        cur.execute("""
            SELECT sample_id,x,y FROM w08_demo.measurements
            WHERE dataset=%s ORDER BY sample_id
            """, (dataset,))
        rows = cur.fetchall()
    if not rows:
        raise ValueError("course query returned no observations")
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    np.savetxt(output, rows, delimiter=",", header="sample_id,x,y", comments="",
               fmt=["%d", "%.17g", "%.17g"])
    metadata = {
        "batch_id": batch[0], "generated_at": batch[1].isoformat(),
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "source": {"kind": "postgresql", "data_kind": "synthetic_measurements", "dataset": dataset,
                   "table": "w08_demo.measurements", "order_by": "sample_id"},
    }
    output.with_suffix(".meta.json").write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return metadata


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", choices=["calibration", "application"], required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--service", default=os.environ.get("PGSERVICE", "w08_demo"))
    args = parser.parse_args()
    import psycopg

    try:
        with psycopg.connect(service=args.service, connect_timeout=5,
                             options="-c default_transaction_read_only=on") as conn:
            metadata = export_dataset(conn, args.dataset, args.out)
        print(f"source=postgresql dataset={args.dataset} batch={metadata['batch_id']} csv={args.out}")
        return 0
    except psycopg.Error as exc:
        print(f"Database query failed ({type(exc).__name__}); inspect local settings privately.", file=sys.stderr)
        return 1
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
