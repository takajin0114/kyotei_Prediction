"""
A/B比較ユースケース: 同一条件で A案・B案の予測を検証し、結果を並べて出力する。

同一の data_dir / evaluation_mode で verify を実行し、
model_name, approach, betting_strategy, hit_rate, roi_pct 等を一覧する。
"""

from pathlib import Path
from typing import Any, Dict, List, Optional

from kyotei_predictor.application.verify_usecase import run_verify
from kyotei_predictor.infrastructure.file_loader import load_json


def _summary_to_row(
    prediction_path: Path,
    summary: Dict[str, Any],
    approach: str,
    model_name: Optional[str] = None,
) -> Dict[str, Any]:
    """検証 summary を比較用の1行（辞書）に変換する。"""
    try:
        payload = load_json(prediction_path)
    except Exception:
        payload = {}
    info = payload.get("model_info") or {}
    exec_summary = payload.get("execution_summary") or {}
    display_name = model_name or info.get("model_path", str(prediction_path))
    betting = exec_summary.get("betting_strategy") if summary.get("evaluation_mode") == "selected_bets" else None
    return {
        "model_name": display_name,
        "approach": approach,
        "betting_strategy": betting or ("first_only" if summary.get("evaluation_mode") == "first_only" else "selected_bets"),
        "evaluation_mode": summary.get("evaluation_mode", "first_only"),
        "hit_rate_rank1_pct": summary.get("hit_rate_rank1_pct"),
        "hit_rate_top3_pct": summary.get("hit_rate_top3_pct"),
        "roi_pct": summary.get("roi_pct"),
        "total_bet": summary.get("total_bet"),
        "total_payout": summary.get("total_payout"),
        "hit_count": summary.get("hit_count"),
        "races_with_result": summary.get("races_with_result"),
    }


def run_compare_ab(
    prediction_a_path: Path,
    prediction_b_path: Path,
    data_dir: Path,
    evaluation_mode: str = "first_only",
    model_name_a: str = "A",
    model_name_b: str = "B",
) -> List[Dict[str, Any]]:
    """
    2つの予測ファイルを同一条件で検証し、比較用の行リストを返す。

    Args:
        prediction_a_path: A案の予測 JSON パス（例: predictions_2024-05-01.json）
        prediction_b_path: B案の予測 JSON パス（例: predictions_baseline_2024-05-01.json）
        data_dir: race_data / odds_data のディレクトリ
        evaluation_mode: "first_only" または "selected_bets"
        model_name_a: 比較表の A の表示名
        model_name_b: 比較表の B の表示名

    Returns:
        比較行のリスト。各要素は model_name, approach, betting_strategy, evaluation_mode,
        hit_rate_rank1_pct, roi_pct, total_bet, total_payout, hit_count 等を持つ。
    """
    data_dir = Path(data_dir)
    results = []

    for path, approach, name in [
        (prediction_a_path, "A", model_name_a),
        (prediction_b_path, "B", model_name_b),
    ]:
        path = Path(path)
        if not path.exists():
            results.append({
                "model_name": name,
                "approach": approach,
                "error": f"ファイルが存在しません: {path}",
            })
            continue
        try:
            summary, _ = run_verify(path, data_dir, evaluation_mode=evaluation_mode)
            results.append(_summary_to_row(path, summary, approach, model_name=name))
        except Exception as e:
            results.append({
                "model_name": name,
                "approach": approach,
                "error": str(e),
            })

    return results
