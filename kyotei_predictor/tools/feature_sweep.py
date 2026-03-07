"""
特徴量セット比較: current_features vs extended_features で同一条件の rolling validation を実行。

- current_features: KYOTEI_USE_MOTOR_WIN_PROXY=0（既存状態ベクトルのみ）
- extended_features: KYOTEI_USE_MOTOR_WIN_PROXY=1（モーター勝率代理を追加）

戦略は現状ベスト（top_n=6, ev_threshold=1.20）で固定。DB 必須。
出力: outputs/feature_comparison_summary.json
"""

import argparse
import json
import os
import statistics
import sys
from pathlib import Path

_THIS_DIR = Path(__file__).resolve().parent
_PROJECT_ROOT = _THIS_DIR.parent.parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from kyotei_predictor.tools.rolling_validation_roi import run_rolling_validation_roi

FEATURE_SETS = [
    ("current_features", "0"),
    ("extended_features", "1"),
]
ENV_MOTOR_PROXY = "KYOTEI_USE_MOTOR_WIN_PROXY"


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
    parser.add_argument("--calibration", type=str, default="sigmoid")
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    raw_dir = args.data_dir or _PROJECT_ROOT / "kyotei_predictor" / "data" / "raw"
    if not raw_dir.is_dir():
        raw_dir = Path("kyotei_predictor/data/raw")
    if not raw_dir.is_dir():
        print("data_dir not found:", raw_dir, file=sys.stderr)
        return 1

    args.output_dir.mkdir(parents=True, exist_ok=True)
    prev_env = os.environ.get(ENV_MOTOR_PROXY)
    results = []
    try:
        for name, proxy_val in FEATURE_SETS:
            os.environ[ENV_MOTOR_PROXY] = proxy_val
            sub_dir = args.output_dir / f"feature_{name}"
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
                calibration=args.calibration,
                seed=args.seed,
            )
            bets = [w["selected_bets_total_count"] for w in windows]
            results.append({
                "feature_set": name,
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
    finally:
        if prev_env is not None:
            os.environ[ENV_MOTOR_PROXY] = prev_env
        elif ENV_MOTOR_PROXY in os.environ:
            os.environ.pop(ENV_MOTOR_PROXY, None)

    out_path = args.output_dir / "feature_comparison_summary.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump({
            "feature_sets": [f[0] for f in FEATURE_SETS],
            "note": "extended_features = current + motor_win_proxy (KYOTEI_USE_MOTOR_WIN_PROXY=1)",
            "strategy": {"top_n": args.top_n, "ev_threshold": args.ev_threshold},
            "calibration": args.calibration,
            "n_windows": args.n_windows,
            "results": results,
        }, f, ensure_ascii=False, indent=2)
    print("Saved", out_path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
