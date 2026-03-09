"""
ROI 改善用ロールング検証: DB 必須・window 数増・1 window ごと結果保存・summary 集計。

出力:
  outputs/rolling_validation_summary.json
  outputs/rolling_validation_windows.json
"""

import argparse
import json
import sqlite3
import statistics
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional, Tuple, Union

_THIS_DIR = Path(__file__).resolve().parent
_PROJECT_ROOT = _THIS_DIR.parent.parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from kyotei_predictor.tools.rolling_validation_windows import (
    _date_range,
    run_one_window,
)


def get_db_date_range(db_path: str) -> Tuple[str, str]:
    """DB の races テーブルから race_date の min/max を返す。"""
    with sqlite3.connect(db_path) as conn:
        row = conn.execute(
            "SELECT MIN(race_date), MAX(race_date) FROM races"
        ).fetchone()
    if not row or not row[0]:
        raise ValueError(f"No race_date in DB: {db_path}")
    return (row[0], row[1])


def build_windows(
    min_date: str,
    max_date: str,
    train_days: int,
    test_days: int,
    step_days: int,
    n_windows: int,
) -> List[Tuple[str, str, str, str]]:
    """(train_start, train_end, test_start, test_end) のリストを最大 n_windows 個返す。"""
    out: List[Tuple[str, str, str, str]] = []
    end_dt = datetime.strptime(max_date, "%Y-%m-%d")
    start_dt = datetime.strptime(min_date, "%Y-%m-%d")
    # 最初の test 期間を test_days で確保し、その直前に train 期間を train_days で確保
    train_end_dt = start_dt + timedelta(days=train_days - 1)
    test_start_dt = train_end_dt + timedelta(days=1)
    test_end_dt = test_start_dt + timedelta(days=test_days - 1)
    while test_end_dt <= end_dt and len(out) < n_windows:
        train_start = (test_start_dt - timedelta(days=train_days)).strftime("%Y-%m-%d")
        if train_start < min_date:
            train_start = min_date
        train_end = (test_start_dt - timedelta(days=1)).strftime("%Y-%m-%d")
        test_start = test_start_dt.strftime("%Y-%m-%d")
        test_end = test_end_dt.strftime("%Y-%m-%d")
        out.append((train_start, train_end, test_start, test_end))
        test_start_dt += timedelta(days=step_days)
        test_end_dt = test_start_dt + timedelta(days=test_days - 1)
    return out


