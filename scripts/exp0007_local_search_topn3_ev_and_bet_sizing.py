#!/usr/bin/env python3
"""
EXP-0007: 正式 reference（top_n=3, ev=1.20）近傍最適化と bet sizing 正式比較。

Task1: top_n=3 固定で ev_threshold 高解像度探索 [1.18, 1.20, 1.22, 1.24, 1.25]。
Task2: Task1 最良条件で bet sizing 正式比較（fixed / half_kelly / capped_kelly_0.02 / capped_kelly_0.05）。

条件: xgboost, sigmoid, extended_features, top_n_ev, rolling, n_windows=12, seed=42。
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

TRAIN_DAYS = 30
TEST_DAYS = 7
STEP_DAYS = 7

# Task1: ev_threshold 候補（top_n=3 固定）
EV_VALUES = [1.18, 1.20, 1.22, 1.24, 1.25]
TOP_N = 3


def _run_ev_sweep(db_path, output_dir, raw_dir, n_windows, seed=42):
    strategies = [(f"top3_ev{int(ev * 100)}", "top_n_ev", TOP_N, ev) for ev in EV_VALUES]
    raw_summaries, raw_windows = run_rolling_validation_roi(
        db_path=db_path,
        output_dir=output_dir,
        data_dir_raw=raw_dir,
        train_days=TRAIN_DAYS,
        test_days=TEST_DAYS,
        step_days=STEP_DAYS,
        n_windows=n_windows,
        strategies=strategies,
        model_type="xgboost",
        calibration="sigmoid",
        feature_set="extended_features",
        seed=seed,
    )
    results = []
    for s, windows in zip(raw_summaries, raw_windows):
        tb = s.get("total_bet_selected") or 0
        tp = s.get("total_payout_selected") or 0
        profit = round(tp - tb, 2) if tb else 0.0
        cum, peak, max_dd = 0.0, 0.0, 0.0
        for w in windows:
            tbw = w.get("total_bet_selected") or 0
            tpw = w.get("total_payout_selected") or 0
            cum += (tpw - tbw) if tbw else 0
            if cum > peak:
                peak = cum
            if peak - cum > max_dd:
                max_dd = peak - cum
        results.append({
            "top_n": s["top_n"],
            "ev_threshold": s["ev_threshold"],
            "overall_roi_selected": s["overall_roi_selected"],
            "mean_roi_selected": s.get("mean_roi_selected"),
            "median_roi_selected": s.get("median_roi_selected"),
            "std_roi_selected": s.get("std_roi_selected"),
            "total_selected_bets": s.get("total_selected_bets") or 0,
            "profit": profit,
            "max_drawdown": round(max_dd, 2),
        })
    return results


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db-path", required=True, help="SQLite DB path")
    parser.add_argument("--output-dir", type=Path, default=None)
    parser.add_argument("--n-windows", type=int, default=12)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    raw_dir = _PROJECT_ROOT / "kyotei_predictor" / "data" / "raw"
    if not raw_dir.is_dir():
        raw_dir = Path("kyotei_predictor/data/raw")
    output_dir = args.output_dir or _PROJECT_ROOT / "outputs"
    output_dir.mkdir(parents=True, exist_ok=True)
    pred_dir = output_dir / "rolling_roi_predictions"

    # Task1: top_n=3, ev in [1.18, 1.20, 1.22, 1.24, 1.25]
    print("Task1: top_n=3 ev_threshold sweep [1.18, 1.20, 1.22, 1.24, 1.25] (n_w=12)...")
    task1_results = _run_ev_sweep(
        args.db_path, output_dir, raw_dir, args.n_windows, args.seed
    )
    for r in task1_results:
        print(
            f"  ev={r['ev_threshold']} -> roi={r['overall_roi_selected']}% "
            f"mean_roi={r.get('mean_roi_selected')} median_roi={r.get('median_roi_selected')} "
            f"std_roi={r.get('std_roi_selected')} total_bets={r['total_selected_bets']} "
            f"profit={r['profit']} max_dd={r['max_drawdown']}"
        )

    best = max(task1_results, key=lambda x: x["overall_roi_selected"])
    best_ev = best["ev_threshold"]
    print(f"Best selection: top_n={TOP_N} ev_threshold={best_ev} roi={best['overall_roi_selected']}%")

    # Task2: 最良条件で bet sizing 比較
    min_date, max_date = get_db_date_range(args.db_path)
    windows_list = build_windows(
        min_date, max_date, TRAIN_DAYS, TEST_DAYS, STEP_DAYS, args.n_windows
    )
    suffix = f"_top{TOP_N}ev{int(best_ev * 100)}"
    all_bets = []
    for ts, te, tst, tend in windows_list:
        for day in _date_range(tst, tend):
            month = day[:7]
            data_dir_month = raw_dir / month
            path = pred_dir / f"predictions_baseline_{day}{suffix}.json"
            if not path.exists() or not data_dir_month.exists():
                continue
            try:
                pred = load_json(path)
                predictions = pred.get("predictions") or []
                _, details = run_verify(
                    path, data_dir_month,
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
            all_bets, initial_bankroll=100_000.0,
            bet_sizing=sizing, unit_stake=100.0,
        )
        bet_sizing_results.append({
            "bet_sizing": sizing,
            "overall_roi_selected": sim["roi_pct"],
            "profit": round(sim["total_payout"] - sim["total_stake"], 2),
            "max_drawdown": sim["max_drawdown"],
            "total_selected_bets": sim["bet_count"],
        })
    print("Task2: bet sizing done.")

    out = {
        "experiment_id": "EXP-0007",
        "local_search_topn3_ev_and_bet_sizing": True,
        "model": "xgboost",
        "calibration": "sigmoid",
        "features": "extended_features",
        "strategy": "top_n_ev",
        "n_windows": args.n_windows,
        "seed": args.seed,
        "task1_top3_ev_sweep": task1_results,
        "best_ev_threshold": best_ev,
        "bet_sizing_comparison": bet_sizing_results,
    }
    out_path = output_dir / "exp0007_local_search_topn3_ev_and_bet_sizing.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    print(f"Saved {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
