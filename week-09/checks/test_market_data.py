"""Public W9 checks: copy into tests/ and run from your own project root.

Run one group while developing:
    uv run pytest -q tests/test_market_data.py -k validate
    uv run pytest -q tests/test_market_data.py -k fetch
    uv run pytest -q tests/test_market_data.py -k analysis

The teacher can set W9_PROJECT_ROOT to another implementation. Tests use only
validate_bars and the two advertised CLIs. All input is synthetic; CLI runs use
temporary source copies and a fake longbridge, never the real service.
"""

import copy
import csv
from datetime import datetime, timezone
import importlib.util
import json
import math
import numbers
import os
from pathlib import Path
import shutil
import subprocess
import sys

import pytest


PROJECT = Path(os.environ.get("W9_PROJECT_ROOT", Path.cwd())).resolve()
FIELDS = ["time", "open", "high", "low", "close", "volume", "turnover"]


def known_rows():
    """Independent input, not an output copied from the implementation."""
    return [
        {"time": "2025-01-02T05:00:00Z", "open": "100", "high": "102",
         "low": "99", "close": "100", "volume": 1000, "turnover": "100000"},
        {"time": "2025-01-03T05:00:00Z", "open": "100", "high": "112",
         "low": "99", "close": "110", "volume": 1200, "turnover": "130000"},
        {"time": "2025-01-06T05:00:00Z", "open": "110", "high": "111",
         "low": "98", "close": "99", "volume": 1500, "turnover": "150000"},
    ]


def instant(value):
    if isinstance(value, datetime):
        result = value
    else:
        result = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    assert result.tzinfo is not None and result.utcoffset() is not None
    return result.astimezone(timezone.utc)


@pytest.fixture(scope="module")
def validate():
    source = PROJECT / "checks.py"
    assert source.is_file(), (
        f"Missing {source}; run from your project root or set W9_PROJECT_ROOT."
    )
    spec = importlib.util.spec_from_file_location("w9_candidate_checks", source)
    module = importlib.util.module_from_spec(spec)
    sys.path.insert(0, str(PROJECT))
    sys.modules[spec.name] = module
    try:
        spec.loader.exec_module(module)
    finally:
        sys.path.pop(0)
    return module.validate_bars


def test_validate_sorts_and_converts_without_changing_input(validate):
    original = known_rows()
    source = [original[2], original[0], original[1]]
    before = copy.deepcopy(source)

    result = validate(source)

    assert source == before, "Validation must preserve the original input."
    assert isinstance(result, list) and result is not source
    assert [instant(row["time"]) for row in result] == [
        instant(row["time"]) for row in original
    ]
    assert [float(row["close"]) for row in result] == [100.0, 110.0, 99.0]
    for row in result:
        for field in FIELDS[1:]:
            assert isinstance(row[field], numbers.Number), (
                f"{field} should be converted from text to a number."
            )
            assert math.isfinite(float(row[field]))


def test_validate_uses_the_input_values_not_a_fixed_answer(validate):
    source = known_rows()
    for row, value in zip(source, [10, 12, 9]):
        row.update(open=str(value), high=str(value + 1),
                   low=str(value - 1), close=str(value))
    assert [float(row["close"]) for row in validate(source)] == [10, 12, 9]


def invalid_input(case):
    rows = known_rows()
    if case == "missing-close":
        del rows[1]["close"]
    elif case == "duplicate-time":
        rows[1]["time"] = rows[0]["time"]
    elif case == "same-instant-different-offset":
        rows[1]["time"] = "2025-01-02T13:00:00+08:00"
    elif case == "nan":
        rows[1]["close"] = "NaN"
    elif case == "infinity":
        rows[1]["turnover"] = "Infinity"
    elif case == "invalid-price-range":
        rows[1]["high"] = "105"  # close is 110.
    elif case == "nonpositive-price":
        rows[1]["low"] = "0"
    elif case == "negative-volume":
        rows[1]["volume"] = -1
    elif case == "negative-turnover":
        rows[1]["turnover"] = -1
    elif case == "naive-time":
        rows[1]["time"] = "2025-01-03T05:00:00"
    elif case == "empty":
        return []
    elif case == "error-object":
        return {"error": {"code": 301607, "message": "synthetic quota error"}}
    else:
        raise AssertionError(case)
    return rows


