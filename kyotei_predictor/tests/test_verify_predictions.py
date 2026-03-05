#!/usr/bin/env python3
"""tools.verify_predictions の単体テスト（純粋関数）"""
import json
import tempfile
from pathlib import Path

import pytest

from kyotei_predictor.tools import verify_predictions as vp


class TestGetActualTrifectaFromRaceData:
    def test_returns_none_when_records_less_than_3(self):
        assert vp.get_actual_trifecta_from_race_data({"race_records": []}) is None
        assert vp.get_actual_trifecta_from_race_data({"race_records": [{"arrival": 1}, {"arrival": 2}]}) is None

    def test_returns_none_when_1st_2nd_3rd_arrival_missing(self):
        # 1着・2着・3着のいずれかが欠けている場合は None
        data = {
            "race_records": [
                {"pit_number": 1, "arrival": 1},
                {"pit_number": 2, "arrival": None},
                {"pit_number": 3, "arrival": 3},
                {"pit_number": 4, "arrival": 4},
            ]
        }
        assert vp.get_actual_trifecta_from_race_data(data) is None

    def test_returns_1_2_3_format(self):
        data = {
            "race_records": [
                {"pit_number": 3, "arrival": 1},
                {"pit_number": 1, "arrival": 2},
                {"pit_number": 2, "arrival": 3},
                {"pit_number": 4, "arrival": 4},
            ]
        }
        assert vp.get_actual_trifecta_from_race_data(data) == "3-1-2"


class TestGetOddsForCombination:
    def test_returns_none_when_empty_odds(self):
        assert vp.get_odds_for_combination({}, "1-2-3") is None
        assert vp.get_odds_for_combination({"odds_data": []}, "1-2-3") is None

    def test_returns_ratio_when_match(self):
        data = {"odds_data": [{"combination": "1-2-3", "ratio": 12.5}, {"combination": "1-3-2", "ratio": 8.0}]}
        assert vp.get_odds_for_combination(data, "1-2-3") == 12.5
        assert vp.get_odds_for_combination(data, "1-3-2") == 8.0

    def test_ignores_spaces_in_combination(self):
        data = {"odds_data": [{"combination": "1 - 2 - 3", "ratio": 10.0}]}
        assert vp.get_odds_for_combination(data, "1-2-3") == 10.0


class TestRunVerification:
    def test_returns_structure_with_empty_predictions(self, tmp_path):
        pred_path = tmp_path / "pred.json"
        pred_path.write_text(json.dumps({"prediction_date": "2024-01-01", "predictions": []}), encoding="utf-8")
        summary, details = vp.run_verification(pred_path, tmp_path)
        assert isinstance(summary, dict)
        assert isinstance(details, list)
        assert "races_with_result" in summary
        assert summary["races_with_result"] == 0
