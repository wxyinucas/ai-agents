"""Copy this file to your project's tests/; run pytest from the project root.

The teacher can instead set W8_PROJECT to the project being checked.
These checks validate fit_line, not the entire experiment or engineering habits.
"""

import importlib.util
import os
from pathlib import Path
import subprocess
import sys

import numpy as np
import pytest


PROJECT = Path(os.environ.get("W8_PROJECT", Path.cwd())).resolve()


@pytest.fixture(scope="module")
def fit_line():
    path = PROJECT / "analyze.py"
    assert path.is_file(), f"Run from your project root, or set W8_PROJECT; missing {path}"
    spec = importlib.util.spec_from_file_location("w8_student_analyze", path)
    module = importlib.util.module_from_spec(spec)
    sys.path.insert(0, str(PROJECT))
    try:
        spec.loader.exec_module(module)
    finally:
        sys.path.pop(0)
    return module.fit_line


@pytest.mark.parametrize("x,y,expected", [
    ([0, 1, 2], [1, 3, 5], (2, 1)),
    ([0, 1, 2], [4, 3.5, 3], (-0.5, 4)),
    ([3, -1, 2, 0], [7, -5, 4, -2], (3, -2)),
    ([0, 1, 2], [3, 3, 3], (0, 3)),
])
def test_known_answers(fit_line, x, y, expected):
    np.testing.assert_allclose(fit_line(x, y), expected, atol=1e-10, rtol=1e-10)


def test_does_not_modify_input(fit_line):
    x, y = np.array([2., 0., 1.]), np.array([5., 1., 3.])
    before_x, before_y = x.copy(), y.copy()
    fit_line(x, y)
    np.testing.assert_array_equal(x, before_x)
    np.testing.assert_array_equal(y, before_y)


def test_import_does_not_launch_analysis(tmp_path):
    source = PROJECT / "analyze.py"
    code = (
        "import importlib.util,sys; "
        f"sys.path.insert(0,{str(PROJECT)!r}); "
        f"spec=importlib.util.spec_from_file_location('w8_import_check',{str(source)!r}); "
        "m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m)"
    )
    result = subprocess.run([sys.executable, "-c", code], cwd=tmp_path,
                            text=True, capture_output=True, timeout=20)
    assert result.returncode == 0, result.stderr
    assert result.stdout == "", "Import should define functions, not launch an analysis."
    assert not list(tmp_path.iterdir()), "Import should not create data or figures."
