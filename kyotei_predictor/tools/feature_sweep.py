"""
特徴量セット比較: current_features / extended_features / extended_features_v2 で同一条件の rolling validation を実行。

- current_features: 既存状態ベクトルのみ
- extended_features: モーター勝率代理を追加
- extended_features_v2: extended + venue_course/recent_form/motor_trend/relative_race_strength 系

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
    ("current_features", None),
    ("extended_features", "extended_features"),
    ("extended_features_v2", "extended_features_v2"),
]
ENV_FEATURE_SET = "KYOTEI_FEATURE_SET"
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
    prev_feature_set = os.environ.get(ENV_FEATURE_SET)
    prev_motor = os.environ.get(ENV_MOTOR_PROXY)
    results = []
    try:
        for name, feature_set_val in FEATURE_SETS:
            if feature_set_val is not None:
                os.environ[ENV_FEATURE_SET] = feature_set_val
            else:
                os.environ[ENV_FEATURE_SET] = "current_features"
                os.environ[ENV_MOTOR_PROXY] = "0"
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
                "model_type": summary.get("model_type", "sklearn"),
                "calibration": summary.get("calibration", args.calibration),
                "strategy": summary.get("strategy", "top_n_ev"),
                "top_n": summary.get("top_n", args.top_n),
                "ev_threshold": summary.get("ev_threshold", args.ev_threshold),
                "seed": summary.get("seed", args.seed),
                "n_windows": summary.get("n_windows") or summary.get("number_of_windows"),
                "overall_roi_selected": summary.get("overall_roi_selected"),
                "mean_roi_selected": summary.get("mean_roi_selected"),
                "median_roi_selected": summary.get("median_roi_selected"),
                "std_roi_selected": summary.get("std_roi_selected"),
                "total_selected_bets": summary.get("total_selected_bets"),
                "mean_selected_bets_per_window": round(statistics.mean(bets), 2) if bets else None,
                "mean_log_loss": summary.get("mean_log_loss"),
                "mean_brier_score": summary.get("mean_brier_score"),
                "number_of_windows": summary.get("number_of_windows"),
            })
    finally:
        if prev_feature_set is not None:
            os.environ[ENV_FEATURE_SET] = prev_feature_set
        elif ENV_FEATURE_SET in os.environ:
            os.environ.pop(ENV_FEATURE_SET, None)
        if prev_motor is not None:
            os.environ[ENV_MOTOR_PROXY] = prev_motor
        elif ENV_MOTOR_PROXY in os.environ:
            os.environ.pop(ENV_MOTOR_PROXY, None)

    out_path = args.output_dir / "feature_comparison_summary.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump({
            "model_type": "sklearn",
            "feature_sets": [f[0] for f in FEATURE_SETS],
            "note": "extended_features = +motor_win_proxy; extended_features_v2 = +venue_course/recent_form/motor_trend/relative_race_strength",
            "strategy": "top_n_ev",
            "top_n": args.top_n,
            "ev_threshold": args.ev_threshold,
            "calibration": args.calibration,
            "n_windows": args.n_windows,
            "seed": args.seed,
            "results": results,
        }, f, ensure_ascii=False, indent=2)
    print("Saved", out_path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
