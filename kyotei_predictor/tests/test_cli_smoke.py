"""
CLI smoke tests: --help and argument parsing.

No heavy runs; only that entrypoints parse args and help works.
"""

import subprocess
import sys


def test_baseline_predict_help():
    """baseline_predict --help exits 0 and prints usage."""
    r = subprocess.run(
        [sys.executable, "-m", "kyotei_predictor.cli.baseline_predict", "--help"],
        capture_output=True,
        text=True,
        timeout=10,
        cwd=None,
    )
    assert r.returncode == 0
    assert "predict-date" in r.stdout or "予測" in r.stdout
    assert "data-dir" in r.stdout or "model-path" in r.stdout


def test_prediction_tool_help():
    """prediction_tool --help exits 0."""
    r = subprocess.run(
        [sys.executable, "-m", "kyotei_predictor.tools.prediction_tool", "--help"],
        capture_output=True,
        text=True,
        timeout=10,
    )
    assert r.returncode == 0
    assert "predict" in r.stdout.lower() or "data" in r.stdout.lower()
