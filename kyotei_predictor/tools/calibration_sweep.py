"""
Calibration 比較: none / sigmoid / isotonic で同一条件の rolling validation を実行。

戦略は現状ベスト（top_n=6, ev_threshold=1.20）で固定。DB 必須。
出力: outputs/calibration_comparison_summary.json
"""

import argparse
import json
import statistics
import sys
from pathlib import Path

_THIS_DIR = Path(__file__).resolve().parent
_PROJECT_ROOT = _THIS_DIR.parent.parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from kyotei_predictor.tools.rolling_validation_roi import run_rolling_validation_roi

CALIBRATION_TYPES = ["none", "sigmoid", "isotonic"]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db-path", required=True)
    parser.add_argument("--output-dir", type=Path, default=Path("outputs"))
    parser.add_argument("--data-dir", type=Path, default=None)
    parser.add_argument("--train-days", type=int, default=30)
    parser.add_argument("--test-days", type=int, default=7)
    parser.add_argument("--step-days", type=int, default=7)
    parser.add_argument("--n-windows", type=int, default=12)
    parser.add_argument("--top-n", type=int, default=6)
    parser.add_argument("--ev-threshold", type=float, default=1.20)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    raw_dir = args.data_dir or _PROJECT_ROOT / "kyotei_predictor" / "data" / "raw"
    if not raw_dir.is_dir():
        raw_dir = Path("kyotei_predictor/data/raw")
    if not raw_dir.is_dir():
        print("data_dir not found:", raw_dir, file=sys.stderr)
        return 1

    args.output_dir.mkdir(parents=True, exist_ok=True)
    results = []
    for calib in CALIBRATION_TYPES:
        sub_dir = args.output_dir / f"calib_{calib}"
        sub_dir.mkdir(parents=True, exist_ok=True)
        summary, windows = run_rolling_validation_roi(
            db_path=args.db_path,
            output_dir=sub_dir,
            data_dir_raw=raw_dir,
            train_days=args.train_days,
            test_days=args.test_days,
            step_days=args.step_days,
            n_windows=args.n_windows,
            top_n=args.top_n,
            ev_threshold=args.ev_threshold,
            calibration=calib,
            seed=args.seed,
        )
        bets = [w["selected_bets_total_count"] for w in windows]
        results.append({
            "calibration": calib,
            "mean_roi_selected": summary.get("mean_roi_selected"),
            "median_roi_selected": summary.get("median_roi_selected"),
            "std_roi_selected": summary.get("std_roi_selected"),
            "overall_roi_selected": summary.get("overall_roi_selected"),
            "total_selected_bets": summary.get("total_selected_bets"),
            "mean_selected_bets_per_window": round(statistics.mean(bets), 2) if bets else None,
            "mean_log_loss": summary.get("mean_log_loss"),
            "mean_brier_score": summary.get("mean_brier_score"),
            "number_of_windows": summary.get("number_of_windows"),
        })

    out_path = args.output_dir / "calibration_comparison_summary.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump({
            "calibration_types": CALIBRATION_TYPES,
            "strategy": {"top_n": args.top_n, "ev_threshold": args.ev_threshold},
            "n_windows": args.n_windows,
            "results": results,
        }, f, ensure_ascii=False, indent=2)
    print("Saved", out_path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
