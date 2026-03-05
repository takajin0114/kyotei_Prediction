#!/usr/bin/env python3
"""
メイン処理（第1優先）: PredictionTool の単体テスト。

- 初期化（data_dir 指定）
- get_race_data_paths（一時ディレクトリに race_data_*.json を置いて取得）
"""
import json
import pytest
from pathlib import Path


def _minimal_race_json():
    """get_race_data_paths で「ファイルがある」ことを確認するための最小 JSON"""
    return {"race_info": {"date": "2024-06-01", "stadium": "KIRYU", "race_number": 1}, "race_entries": []}


class TestPredictionToolMain:
    """PredictionTool のメイン処理テスト"""

    def test_tool_initializes_with_data_dir(self, tmp_path):
        from kyotei_predictor.tools.prediction_tool import PredictionTool
        tool = PredictionTool(log_level=50, data_dir=str(tmp_path))
        assert tool.data_dir == tmp_path
        assert tool.utils is not None
        assert hasattr(tool, "logger")

    def test_get_race_data_paths_returns_list_from_dir(self, tmp_path):
        from kyotei_predictor.tools.prediction_tool import PredictionTool
        (tmp_path / "race_data_2024-06-01_KIRYU_R1.json").write_text(
            json.dumps(_minimal_race_json(), ensure_ascii=False), encoding="utf-8"
        )
        (tmp_path / "odds_data_2024-06-01_KIRYU_R1.json").write_text("{}", encoding="utf-8")
        tool = PredictionTool(log_level=50, data_dir=str(tmp_path))
        paths = tool.get_race_data_paths("2024-06-01", venues=["KIRYU"])
        assert isinstance(paths, list)
        assert len(paths) >= 1
        entry = paths[0]
        assert len(entry) >= 3
        assert "KIRYU" in str(entry)
        assert "2024-06-01" in str(entry)

    def test_get_race_data_paths_empty_dir_returns_empty(self, tmp_path):
        from kyotei_predictor.tools.prediction_tool import PredictionTool
        tool = PredictionTool(log_level=50, data_dir=str(tmp_path))
        paths = tool.get_race_data_paths("2024-06-02", venues=["KIRYU"])
        assert paths == []
