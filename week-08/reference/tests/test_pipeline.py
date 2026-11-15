"""Maintainer checks for concrete batch and provenance promises; no database access."""

from datetime import datetime, timezone
import json
from pathlib import Path
import sys

import numpy as np
import pytest

WEEK = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(WEEK))
from reference.analyze import analyze_file, load_data
from reference.fetch_data import export_dataset
from reference.simulate import generate_data, write_batch


@pytest.fixture
def config():
    return json.loads((WEEK / "reference/configs/base-001.json").read_text())


def test_seed_and_design_make_different_batches_without_modifying_config(config):
    before = config.copy()
    a, b = generate_data(config), generate_data(config)
    np.testing.assert_array_equal(a["y"], b["y"])
    assert a["y"] is not b["y"]
    other = generate_data({**config, "seed": 43})
    assert not np.array_equal(a["y"], other["y"])
    assert config == before


def test_new_batches_keep_old_csv_and_metadata_snapshot(tmp_path, config):
    old = tmp_path / "base-001.csv"
    write_batch(config, old)
    csv_before = old.read_bytes()
    meta_before = old.with_suffix(".meta.json").read_bytes()
    config["noise_std"] = 2
    config["batch_id"] = "noise-002"
    write_batch(config, tmp_path / "noise-002.csv")
    assert old.read_bytes() == csv_before
    assert old.with_suffix(".meta.json").read_bytes() == meta_before
    assert json.loads(meta_before)["config"]["noise_std"] == 1


def test_fit_uses_observations_instead_of_metadata_truth(tmp_path, config):
    source = tmp_path / "data.csv"
    write_batch({**config, "slope": 3, "intercept": -2, "noise_std": 0}, source)
    meta_path = source.with_suffix(".meta.json")
    metadata = json.loads(meta_path.read_text())
    metadata["config"].update(slope=999, intercept=999)
    meta_path.write_text(json.dumps(metadata))
    result = analyze_file(source, tmp_path / "result")
    np.testing.assert_allclose([result["slope"], result["intercept"]], [3, -2], atol=1e-12)
    assert Path(result["fit_plot"]).exists()
    assert Path(result["residual_plot"]).exists()


def test_application_fixture_has_no_truth_and_is_not_a_database_response(tmp_path):
    source = WEEK / "data/application.csv"
    metadata = json.loads(source.with_suffix(".meta.json").read_text())
    assert metadata["source"]["kind"] == "synthetic_fixture"
    assert "config" not in metadata
    assert "exported_at" not in metadata
    result = analyze_file(source, tmp_path / "application")
    assert result["n"] == 80
    assert result["noise_plot"] is None
    assert "noise_stats" not in result


class FakeCursor:
    def __init__(self):
        self.calls = []

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass

    def execute(self, sql, params):
        self.calls.append((sql, params))

    def fetchone(self):
        return ("application-001", datetime(2026, 11, 15, tzinfo=timezone.utc))

    def fetchall(self):
        return [(1, 0., 4.), (2, 1., 3.5)]


def test_database_export_contains_only_public_provenance(tmp_path):
    cursor = FakeCursor()

    class Connection:
        def cursor(self):
            return cursor

    output = tmp_path / "application.csv"
    metadata = export_dataset(Connection(), "application", output)
    assert metadata["source"]["kind"] == "postgresql"
    assert metadata["batch_id"] == "application-001"
    assert "generated_at" in metadata and "exported_at" in metadata
    assert "config" not in metadata
    assert all(sql.lstrip().startswith("SELECT") for sql, _ in cursor.calls)
    assert all(params == ("application",) for _, params in cursor.calls)
    assert all("config" not in sql for sql, _ in cursor.calls)
    data = load_data(output)
    np.testing.assert_allclose(data["y"], [4., 3.5])
