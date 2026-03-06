"""
予測ユースケース: 指定日の予測を実行する。

TODO: 現状は tools.prediction_tool が実装を保持。段階的に application に寄せる。
"""

from pathlib import Path
from typing import Any, Dict, Optional


def run_predict(
    predict_date: str,
    data_dir: Optional[Path] = None,
    data_source: str = "db",
    venues: Optional[list] = None,
    **kwargs: Any,
) -> Optional[Dict]:
    """
    指定日の予測を実行し、結果辞書を返す。

    Args:
        predict_date: 予測対象日 (YYYY-MM-DD)
        data_dir: データディレクトリ（data_source=file のとき）
        data_source: "file" | "db"
        venues: 対象会場リスト（None で全会場）
        **kwargs: その他 prediction_tool に渡すオプション

    Returns:
        予測結果の辞書。失敗時は None。
    """
    # TODO: tools.prediction_tool の処理を application に移し、ここから呼ぶ
    from kyotei_predictor.tools.prediction_tool import PredictionTool
    import logging
    tool = PredictionTool(logging.INFO, data_dir=str(data_dir) if data_dir else None, data_source=data_source)
    result = tool.predict_races(predict_date, venues, include_selected_bets=kwargs.get("include_selected_bets", False))
    if result:
        _ = tool.save_prediction_result(result, kwargs.get("output_dir"))
    return result
