import os
import json
import tempfile
from kyotei_predictor.tools.batch import list_fetched_data_summary

def test_collect_summary_with_subdirs(tmp_path):
    # サブディレクトリ作成
    subdir = tmp_path / "2025-07"
    subdir.mkdir()
    # テスト用ファイル作成
    fname = "race_data_2025-07-20_TESTVENUE_R1.json"
    fpath = subdir / fname
    with open(fpath, 'w', encoding='utf-8') as f:
        json.dump({"test": True}, f)
    # 集計実行（raw_dir を渡す）
    summary = list_fetched_data_summary.collect_summary(
        list_fetched_data_summary.race_pattern, str(tmp_path)
    )
    # サマリに正しく反映されているか
    assert "TESTVENUE" in summary
    assert "2025-07-20" in summary["TESTVENUE"] 