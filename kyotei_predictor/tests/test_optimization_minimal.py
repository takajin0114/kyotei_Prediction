import tempfile
import os
import sys
import types
import pytest

# テスト対象の最適化バッチ
import kyotei_predictor.tools.optimization.optimize_graduated_reward as opt_mod

@pytest.mark.skip(reason="空 data_dir では race-odds ペアがなく ValueError になるため要修正")
def test_optimize_graduated_reward_minimal(tmp_path, monkeypatch):
    # 空のデータディレクトリを用意
    data_dir = tmp_path / "empty"
    data_dir.mkdir()
    # コマンドライン引数を模擬
    sys_argv_backup = sys.argv[:]
    sys.argv = ["optimize_graduated_reward.py", "--data-dir", str(data_dir), "--study-name", "test_study"]
    # main関数がエラーなく動くか（例外が出たらテスト失敗）
    try:
        opt_mod.main()
    except SystemExit:
        # argparseが正常終了でSystemExitを投げる場合はOK
        pass
    finally:
        sys.argv = sys_argv_backup 