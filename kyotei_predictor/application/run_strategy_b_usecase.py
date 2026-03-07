"""
主戦略（baseline B + sigmoid + top_n=5 + EV>=1.15 + fixed）の 1 本化フロー。

学習 → 予測（selected_bets 付与）→ 検証 → サマリ保存 を一括実行する。
再現手順を固定し、別期間での再検証にも利用する。
"""

import json
from pathlib import Path
from typing import Any, Dict, Optional, Union


# 主戦略の固定パラメータ（EV_BETTING_STRATEGY.md と一致）
STRATEGY_B_CALIBRATION = "sigmoid"
STRATEGY_B_STRATEGY = "top_n_ev"
STRATEGY_B_TOP_N = 5
STRATEGY_B_EV_THRESHOLD = 1.15
STRATEGY_B_BET_SIZING = "fixed"
STRATEGY_B_EVALUATION_MODE = "selected_bets"


def run_strategy_b(
    train_start: str,
    train_end: str,
    predict_date: str,
    data_dir_raw: Path,
    model_save_path: Optional[Path] = None,
    output_dir: Optional[Path] = None,
    data_source: Optional[str] = None,
    db_path: Optional[Union[str, Path]] = None,
) -> Dict[str, Any]:
    """
    主戦略で 学習 → 予測 → 検証 を一括実行し、サマリと実行条件を返す。

    Args:
        train_start: 学習開始日 YYYY-MM-DD
        train_end: 学習終了日 YYYY-MM-DD
        predict_date: 予測対象日 YYYY-MM-DD（1 日分）
        data_dir_raw: 生データルート（月別サブディレクトリ YYYY-MM を想定）
        model_save_path: モデル保存先。None のとき output_dir または data_dir_raw の親基準で自動生成
        output_dir: 予測 JSON とサマリの出力先。None のとき data_dir_raw の親の outputs/strategy_b
        data_source: "json" | "db" | None
        db_path: data_source=db 時の DB パス

    Returns:
        {
            "summary": 検証サマリ辞書,
            "conditions": 実行条件,
            "prediction_path": 予測 JSON パス,
            "model_path": モデル保存パス,
            "evaluation_mode": "selected_bets",
        }
    """
    from kyotei_predictor.application.baseline_train_usecase import run_baseline_train
    from kyotei_predictor.application.baseline_predict_usecase import run_baseline_predict
    from kyotei_predictor.application.verify_usecase import run_verify

    data_dir_raw = Path(data_dir_raw)
    if output_dir is None:
        output_dir = data_dir_raw.parent / "outputs" / "strategy_b"
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    if model_save_path is None:
        model_save_path = output_dir / "strategy_b_model.joblib"
    else:
        model_save_path = Path(model_save_path)

    # 1. 学習（calibration=sigmoid）
    run_baseline_train(
        data_dir=data_dir_raw,
        model_save_path=model_save_path,
        max_samples=50000,
        train_start=train_start,
        train_end=train_end,
        data_source=data_source,
        db_path=db_path,
        calibration=STRATEGY_B_CALIBRATION,
    )

    # 2. 予測（主戦略パラメータ）
    month = predict_date[:7]
    data_dir_month = data_dir_raw / month
    if not data_dir_month.exists():
        data_dir_month = data_dir_raw

    pred_path = output_dir / f"predictions_strategy_b_{predict_date}.json"
    result = run_baseline_predict(
        model_path=model_save_path,
        data_dir=data_dir_month,
        prediction_date=predict_date,
        include_selected_bets=True,
        betting_strategy=STRATEGY_B_STRATEGY,
        betting_top_n=STRATEGY_B_TOP_N,
        betting_score_threshold=None,
        betting_ev_threshold=STRATEGY_B_EV_THRESHOLD,
        data_source=data_source,
        db_path=db_path,
    )
    with open(pred_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    # 3. 検証（selected_bets）
    summary, details = run_verify(
        pred_path,
        data_dir_month,
        evaluation_mode=STRATEGY_B_EVALUATION_MODE,
        data_source=data_source,
        db_path=db_path,
    )

    conditions = {
        "model": "baseline_b",
        "calibration": STRATEGY_B_CALIBRATION,
        "strategy": STRATEGY_B_STRATEGY,
        "top_n": STRATEGY_B_TOP_N,
        "ev_threshold": STRATEGY_B_EV_THRESHOLD,
        "bet_sizing": STRATEGY_B_BET_SIZING,
        "evaluation_mode": STRATEGY_B_EVALUATION_MODE,
        "train_start": train_start,
        "train_end": train_end,
        "predict_date": predict_date,
    }

    # 4. サマリ保存（実行条件付き）
    summary_path = output_dir / f"strategy_b_summary_{predict_date}.json"
    to_save = {
        "conditions": conditions,
        "summary": summary,
        "prediction_path": str(pred_path),
        "model_path": str(model_save_path),
    }
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(to_save, f, ensure_ascii=False, indent=2)

    run_result = {
        "summary": summary,
        "conditions": conditions,
        "prediction_path": str(pred_path),
        "summary_path": str(summary_path),
        "model_path": str(model_save_path),
        "evaluation_mode": STRATEGY_B_EVALUATION_MODE,
    }
    return run_result
