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
        tool = PredictionTool(log_level=50, data_dir=str(tmp_path), data_source="file")
        assert tool.data_dir == tmp_path
        assert tool.utils is not None
        assert hasattr(tool, "logger")

    def test_get_race_data_paths_returns_list_from_dir(self, tmp_path):
        from kyotei_predictor.tools.prediction_tool import PredictionTool
        (tmp_path / "race_data_2024-06-01_KIRYU_R1.json").write_text(
            json.dumps(_minimal_race_json(), ensure_ascii=False), encoding="utf-8"
        )
        (tmp_path / "odds_data_2024-06-01_KIRYU_R1.json").write_text("{}", encoding="utf-8")
        tool = PredictionTool(log_level=50, data_dir=str(tmp_path), data_source="file")
        paths = tool.get_race_data_paths("2024-06-01", venues=["KIRYU"])
        assert isinstance(paths, list)
        assert len(paths) >= 1
        entry = paths[0]
        assert len(entry) >= 3
        assert "KIRYU" in str(entry)
        assert "2024-06-01" in str(entry)

    def test_get_race_data_paths_empty_dir_returns_empty(self, tmp_path):
        from kyotei_predictor.tools.prediction_tool import PredictionTool
        tool = PredictionTool(log_level=50, data_dir=str(tmp_path), data_source="file")
        paths = tool.get_race_data_paths("2024-06-02", venues=["KIRYU"])
        assert paths == []

    def test_run_complete_prediction_prediction_only_returns_structure(self, tmp_path):
        """run_complete_prediction(prediction_only=True) がモックで実行パスを通し結果構造を返す"""
        from unittest.mock import patch
        from kyotei_predictor.tools.prediction_tool import PredictionTool

        (tmp_path / "race_data_2024-06-01_KIRYU_R1.json").write_text(
            json.dumps(_minimal_race_json(), ensure_ascii=False), encoding="utf-8"
        )
        (tmp_path / "odds_data_2024-06-01_KIRYU_R1.json").write_text("{}", encoding="utf-8")

        fake_combos = [
            {"combination": f"{a}-{b}-{c}", "probability": 0.01, "expected_value": 0.0, "rank": i + 1}
            for i, (a, b, c) in enumerate(
                [(1, 2, 3), (1, 2, 4), (1, 2, 5), (1, 2, 6), (1, 3, 2)] + [(1, 3, 4)] * 115
            )
        ]
        assert len(fake_combos) >= 120
        fake_combos = fake_combos[:120]

        tool = PredictionTool(log_level=50, data_dir=str(tmp_path), data_source="file")
        with patch.object(tool, "load_model", return_value=True), patch.object(
            tool, "predict_trifecta_probabilities", return_value=fake_combos
        ):
            result = tool.run_complete_prediction(
                target_date="2024-06-01",
                venues=["KIRYU"],
                fetch_data=False,
                prediction_only=True,
            )
        assert result is not None
        assert "predictions" in result
        assert "execution_summary" in result
        assert result["execution_summary"]["prediction_only"] is True
        assert len(result["predictions"]) >= 1
        pred = result["predictions"][0]
        assert "venue" in pred and "all_combinations" in pred
        assert len(pred["all_combinations"]) == 120

    def test_result_payload_contract_keys(self, tmp_path):
        """predict_races / run_complete_prediction 返却の主要キーが壊れないことを担保する契約テスト"""
        from unittest.mock import patch
        from kyotei_predictor.tools.prediction_tool import PredictionTool

        (tmp_path / "race_data_2024-06-01_KIRYU_R1.json").write_text(
            json.dumps(_minimal_race_json(), ensure_ascii=False), encoding="utf-8"
        )
        (tmp_path / "odds_data_2024-06-01_KIRYU_R1.json").write_text("{}", encoding="utf-8")
        fake_combos = [{"combination": f"{i}-{j}-{k}", "probability": 0.01, "expected_value": 0.0, "rank": idx + 1}
                      for idx, (i, j, k) in enumerate([(1, 2, 3)] * 120)]

        tool = PredictionTool(log_level=50, data_dir=str(tmp_path), data_source="file")
        with patch.object(tool, "load_model", return_value=True), patch.object(
            tool, "predict_trifecta_probabilities", return_value=fake_combos
        ):
            result = tool.run_complete_prediction(
                target_date="2024-06-01", venues=["KIRYU"],
                fetch_data=False, prediction_only=True,
            )
        assert result is not None
        # トップレベル契約
        for key in ("prediction_date", "generated_at", "model_info", "execution_summary", "predictions", "venue_summaries"):
            assert key in result, f"missing key: {key}"
        # execution_summary 必須キー
        es = result["execution_summary"]
        for key in ("total_races", "successful_predictions", "execution_time_minutes"):
            assert key in es, f"execution_summary missing key: {key}"
        assert "predictions" in result and isinstance(result["predictions"], list)
