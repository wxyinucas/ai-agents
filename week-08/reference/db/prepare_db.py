"""Teacher-only setup: explicitly replace two datasets in the W8 course schema."""

import argparse
from datetime import datetime
import json
from pathlib import Path
import sys

REFERENCE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REFERENCE))
from analyze import load_data


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--service", default="w08_demo_admin")
    args = parser.parse_args()
    import psycopg
    from psycopg.types.json import Jsonb

    # Validate every local file before opening a connection or changing a table.
    batches = []
    for dataset, config_name in (("calibration", "base-001"), ("application", "application")):
        path = REFERENCE.parent / "data" / f"{dataset}.csv"
        values = load_data(path)
        metadata = json.loads(path.with_suffix(".meta.json").read_text(encoding="utf-8"))
        config = json.loads((REFERENCE / "configs" / f"{config_name}.json").read_text(encoding="utf-8"))
        generated_at = datetime.fromisoformat(metadata["generated_at"])
        batches.append((dataset, values, metadata, config, generated_at))
    try:
        with psycopg.connect(service=args.service, connect_timeout=5) as conn:
            conn.execute((REFERENCE / "db" / "schema.sql").read_text(encoding="utf-8"))
            for dataset, values, metadata, config, generated_at in batches:
                conn.execute("""
                    INSERT INTO w08_demo.batches (dataset,batch_id,generated_at,config)
                    VALUES (%s,%s,%s,%s)
                    ON CONFLICT (dataset) DO UPDATE SET
                    batch_id=EXCLUDED.batch_id, generated_at=EXCLUDED.generated_at, config=EXCLUDED.config
                    """, (dataset, metadata["batch_id"], generated_at, Jsonb(config)))
                conn.execute("DELETE FROM w08_demo.measurements WHERE dataset=%s", (dataset,))
                rows = [(dataset, int(i), float(x), float(y))
                        for i, x, y in zip(values["sample_id"], values["x"], values["y"], strict=True)]
                with conn.cursor() as cur:
                    cur.executemany("""
                        INSERT INTO w08_demo.measurements (dataset,sample_id,x,y)
                        VALUES (%s,%s,%s,%s)
                        """, rows)
        print("Prepared W8 calibration/application datasets; other schemas were not changed.")
        return 0
    except psycopg.Error as exc:
        # Do not print a DSN or a full connection error to a classroom projector.
        print(f"Database preparation failed ({type(exc).__name__}); inspect local settings privately.", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
