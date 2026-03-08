"""
B案ベースラインの学習ユースケース。

既存の race_data_*.json（着順入り）または DB からレースデータを読み、
状態ベクトルと 3連単クラスを用意して軽量分類器を学習し、モデルを保存する。
data_source で "json" / "db" を切り替え可能（既定は従来の JSON 直読）。
feature_set は明示引数優先。未指定時は KYOTEI_FEATURE_SET / KYOTEI_USE_MOTOR_WIN_PROXY で決定し meta に保存する。
"""

import hashlib
import json
import logging
import os
import random
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

ENV_FEATURE_SET = "KYOTEI_FEATURE_SET"
ENV_MOTOR_PROXY = "KYOTEI_USE_MOTOR_WIN_PROXY"

import numpy as np

logger = logging.getLogger(__name__)

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
    sample_mode: str = "head",
    seed: Optional[int] = None,
    racer_history_cache: Optional[List[tuple]] = None,
) -> Tuple[np.ndarray, np.ndarray, Optional[Dict[str, Any]]]:
    """
    data_dir 配下の race_data_*.json から、着順があるレースのみを集め、
    状態ベクトル X と 3連単クラス y を返す。再現性診断用にマニフェストも返す。

    Args:
        data_dir: race_data_*.json が入ったディレクトリ（サブディレクトリも検索）
        max_samples: 最大サンプル数（None で全件）。sample_mode=all のときは無視。
        train_start: 学習に含める開始日（YYYY-MM-DD）。None で制限なし。
        train_end: 学習に含める終了日（YYYY-MM-DD）。None で制限なし。
        sample_mode: "head"=先頭から, "random"=seed固定でランダム抽出, "all"=期間内全件
        seed: sample_mode=random 時の乱数シード（再現用）

    Returns:
        (X, y, manifest): X shape=(n, state_dim), y shape=(n,), manifest は学習実態の情報（JSON用）
    """
    race_files = sorted(data_dir.rglob("race_data_*.json"))
    # 期間フィルタを先に適用した候補リストを作成
    candidate_paths: List[Path] = []
    for path in race_files:
        if train_start is not None or train_end is not None:
            date_str = _parse_date_from_race_path(path)
            if date_str is None:
                continue
            if train_start is not None and date_str < train_start:
                continue
            if train_end is not None and date_str > train_end:
                continue
        candidate_paths.append(path)

    if sample_mode == "random" and seed is not None and candidate_paths:
        rng = random.Random(seed)
        candidate_paths = list(candidate_paths)
        rng.shuffle(candidate_paths)
    elif sample_mode == "all":
        max_samples = None  # 期間内全件使用

    X_list: List[np.ndarray] = []
    y_list: List[int] = []
    used_paths: List[str] = []
    used_dates: List[str] = []
    for path in candidate_paths:
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
            state = build_race_state_vector(race_data, None, racer_history_cache=racer_history_cache)
        except Exception:
            continue
        try:
            label = trifecta_to_class_index(actual)
        except ValueError:
            continue
        X_list.append(state)
        y_list.append(label)
        used_paths.append(str(path.resolve()))
        date_str = _parse_date_from_race_path(path)
        used_dates.append(date_str or "")

    n = len(X_list)
    max_samples_reached = max_samples is not None and n >= max_samples
    first_date = min(used_dates) if used_dates else None
    last_date = max(used_dates) if used_dates else None
    manifest = {
        "file_count": len(used_paths),
        "sample_count": n,
        "first_date": first_date,
        "last_date": last_date,
        "max_samples_reached": max_samples_reached,
        "max_samples": max_samples,
        "sample_mode": sample_mode,
        "file_paths": used_paths,
    }

    # 再現性診断用ログ（Task 2）
    logger.info(
        "[train_manifest] file_count=%s sample_count=%s first_date=%s last_date=%s max_samples_reached=%s",
        manifest["file_count"],
        manifest["sample_count"],
        first_date,
        last_date,
        max_samples_reached,
    )
    head_show = 3
    tail_show = 2
    if used_paths:
        head_paths = used_paths[:head_show]
        tail_paths = used_paths[-tail_show:] if len(used_paths) > head_show else []
        logger.info("[train_manifest] files_head=%s", head_paths)
        if tail_paths and tail_paths != head_paths:
            logger.info("[train_manifest] files_tail=%s", tail_paths)

    if not X_list:
        empty = np.zeros((0, get_state_dim()), dtype=np.float32), np.array([], dtype=np.int64)
        return empty[0], empty[1], manifest
    return np.stack(X_list, axis=0), np.array(y_list, dtype=np.int64), manifest


