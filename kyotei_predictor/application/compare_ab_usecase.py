"""
A/B比較ユースケース: 同一条件で A案・B案の予測を検証し、結果を並べて出力する。

同一の data_dir / evaluation_mode で verify を実行。
data_source=db 時は検証用 race_data を DB から取得する。
"""

from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

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
    data_source: Optional[str] = None,
    db_path: Optional[Union[str, Path]] = None,
) -> List[Dict[str, Any]]:
    """
    2つの予測ファイルを同一条件で検証し、比較用の行リストを返す。

    Args:
        prediction_a_path: A案の予測 JSON パス
        prediction_b_path: B案の予測 JSON パス
        data_dir: race_data / odds_data のディレクトリ
        evaluation_mode: "first_only" または "selected_bets"
        model_name_a / model_name_b: 比較表の表示名
        data_source: "json" | "db" | None。検証時の race_data 読込元。
        db_path: data_source=db 時の SQLite パス。

    Returns:
        比較行のリスト。
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
            summary, _ = run_verify(
                path,
                data_dir,
                evaluation_mode=evaluation_mode,
                data_source=data_source,
                db_path=db_path,
            )
            results.append(_summary_to_row(path, summary, approach, model_name=name))
        except Exception as e:
            results.append({
                "model_name": name,
                "approach": approach,
                "error": str(e),
            })

    return results


def run_compare_ab_multi(
    prediction_specs: List[Tuple[Path, str, str]],
    data_dir: Path,
    evaluation_mode: str = "first_only",
    data_source: Optional[str] = None,
    db_path: Optional[Union[str, Path]] = None,
) -> List[Dict[str, Any]]:
    """
    複数予測ファイルを同一条件で検証し、比較用の行リストを返す。

    Args:
        prediction_specs: [(予測JSONパス, 表示名, approach), ...]
        data_dir: race_data / odds_data のディレクトリ
        evaluation_mode: "first_only" または "selected_bets"
        data_source: "json" | "db" | None
        db_path: data_source=db 時の SQLite パス

    Returns:
        比較行のリスト。
    """
    data_dir = Path(data_dir)
    results = []
    for path, name, approach in prediction_specs:
        path = Path(path)
        if not path.exists():
            results.append({"model_name": name, "approach": approach, "error": f"ファイルが存在しません: {path}"})
            continue
        try:
            summary, _ = run_verify(
                path,
                data_dir,
                evaluation_mode=evaluation_mode,
                data_source=data_source,
                db_path=db_path,
            )
            results.append(_summary_to_row(path, summary, approach, model_name=name))
        except Exception as e:
            results.append({"model_name": name, "approach": approach, "error": str(e)})
    return results
