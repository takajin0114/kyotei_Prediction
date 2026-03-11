"""
EXP-0024: confidence-weighted sizing の閾値微調整（ev_gap_high sweep + normal_unit 比較）。

weighted_ev_gap_v1 を基準に ev_gap_high を 0.09 / 0.10 / 0.11 で sweep し、
必要なら normal_unit を 0.5 / 0.6 / 0.7 も比較する。
summary に ROI, total_profit, max_drawdown, profit_per_1000_bets, bet_count を必ず出す。
"""

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Tuple

_THIS_DIR = Path(__file__).resolve().parent
_REPO_ROOT = _THIS_DIR.parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

os.environ["KYOTEI_USE_MOTOR_WIN_PROXY"] = os.environ.get("KYOTEI_USE_MOTOR_WIN_PROXY", "1")
os.environ["KYOTEI_FEATURE_SET"] = os.environ.get("KYOTEI_FEATURE_SET", "extended_features")

from kyotei_predictor.tools.rolling_validation_roi import (
    build_windows,
    get_db_date_range,
    run_rolling_validation_roi,
)
from kyotei_predictor.tools.rolling_validation_windows import _date_range, _month_dir
from kyotei_predictor.application.verify_usecase import run_verify

TRAIN_DAYS = 30
TEST_DAYS = 7
STEP_DAYS = 7
TOP_N = 3
EV_THRESHOLD = 1.20
EV_GAP = 0.07
EXP0015_BEST_ROI = -12.71

# ev_gap_high sweep (0.09, 0.10, 0.11) + normal_unit 比較 (0.5, 0.6, 0.7 @ ev_gap_high=0.10)
SIZING_VARIANTS: List[Tuple[str, str, Dict]] = [
    ("fixed_base", "fixed", {}),
    ("ev_gap_high_0x09_normal0x5", "confidence_weighted_ev_gap_v1", {"ev_gap_high": 0.09, "normal_unit": 0.5}),
    ("ev_gap_high_0x10_normal0x5", "confidence_weighted_ev_gap_v1", {"ev_gap_high": 0.10, "normal_unit": 0.5}),
    ("ev_gap_high_0x11_normal0x5", "confidence_weighted_ev_gap_v1", {"ev_gap_high": 0.11, "normal_unit": 0.5}),
    ("ev_gap_high_0x10_normal0x6", "confidence_weighted_ev_gap_v1", {"ev_gap_high": 0.10, "normal_unit": 0.6}),
    ("ev_gap_high_0x10_normal0x7", "confidence_weighted_ev_gap_v1", {"ev_gap_high": 0.10, "normal_unit": 0.7}),
]

BASELINE_SUFFIX = "_top3ev120_evgap0x07"


