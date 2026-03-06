"""
B案ベースラインの学習ユースケース。

既存の race_data_*.json（着順入り）を読み、状態ベクトルと 3連単クラスを用意して
軽量分類器を学習し、モデルを保存する。既存 verify / betting と比較可能なモデルを目指す。
"""

from pathlib import Path
from typing import List, Optional, Tuple

import numpy as np

from kyotei_predictor.domain.verification_models import get_actual_trifecta_from_race_data
from kyotei_predictor.infrastructure.file_loader import load_json
from kyotei_predictor.infrastructure.baseline_model_repository import save_baseline_model
from kyotei_predictor.infrastructure.baseline_model_runner import (
    create_baseline_model,
    MODEL_TYPE_SKLEARN,
    trifecta_to_class_index,
)
from kyotei_predictor.pipelines.state_vector import build_race_state_vector, get_state_dim


def _parse_date_from_race_path(path: Path) -> Optional[str]:
    """
    ファイルパスからレース日付 YYYY-MM-DD を抽出する。
    例: race_data_2024-06-01_EDOGAWA_R1.json -> 2024-06-01
    """
    stem = path.stem
    if not stem.startswith("race_data_"):
        return None
    rest = stem[len("race_data_"):]
    if len(rest) >= 10 and rest[4] == "-" and rest[7] == "-":
        return rest[:10]
    return None


def collect_training_data(
    data_dir: Path,
    max_samples: Optional[int] = None,
    train_start: Optional[str] = None,
    train_end: Optional[str] = None,
) -> Tuple[np.ndarray, np.ndarray]:
    """
    data_dir 配下の race_data_*.json から、着順があるレースのみを集め、
    状態ベクトル X と 3連単クラス y を返す。

    Args:
        data_dir: race_data_*.json が入ったディレクトリ（サブディレクトリも検索）
        max_samples: 最大サンプル数（None で全件）
        train_start: 学習に含める開始日（YYYY-MM-DD）。None で制限なし。
        train_end: 学習に含める終了日（YYYY-MM-DD）。None で制限なし。

    Returns:
        (X, y): X shape=(n, state_dim), y shape=(n,) クラスインデックス 0..119
    """
    race_files = sorted(data_dir.rglob("race_data_*.json"))
    X_list = []
    y_list = []
    for path in race_files:
        if train_start is not None or train_end is not None:
            date_str = _parse_date_from_race_path(path)
            if date_str is None:
                continue
            if train_start is not None and date_str < train_start:
                continue
            if train_end is not None and date_str > train_end:
                continue
        if max_samples is not None and len(X_list) >= max_samples:
            break
        try:
            race_data = load_json(path)
        except Exception:
            continue
        actual = get_actual_trifecta_from_race_data(race_data)
        if actual is None:
            continue
        try:
            state = build_race_state_vector(race_data, None)
        except Exception:
            continue
        try:
            label = trifecta_to_class_index(actual)
        except ValueError:
            continue
        X_list.append(state)
        y_list.append(label)
    if not X_list:
        return np.zeros((0, get_state_dim()), dtype=np.float32), np.array([], dtype=np.int64)
    return np.stack(X_list, axis=0), np.array(y_list, dtype=np.int64)


def run_baseline_train(
    data_dir: Path,
    model_save_path: Path,
    max_samples: Optional[int] = 5000,
    n_estimators: int = 50,
    max_depth: int = 10,
    model_type: str = "sklearn",
    train_start: Optional[str] = None,
    train_end: Optional[str] = None,
) -> dict:
    """
    B案ベースラインを学習し、モデルを保存する。

    Args:
        data_dir: 学習用 race_data_*.json のディレクトリ（サブディレクトリも検索）
        model_save_path: モデル保存先パス
        max_samples: 最大学習サンプル数（30分程度で終わるよう抑える）
        n_estimators: 本数（RandomForest / LightGBM / XGBoost 共通）
        max_depth: 最大深さ
        model_type: "sklearn" | "lightgbm" | "xgboost"。未導入時は sklearn にフォールバック
        train_start: 学習に含める開始日（YYYY-MM-DD）。None で制限なし。
        train_end: 学習に含める終了日（YYYY-MM-DD）。None で制限なし。

    Returns:
        学習結果サマリ（n_samples, model_type, train_accuracy 等）
    """
    data_dir = Path(data_dir)
    X, y = collect_training_data(
        data_dir,
        max_samples=max_samples,
        train_start=train_start,
        train_end=train_end,
    )
    if len(X) == 0:
        raise ValueError(f"学習データがありません: {data_dir}")

    model_type = (model_type or MODEL_TYPE_SKLEARN).strip().lower()
    model = create_baseline_model(
        model_type=model_type,
        n_estimators=n_estimators,
        max_depth=max_depth,
    )
    model.fit(X, y)

    save_baseline_model(model, Path(model_save_path), model_type=model_type)
    acc = float(np.mean(model.predict(X) == y))
    return {
        "n_samples": int(len(X)),
        "model_path": str(model_save_path),
        "model_type": model_type,
        "train_accuracy": round(acc, 4),
    }
