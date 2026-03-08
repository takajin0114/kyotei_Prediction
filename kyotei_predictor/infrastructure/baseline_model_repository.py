"""
B案ベースラインモデルの保存・読込（I/O 層）。

学習済みモデルをファイルに保存し、予測時に読み込む。
モデル種別（sklearn / lightgbm / xgboost）は .meta.json に保存し、ログ・比較に利用する。
"""

import json
from pathlib import Path
from typing import Any, Optional

try:
    import joblib
    _HAS_JOBLIB = True
except ImportError:
    _HAS_JOBLIB = False


def _meta_path(model_path: Path) -> Path:
    return Path(str(model_path) + ".meta.json")


def save_baseline_model_metadata(
    model_path: Path,
    model_type: str,
    calibration: Optional[str] = None,
    seed: Optional[int] = None,
    feature_set: Optional[str] = None,
) -> None:
    """モデル種別・キャリブレーション・seed・feature_set を .meta.json に保存する。"""
    path = _meta_path(Path(model_path))
    path.parent.mkdir(parents=True, exist_ok=True)
    meta = {"model_type": model_type, "calibration": calibration or "none"}
    if seed is not None:
        meta["seed"] = seed
    if feature_set is not None:
        meta["feature_set"] = feature_set
    with open(path, "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False)


def load_baseline_model_metadata(model_path: Path) -> dict:
    """
    保存済みメタデータを読む。
    Returns:
        {"model_type", "calibration", "seed", "feature_set"}。ファイルが無い場合は feature_set=None。
    """
    path = _meta_path(Path(model_path))
    if not path.exists():
        return {"model_type": None, "calibration": "none", "seed": None, "feature_set": None}
    try:
        with open(path, "r", encoding="utf-8") as f:
            d = json.load(f)
        return {
            "model_type": d.get("model_type"),
            "calibration": d.get("calibration", "none"),
            "seed": d.get("seed"),
            "feature_set": d.get("feature_set"),
        }
    except Exception:
        return {"model_type": None, "calibration": "none", "seed": None, "feature_set": None}


def save_baseline_model(
    model: Any,
    path: Path,
    model_type: Optional[str] = None,
    calibration: Optional[str] = None,
    seed: Optional[int] = None,
    feature_set: Optional[str] = None,
) -> None:
    """
    ベースラインモデルをファイルに保存する。

    Args:
        model: fit と predict_proba を持つオブジェクト（sklearn / lightgbm / xgboost / CalibratedClassifierCV）
        path: 保存先パス（.joblib または .pkl 推奨）
        model_type: モデル種別（sklearn / lightgbm / xgboost）。指定時は .meta.json に保存する。
        calibration: キャリブレーション種別（none / sigmoid / isotonic）。.meta.json に保存する。
        seed: 学習時の乱数シード。再現性用に .meta.json に保存する。
        feature_set: 学習時に使用した特徴量セット。.meta.json に保存する。
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if _HAS_JOBLIB:
        joblib.dump(model, path)
    else:
        import pickle
        with open(path, "wb") as f:
            pickle.dump(model, f)
    if model_type is not None:
        save_baseline_model_metadata(path, model_type, calibration=calibration, seed=seed, feature_set=feature_set)


def load_baseline_model(path: Path) -> Any:
    """
    保存済みベースラインモデルを読み込む。

    Args:
        path: モデルファイルのパス

    Returns:
        predict_proba(X) をサポートするモデル
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"モデルファイルが見つかりません: {path}")
    if _HAS_JOBLIB:
        return joblib.load(path)
    import pickle
    with open(path, "rb") as f:
        return pickle.load(f)
