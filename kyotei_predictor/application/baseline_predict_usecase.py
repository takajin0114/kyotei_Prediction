"""
B案ベースラインの予測ユースケース。

学習済みモデルを読み、指定日の race_data に対して 3連単スコアを出力する。
既存の prediction 形式（all_combinations, venue, race_number）に合わせ、
verify_predictions / betting_selector にそのまま渡せる形で返す。
"""

from pathlib import Path
from typing import Any, Dict, List, Optional

from kyotei_predictor.infrastructure.file_loader import load_json
from kyotei_predictor.infrastructure.baseline_model_repository import load_baseline_model
from kyotei_predictor.infrastructure.baseline_model_runner import (
    predict_proba_120,
    scores_to_all_combinations,
)
from kyotei_predictor.pipelines.state_vector import build_race_state_vector


def run_baseline_predict(
    model_path: Path,
    data_dir: Path,
    prediction_date: str,
    venues: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    B案ベースラインで予測を実行し、A案と同一形式の予測辞書を返す。

    Args:
        model_path: 学習済みモデルのパス
        data_dir: race_data_*.json が入ったディレクトリ
        prediction_date: 予測日 YYYY-MM-DD（ファイル名の日付部分に使う）
        venues: 対象会場リスト。None の場合は data_dir 内の全レース

    Returns:
        prediction_tool と同形式: prediction_date, predictions[{ venue, race_number, all_combinations }],
        model_info, execution_summary
    """
    data_dir = Path(data_dir)
    model = load_baseline_model(Path(model_path))

    prefix = f"race_data_{prediction_date}_"
    race_files = sorted(data_dir.rglob("race_data_*.json"))
    predictions = []
    for path in race_files:
        if not path.name.startswith(prefix):
            continue
        # race_data_2024-05-01_KIRYU_R1.json -> venue=KIRYU, race_number=1
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
        predictions.append({
            "venue": venue or path.stem,
            "race_number": race_number,
            "all_combinations": all_combinations,
        })

    return {
        "prediction_date": prediction_date,
        "model_info": {"model_type": "baseline_b", "model_path": str(model_path)},
        "execution_summary": {
            "total_races": len(predictions),
            "successful_predictions": len(predictions),
        },
        "predictions": predictions,
    }