def run_rolling_validation_roi(
    db_path: str,
    output_dir: Path,
    data_dir_raw: Path,
    train_days: int = 30,
    test_days: int = 7,
    step_days: int = 7,
    n_windows: int = 12,
    model: str = "baseline B",
    calibration: str = "sigmoid",
    strategy: str = "top_n_ev",
    top_n: int = 5,
    ev_threshold: float = 1.15,
    strategies: Optional[List[Tuple[str, str, int, Optional[float]]]] = None,
    model_type: Optional[str] = None,
    feature_set: Optional[str] = None,
    seed: int = 42,
) -> Tuple[Union[dict, List[dict]], Union[list, List[list]]]:
    """
    DB のみでロールング検証を実行し、各 window の結果と summary を返す。
    strategies を渡すと複数戦略を同一 train で比較し、
    (summaries のリスト, windows のリストのリスト) を返す。
    feature_set: 記録用（current_features / extended_features / extended_features_v2）。None のときは環境変数から取得。
    """
    import os as _os
    _feature_set = feature_set or _os.environ.get("KYOTEI_FEATURE_SET", "extended_features")
    if _feature_set == "extended_features" and _os.environ.get("KYOTEI_USE_MOTOR_WIN_PROXY", "0") == "0":
        _feature_set = "current_features"
    _model_type = model_type or "sklearn"
    min_date, max_date = get_db_date_range(db_path)
    windows = build_windows(
        min_date, max_date, train_days, test_days, step_days, n_windows
    )
    if not windows:
        raise ValueError(
            f"No windows in date range {min_date}..{max_date} "
            f"(train_days={train_days}, test_days={test_days}, step_days={step_days})"
        )

    if strategies is None:
        strategies = [(f"top_n_ev_ev{ev_threshold}", strategy, top_n, ev_threshold)]
    out_pred_dir = output_dir / "rolling_roi_predictions"
    out_pred_dir.mkdir(parents=True, exist_ok=True)
    model_path = output_dir / "rolling_roi_model.joblib"

    # 戦略ごとの window レコードを収集
    per_strategy_windows: List[list] = [[] for _ in strategies]
    for i, (ts, te, tst, tend) in enumerate(windows):
        row = run_one_window(
            train_start=ts,
            train_end=te,
            test_start=tst,
            test_end=tend,
            data_dir_raw=data_dir_raw,
            model_path=model_path,
            out_pred_dir=out_pred_dir,
            strategies=strategies,
            train_days=train_days,
            data_source="db",
            db_path=db_path,
            calibration=calibration,
            model_type=_model_type,
            feature_set=_feature_set,
            seed=seed,
        )
        for j, res in enumerate(row["results"]):
            if j >= len(per_strategy_windows):
                break
            rec = {
                "window_id": i + 1,
                "train_start": ts,
                "train_end": te,
                "test_start": tst,
                "test_end": tend,
                "model": model,
                "calibration": calibration,
                "strategy": res.get("strategy", strategy),
                "top_n": res.get("top_n", top_n),
                "ev_threshold": res.get("ev_threshold"),
                "selected_bets_count": res.get("selected_bets_total_count", 0),
                "selected_bets_total_count": res.get("selected_bets_total_count", 0),
                "total_bet_selected": res.get("total_bet_selected", 0),
                "total_payout_selected": res.get("total_payout_selected", 0),
                "roi_selected": res.get("roi_selected", 0.0),
                "hit_rate_rank1_pct": res.get("hit_rate_rank1_pct", 0.0),
                "odds_missing_count": res.get("odds_missing_count", 0),
                "races_with_result": res.get("races_with_result", 0),
                "races_with_selected_bets": res.get("races_with_selected_bets", 0),
                "log_loss": res.get("log_loss"),
                "brier_score": res.get("brier_score"),
            }
            per_strategy_windows[j].append(rec)

    def _summary(recs: list, strat: tuple) -> dict:
        rois = [r["roi_selected"] for r in recs]
        total_bet = sum(r["total_bet_selected"] for r in recs)
        total_payout = sum(r["total_payout_selected"] for r in recs)
        total_selected_bets = sum(r["selected_bets_total_count"] for r in recs)
        total_races_with_result = sum(r.get("races_with_result", 0) for r in recs)
        total_races_with_selected_bets = sum(r.get("races_with_selected_bets", 0) for r in recs)
        overall_roi = round((total_payout / total_bet - 1) * 100, 2) if total_bet else 0.0
        log_losses = [r["log_loss"] for r in recs if r.get("log_loss") is not None]
        briers = [r["brier_score"] for r in recs if r.get("brier_score") is not None]
        name, s, tn, ev = strat[0], strat[1], strat[2], strat[3]
        confidence_type = strat[4] if len(strat) >= 5 else None
        out = {
            "model_type": _model_type,
            "model": model,
            "calibration": calibration,
            "feature_set": _feature_set,
            "strategy": s,
            "strategy_name": name,
            "top_n": tn,
            "ev_threshold": ev,
            "seed": seed,
            "n_windows": len(recs),
            "number_of_windows": len(recs),
            "train_days": train_days,
            "test_days": test_days,
            "step_days": step_days,
            "date_range": {"min": min_date, "max": max_date},
            "overall_roi_selected": overall_roi,
            "mean_roi_selected": round(statistics.mean(rois), 2) if rois else None,
            "median_roi_selected": round(statistics.median(rois), 2) if rois else None,
            "std_roi_selected": round(statistics.stdev(rois), 2) if len(rois) > 1 else None,
            "min_roi_selected": round(min(rois), 2) if rois else None,
            "max_roi_selected": round(max(rois), 2) if rois else None,
            "total_selected_bets": total_selected_bets,
            "total_bet_selected": round(total_bet, 2),
            "total_payout_selected": round(total_payout, 2),
            "selected_race_count": total_races_with_selected_bets,
            "total_evaluated_races": total_races_with_result,
            "selected_race_ratio": round(total_races_with_selected_bets / total_races_with_result, 4) if total_races_with_result else None,
            "avg_bets_per_selected_race": round(total_selected_bets / total_races_with_selected_bets, 2) if total_races_with_selected_bets else None,
        }
        if confidence_type is not None:
            out["confidence_type"] = confidence_type
        if s == "top_n_ev_prob_pool" and len(strat) >= 6 and strat[5] is not None:
            out["pool_k"] = int(strat[5])
        elif s == "top_n_ev_power_prob" and len(strat) >= 6 and strat[5] is not None:
            out["alpha"] = float(strat[5])
        elif len(strat) >= 7 and strat[5] is not None:
            out["prob_gap_min"] = strat[5]
        if len(strat) >= 7 and strat[6] is not None:
            out["entropy_max"] = strat[6]
        if log_losses:
            out["mean_log_loss"] = round(statistics.mean(log_losses), 6)
        else:
            out["mean_log_loss"] = None
        if briers:
            out["mean_brier_score"] = round(statistics.mean(briers), 6)
        else:
            out["mean_brier_score"] = None
        hr1_list = [r.get("hit_rate_rank1_pct") for r in recs if r.get("hit_rate_rank1_pct") is not None]
        out["hit_rate_rank1_pct"] = round(statistics.mean(hr1_list), 2) if hr1_list else None
        return out

    if len(strategies) == 1:
        summary = _summary(per_strategy_windows[0], strategies[0])
        return summary, per_strategy_windows[0]

    summaries = [_summary(per_strategy_windows[j], strategies[j]) for j in range(len(strategies))]
    return summaries, per_strategy_windows


