#!/usr/bin/env python3
"""
verify_predictions の実行時ログ（evaluation_mode / source）を保証するテスト。

比較条件の追跡のため、stdout に evaluation_mode= と source= が含まれることを assert する。
将来の変更でこのログが消えないようにする。
"""
import io
import json
import sys
from pathlib import Path

import pytest

# テスト用にプロジェクトルートをパスに追加
TESTS_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = TESTS_DIR.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def test_stdout_contains_evaluation_mode_and_source(tmp_path):
    """
    verify_predictions 実行時に stdout に evaluation_mode= と source= が含まれること。
    """
    pred = {
        "prediction_date": "2024-01-01",
        "predictions": [
            {
                "venue": "KIRYU",
                "race_number": 1,
                "all_combinations": [{"combination": "1-2-3", "probability": 0.1}],
            }
        ],
    }
    pred_path = tmp_path / "pred.json"
    pred_path.write_text(json.dumps(pred), encoding="utf-8")
    race_data = {
        "race_records": [
            {"pit_number": 1, "arrival": 1},
            {"pit_number": 2, "arrival": 2},
            {"pit_number": 3, "arrival": 3},
            {"pit_number": 4, "arrival": 4},
        ]
    }
    (tmp_path / "race_data_2024-01-01_KIRYU_R1.json").write_text(
        json.dumps(race_data), encoding="utf-8"
    )

    # main() を呼ぶために argv を差し替え、stdout をキャプチャ
    from kyotei_predictor.tools import verify_predictions as vp

    old_argv = sys.argv
    old_stdout = sys.stdout
    try:
        sys.argv = [
            "verify_predictions",
            "--prediction",
            str(pred_path),
            "--data-dir",
            str(tmp_path),
        ]
        buf = io.StringIO()
        sys.stdout = buf
        exit_code = vp.main()
        sys.stdout = old_stdout
        stdout_text = buf.getvalue()
    finally:
        sys.argv = old_argv
        sys.stdout = old_stdout

    assert exit_code == 0, f"verify_predictions failed: {stdout_text}"
    assert "evaluation_mode=" in stdout_text, (
        "stdout に evaluation_mode= が含まれること（比較条件の追跡用）"
    )
    assert "source=" in stdout_text, (
        "stdout に source= が含まれること（config/cli 由来の追跡用）"
    )


def test_stdout_source_cli_when_evaluation_mode_passed(tmp_path):
    """--evaluation-mode を渡した場合は source=cli が出力されること。"""
    pred_path = tmp_path / "pred.json"
    pred_path.write_text(
        json.dumps({"prediction_date": "2024-01-01", "predictions": []}), encoding="utf-8"
    )

    from kyotei_predictor.tools import verify_predictions as vp

    old_argv = sys.argv
    old_stdout = sys.stdout
    try:
        sys.argv = [
            "verify_predictions",
            "--prediction",
            str(pred_path),
            "--data-dir",
            str(tmp_path),
            "--evaluation-mode",
            "selected_bets",
        ]
        buf = io.StringIO()
        sys.stdout = buf
        vp.main()
        stdout_text = buf.getvalue()
    finally:
        sys.argv = old_argv
        sys.stdout = old_stdout

    assert "evaluation_mode=selected_bets" in stdout_text
    assert "source=cli" in stdout_text
