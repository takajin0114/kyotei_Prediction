#!/usr/bin/env python3
"""
EXP-0006: XGBoost + sigmoid + extended_features で EV threshold sweep & strategy 比較。
n_windows=12, seed=42。閾値 1.05〜1.30（top_n_ev）および top_n_ev vs ev_threshold_only 比較。
リポジトリルートで実行: python3 scripts/exp0006_xgb_ev_threshold_sweep.py --db-path kyotei_predictor/data/kyotei_races.sqlite
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

# extended_features を使うために motor proxy を有効化（または KYOTEI_FEATURE_SET=extended_features）
os.environ["KYOTEI_USE_MOTOR_WIN_PROXY"] = os.environ.get("KYOTEI_USE_MOTOR_WIN_PROXY", "1")
os.environ["KYOTEI_FEATURE_SET"] = os.environ.get("KYOTEI_FEATURE_SET", "extended_features")

from kyotei_predictor.tools.rolling_validation_roi import run_rolling_validation_roi

EV_THRESHOLDS = [1.05, 1.10, 1.15, 1.20, 1.25, 1.30]
TOP_N = 6
EV_REF = 1.20


def _to_result(s: dict, windows: list) -> dict:
    total_bet = s.get("total_bet_selected") or 0
    total_payout = s.get("total_payout_selected") or 0
    profit = round(total_payout - total_bet, 2) if total_bet else 0.0
    return {
        "strategy": s.get("strategy"),
        "top_n": s.get("top_n"),
        "ev_threshold": s.get("ev_threshold"),
        "overall_roi_selected": s.get("overall_roi_selected"),
        "mean_roi_selected": s.get("mean_roi_selected"),
        "median_roi_selected": s.get("median_roi_selected"),
        "std_roi_selected": s.get("std_roi_selected"),
        "total_selected_bets": s.get("total_selected_bets") or 0,
        "profit": profit,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="EXP-0006 XGBoost EV threshold sweep & strategy comparison")
    parser.add_argument("--db-path", required=True)
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
    pred_dir.mkdir(parents=True, exist_ok=True)

    # Part 1: EV threshold sweep (top_n_ev, top_n=6)
    strategies_sweep = [
        (f"top6_ev{int(ev * 100)}", "top_n_ev", TOP_N, ev) for ev in EV_THRESHOLDS
    ]
    summaries_sweep, per_strategy_sweep = run_rolling_validation_roi(
        db_path=args.db_path,
        output_dir=output_dir,
        data_dir_raw=raw_dir,
        train_days=30,
        test_days=7,
        step_days=7,
        n_windows=args.n_windows,
        strategies=strategies_sweep,
        model_type="xgboost",
        calibration="sigmoid",
        feature_set="extended_features",
        seed=args.seed,
    )

    ev_sweep_results = [_to_result(s, w) for s, w in zip(summaries_sweep, per_strategy_sweep)]

    # Part 2: Strategy comparison (top_n_ev vs ev_threshold_only at ev=1.20)
    strategies_cmp = [
        (f"top_n_ev_top{TOP_N}_ev{int(EV_REF * 100)}", "top_n_ev", TOP_N, EV_REF),
        (f"ev_threshold_only_ev{int(EV_REF * 100)}", "ev_threshold_only", 0, EV_REF),
    ]
    summaries_cmp, per_strategy_cmp = run_rolling_validation_roi(
        db_path=args.db_path,
        output_dir=output_dir,
        data_dir_raw=raw_dir,
        train_days=30,
        test_days=7,
        step_days=7,
        n_windows=args.n_windows,
        strategies=strategies_cmp,
        model_type="xgboost",
        calibration="sigmoid",
        feature_set="extended_features",
        seed=args.seed,
    )

    strategy_cmp_results = [_to_result(s, w) for s, w in zip(summaries_cmp, per_strategy_cmp)]

    out = {
        "experiment_id": "EXP-0006",
        "model": "xgboost",
        "calibration": "sigmoid",
        "features": "extended_features",
        "n_windows": args.n_windows,
        "seed": args.seed,
        "ev_threshold_sweep": ev_sweep_results,
        "strategy_comparison": strategy_cmp_results,
    }

    out_path = output_dir / "exp0006_xgb_strategy_optimization.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    print(f"Saved {out_path}")

    print("\n## EV Threshold Sweep (top_n_ev, top_n=6)")
    for r in ev_sweep_results:
        print(f"  ev={r['ev_threshold']}: roi={r['overall_roi_selected']}% mean={r['mean_roi_selected']} median={r['median_roi_selected']} "
              f"std={r['std_roi_selected']} bets={r['total_selected_bets']} profit={r['profit']}")

    print("\n## Strategy Comparison (ev=1.20)")
    for r in strategy_cmp_results:
        print(f"  {r['strategy']}: roi={r['overall_roi_selected']}% mean={r['mean_roi_selected']} bets={r['total_selected_bets']} profit={r['profit']}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
