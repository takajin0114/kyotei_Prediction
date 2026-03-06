"""
学習→予測→検証の一連実行ユースケース。

1 つの Python 関数で 学習 → 予測 → 検証 を順に実行する。
"""

from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


def run_cycle(
    year_month: str,
    predict_date: str,
    data_dir: Path,
    evaluation_mode: str = "first_only",
    n_trials: int = 1,
    minimal_mode: bool = True,
    data_source: str = "file",
) -> Tuple[Optional[Dict], Optional[Dict], Optional[Dict], List[Dict]]:
    """
    学習 → 予測 → 検証 を順に実行する。

    Args:
        year_month: 学習用年月 (YYYY-MM)
        predict_date: 予測対象日 (YYYY-MM-DD)
        data_dir: データディレクトリ
        evaluation_mode: 検証モード "first_only" | "selected_bets"
        n_trials: 最適化の試行回数（1 で短時間）
        minimal_mode: True で最小限の学習
        data_source: "file" | "db"

    Returns:
        (学習結果の Study 相当, 予測結果辞書, 検証 summary, 検証 details)
        いずれも失敗時は None / 空リスト。
    """
    study = None
    pred_result = None
    summary = None
    details: List[Dict] = []

    # 1. 学習（最適化）
    try:
        from kyotei_predictor.application.optimize_usecase import run_optimize
        study = run_optimize(
            n_trials=n_trials,
            year_month=year_month,
            minimal_mode=minimal_mode,
            data_dir=data_dir,
            data_source=data_source,
        )
    except Exception as e:
        # TODO: ログ出力
        raise

    # 2. 予測
    try:
        from kyotei_predictor.application.predict_usecase import run_predict
        pred_result = run_predict(
            predict_date=predict_date,
            data_dir=data_dir,
            data_source=data_source,
        )
    except Exception as e:
        raise

    # 3. 検証（予測結果がある場合）
    if pred_result and data_dir is not None:
        from kyotei_predictor.application.verify_usecase import run_verify
        from kyotei_predictor.infrastructure.path_manager import PROJECT_ROOT
        # 予測JSONは prediction_tool が outputs/predictions_*.json に保存する想定
        pred_path = PROJECT_ROOT / "outputs" / f"predictions_{predict_date}.json"
        if pred_path.exists():
            summary, details = run_verify(pred_path, data_dir, evaluation_mode=evaluation_mode)

    return study, pred_result, summary, details