def _month_dir(date_str: str) -> str:
    return date_str[:7]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db-path", required=True, help="SQLite DB path")
    parser.add_argument("--output-dir", type=Path, default=None)
    parser.add_argument("--n-windows", type=int, default=12)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    raw_dir = _REPO_ROOT / "kyotei_predictor" / "data" / "raw"
    if not raw_dir.is_dir():
        raw_dir = Path("kyotei_predictor/data/raw")
    output_dir = args.output_dir or _REPO_ROOT / "outputs" / "confidence_weighted_sizing_experiments"
    output_dir.mkdir(parents=True, exist_ok=True)
    out_pred_dir = output_dir / "rolling_roi_predictions"

    strategies = [
        ("fixed_base", "top_n_ev_gap_filter", TOP_N, EV_THRESHOLD, None, None, None, EV_GAP),
    ]
    print(f"Running rolling validation (n_windows={args.n_windows}) to generate predictions...")
    summary_or_list, windows_or_list = run_rolling_validation_roi(
        db_path=args.db_path,
        output_dir=output_dir,
        data_dir_raw=raw_dir,
        train_days=TRAIN_DAYS,
        test_days=TEST_DAYS,
        step_days=STEP_DAYS,
        n_windows=args.n_windows,
        strategies=strategies,
        model_type="xgboost",
        calibration="sigmoid",
        feature_set="extended_features",
        seed=args.seed,
    )
    fixed_summary = summary_or_list if isinstance(summary_or_list, dict) else (summary_or_list[0] if summary_or_list else {})
    windows = windows_or_list if isinstance(windows_or_list, list) else []

    min_date, max_date = get_db_date_range(args.db_path)
    window_list = build_windows(
        min_date, max_date, TRAIN_DAYS, TEST_DAYS, STEP_DAYS, args.n_windows
    )

    results_by_sizing: Dict[str, Dict] = {}
    for sname, mode, config in SIZING_VARIANTS:
        results_by_sizing[sname] = {
            "sizing_name": sname,
            "bet_sizing_mode": mode,
            "config": dict(config),
            "total_bet_selected": 0.0,
            "total_payout_selected": 0.0,
            "selected_bets_total_count": 0,
            "total_profit": 0.0,
            "window_profits": [],
            "total_staked": 0.0,
            "average_bet_size": 0.0,
            "profit_per_1000_bets": 0.0,
        }

    for wi, (ts, te, tst, tend) in enumerate(window_list):
        test_dates = _date_range(tst, tend)
        for day in test_dates:
            month = _month_dir(day)
            data_dir_month = raw_dir / month
            path = out_pred_dir / f"predictions_baseline_{day}{BASELINE_SUFFIX}.json"
            if not path.exists() or not data_dir_month.exists():
                continue
            for sname, mode, config in SIZING_VARIANTS:
                try:
                    summary, _ = run_verify(
                        path,
                        data_dir_month,
                        evaluation_mode="selected_bets",
                        data_source="db",
                        db_path=args.db_path,
                        bet_sizing_mode=mode,
                        bet_sizing_config=config,
                    )
                except Exception:
                    continue
                r = results_by_sizing[sname]
                tb = summary.get("total_bet_selected") or 0
                tp = summary.get("total_payout_selected") or 0
                cnt = summary.get("selected_bets_total_count") or 0
                r["total_bet_selected"] += tb
                r["total_payout_selected"] += tp
                r["selected_bets_total_count"] += cnt
                while len(r["window_profits"]) <= wi:
                    r["window_profits"].append(0.0)
                r["window_profits"][wi] += (tp - tb)

    for sname in results_by_sizing:
        r = results_by_sizing[sname]
        tb = r["total_bet_selected"]
        tp = r["total_payout_selected"]
        cnt = r["selected_bets_total_count"]
        r["total_staked"] = round(tb, 2)
        r["total_profit"] = round(tp - tb, 2)
        r["average_bet_size"] = round(tb / cnt, 2) if cnt else 0.0
        r["profit_per_1000_bets"] = round(1000.0 * (tp - tb) / cnt, 2) if cnt else 0.0
        r["overall_roi_selected"] = round((tp / tb - 1) * 100, 2) if tb else 0.0
        r["baseline_diff_roi"] = round(r["overall_roi_selected"] - EXP0015_BEST_ROI, 2) if r.get("overall_roi_selected") is not None else None
        cum = 0.0
        peak = 0.0
        dd = 0.0
        for wprof in r["window_profits"]:
            cum += wprof
            if cum > peak:
                peak = cum
            if peak - cum > dd:
                dd = peak - cum
        r["max_drawdown"] = round(dd, 2)
        r["avg_profit_per_window"] = round(sum(r["window_profits"]) / len(r["window_profits"]), 2) if r["window_profits"] else 0.0
        r["bet_count"] = r["selected_bets_total_count"]

    if fixed_summary:
        results_by_sizing["fixed_base"]["overall_roi_selected"] = fixed_summary.get("overall_roi_selected")
        results_by_sizing["fixed_base"]["baseline_diff_roi"] = round(
            (fixed_summary.get("overall_roi_selected") or 0) - EXP0015_BEST_ROI, 2
        )

    results_list = []
    for sname in [x[0] for x in SIZING_VARIANTS]:
        r = results_by_sizing[sname].copy()
        r["strategy_name"] = sname
        results_list.append(r)

    out_path = output_dir / "exp0024_confidence_weighted_sizing_threshold_sweep_results.json"
    payload = {
        "experiment_id": "EXP-0024",
        "n_windows": args.n_windows,
        "seed": args.seed,
        "baseline_strategy": "top_n_ev_gap_filter",
        "baseline_params": {"top_n": TOP_N, "ev_threshold": EV_THRESHOLD, "ev_gap_threshold": EV_GAP},
        "exp0015_best_roi": EXP0015_BEST_ROI,
        "sizing_variants": [x[0] for x in SIZING_VARIANTS],
        "results": results_list,
    }
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    print(f"Saved {out_path}")

    print("\n--- Results (ROI | bet_count | total_profit | max_drawdown | profit_per_1000_bets | baseline_diff_roi) ---")
    for r in results_list:
        print(
            f"  {r['strategy_name']} | ROI={r.get('overall_roi_selected')}% | bet_count={r.get('bet_count')} | "
            f"total_profit={r.get('total_profit')} | max_drawdown={r.get('max_drawdown')} | "
            f"profit_per_1000_bets={r.get('profit_per_1000_bets')} | baseline_diff_roi={r.get('baseline_diff_roi')}%"
        )

    best_roi = max(
        (r for r in results_list if r.get("overall_roi_selected") is not None),
        key=lambda x: x["overall_roi_selected"],
        default=None,
    )
    if best_roi:
        print(f"\nBest by ROI: {best_roi['strategy_name']} ({best_roi.get('overall_roi_selected')}%)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
