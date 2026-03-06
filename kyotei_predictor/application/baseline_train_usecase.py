"""
B案ベースラインの学習ユースケース。

既存の race_data_*.json（着順入り）または DB からレースデータを読み、
状態ベクトルと 3連単クラスを用意して軽量分類器を学習し、モデルを保存する。
data_source で "json" / "db" を切り替え可能（既定は従来の JSON 直読）。
"""

from pathlib import Path
from typing import List, Optional, Tuple, Union

import numpy as np

from kyotei_predictor.domain.verification_models import get_actual_trifecta_from_race_data
from kyotei_predictor.domain.repositories.race_data_repository import RaceDataRepositoryProtocol
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


def _collect_training_data_from_repository(
    repository: RaceDataRepositoryProtocol,
    max_samples: Optional[int] = None,
    train_start: Optional[str] = None,
    train_end: Optional[str] = None,
) -> Tuple[np.ndarray, np.ndarray]:
    """
    リポジトリから期間内のレースを取得し、着順があるものだけ状態ベクトル X とクラス y に変換する。
    """
    start = train_start or "0000-01-01"
    end = train_end or "9999-12-31"
    races = repository.load_races_between(start, end, max_samples=max_samples)
    X_list: List[np.ndarray] = []
    y_list: List[int] = []
    for race_data in races:
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
    data_source: Optional[str] = None,
    race_repository: Optional[RaceDataRepositoryProtocol] = None,
    db_path: Optional[Union[str, Path]] = None,
) -> dict:
    """
    B案ベースラインを学習し、モデルを保存する。

    Args:
        data_dir: 学習用 race_data_*.json のディレクトリ（data_source=json 時）。db 時は JSON 用の raw 参照に使う場合あり。
        model_save_path: モデル保存先パス
        max_samples: 最大学習サンプル数（30分程度で終わるよう抑える）
        n_estimators: 本数（RandomForest / LightGBM / XGBoost 共通）
        max_depth: 最大深さ
        model_type: "sklearn" | "lightgbm" | "xgboost"。未導入時は sklearn にフォールバック
        train_start: 学習に含める開始日（YYYY-MM-DD）。None で制限なし。
        train_end: 学習に含める終了日（YYYY-MM-DD）。None で制限なし。
        data_source: "json" | "db" | None。None のときは従来通り data_dir の JSON 直読。
        race_repository: 指定時は data_source を無視してこのリポジトリを使用。
        db_path: data_source=db 時の SQLite パス。None なら Settings.DB_PATH。

    Returns:
        学習結果サマリ（n_samples, model_type, train_accuracy 等）
    """
    data_dir = Path(data_dir)
    if race_repository is not None:
        X, y = _collect_training_data_from_repository(
            race_repository,
            max_samples=max_samples,
            train_start=train_start,
            train_end=train_end,
        )
    elif data_source and data_source.strip().lower() in ("json", "db"):
        from kyotei_predictor.infrastructure.repositories.race_data_repository_factory import (
            get_race_data_repository,
        )
        repo = get_race_data_repository(
            data_source.strip().lower(),
            data_dir=data_dir,
            db_path=str(db_path) if db_path else None,
        )
        X, y = _collect_training_data_from_repository(
            repo,
            max_samples=max_samples,
            train_start=train_start,
            train_end=train_end,
        )
    else:
        X, y = collect_training_data(
            data_dir,
            max_samples=max_samples,
            train_start=train_start,
            train_end=train_end,
        )
    if len(X) == 0:
        raise ValueError("学習データがありません（data_dir または data_source=db の場合は DB を確認してください）")

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
