"""
B案ベースラインの予測ユースケース。

学習済みモデルを読み、指定日の race_data に対して 3連単スコアを出力する。
data_source で "json" / "db" を切り替え可能。既存の prediction 形式に合わせ、
verify_predictions / betting_selector にそのまま渡せる形で返す。
feature_set は明示引数優先。meta.json の feature_set と不一致の場合は警告する。
"""

import logging
import os
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Union

logger = logging.getLogger(__name__)
ENV_FEATURE_SET = "KYOTEI_FEATURE_SET"
ENV_MOTOR_PROXY = "KYOTEI_USE_MOTOR_WIN_PROXY"

from kyotei_predictor.domain.verification_models import get_odds_for_combination
from kyotei_predictor.domain.repositories.race_data_repository import RaceDataRepositoryProtocol
from kyotei_predictor.infrastructure.file_loader import load_json
from kyotei_predictor.infrastructure.baseline_model_repository import (
    load_baseline_model,
    load_baseline_model_metadata,
)
from kyotei_predictor.infrastructure.baseline_model_runner import (
    predict_proba_120,
    scores_to_all_combinations,
)
from kyotei_predictor.pipelines.state_vector import build_race_state_vector


def _get_betting_params_from_config() -> Dict[str, Any]:
    """ImprovementConfigManager から買い目パラメータを取得。未読込時はデフォルト。"""
    try:
        from kyotei_predictor.config.improvement_config_manager import ImprovementConfigManager
        cfg = ImprovementConfigManager()
        return {
            "strategy": (cfg.get_betting_strategy() or "single").strip().lower(),
            "top_n": cfg.get_betting_top_n(),
            "score_threshold": cfg.get_betting_score_threshold(),
            "ev_threshold": cfg.get_betting_ev_threshold(),
        }
    except Exception:
        return {"strategy": "single", "top_n": 3, "score_threshold": 0.05, "ev_threshold": 0.0}


def _attach_odds_to_combinations(
    all_combinations: List[Dict[str, Any]],
    data_dir: Path,
    prediction_date: str,
    venue: str,
    race_number: int,
    odds_getter: Optional[Callable[[str, str, int], Optional[Dict[str, Any]]]] = None,
) -> None:
    """all_combinations の各要素に ratio（オッズ）を付与する。オッズがない場合は付与しない。in-place。"""
    if odds_getter is not None:
        odds_data = odds_getter(prediction_date, venue, race_number)
    else:
        odds_file = data_dir / f"odds_data_{prediction_date}_{venue}_R{race_number}.json"
        if not odds_file.exists():
            return
        try:
            odds_data = load_json(odds_file)
        except Exception:
            return
    if odds_data is None:
        return
    for c in all_combinations:
        comb = (c.get("combination") or "").strip()
        if not comb:
            continue
        od = get_odds_for_combination(odds_data, comb)
        if od is not None:
            c["ratio"] = od


def _apply_selected_bets(
    predictions: List[Dict[str, Any]],
    strategy: str,
    top_n: int,
    score_threshold: float,
    ev_threshold: float,
    confidence_type: Optional[str] = None,
    race_ev_min: Optional[float] = None,
    prob_gap_min: Optional[float] = None,
    entropy_max: Optional[float] = None,
    candidate_min: Optional[int] = None,
    pool_k: Optional[int] = None,
    alpha: Optional[float] = None,
    ev_gap_threshold: Optional[float] = None,
) -> None:
    """
    各レースの all_combinations に betting_selector を適用し、
    selected_bets（および ev 時は ev_selection_metadata）を付与する。in-place で更新。
    """
    from kyotei_predictor.utils.betting_selector import (
        select_bets,
        STRATEGY_EV,
    )
    extra_kwargs: Dict[str, Any] = {}
    if confidence_type:
        extra_kwargs["confidence_type"] = confidence_type
    if race_ev_min is not None:
        extra_kwargs["race_ev_min"] = race_ev_min
    if prob_gap_min is not None:
        extra_kwargs["prob_gap_min"] = prob_gap_min
    if entropy_max is not None:
        extra_kwargs["entropy_max"] = entropy_max
    if candidate_min is not None:
        extra_kwargs["candidate_min"] = candidate_min
    if pool_k is not None:
        extra_kwargs["pool_k"] = int(pool_k)
    if alpha is not None:
        extra_kwargs["alpha"] = float(alpha)
    if ev_gap_threshold is not None:
        extra_kwargs["ev_gap_threshold"] = float(ev_gap_threshold)
    for pred in predictions:
        ac = pred.get("all_combinations") or []
        if not ac:
            pred["selected_bets"] = []
            continue
        use_metadata = strategy == STRATEGY_EV
        try:
            res = select_bets(
                ac,
                strategy=strategy,
                top_n=top_n,
                score_threshold=score_threshold,
                ev_threshold=ev_threshold,
                return_metadata=use_metadata,
                **extra_kwargs,
            )
            if use_metadata and isinstance(res, tuple):
                pred["selected_bets"], pred["ev_selection_metadata"] = res[0], res[1]
            else:
                pred["selected_bets"] = res if isinstance(res, list) else list(res)
                if "ev_selection_metadata" in pred:
                    del pred["ev_selection_metadata"]
        except Exception:
            pred["selected_bets"] = []


