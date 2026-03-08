"""
Contract tests for baseline (Strategy B) metadata and usecase return structure.

- Model metadata save/load and default when missing.
- run_baseline_predict return keys (model_info, execution_summary, predictions)
  so that verify_predictions and docs stay in sync.
"""

import pytest
from pathlib import Path


def test_load_baseline_model_metadata_missing_returns_default():
    """Missing .meta.json returns default dict (backward compatible)."""
    from kyotei_predictor.infrastructure.baseline_model_repository import load_baseline_model_metadata

    missing = Path("/nonexistent/model.joblib")
    meta = load_baseline_model_metadata(missing)
    assert meta["model_type"] is None
    assert meta["calibration"] in ("none", None) or meta["calibration"] == "none"
    assert "seed" in meta


def test_save_and_load_baseline_model_metadata_roundtrip(tmp_path):
    """Save metadata then load; required keys present."""
    from kyotei_predictor.infrastructure.baseline_model_repository import (
        save_baseline_model_metadata,
        load_baseline_model_metadata,
    )

    model_path = tmp_path / "m.joblib"
    save_baseline_model_metadata(model_path, model_type="sklearn", calibration="sigmoid", seed=42)
    meta = load_baseline_model_metadata(model_path)
    assert meta["model_type"] == "sklearn"
    assert meta["calibration"] == "sigmoid"
    assert meta["seed"] == 42


def test_save_and_load_baseline_model_metadata_includes_feature_set(tmp_path):
    """feature_set を保存すると load で feature_set が返ること。"""
    from kyotei_predictor.infrastructure.baseline_model_repository import (
        save_baseline_model_metadata,
        load_baseline_model_metadata,
    )

    model_path = tmp_path / "m.joblib"
    save_baseline_model_metadata(
        model_path, model_type="sklearn", calibration="sigmoid", seed=42, feature_set="extended_features_v2"
    )
    meta = load_baseline_model_metadata(model_path)
    assert meta["feature_set"] == "extended_features_v2"


def test_baseline_predict_return_structure_has_required_keys(tmp_path, monkeypatch):
    """run_baseline_predict return value has contract keys for verify_predictions / docs."""
    import numpy as np
    from kyotei_predictor.application import baseline_predict_usecase

    # Avoid real model load: mock load_baseline_model and metadata
    class DummyModel:
        def predict_proba(self, X):
            return np.ones((X.shape[0], 120)) / 120.0

    def _fake_load_model(path):
        return DummyModel()

    def _fake_load_meta(path):
        return {"model_type": "sklearn", "calibration": "sigmoid", "seed": None}

    monkeypatch.setattr(baseline_predict_usecase, "load_baseline_model", _fake_load_model)
    monkeypatch.setattr(baseline_predict_usecase, "load_baseline_model_metadata", _fake_load_meta)

    model_path = tmp_path / "model.joblib"
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    # No race files → predictions list empty but structure still returned
    result = baseline_predict_usecase.run_baseline_predict(
        model_path=model_path,
        data_dir=data_dir,
        prediction_date="2025-01-01",
        include_selected_bets=False,
    )

    assert "prediction_date" in result
    assert result["prediction_date"] == "2025-01-01"
    assert "model_info" in result
    assert "model_type" in result["model_info"]
    assert "model_path" in result["model_info"]
    assert "backend" in result["model_info"]
    assert "calibration" in result["model_info"]
    assert "feature_set" in result["model_info"]
    assert "execution_summary" in result
    assert "total_races" in result["execution_summary"]
    assert "predictions" in result
    assert isinstance(result["predictions"], list)


def test_baseline_predict_feature_set_mismatch_logs_warning(tmp_path, monkeypatch, caplog):
    """meta の feature_set と実行時 feature_set が不一致のとき warning がログに出すこと。"""
    import logging
    import numpy as np
    from kyotei_predictor.application import baseline_predict_usecase

    class DummyModel:
        def predict_proba(self, X):
            return np.ones((X.shape[0], 120)) / 120.0

    def _fake_load_meta(path):
        return {"model_type": "sklearn", "calibration": "sigmoid", "seed": None, "feature_set": "extended_features"}

    monkeypatch.setattr(baseline_predict_usecase, "load_baseline_model", lambda path: DummyModel())
    monkeypatch.setattr(baseline_predict_usecase, "load_baseline_model_metadata", _fake_load_meta)

    model_path = tmp_path / "model.joblib"
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    with caplog.at_level(logging.WARNING):
        baseline_predict_usecase.run_baseline_predict(
            model_path=model_path,
            data_dir=data_dir,
            prediction_date="2025-01-01",
            feature_set="extended_features_v2",
        )
    msg_text = [getattr(rec, "message", rec.getMessage()) for rec in caplog.records]
    assert any("feature_set mismatch" in m for m in msg_text)
