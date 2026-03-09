#!/usr/bin/env python3
"""
EXP-0006: XGBoost + sigmoid + extended_features で top_n × ev_threshold 2D grid、
bet sizing 比較、xgboost vs lightgbm 再比較。
リポジトリルートで実行。
"""

import argparse
import json
import os
import sys
from pathlib import Path

_SCRIPT_DIR = Path(__file__).resolve().parent
_PROJECT_ROOT = _SCRIPT_DIR.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

os.environ["KYOTEI_USE_MOTOR_WIN_PROXY"] = os.environ.get("KYOTEI_USE_MOTOR_WIN_PROXY", "1")
os.environ["KYOTEI_FEATURE_SET"] = os.environ.get("KYOTEI_FEATURE_SET", "extended_features")

from kyotei_predictor.tools.rolling_validation_roi import (
    run_rolling_validation_roi,
    get_db_date_range,
    build_windows,
)
from kyotei_predictor.tools.rolling_validation_windows import _date_range
from kyotei_predictor.application.verify_usecase import run_verify
from kyotei_predictor.betting.bankroll_simulation import (
    simulate_bankroll,
    build_bet_list_from_verify,
)
from kyotei_predictor.infrastructure.file_loader import load_json

TOP_N_VALS = [3, 5, 6, 8]
EV_THRESHOLDS = [1.05, 1.10, 1.15, 1.20, 1.25]
N_WINDOWS = 12
TRAIN_DAYS = 30
TEST_DAYS = 7
STEP_DAYS = 7


