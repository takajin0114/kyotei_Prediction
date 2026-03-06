"""
B案ベースラインモデルの保存・読込（I/O 層）。

学習済みモデルをファイルに保存し、予測時に読み込む。
TODO: LightGBM / XGBoost 差し替え時も同じ save/load インターフェースを使う。
"""

from pathlib import Path
from typing import Any, Optional

# デフォルトは sklearn + joblib。将来 LightGBM 等に差し替え可能にするため
# モデルオブジェクトは fit / predict_proba を持つ前提で抽象化する。
try:
    import joblib
    _HAS_JOBLIB = True
except ImportError:
    _HAS_JOBLIB = False


def save_baseline_model(model: Any, path: Path) -> None:
    """
    ベースラインモデルをファイルに保存する。

    Args:
        model: fit と predict_proba を持つオブジェクト（sklearn 等）
        path: 保存先パス（.joblib または .pkl 推奨）
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if _HAS_JOBLIB:
        joblib.dump(model, path)
    else:
        import pickle
        with open(path, "wb") as f:
            pickle.dump(model, f)


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
