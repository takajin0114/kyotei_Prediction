"""
B案ベースラインの予測ユースケース。

学習済みモデルを読み、指定日の race_data に対して 3連単スコアを出力する。
既存の prediction 形式（all_combinations, venue, race_number）に合わせ、
verify_predictions / betting_selector にそのまま渡せる形で返す。
include_selected_bets=True で既存 betting_selector を適用し、selected_bets を付与する。
"""

from pathlib import Path
from typing import Any, Dict, List, Optional

from kyotei_predictor.domain.verification_models import get_odds_for_combination
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
) -> None:
    """all_combinations の各要素に ratio（オッズ）を付与する。オッズがない場合は付与しない。in-place。"""
    odds_file = data_dir / f"odds_data_{prediction_date}_{venue}_R{race_number}.json"
    if not odds_file.exists():
        return
    try:
        odds_data = load_json(odds_file)
    except Exception:
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
) -> None:
    """
    各レースの all_combinations に betting_selector を適用し、
    selected_bets（および ev 時は ev_selection_metadata）を付与する。in-place で更新。
    """
    from kyotei_predictor.utils.betting_selector import (
        select_bets,
        STRATEGY_EV,
    )
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
) -> Dict[str, Any]:
    """
    B案ベースラインで予測を実行し、A案と同一形式の予測辞書を返す。

    Args:
        model_path: 学習済みモデルのパス
        data_dir: race_data_*.json が入ったディレクトリ
        prediction_date: 予測日 YYYY-MM-DD（ファイル名の日付部分に使う）
        venues: 対象会場リスト。None の場合は data_dir 内の全レース
        include_selected_bets: True で既存 betting_selector を適用し selected_bets を付与
        betting_strategy: single / top_n / threshold / ev。None 時は config または single
        betting_top_n: strategy=top_n の N
        betting_score_threshold: strategy=threshold の閾値
        betting_ev_threshold: strategy=ev の閾値

    Returns:
        prediction_tool と同形式。include_selected_bets 時は selected_bets 付きで verify(selected_bets) 可能。
    """
    data_dir = Path(data_dir)
    model_path_resolved = Path(model_path)
    model = load_baseline_model(model_path_resolved)
    saved_model_type = load_baseline_model_metadata(model_path_resolved)

    prefix = f"race_data_{prediction_date}_"
    race_files = sorted(data_dir.rglob("race_data_*.json"))
    predictions = []
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
            state = build_race_state_vector(race_data, None)
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
        _apply_selected_bets(predictions, strategy, top_n, score_threshold, ev_threshold)
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

    out = {
        "prediction_date": prediction_date,
        "model_info": {
            "model_type": "baseline_b",
            "model_path": str(model_path),
            "backend": saved_model_type or "sklearn",
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
