"""
EXP-0029: 確率キャリブレーション（isotonic regression）による ROI 改善検証。

手法: 学習時に isotonic regression で model_prob → calibrated_prob。
EV = calibrated_prob × odds で選別（学習時キャリブレーションにより予測確率が補正される）。

比較: baseline（sigmoid） vs calibrated（isotonic）
対象戦略: EXP-0015, EXP-0013, EXP-0007
出力: ROI, total_profit, max_drawdown, profit_per_1000_bets, bet_count
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

STRATEGIES: List[Tuple] = [
    ("exp0015", "top_n_ev_gap_filter", TOP_N, 1.20, None, None, None, 0.07),
    ("exp0013", "top_n_ev_gap_filter", TOP_N, 1.18, None, None, None, 0.05),
    ("exp0007", "top_n_ev", TOP_N, 1.18, None, None, None, None),
]

STRATEGY_SUFFIXES: Dict[str, str] = {
    "exp0015": "_top3ev120_evgap0x07",
    "exp0013": "_top3ev118_evgap0x05",
    "exp0007": "_top3ev118",
}

CONDITIONS = ["baseline", "calibrated"]
# baseline = sigmoid (existing predictions), calibrated = isotonic (run and save here)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db-path", required=True, help="SQLite DB path")
    parser.add_argument("--output-dir", type=Path, default=None)
    parser.add_argument("--baseline-pred-dir", type=Path, default=None, help="Existing sigmoid predictions dir")
    parser.add_argument("--n-windows", type=int, default=12)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    raw_dir = _REPO_ROOT / "kyotei_predictor" / "data" / "raw"
    if not raw_dir.is_dir():
        raw_dir = Path("kyotei_predictor/data/raw")
    output_dir = args.output_dir or _REPO_ROOT / "outputs" / "probability_calibration_experiments"
    output_dir.mkdir(parents=True, exist_ok=True)
    baseline_pred_dir = args.baseline_pred_dir or (_REPO_ROOT / "outputs" / "confidence_weighted_sizing_experiments" / "rolling_roi_predictions")
    out_pred_dir_isotonic = output_dir / "rolling_roi_predictions"
    out_pred_dir_isotonic.mkdir(parents=True, exist_ok=True)

    min_date, max_date = get_db_date_range(args.db_path)
    window_list = build_windows(
        min_date, max_date, TRAIN_DAYS, TEST_DAYS, STEP_DAYS, args.n_windows
    )

    # 1) Calibrated (isotonic): rolling validation を calibration=isotonic で実行
    need_isotonic = not (out_pred_dir_isotonic.exists() and list(out_pred_dir_isotonic.glob("predictions_baseline_*")))
    if need_isotonic:
        print(f"Running rolling validation (n_windows={args.n_windows}) with calibration=isotonic...")
        run_rolling_validation_roi(
            db_path=args.db_path,
            output_dir=output_dir,
            data_dir_raw=raw_dir,
            train_days=TRAIN_DAYS,
            test_days=TEST_DAYS,
            step_days=STEP_DAYS,
            n_windows=args.n_windows,
            strategies=STRATEGIES,
            model_type="xgboost",
            calibration="isotonic",
            feature_set="extended_features",
            seed=args.seed,
        )
    else:
        print(f"Using existing isotonic predictions in {out_pred_dir_isotonic}")

    results: Dict[str, Dict[str, Dict]] = {}
    for (strat_name, *_) in STRATEGIES:
        results[strat_name] = {}
        for cond in CONDITIONS:
            results[strat_name][cond] = {
                "condition": cond,
                "total_bet_selected": 0.0,
                "total_payout_selected": 0.0,
                "selected_bets_total_count": 0,
                "total_profit": 0.0,
                "window_profits": [],
                "max_drawdown": 0.0,
                "profit_per_1000_bets": 0.0,
                "overall_roi_selected": None,
                "bet_count": 0,
            }

    for wi, (ts, te, tst, tend) in enumerate(window_list):
        test_dates = _date_range(tst, tend)
        for day in test_dates:
            month = _month_dir(day)
            data_dir_month = raw_dir / month
            if not data_dir_month.exists():
                continue
            for strat_name in STRATEGY_SUFFIXES:
                suffix = STRATEGY_SUFFIXES[strat_name]
                for cond in CONDITIONS:
                    if cond == "baseline":
                        path = baseline_pred_dir / f"predictions_baseline_{day}{suffix}.json"
                    else:
                        path = out_pred_dir_isotonic / f"predictions_baseline_{day}{suffix}.json"
                    if not path.exists():
                        continue
                    try:
                        summary, _ = run_verify(
                            path,
                            data_dir_month,
                            evaluation_mode="selected_bets",
                            data_source="db",
                            db_path=args.db_path,
                            bet_sizing_mode="fixed",
                        )
                    except Exception:
                        continue
                    r = results[strat_name][cond]
                    tb = summary.get("total_bet_selected") or 0
                    tp = summary.get("total_payout_selected") or 0
                    cnt = summary.get("selected_bets_total_count") or 0
                    r["total_bet_selected"] += tb
                    r["total_payout_selected"] += tp
                    r["selected_bets_total_count"] += cnt
                    while len(r["window_profits"]) <= wi:
                        r["window_profits"].append(0.0)
                    r["window_profits"][wi] += (tp - tb)

    for strat_name in results:
        for cond in results[strat_name]:
            r = results[strat_name][cond]
            tb = r["total_bet_selected"]
            tp = r["total_payout_selected"]
            cnt = r["selected_bets_total_count"]
            r["total_profit"] = round(tp - tb, 2)
            r["profit_per_1000_bets"] = round(1000.0 * (tp - tb) / cnt, 2) if cnt else 0.0
            r["overall_roi_selected"] = round((tp / tb - 1) * 100, 2) if tb else None
            r["bet_count"] = cnt
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

    results_list: List[Dict] = []
    for strat_name in ["exp0015", "exp0013", "exp0007"]:
        for cond in CONDITIONS:
            r = results[strat_name][cond].copy()
            r["strategy_id"] = strat_name
            r["strategy_name"] = f"{strat_name}_{cond}"
            results_list.append(r)

    out_path = output_dir / "exp0029_probability_calibration_results.json"
    payload = {
        "experiment_id": "EXP-0029",
        "n_windows": args.n_windows,
        "baseline_calibration": "sigmoid",
        "calibrated_calibration": "isotonic",
        "strategies": [{"name": s[0], "strategy": s[1]} for s in STRATEGIES],
        "results": results_list,
    }
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    print(f"Saved {out_path}")

    print("\n--- Results (strategy_id | condition | ROI | total_profit | max_drawdown | profit_per_1000_bets | bet_count) ---")
    for strat_name in ["exp0015", "exp0013", "exp0007"]:
        for cond in CONDITIONS:
            r = results[strat_name][cond]
            print(
                f"  {strat_name} | {cond} | ROI={r.get('overall_roi_selected')}% | total_profit={r.get('total_profit')} | "
                f"max_drawdown={r.get('max_drawdown')} | profit_per_1000_bets={r.get('profit_per_1000_bets')} | bet_count={r.get('bet_count')}"
            )

    return 0


if __name__ == "__main__":
    sys.exit(main())
