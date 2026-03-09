#!/usr/bin/env python3
"""
EXP-0007 Betting strategy optimization.
Reference: xgboost + sigmoid + extended_features + top_n_ev, top_n=6, ev_threshold=1.05, ROI -19.71%.

Task1: Bet sizing comparison (selection fixed: top_n=6, ev=1.05).
  fixed / half_kelly / capped_kelly_0.02 / capped_kelly_0.05
Task2: top_n local search (ev=1.05 fixed). top_n in [4, 5, 6, 7].
Task3: Calibration comparison (none / sigmoid / isotonic). Same conditions.

n_windows=12, seed=42. リポジトリルートで実行。
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
REF_TOP_N = 6
REF_EV = 1.05


def _run_sweep(db_path, output_dir, raw_dir, n_windows, strategies, seed=42, calibration="sigmoid"):
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
        calibration=calibration,
        feature_set="extended_features",
        seed=seed,
    )
    if isinstance(raw_summaries, dict):
        summaries, per_windows = [raw_summaries], [raw_windows]
    else:
        summaries, per_windows = raw_summaries, raw_windows
    results = []
    for s, windows in zip(summaries, per_windows):
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
            "calibration": s.get("calibration", calibration),
            "overall_roi_selected": s["overall_roi_selected"],
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
    base_output = args.output_dir or _PROJECT_ROOT / "outputs"
    base_output.mkdir(parents=True, exist_ok=True)
    pred_dir = base_output / "rolling_roi_predictions"

    # Task1: Bet sizing (selection top_n=6, ev=1.05). First run rolling validation to get predictions.
    strategies_ref = [("top6_ev105", "top_n_ev", REF_TOP_N, REF_EV)]
    print("Task1: Running rolling validation for top_n=6, ev=1.05 (sigmoid)...")
    _run_sweep(
        args.db_path, base_output, raw_dir, args.n_windows,
        strategies_ref, args.seed, calibration="sigmoid",
    )
    suffix = f"_top{REF_TOP_N}ev{int(REF_EV * 100)}"
    min_date, max_date = get_db_date_range(args.db_path)
    windows_list = build_windows(
        min_date, max_date, TRAIN_DAYS, TEST_DAYS, STEP_DAYS, args.n_windows
    )
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
            "bet_count": sim["bet_count"],
        })
    print("Task1: bet sizing done.")

    # Task2: top_n local search [4, 5, 6, 7], ev=1.05
    strategies_topn = [(f"top{n}_ev105", "top_n_ev", n, REF_EV) for n in [4, 5, 6, 7]]
    print("Task2: top_n sweep [4, 5, 6, 7] ev=1.05...")
    task2_results = _run_sweep(
        args.db_path, base_output, raw_dir, args.n_windows,
        strategies_topn, args.seed, calibration="sigmoid",
    )
    for r in task2_results:
        print(f"  top_n={r['top_n']} -> roi={r['overall_roi_selected']}% profit={r['profit']}")

    # Task3: Calibration comparison (none / sigmoid / isotonic). Same selection top_n=6, ev=1.05.
    task3_results = []
    for cal in ["none", "sigmoid", "isotonic"]:
        out_sub = base_output / f"exp0007_calib_{cal}"
        out_sub.mkdir(parents=True, exist_ok=True)
        print(f"Task3: calibration={cal}...")
        res = _run_sweep(
            args.db_path, out_sub, raw_dir, args.n_windows,
            strategies_ref, args.seed, calibration=cal,
        )
        if res:
            r = res[0]
            r["calibration"] = cal
            task3_results.append(r)
    print("Task3: calibration comparison done.")

    out = {
        "experiment_id": "EXP-0007",
        "reference": {"top_n": REF_TOP_N, "ev_threshold": REF_EV, "roi": -19.71},
        "model": "xgboost",
        "features": "extended_features",
        "n_windows": args.n_windows,
        "seed": args.seed,
        "task1_bet_sizing": bet_sizing_results,
        "task2_topn_sweep": task2_results,
        "task3_calibration": task3_results,
    }
    out_path = base_output / "exp0007_strategy_optimization.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    print(f"Saved {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