def main() -> int:
    parser = argparse.ArgumentParser(description="Rolling validation for ROI (DB only)")
    parser.add_argument("--db-path", required=True, help="SQLite DB path (races)")
    parser.add_argument("--output-dir", type=Path, default=Path("outputs"))
    parser.add_argument("--data-dir", type=Path, default=None)
    parser.add_argument("--train-days", type=int, default=30)
    parser.add_argument("--test-days", type=int, default=7)
    parser.add_argument("--step-days", type=int, default=7)
    parser.add_argument("--n-windows", type=int, default=12)
    parser.add_argument("--top-n", type=int, default=5)
    parser.add_argument("--ev-threshold", type=float, default=1.15)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    raw_dir = args.data_dir
    if raw_dir is None:
        raw_dir = _PROJECT_ROOT / "kyotei_predictor" / "data" / "raw"
    if not raw_dir.is_dir():
        raw_dir = Path("kyotei_predictor/data/raw")
    if not raw_dir.is_dir():
        print("data_dir not found:", raw_dir, file=sys.stderr)
        return 1

    args.output_dir.mkdir(parents=True, exist_ok=True)
    summary, windows = run_rolling_validation_roi(
        db_path=args.db_path,
        output_dir=args.output_dir,
        data_dir_raw=raw_dir,
        train_days=args.train_days,
        test_days=args.test_days,
        step_days=args.step_days,
        n_windows=args.n_windows,
        top_n=args.top_n,
        ev_threshold=args.ev_threshold,
        seed=args.seed,
    )

    summary_path = args.output_dir / "rolling_validation_summary.json"
    windows_path = args.output_dir / "rolling_validation_windows.json"
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    with open(windows_path, "w", encoding="utf-8") as f:
        json.dump({"windows": windows}, f, ensure_ascii=False, indent=2)
    print("Saved", summary_path, "and", windows_path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