def run_baseline_predict(
    model_path: Path,
    data_dir: Path,
    prediction_date: str,
    venues: Optional[List[str]] = None,
    include_selected_bets: bool = False,
    betting_strategy: Optional[str] = None,
    betting_top_n: Optional[int] = None,
    betting_score_threshold: Optional[float] = None,
    betting_ev_threshold: Optional[float] = None,
    betting_confidence_type: Optional[str] = None,
    betting_prob_gap_min: Optional[float] = None,
    betting_entropy_max: Optional[float] = None,
    betting_race_ev_min: Optional[float] = None,
    betting_candidate_min: Optional[int] = None,
    betting_pool_k: Optional[int] = None,
    betting_alpha: Optional[float] = None,
    betting_ev_gap_threshold: Optional[float] = None,
    data_source: Optional[str] = None,
    race_repository: Optional[RaceDataRepositoryProtocol] = None,
    db_path: Optional[Union[str, Path]] = None,
    feature_set: Optional[str] = None,
) -> Dict[str, Any]:
    """
    B案ベースラインで予測を実行し、A案と同一形式の予測辞書を返す。

    Args:
        model_path: 学習済みモデルのパス
        data_dir: race_data_*.json が入ったディレクトリ（JSON 時）。オッズ読込にも使用。
        prediction_date: 予測日 YYYY-MM-DD
        venues: 対象会場リスト。None の場合は全レース
        include_selected_bets: True で既存 betting_selector を適用し selected_bets を付与
        betting_strategy / betting_top_n / betting_score_threshold / betting_ev_threshold / betting_confidence_type: 買い目パラメータ（top_n_ev_confidence 時は confidence_type）
        data_source: "json" | "db" | None。None のときは従来通り data_dir の JSON 直読。
        race_repository: 指定時はこのリポジトリでレース取得（data_source は無視）。
        db_path: data_source=db 時の SQLite パス。
        feature_set: 使用する特徴量セット。None のときは meta または環境変数に従う。meta と不一致なら警告。

    Returns:
        prediction_tool と同形式。include_selected_bets 時は selected_bets 付きで verify 可能。
    """
    data_dir = Path(data_dir)
    model_path_resolved = Path(model_path)
    model = load_baseline_model(model_path_resolved)
    meta = load_baseline_model_metadata(model_path_resolved)
    saved_model_type = meta.get("model_type")
    saved_calibration = meta.get("calibration", "none")
    saved_feature_set = meta.get("feature_set")

    effective_fs = None
    if feature_set is not None:
        effective_fs = feature_set.strip().lower()
        if effective_fs not in ("current_features", "extended_features", "extended_features_v2"):
            effective_fs = saved_feature_set or "extended_features"
    if effective_fs is None:
        effective_fs = os.environ.get(ENV_FEATURE_SET, "").strip().lower() or None
    if not effective_fs:
        effective_fs = "extended_features" if os.environ.get(ENV_MOTOR_PROXY, "0") == "1" else "current_features"

    if saved_feature_set is not None and effective_fs != saved_feature_set:
        logger.warning(
            "feature_set mismatch: model was trained with feature_set=%s but predict is using %s. Results may be wrong.",
            saved_feature_set,
            effective_fs,
        )

    prev_fs = os.environ.get(ENV_FEATURE_SET)
    prev_motor = os.environ.get(ENV_MOTOR_PROXY)
    try:
        os.environ[ENV_FEATURE_SET] = effective_fs
        if ENV_MOTOR_PROXY in os.environ:
            os.environ.pop(ENV_MOTOR_PROXY, None)
    except Exception:
        pass

    racer_history_cache = None
    if effective_fs == "extended_features_v2" and db_path:
        try:
            from kyotei_predictor.pipelines.racer_history import get_racer_history_from_db
            racer_history_cache = get_racer_history_from_db(
                str(db_path),
                date_to=prediction_date,
            )
        except Exception as e:
            logger.warning("racer_history cache build failed for predict: %s", e)

    predictions: List[Dict[str, Any]] = []
    if race_repository is not None or (data_source and data_source.strip().lower() in ("json", "db")):
        if race_repository is None:
            from kyotei_predictor.infrastructure.repositories.race_data_repository_factory import (
                get_race_data_repository,
            )
            race_repository = get_race_data_repository(
                (data_source or "json").strip().lower(),
                data_dir=data_dir,
                db_path=str(db_path) if db_path else None,
            )
        odds_getter = None
        if hasattr(race_repository, "get_odds"):
            odds_getter = lambda d, v, n: race_repository.get_odds(d, v, n)
        for race_data, venue, race_number in race_repository.load_races_by_date(
            prediction_date, venues=venues
        ):
            try:
                state = build_race_state_vector(race_data, None, racer_history_cache=racer_history_cache)
            except Exception:
                continue
            proba = predict_proba_120(model, state)
            all_combinations = scores_to_all_combinations(proba)
            _attach_odds_to_combinations(
                all_combinations, data_dir, prediction_date, venue, race_number, odds_getter=odds_getter
            )
            predictions.append({
                "venue": venue,
                "race_number": race_number,
                "all_combinations": all_combinations,
            })
    else:
        prefix = f"race_data_{prediction_date}_"
        race_files = sorted(data_dir.rglob("race_data_*.json"))
        for path in race_files:
            if not path.name.startswith(prefix):
                continue
            venue = ""
            race_number = 0
            try:
                rest = path.stem[len("race_data_"):]
                parts = rest.split("_")
                if len(parts) >= 3:
                    venue = parts[-2]
                    rn = parts[-1]
                    if rn.startswith("R"):
                        race_number = int(rn[1:])
            except (ValueError, IndexError):
                continue
            if venues is not None and venue and venue not in venues:
                continue
            try:
                race_data = load_json(path)
            except Exception:
                continue
            try:
                state = build_race_state_vector(race_data, None, racer_history_cache=racer_history_cache)
            except Exception:
                continue
            proba = predict_proba_120(model, state)
            all_combinations = scores_to_all_combinations(proba)
            _attach_odds_to_combinations(all_combinations, data_dir, prediction_date, venue or "", race_number)
            predictions.append({
                "venue": venue or path.stem,
                "race_number": race_number,
                "all_combinations": all_combinations,
            })

    if include_selected_bets:
        params = _get_betting_params_from_config()
        strategy = betting_strategy or params["strategy"]
        top_n = betting_top_n if betting_top_n is not None else params["top_n"]
        score_threshold = betting_score_threshold if betting_score_threshold is not None else params["score_threshold"]
        ev_threshold = betting_ev_threshold if betting_ev_threshold is not None else params["ev_threshold"]
        confidence_type = betting_confidence_type
        _apply_selected_bets(
            predictions, strategy, top_n, score_threshold, ev_threshold,
            confidence_type=confidence_type,
            race_ev_min=betting_race_ev_min,
            prob_gap_min=betting_prob_gap_min,
            entropy_max=betting_entropy_max,
            candidate_min=betting_candidate_min,
            pool_k=betting_pool_k,
            alpha=betting_alpha,
            ev_gap_threshold=betting_ev_gap_threshold,
        )
        # execution_summary に ev_selection 集計を追加（A案互換）
        ev_metas = [p.get("ev_selection_metadata") for p in predictions if p.get("ev_selection_metadata")]
        if ev_metas:
            exec_ev = {
                "ev_threshold": ev_metas[0].get("ev_threshold"),
                "fallback_used_count": sum(1 for m in ev_metas if m.get("fallback_used")),
                "final_selected_count_total": sum(m.get("purchased_count", 0) for m in ev_metas),
            }
        else:
            exec_ev = None
    else:
        strategy = None
        exec_ev = None

    try:
        if prev_fs is not None:
            os.environ[ENV_FEATURE_SET] = prev_fs
        elif ENV_FEATURE_SET in os.environ:
            os.environ.pop(ENV_FEATURE_SET, None)
        if prev_motor is not None:
            os.environ[ENV_MOTOR_PROXY] = prev_motor
    except Exception:
        pass

    out = {
        "prediction_date": prediction_date,
        "model_info": {
            "model_type": "baseline_b",
            "model_path": str(model_path),
            "backend": saved_model_type or "sklearn",
            "calibration": saved_calibration,
            "feature_set": effective_fs,
        },
        "execution_summary": {
            "total_races": len(predictions),
            "successful_predictions": len(predictions),
        },
        "predictions": predictions,
    }
    if include_selected_bets and strategy:
        out["execution_summary"]["betting_strategy"] = strategy
    if exec_ev:
        out["execution_summary"]["ev_selection"] = exec_ev
    return out