@pytest.mark.parametrize("case", [
    "missing-close", "duplicate-time", "same-instant-different-offset",
    "nan", "infinity", "invalid-price-range", "nonpositive-price",
    "negative-volume", "negative-turnover",
    "naive-time", "empty", "error-object",
])
def test_validate_rejects_an_unusable_input(validate, case):
    source = invalid_input(case)
    before = copy.deepcopy(source)
    with pytest.raises(ValueError) as error:
        validate(source)
    assert str(error.value).strip(), "The error should explain the reason."
    assert source == before


def copy_python_sources(source, destination):
    """Isolate source code, without copying data, environments or secrets."""
    excluded = {"tests", "checks", "fixtures", "data", "outputs",
                "__pycache__", "node_modules"}
    for item in source.iterdir():
        if item.name.startswith(".") or item.name in excluded:
            continue
        if item.is_dir():
            target = destination / item.name
            target.mkdir(exist_ok=True)
            copy_python_sources(item, target)
        elif item.suffix == ".py":
            shutil.copy2(item, destination / item.name)


@pytest.fixture
def sandbox(tmp_path):
    root = tmp_path / "project"
    root.mkdir()
    copy_python_sources(PROJECT, root)

    # Every CLI test must remain offline, even when a candidate is broken.
    bin_dir = tmp_path / "fake-bin"
    bin_dir.mkdir()
    marker = tmp_path / "unexpected-longbridge-call"
    fake_cli = bin_dir / "longbridge"
    fake_cli.write_text(
        "#!/bin/sh\n"
        ': > "$W9_NETWORK_MARKER"\n'
        "exit 91\n",
        encoding="utf-8",
    )
    fake_cli.chmod(0o755)
    env = os.environ.copy()
    env["PATH"] = str(bin_dir) + os.pathsep + env.get("PATH", "")
    env["W9_NETWORK_MARKER"] = str(marker)
    env["MPLBACKEND"] = "Agg"
    env["MPLCONFIGDIR"] = str(tmp_path / "matplotlib-cache")
    env["PYTHONPATH"] = str(root)
    return root, env, marker


def cli(sandbox, name, *args):
    root, env, marker = sandbox
    assert (root / name).is_file(), f"Missing {PROJECT / name}"
    result = subprocess.run(
        [sys.executable, str(root / name), *map(str, args)],
        cwd=root, env=env, text=True, capture_output=True, timeout=120,
    )
    assert not marker.exists(), "This check must not call Longbridge."
    return result


def write_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False), encoding="utf-8")
    return path


def read_csv(path):
    with path.open(newline="", encoding="utf-8-sig") as stream:
        reader = csv.DictReader(stream)
        return reader.fieldnames, list(reader)


def snapshot(directory):
    return {
        str(path.relative_to(directory)): path.read_bytes()
        for path in directory.rglob("*") if path.is_file()
    }


def test_fetch_offline_keeps_the_original_and_records_its_source(sandbox):
    root, _, _ = sandbox
    source = known_rows()
    source = [source[2], source[0], source[1]]
    input_file = write_json(root / "synthetic.json", source)
    before = input_file.read_bytes()

    result = cli(sandbox, "fetch_batch.py", "--batch", "fixture-001",
                 "--input", input_file)
    assert result.returncode == 0, result.stderr or result.stdout
    folder = root / "data" / "fixture-001"
    assert json.loads((folder / "raw.json").read_text()) == source
    fields, bars = read_csv(folder / "bars.csv")
    assert fields == FIELDS
    assert len(bars) == 3
    assert [float(row["close"]) for row in bars] == [100, 110, 99]
    assert [instant(row["time"]) for row in bars] == sorted(
        instant(row["time"]) for row in source
    )
    metadata = json.loads((folder / "metadata.json").read_text())
    assert metadata["source"] == "fixture"
    assert metadata["actual_rows"] == 3
    assert metadata.get("fetched_at_utc") in (None, "")
    assert metadata.get("request") in (None, {}, "")
    assert input_file.name in json.dumps(metadata, ensure_ascii=False)
    assert input_file.read_bytes() == before


