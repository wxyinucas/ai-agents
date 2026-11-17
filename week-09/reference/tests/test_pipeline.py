"""Offline verification of the teacher reference, with no real broker calls."""

import csv
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

REFERENCE = Path(__file__).resolve().parents[1]
FIXTURES = REFERENCE.parent / "fixtures"
spec = importlib.util.spec_from_file_location("w9_reference_checks", REFERENCE / "checks.py")
checks = importlib.util.module_from_spec(spec)
spec.loader.exec_module(checks)


def invoke(script, cwd, *args, extra_env=None):
    environment = os.environ.copy()
    environment["MPLCONFIGDIR"] = str(cwd / ".mplconfig")
    if extra_env:
        environment.update(extra_env)
    return subprocess.run(
        [sys.executable, str(REFERENCE / script), *map(str, args)],
        cwd=cwd, env=environment, stdin=subprocess.DEVNULL,
        capture_output=True, text=True, timeout=120,
    )


def fake_cli(tmp_path, response, returncode=0):
    """Install a fake executable only in this test's temporary PATH."""
    binary = tmp_path / "bin"
    binary.mkdir()
    marker = tmp_path / "cli-called.json"
    executable = binary / "longbridge"
    executable.write_text(
        "#!" + sys.executable + "\n"
        "import json, os, pathlib, sys\n"
        f"pathlib.Path({str(marker)!r}).write_text(json.dumps("
        "{'args':sys.argv[1:], 'region':os.environ.get('LONGBRIDGE_REGION')}))\n"
        f"print({json.dumps(response)!r}, file=sys.{'stdout' if returncode == 0 else 'stderr'})\n"
        f"raise SystemExit({returncode})\n",
        encoding="utf-8",
    )
    executable.chmod(0o755)
    return {"PATH": str(binary) + os.pathsep + os.environ.get("PATH", "")}, marker


def read_csv(path):
    with path.open(newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


def test_online_wrapper_records_actual_result_and_exact_request(tmp_path):
    # A short fake reply deliberately differs from the requested count.
    data = json.loads((FIXTURES / "good.json").read_text())
    env, marker = fake_cli(tmp_path, data)
    result = invoke("fetch_batch.py", tmp_path, "--batch", "fake-online", "--count", "20", extra_env=env)
    assert result.returncode == 0, result.stderr
    called = json.loads(marker.read_text())
    assert called["args"] == [
        "kline", "AAPL.US", "--period", "day", "--count", "20",
        "--adjust", "none", "--session", "intraday", "--format", "json",
    ]
    assert called["region"] == "global"
    batch = tmp_path / "data" / "fake-online"
    metadata = json.loads((batch / "metadata.json").read_text())
    assert metadata["source"] == "longbridge"
    assert metadata["request"]["count"] == 20
    assert metadata["actual_rows"] == 3
    assert len(read_csv(batch / "bars.csv")) == 3
    assert "fetched_at_utc" in metadata
    assert json.loads((batch / "raw.json").read_text()) == data


@pytest.mark.parametrize("returncode", [0, 1])
def test_business_error_never_becomes_a_success_batch(tmp_path, returncode):
    env, _ = fake_cli(tmp_path, {"error": {"code": 301607, "message": "example quota error"}}, returncode)
    result = invoke("fetch_batch.py", tmp_path, "--batch", "failed", extra_env=env)
    assert result.returncode != 0
    assert not (tmp_path / "data" / "failed").exists()


def test_analysis_reads_csv_not_raw_json_and_preserves_input(tmp_path):
    result = invoke("fetch_batch.py", tmp_path, "--batch", "fixture-demo",
                    "--input", FIXTURES / "good.json")
    assert result.returncode == 0, result.stderr
    batch = tmp_path / "data" / "fixture-demo"
    # Deliberately change the unused raw artifact in the temporary experiment.
    (batch / "raw.json").write_text('{"error":"not the analysis input"}\n', encoding="utf-8")
    before = {p.name: p.read_bytes() for p in batch.iterdir()}
    result = invoke("analyze.py", tmp_path, "--batch", "fixture-demo", "--tail", "2")
    assert result.returncode == 0, result.stderr
    rows = read_csv(tmp_path / "outputs" / "fixture-demo" / "tail-2" / "analysis.csv")
    assert [float(r["change"]) for r in rows] == pytest.approx([0.1, -0.1])
    assert before == {p.name: p.read_bytes() for p in batch.iterdir()}
    meta = json.loads((tmp_path / "outputs" / "fixture-demo" / "tail-2" / "analysis.meta.json").read_text())
    assert Path(meta["input_file"]) == batch / "bars.csv"
    assert meta["source"] == "fixture"


def test_equivalent_instants_are_duplicates():
    rows = json.loads((FIXTURES / "good.json").read_text())
    rows[1]["time"] = "2025-01-02T00:00:00-05:00"
    with pytest.raises(ValueError, match="duplicate"):
        checks.validate_bars(rows)