def _collect_training_data_from_repository(
    repository: RaceDataRepositoryProtocol,
    max_samples: Optional[int] = None,
    train_start: Optional[str] = None,
    train_end: Optional[str] = None,
    racer_history_cache: Optional[List[tuple]] = None,
) -> Tuple[np.ndarray, np.ndarray, Optional[Dict[str, Any]]]:
    """
    リポジトリから期間内のレースを取得し、着順があるものだけ状態ベクトル X とクラス y に変換する。
    racer_history_cache が渡されると extended_features_v2 で DB 由来の recent/venue を使う。
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
            state = build_race_state_vector(race_data, None, racer_history_cache=racer_history_cache)
        except Exception:
            continue
        try:
            label = trifecta_to_class_index(actual)
        except ValueError:
            continue
        X_list.append(state)
        y_list.append(label)
    if not X_list:
        empty_x = np.zeros((0, get_state_dim()), dtype=np.float32)
        empty_y = np.array([], dtype=np.int64)
        return empty_x, empty_y, None
    return np.stack(X_list, axis=0), np.array(y_list, dtype=np.int64), None


def run_baseline_train(
    data_dir: Path,
    model_save_path: Path,
    max_samples: Optional[int] = 5000,
    sample_mode: str = "head",
    n_estimators: int = 50,
    max_depth: int = 10,
    model_type: str = "sklearn",
    train_start: Optional[str] = None,
    train_end: Optional[str] = None,
    data_source: Optional[str] = None,
    race_repository: Optional[RaceDataRepositoryProtocol] = None,
    db_path: Optional[Union[str, Path]] = None,
    calibration: Optional[str] = None,
    seed: Optional[int] = 42,
    feature_set: Optional[str] = None,
) -> dict:
    """
    B案ベースラインを学習し、モデルを保存する。

    Args:
        data_dir: 学習用 race_data_*.json のディレクトリ（data_source=json 時）。db 時は JSON 用の raw 参照に使う場合あり。
        model_save_path: モデル保存先パス
        max_samples: 最大学習サンプル数（30分程度で終わるよう抑える）。sample_mode=all のときは無視。
        sample_mode: "head"=先頭から, "random"=seed固定ランダム抽出, "all"=期間内全件
        n_estimators: 本数（RandomForest / LightGBM / XGBoost 共通）
        max_depth: 最大深さ
        model_type: "sklearn" | "lightgbm" | "xgboost"。未導入時は sklearn にフォールバック
        train_start: 学習に含める開始日（YYYY-MM-DD）。None で制限なし。
        train_end: 学習に含める終了日（YYYY-MM-DD）。None で制限なし。
        data_source: "json" | "db" | None。None のときは従来通り data_dir の JSON 直読。
        race_repository: 指定時は data_source を無視してこのリポジトリを使用。
        db_path: data_source=db 時の SQLite パス。None なら Settings.DB_PATH。
        calibration: 確率キャリブレーション。"none" | "sigmoid" | "isotonic"。None は "none" 扱い。
        seed: 乱数シード。再現性用。None のときは 42 を使用。numpy / random を固定する。
        feature_set: 使用する特徴量セット（current_features / extended_features / extended_features_v2）。None のときは環境変数で決定。

    Returns:
        学習結果サマリ（n_samples, model_type, calibration, train_accuracy, seed, feature_set 等）
    """
    if seed is None:
        seed = 42
    np.random.seed(seed)
    random.seed(seed)

    # feature_set: 明示引数 > 環境変数 > デフォルト。学習中は ENV を設定して state_vector に伝える。
    if feature_set is not None:
        feature_set = feature_set.strip().lower()
        if feature_set not in ("current_features", "extended_features", "extended_features_v2"):
            feature_set = "extended_features"
    if feature_set is None:
        feature_set = os.environ.get(ENV_FEATURE_SET, "").strip().lower() or None
    if not feature_set:
        feature_set = "extended_features" if os.environ.get(ENV_MOTOR_PROXY, "0") == "1" else "current_features"
    prev_fs = os.environ.get(ENV_FEATURE_SET)
    prev_motor = os.environ.get(ENV_MOTOR_PROXY)
    try:
        os.environ[ENV_FEATURE_SET] = feature_set
        if ENV_MOTOR_PROXY in os.environ:
            os.environ.pop(ENV_MOTOR_PROXY, None)
    except Exception:
        pass

    racer_history_cache = None
    if feature_set == "extended_features_v2" and db_path:
        try:
            from kyotei_predictor.pipelines.racer_history import get_racer_history_from_db
            racer_history_cache = get_racer_history_from_db(
                str(db_path),
                date_from=train_start,
                date_to=train_end,
            )
        except Exception as e:
            logger.warning("racer_history cache build failed: %s", e)

    try:
        data_dir = Path(data_dir)
        train_manifest = None
        if race_repository is not None:
            X, y, train_manifest = _collect_training_data_from_repository(
                race_repository,
                max_samples=max_samples,
                train_start=train_start,
                train_end=train_end,
                racer_history_cache=racer_history_cache,
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
            X, y, train_manifest = _collect_training_data_from_repository(
                repo,
                max_samples=max_samples,
                train_start=train_start,
                train_end=train_end,
                racer_history_cache=racer_history_cache,
            )
        else:
            X, y, train_manifest = collect_training_data(
                data_dir,
                max_samples=max_samples,
                train_start=train_start,
                train_end=train_end,
                sample_mode=sample_mode,
                seed=seed,
                racer_history_cache=racer_history_cache,
            )
        if len(X) == 0:
            raise ValueError("学習データがありません（data_dir または data_source=db の場合は DB を確認してください）")

        model_type = (model_type or MODEL_TYPE_SKLEARN).strip().lower()
        calib = (calibration or "none").strip().lower()

        # XGBoost は全クラス 0..119 が y に含まれる必要がある。欠損クラスにダミーサンプルを 1 件ずつ追加
        NUM_CLASSES = 120
        if model_type == "xgboost":
            present = set(np.unique(y))
            missing = [c for c in range(NUM_CLASSES) if c not in present]
            if missing:
                dummy_X = np.zeros((len(missing), X.shape[1]), dtype=X.dtype)
                dummy_y = np.array(missing, dtype=np.int64)
                X = np.vstack([X, dummy_X])
                y = np.concatenate([y, dummy_y])

        model = create_baseline_model(
            model_type=model_type,
            n_estimators=n_estimators,
            max_depth=max_depth,
            random_state=seed,
        )
        model.fit(X, y)

        if calib in ("sigmoid", "isotonic"):
            from sklearn.calibration import CalibratedClassifierCV
            from sklearn.frozen import FrozenEstimator
            frozen = FrozenEstimator(model)
            calibrated = CalibratedClassifierCV(estimator=frozen, method=calib, cv=None)
            calibrated.fit(X, y)
            model = calibrated

        save_baseline_model(
            model,
            Path(model_save_path),
            model_type=model_type,
            calibration=calib,
            seed=seed,
            feature_set=feature_set,
        )
        acc = float(np.mean(model.predict(X) == y))
        out = {
            "n_samples": int(len(X)),
            "model_path": str(model_save_path),
            "model_type": model_type,
            "calibration": calib,
            "train_accuracy": round(acc, 4),
            "seed": seed,
            "feature_set": feature_set,
            "max_samples": max_samples,
            "sample_mode": sample_mode,
        }
        train_file_manifest_path = None
        train_file_manifest_hash = None
        if train_manifest:
            out["train_file_count"] = train_manifest.get("file_count")
            out["train_first_date"] = train_manifest.get("first_date")
            out["train_last_date"] = train_manifest.get("last_date")
            out["max_samples_reached"] = train_manifest.get("max_samples_reached")
            manifest_path = Path(model_save_path).parent / "train_file_manifest.json"
            try:
                body: Dict[str, Any] = {
                    "file_count": train_manifest.get("file_count"),
                    "sample_count": train_manifest.get("sample_count"),
                    "first_date": train_manifest.get("first_date"),
                    "last_date": train_manifest.get("last_date"),
                    "max_samples_reached": train_manifest.get("max_samples_reached"),
                    "max_samples": train_manifest.get("max_samples"),
                    "sample_mode": train_manifest.get("sample_mode", "head"),
                    "file_paths": train_manifest.get("file_paths", []),
                }
                file_paths_json = json.dumps(body["file_paths"], sort_keys=True, ensure_ascii=False)
                body["file_paths_hash"] = hashlib.sha256(file_paths_json.encode()).hexdigest()[:16]
                body["manifest_hash"] = hashlib.sha256(
                    json.dumps({k: v for k, v in body.items() if k != "manifest_hash"}, sort_keys=True, ensure_ascii=False).encode()
                ).hexdigest()[:16]
                train_file_manifest_hash = body["manifest_hash"]
                with open(manifest_path, "w", encoding="utf-8") as f:
                    json.dump(body, f, ensure_ascii=False, indent=2)
                train_file_manifest_path = str(manifest_path)
            except Exception as e:
                logger.warning("train_file_manifest.json の保存に失敗: %s", e)
        out["train_file_manifest_path"] = train_file_manifest_path
        out["train_file_manifest_hash"] = train_file_manifest_hash
        return out
    finally:
        try:
            if prev_fs is not None:
                os.environ[ENV_FEATURE_SET] = prev_fs
            elif ENV_FEATURE_SET in os.environ:
                os.environ.pop(ENV_FEATURE_SET, None)
            if prev_motor is not None:
                os.environ[ENV_MOTOR_PROXY] = prev_motor
        except Exception:
            pass
