"""
B案ベースラインの軽量テスト。

学習・予測の最小経路と、A案互換の出力形式を確認する。
"""

import json
import pytest
from pathlib import Path


def _minimal_race_data_with_result():
    """着順入りの最小 race_data（1-2-3 着が確定）"""
    return {
        "race_info": {"stadium": "KIRYU", "race_number": 1, "number_of_laps": 3, "is_course_fixed": False},
        "race_records": [
            {"pit_number": 1, "arrival": 1},
            {"pit_number": 2, "arrival": 2},
            {"pit_number": 3, "arrival": 3},
            {"pit_number": 4, "arrival": 4},
            {"pit_number": 5, "arrival": 5},
            {"pit_number": 6, "arrival": 6},
        ],
        "race_entries": [
            {"pit_number": i, "racer": {"current_rating": "B1"}, "performance": {"rate_in_all_stadium": 5.0, "rate_in_event_going_stadium": 5.0}, "boat": {"quinella_rate": 50.0, "trio_rate": 50.0}, "motor": {"quinella_rate": 50.0, "trio_rate": 50.0}}
            for i in range(1, 7)
        ],
    }


def test_trifecta_to_class_index():
    """3連単文字列がクラスインデックスに変換できること"""
    from kyotei_predictor.infrastructure.baseline_model_runner import trifecta_to_class_index, TRIFECTA_STRINGS
    assert trifecta_to_class_index("1-2-3") == 0
    assert TRIFECTA_STRINGS[0] == "1-2-3"
    idx = trifecta_to_class_index("6-5-4")
    assert 0 <= idx < 120


def test_scores_to_all_combinations():
    """120 スコアが all_combinations 形式に変換できること"""
    import numpy as np
    from kyotei_predictor.infrastructure.baseline_model_runner import scores_to_all_combinations
    proba = np.zeros(120)
    proba[0] = 0.5
    proba[1] = 0.3
    proba[2] = 0.2
    out = scores_to_all_combinations(proba)
    assert len(out) == 120
    assert out[0]["combination"] == "1-2-3"
    assert out[0]["probability"] == 0.5
    assert out[0]["rank"] == 1
    assert "expected_value" in out[0]


def test_baseline_train_and_predict(tmp_path):
    """最小データで学習→保存→読込→予測が通ること"""
    from kyotei_predictor.application.baseline_train_usecase import run_baseline_train, collect_training_data
    from kyotei_predictor.application.baseline_predict_usecase import run_baseline_predict
    from kyotei_predictor.infrastructure.file_loader import load_json

    data_dir = tmp_path / "data"
    data_dir.mkdir()
    for i in range(5):
        race = _minimal_race_data_with_result()
        path = data_dir / f"race_data_2024-05-01_KIRYU_R{i+1}.json"
        with open(path, "w", encoding="utf-8") as f:
            json.dump(race, f, ensure_ascii=False)

    X, y = collect_training_data(data_dir, max_samples=10)
    assert len(X) == 5
    assert len(y) == 5

    model_path = tmp_path / "model.joblib"
    summary = run_baseline_train(
        data_dir=data_dir,
        model_save_path=model_path,
        max_samples=100,
        n_estimators=5,
        max_depth=3,
    )
    assert summary["n_samples"] == 5
    assert model_path.exists()

    result = run_baseline_predict(
        model_path=model_path,
        data_dir=data_dir,
        prediction_date="2024-05-01",
    )
    assert result["prediction_date"] == "2024-05-01"
    assert len(result["predictions"]) == 5
    for pred in result["predictions"]:
        assert "venue" in pred and "race_number" in pred and "all_combinations" in pred
        assert len(pred["all_combinations"]) == 120
        assert pred["all_combinations"][0]["combination"] == "1-2-3"
        assert "probability" in pred["all_combinations"][0]
        assert "rank" in pred["all_combinations"][0]


def test_baseline_predict_with_selected_bets(tmp_path):
    """include_selected_bets=True で selected_bets が付与されること"""
    from kyotei_predictor.application.baseline_train_usecase import run_baseline_train
    from kyotei_predictor.application.baseline_predict_usecase import run_baseline_predict
    import json

    data_dir = tmp_path / "data"
    data_dir.mkdir()
    for i in range(2):
        race = _minimal_race_data_with_result()
        (data_dir / f"race_data_2024-05-01_KIRYU_R{i+1}.json").write_text(
            json.dumps(race, ensure_ascii=False)
        )
    model_path = tmp_path / "m.joblib"
    run_baseline_train(data_dir=data_dir, model_save_path=model_path, max_samples=10, n_estimators=3, max_depth=2)
    result = run_baseline_predict(
        model_path=model_path,
        data_dir=data_dir,
        prediction_date="2024-05-01",
        include_selected_bets=True,
        betting_strategy="top_n",
        betting_top_n=2,
    )
    assert result["execution_summary"].get("betting_strategy") == "top_n"
    for pred in result["predictions"]:
        assert "selected_bets" in pred
        assert isinstance(pred["selected_bets"], list)
        assert len(pred["selected_bets"]) <= 2
