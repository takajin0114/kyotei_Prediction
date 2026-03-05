#!/usr/bin/env python3
"""
メイン処理（第1優先）: PredictionEngine の単体テスト。

- predict() の正常系（basic / rating_weighted）
- データ検証（必須フィールド不足で DataValidationError）
- 未知アルゴリズムで AlgorithmError
- 戻り値の構造（algorithm, predictions, summary, validation）
"""
import pytest

from kyotei_predictor.prediction_engine import (
    PredictionEngine,
    DataValidationError,
    AlgorithmError,
)


def _minimal_race_data():
    """PredictionEngine が要求する最小の race_data"""
    return {
        "race_info": {"date": "2024-06-01", "stadium": "KIRYU", "race_number": 1, "title": "テスト"},
        "race_entries": [
            {
                "pit_number": i,
                "racer": {"name": f"選手{i}", "current_rating": "B1"},
                "performance": {"rate_in_all_stadium": 5.0 + i * 0.5, "rate_in_event_going_stadium": 4.0 + i * 0.3},
            }
            for i in range(1, 7)
        ],
    }


class TestPredictionEngineMain:
    """PredictionEngine のメイン処理テスト"""

    def test_engine_initializes_and_has_algorithms(self):
        engine = PredictionEngine()
        assert "basic" in engine.algorithms
        assert "rating_weighted" in engine.algorithms
        assert "equipment_focused" in engine.algorithms

    def test_predict_basic_returns_expected_structure(self):
        engine = PredictionEngine()
        race_data = _minimal_race_data()
        result = engine.predict(race_data, algorithm="basic")
        assert result["algorithm"] == "basic"
        assert "predictions" in result
        assert "summary" in result
        assert "validation" in result
        assert "execution_time" in result
        assert "race_info" in result
        assert len(result["predictions"]) == 6
        assert result["validation"]["data_quality"] == "good"

    def test_predict_rating_weighted_returns_expected_structure(self):
        engine = PredictionEngine()
        race_data = _minimal_race_data()
        result = engine.predict(race_data, algorithm="rating_weighted")
        assert result["algorithm"] == "rating_weighted"
        assert len(result["predictions"]) == 6
        scores = [p["prediction_score"] for p in result["predictions"]]
        assert all(isinstance(s, (int, float)) for s in scores)

    def test_predict_unknown_algorithm_raises(self):
        engine = PredictionEngine()
        race_data = _minimal_race_data()
        with pytest.raises(AlgorithmError) as exc:
            engine.predict(race_data, algorithm="unknown_algo")
        assert "未知のアルゴリズム" in str(exc.value)

    def test_validate_race_data_missing_race_entries_raises(self):
        engine = PredictionEngine()
        with pytest.raises(DataValidationError) as exc:
            engine.predict({"race_entries": []}, algorithm="basic")
        assert "race_entries" in str(exc.value) or "必須" in str(exc.value)

    def test_validate_race_data_missing_required_field_raises(self):
        engine = PredictionEngine()
        bad = _minimal_race_data()
        del bad["race_entries"]
        with pytest.raises(DataValidationError) as exc:
            engine.predict(bad, algorithm="basic")
        assert "race_entries" in str(exc.value) or "必須" in str(exc.value)

    def test_validate_race_data_entry_missing_performance_raises(self):
        engine = PredictionEngine()
        bad = _minimal_race_data()
        bad["race_entries"][0] = {"pit_number": 1, "racer": {"name": "A", "current_rating": "B1"}}
        with pytest.raises(DataValidationError):
            engine.predict(bad, algorithm="basic")

    def test_summary_contains_favorite_and_score_distribution(self):
        engine = PredictionEngine()
        race_data = _minimal_race_data()
        result = engine.predict(race_data, algorithm="basic")
        summary = result["summary"]
        assert "favorite" in summary
        assert "score_distribution" in summary
        assert "max" in summary["score_distribution"]
        assert "min" in summary["score_distribution"]

    def test_predict_equipment_focused_returns_expected_structure(self):
        engine = PredictionEngine()
        race_data = _minimal_race_data()
        result = engine.predict(race_data, algorithm="equipment_focused")
        assert result["algorithm"] == "equipment_focused"
        assert len(result["predictions"]) == 6
        assert result["validation"]["data_quality"] == "good"

    def test_predict_comprehensive_returns_expected_structure(self):
        engine = PredictionEngine()
        race_data = _minimal_race_data()
        result = engine.predict(race_data, algorithm="comprehensive")
        assert result["algorithm"] == "comprehensive"
        assert len(result["predictions"]) == 6
        assert "predictions" in result and "summary" in result

    def test_predict_relative_strength_returns_expected_structure(self):
        engine = PredictionEngine()
        race_data = _minimal_race_data()
        result = engine.predict(race_data, algorithm="relative_strength")
        assert result["algorithm"] == "relative_strength"
        assert len(result["predictions"]) == 6
        assert "predictions" in result and "summary" in result
