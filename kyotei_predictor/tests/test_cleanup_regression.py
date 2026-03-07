"""
cleanup および主要 CLI の回帰テスト。

削除作業やリファクタの前後に実行し、
cleanup CLI の dry-run と主要 CLI の import/entrypoint が壊れていないことを確認する。
"""

import subprocess
import sys
from pathlib import Path

# プロジェクトルート（テスト実行時は pytest がルートで動く想定）
_TEST_ROOT = Path(__file__).resolve().parent.parent.parent


def _run_cli(module: str, *args, timeout: int = 30) -> subprocess.CompletedProcess:
    """プロジェクトルートを cwd にして CLI を実行する。"""
    return subprocess.run(
        [sys.executable, "-m", module, *args],
        capture_output=True,
        text=True,
        timeout=timeout,
        cwd=str(_TEST_ROOT),
    )


def test_cleanup_cli_dry_run():
    """cleanup CLI が --dry-run でエラーなく終了すること。"""
    r = _run_cli("kyotei_predictor.cli.cleanup", "--dry-run", "--days", "7")
    assert r.returncode == 0, f"cleanup --dry-run failed: {r.stderr or r.stdout}"


def test_cleanup_cli_logs_only_dry_run():
    """cleanup CLI --logs-only --dry-run がエラーなく終了すること。"""
    r = _run_cli("kyotei_predictor.cli.cleanup", "--logs-only", "--days", "30", "--dry-run")
    assert r.returncode == 0, f"cleanup --logs-only --dry-run failed: {r.stderr or r.stdout}"


def test_baseline_train_cli_help():
    """baseline_train CLI が --help で起動できること。"""
    r = _run_cli("kyotei_predictor.cli.baseline_train", "--help", timeout=5)
    assert r.returncode == 0


def test_baseline_predict_cli_help():
    """baseline_predict CLI が --help で起動できること。"""
    r = _run_cli("kyotei_predictor.cli.baseline_predict", "--help", timeout=5)
    assert r.returncode == 0


def test_verify_cli_help():
    """verify CLI が --help で起動できること。"""
    r = _run_cli("kyotei_predictor.cli.verify", "--help", timeout=5)
    assert r.returncode == 0
