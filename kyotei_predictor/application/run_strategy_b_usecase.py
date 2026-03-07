"""
主戦略（baseline B + sigmoid + top_n=5 + EV>=1.15 + fixed）の 1 本化フロー。

学習 → 予測（selected_bets 付与）→ 検証 → サマリ保存 を一括実行する。
再現手順を固定し、別期間での再検証にも利用する。
run ごとの実験条件を完全保存し、再現性の切り分けに使う。
"""

import hashlib
import json
import os
import subprocess
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional, Union


def _db_snapshot_version(db_path: Optional[Union[str, Path]]) -> Optional[str]:
    """DB ファイルの mtime を ISO 文字列で返す。再現性確認用。"""
    if db_path is None:
        return None
    path = Path(db_path)
    if not path.is_file():
        return None
    try:
        mtime = os.path.getmtime(path)
        return datetime.fromtimestamp(mtime, tz=timezone.utc).isoformat()
    except OSError:
        return None


def _get_git_commit_hash() -> Optional[str]:
    """git rev-parse HEAD でコミットハッシュを取得。取得できない場合は None。"""
    try:
        out = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            timeout=2,
            cwd=Path(__file__).resolve().parent.parent.parent,
        )
        if out.returncode == 0 and out.stdout:
            return out.stdout.strip()[:40]
    except Exception:
        pass
    return None


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
    seed: Optional[int] = 42,
    max_samples: Optional[int] = 50000,
    sample_mode: str = "head",
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
        seed: 乱数シード。再現性用。None のときは 42。
        max_samples: 最大学習サンプル数。sample_mode=all のときは無視。既定 50000。
        sample_mode: "head" | "random" | "all"。既定 "head"。

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
    if db_path is not None and data_source is None:
        data_source = "db"
    if output_dir is None:
        output_dir = data_dir_raw.parent / "outputs" / "strategy_b"
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    if model_save_path is None:
        model_save_path = output_dir / "strategy_b_model.joblib"
    else:
        model_save_path = Path(model_save_path)

    # 1. 学習（calibration=sigmoid, seed 固定）
    if seed is None:
        seed = 42
    train_result = run_baseline_train(
        data_dir=data_dir_raw,
        model_save_path=model_save_path,
        max_samples=max_samples,
        sample_mode=sample_mode,
        train_start=train_start,
        train_end=train_end,
        data_source=data_source,
        db_path=db_path,
        calibration=STRATEGY_B_CALIBRATION,
        seed=seed,
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

    # 再現性診断: verify 詳細を JSON で保存（Task 5）
    verify_details_path = output_dir / f"verify_details_{predict_date}.json"
    verify_details_hash: Optional[str] = None
    try:
        verify_details = {
            "evaluated_race_count": summary.get("evaluated_race_count"),
            "races_with_predictions": summary.get("races_with_predictions"),
            "races_with_odds": summary.get("races_with_odds"),
            "races_with_selected_bets": summary.get("races_with_selected_bets"),
            "skipped_race_count": summary.get("skipped_race_count"),
            "skip_reasons": summary.get("skip_reasons"),
            "selected_bets_total_count": summary.get("selected_bets_total_count"),
            "bets_per_date": summary.get("bets_per_date"),
            "details_count": len(details),
            "skipped_race_identifiers": summary.get("skipped_race_identifiers", {}),
            "details": details,
        }
        payload = {k: v for k, v in verify_details.items() if k != "verify_details_hash"}
        verify_details_hash = hashlib.sha256(
            json.dumps(payload, sort_keys=True, ensure_ascii=False, default=str).encode()
        ).hexdigest()[:16]
        verify_details["verify_details_hash"] = verify_details_hash
        with open(verify_details_path, "w", encoding="utf-8") as f:
            json.dump(verify_details, f, ensure_ascii=False, indent=2, default=str)
    except Exception:
        verify_details_path = None

    total_bet_selected = summary.get("total_bet_selected") or summary.get("total_bet") or 0
    total_payout_selected = summary.get("total_payout_selected") or 0
    roi_selected = summary.get("roi_pct")
    selected_bets_count = int(total_bet_selected / 100) if total_bet_selected else 0
    predict_race_count = len(result.get("predictions") or [])
    run_id = uuid.uuid4().hex[:12]
    summary_created_at = datetime.now(timezone.utc).isoformat()

    # 再現性切り分け用: run ごとの実験条件を完全保存（Task 1）
    conditions = {
        "run_id": run_id,
        "train_start": train_start,
        "train_end": train_end,
        "predict_date": predict_date,
        "model": "baseline_b",
        "calibration": STRATEGY_B_CALIBRATION,
        "strategy": STRATEGY_B_STRATEGY,
        "top_n": STRATEGY_B_TOP_N,
        "ev_threshold": STRATEGY_B_EV_THRESHOLD,
        "bet_sizing": STRATEGY_B_BET_SIZING,
        "evaluation_mode": STRATEGY_B_EVALUATION_MODE,
        "seed": seed,
        "max_samples": max_samples,
        "sample_mode": sample_mode,
        "data_source": data_source or "json",
        "db_path": str(db_path) if db_path is not None else None,
        "data_dir": str(data_dir_raw),
        "train_data_source": data_source or "json",
        "predict_data_source": data_source or "json",
        "verify_data_source": data_source or "json",
        "odds_data_source": data_source or "json",
        "result_data_source": data_source or "json",
        "db_table_names": ["races", "odds"] if data_source == "db" else None,
        "db_snapshot_version": _db_snapshot_version(db_path) if data_source == "db" else None,
        "query_date_range": f"{train_start}..{predict_date}" if data_source == "db" else None,
        "train_sample_count": train_result.get("n_samples"),
        "train_file_count": train_result.get("train_file_count"),
        "train_first_date": train_result.get("train_first_date"),
        "train_last_date": train_result.get("train_last_date"),
        "train_file_manifest_path": train_result.get("train_file_manifest_path"),
        "train_file_manifest_hash": train_result.get("train_file_manifest_hash"),
        "verify_details_hash": verify_details_hash,
        "predict_race_count": predict_race_count,
        "odds_missing_count": summary.get("odds_missing_count"),
        "selected_bets_count": selected_bets_count,
        "total_bet_selected": total_bet_selected,
        "total_payout_selected": total_payout_selected,
        "roi_selected": roi_selected,
        "git_commit_hash": _get_git_commit_hash(),
        "model_path": str(model_save_path),
        "verify_details_path": str(verify_details_path) if verify_details_path else None,
        "summary_created_at": summary_created_at,
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
        json.dump(to_save, f, ensure_ascii=False, indent=2, default=str)

    run_result = {
        "summary": summary,
        "conditions": conditions,
        "prediction_path": str(pred_path),
        "summary_path": str(summary_path),
        "model_path": str(model_save_path),
        "evaluation_mode": STRATEGY_B_EVALUATION_MODE,
    }
    return run_result
