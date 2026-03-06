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


def save_baseline_model_metadata(model_path: Path, model_type: str) -> None:
    """モデル種別を .meta.json に保存する。"""
    path = _meta_path(Path(model_path))
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump({"model_type": model_type}, f, ensure_ascii=False)


def load_baseline_model_metadata(model_path: Path) -> Optional[str]:
    """保存済みモデル種別を読む。無ければ None。"""
    path = _meta_path(Path(model_path))
    if not path.exists():
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f).get("model_type")
    except Exception:
        return None


def save_baseline_model(model: Any, path: Path, model_type: Optional[str] = None) -> None:
    """
    ベースラインモデルをファイルに保存する。

    Args:
        model: fit と predict_proba を持つオブジェクト（sklearn / lightgbm / xgboost）
        path: 保存先パス（.joblib または .pkl 推奨）
        model_type: モデル種別（sklearn / lightgbm / xgboost）。指定時は .meta.json に保存する。
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if _HAS_JOBLIB:
        joblib.dump(model, path)
    else:
        import pickle
        with open(path, "wb") as f:
            pickle.dump(model, f)
    if model_type:
        save_baseline_model_metadata(path, model_type)


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