@pytest.mark.parametrize("case", [
    "missing-close", "duplicate-time", "nan", "error-object",
])
def test_fetch_bad_input_cannot_become_a_successful_batch(sandbox, case):
    root, _, _ = sandbox
    preserved = root / "data" / "already-good"
    preserved.mkdir(parents=True)
    (preserved / "sentinel.txt").write_text("keep me", encoding="utf-8")
    before = snapshot(preserved)
    input_file = write_json(root / "bad.json", invalid_input(case))

    result = cli(sandbox, "fetch_batch.py", "--batch", "bad-001",
                 "--input", input_file)

    assert result.returncode != 0
    assert not (root / "data" / "bad-001" / "bars.csv").exists()
    assert snapshot(preserved) == before


@pytest.mark.parametrize("mode", ["offline", "online"])
def test_fetch_existing_batch_is_rejected_before_another_request(sandbox, mode):
    root, _, _ = sandbox
    folder = root / "data" / "fixture-001"
    folder.mkdir(parents=True)
    for filename in ("raw.json", "bars.csv", "metadata.json"):
        (folder / filename).write_text("original " + filename, encoding="utf-8")
    before = snapshot(folder)
    if mode == "offline":
        input_file = write_json(root / "replacement.json", known_rows())
        args = ["--input", input_file]
    else:
        args = ["--count", "100"]

    result = cli(sandbox, "fetch_batch.py", "--batch", "fixture-001", *args)

    assert result.returncode != 0
    assert snapshot(folder) == before


def prepare_analysis_input(root):
    folder = root / "data" / "fixture-001"
    folder.mkdir(parents=True)
    rows = known_rows()
    write_json(folder / "raw.json", rows)
    with (folder / "bars.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    write_json(folder / "metadata.json", {
        "batch_id": "fixture-001",
        "source": "fixture",
        "actual_rows": 3,
        "input_file": "synthetic.json",
        "processed_at_utc": "2025-01-07T00:00:00Z",
    })
    return folder


def assert_changes(path, expected_close, expected_changes):
    fields, rows = read_csv(path)
    assert fields == ["time", "close", "change"]
    assert [float(row["close"]) for row in rows] == expected_close
    assert [instant(row["time"]) for row in rows] == [
        instant(row["time"]) for row in known_rows()[-len(rows):]
    ]
    for row, expected in zip(rows, expected_changes):
        value = row["change"].strip()
        if expected is None:
            assert value.lower() in ("", "nan", "null", "none"), (
                "The first observation has no previous day; do not fill it with 0."
            )
        else:
            assert float(value) == pytest.approx(expected, abs=1e-12)


def assert_analysis_artifacts(folder):
    assert (folder / "figure.png").read_bytes().startswith(b"\x89PNG\r\n\x1a\n")
    metadata = json.loads((folder / "analysis.meta.json").read_text())
    assert "bars.csv" in json.dumps(metadata), (
        "The analysis metadata should identify the actual input CSV."
    )


def test_analysis_computes_before_tail_and_preserves_inputs(sandbox):
    root, _, _ = sandbox
    data_dir = prepare_analysis_input(root)
    before_data = snapshot(data_dir)

    full = cli(sandbox, "analyze.py", "--batch", "fixture-001")
    assert full.returncode == 0, full.stderr or full.stdout
    output = root / "outputs" / "fixture-001"
    assert_changes(output / "analysis.csv", [100, 110, 99], [None, 0.1, -0.1])
    assert_analysis_artifacts(output)
    before_full = {name: (output / name).read_bytes() for name in (
        "analysis.csv", "figure.png", "analysis.meta.json"
    )}

    tail = cli(sandbox, "analyze.py", "--batch", "fixture-001", "--tail", "2")
    assert tail.returncode == 0, tail.stderr or tail.stdout
    tail_dir = output / "tail-2"
    assert_changes(tail_dir / "analysis.csv", [110, 99], [0.1, -0.1])
    assert_analysis_artifacts(tail_dir)
    assert snapshot(data_dir) == before_data
    assert all((output / name).read_bytes() == value
               for name, value in before_full.items())