def _max_drawdown_from_windows(windows: list) -> float:
    cum = 0.0
    peak = 0.0
    max_dd = 0.0
    for w in windows:
        tb = w.get("total_bet_selected") or 0
        tp = w.get("total_payout_selected") or 0
        cum += (tp - tb) if tb else 0
        if cum > peak:
            peak = cum
        dd = peak - cum
        if dd > max_dd:
            max_dd = dd
    return round(max_dd, 2)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db-path", required=True)
    parser.add_argument("--output-dir", type=Path, default=None)
    parser.add_argument("--n-windows", type=int, default=N_WINDOWS)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    raw_dir = _PROJECT_ROOT / "kyotei_predictor" / "data" / "raw"
    if not raw_dir.is_dir():
        raw_dir = Path("kyotei_predictor/data/raw")
    output_dir = args.output_dir or _PROJECT_ROOT / "outputs"
    output_dir.mkdir(parents=True, exist_ok=True)
    pred_dir = output_dir / "rolling_roi_predictions"

    # --- Task1: top_n × ev_threshold grid ---
    strategies_grid = []
    for tn in TOP_N_VALS:
        for ev in EV_THRESHOLDS:
            strategies_grid.append((f"top{tn}_ev{int(ev*100)}", "top_n_ev", tn, ev))

    print("Task1: top_n × ev_threshold grid (XGBoost)...")
    summaries_grid, per_strategy_windows = run_rolling_validation_roi(
        db_path=args.db_path,
        output_dir=output_dir,
        data_dir_raw=raw_dir,
        train_days=TRAIN_DAYS,
        test_days=TEST_DAYS,
        step_days=STEP_DAYS,
        n_windows=args.n_windows,
        strategies=strategies_grid,
        model_type="xgboost",
        calibration="sigmoid",
        feature_set="extended_features",
        seed=args.seed,
    )

    grid_results = []
    for s, windows in zip(summaries_grid, per_strategy_windows):
        tb = s.get("total_bet_selected") or 0
        tp = s.get("total_payout_selected") or 0
        profit = round(tp - tb, 2) if tb else 0.0
        max_dd = _max_drawdown_from_windows(windows)
        grid_results.append({
            "top_n": s["top_n"],
            "ev_threshold": s["ev_threshold"],
            "overall_roi_selected": s["overall_roi_selected"],
            "mean_roi_selected": s.get("mean_roi_selected"),
            "median_roi_selected": s.get("median_roi_selected"),
            "std_roi_selected": s.get("std_roi_selected"),
            "total_selected_bets": s.get("total_selected_bets") or 0,
            "profit": profit,
            "max_drawdown": max_dd,
        })

    best = max(grid_results, key=lambda x: x["overall_roi_selected"])
    best_top_n, best_ev = best["top_n"], best["ev_threshold"]
    print(f"Best: top_n={best_top_n} ev={best_ev} roi={best['overall_roi_selected']}%")

    # --- Task2: bet sizing comparison (using best params) ---
    min_date, max_date = get_db_date_range(args.db_path)
    windows_list = build_windows(
        min_date, max_date, TRAIN_DAYS, TEST_DAYS, STEP_DAYS, args.n_windows
    )
    all_bets = []
    for ts, te, tst, tend in windows_list:
        for day in _date_range(tst, tend):
            month = day[:7]
            data_dir_month = raw_dir / month
            path = pred_dir / f"predictions_baseline_{day}_top{best_top_n}ev{int(best_ev*100)}.json"
            if not path.exists() or not data_dir_month.exists():
                continue
            try:
                pred = load_json(path)
                predictions = pred.get("predictions") or []
                summary, details = run_verify(
                    path,
                    data_dir_month,
                    evaluation_mode="selected_bets",
                    data_source="db",
                    db_path=args.db_path,
                )
                bets = build_bet_list_from_verify(predictions, details, fixed_stake=100.0)
                all_bets.extend(bets)
            except Exception:
                pass

    bet_sizing_results = []
    for sizing in ["fixed", "half_kelly", "capped_kelly_0.02", "capped_kelly_0.05"]:
        sim = simulate_bankroll(
            all_bets,
            initial_bankroll=100_000.0,
            bet_sizing=sizing,
            unit_stake=100.0,
        )
        bet_sizing_results.append({
            "bet_sizing": sizing,
            "overall_roi_selected": sim["roi_pct"],
            "total_stake": sim["total_stake"],
            "total_payout": sim["total_payout"],
            "profit": round(sim["total_payout"] - sim["total_stake"], 2),
            "max_drawdown": sim["max_drawdown"],
            "bet_count": sim["bet_count"],
        })
    print("Task2: bet sizing done.")

    # --- Task3: xgboost vs lightgbm (別 output_dir で予測を分離) ---
    strat_best = [(f"top{best_top_n}_ev{int(best_ev*100)}", "top_n_ev", best_top_n, best_ev)]
    model_comparison = []
    for mtype in ["xgboost", "lightgbm"]:
        out_sub = output_dir / f"model_compare_{mtype}"
        out_sub.mkdir(parents=True, exist_ok=True)
        summ, _ = run_rolling_validation_roi(
            db_path=args.db_path,
            output_dir=out_sub,
            data_dir_raw=raw_dir,
            train_days=TRAIN_DAYS,
            test_days=TEST_DAYS,
            step_days=STEP_DAYS,
            n_windows=args.n_windows,
            strategies=strat_best,
            model_type=mtype,
            calibration="sigmoid",
            feature_set="extended_features",
            seed=args.seed,
        )
        s = summ[0] if isinstance(summ, list) else summ
        model_comparison.append({
            "model": mtype,
            "overall_roi_selected": s.get("overall_roi_selected"),
            "mean_roi_selected": s.get("mean_roi_selected"),
            "std_roi_selected": s.get("std_roi_selected"),
            "total_selected_bets": s.get("total_selected_bets") or 0,
            "mean_log_loss": s.get("mean_log_loss"),
            "mean_brier_score": s.get("mean_brier_score"),
        })
    print("Task3: model comparison done.")

    out = {
        "experiment_id": "EXP-0006",
        "model": "xgboost",
        "calibration": "sigmoid",
        "features": "extended_features",
        "n_windows": args.n_windows,
        "seed": args.seed,
        "grid": grid_results,
        "best_top_n": best_top_n,
        "best_ev_threshold": best_ev,
        "bet_sizing_comparison": bet_sizing_results,
        "model_comparison": model_comparison,
    }
    out_path = output_dir / "exp0006_xgb_strategy_grid_and_bet_sizing.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    print(f"Saved {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
