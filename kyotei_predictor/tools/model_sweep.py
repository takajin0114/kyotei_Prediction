"""
モデル比較: sklearn / lightgbm / xgboost で同一条件の rolling validation を実行。

未導入のモデルはスキップする。戦略は現状ベスト（top_n=6, ev_threshold=1.20）で固定。DB 必須。
--use-extended-features で KYOTEI_USE_MOTOR_WIN_PROXY=1（extended_features）を使用。
出力: outputs/model_comparison_summary.json
"""

import argparse
import json
import os
import statistics
import sys
from pathlib import Path

ENV_MOTOR_PROXY = "KYOTEI_USE_MOTOR_WIN_PROXY"

_THIS_DIR = Path(__file__).resolve().parent
_PROJECT_ROOT = _THIS_DIR.parent.parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from kyotei_predictor.tools.rolling_validation_roi import run_rolling_validation_roi

# 利用可能なモデルを実行時に判定（lightgbm/xgboost は import 失敗時スキップ。Mac では libomp 未導入で落ちる場合あり）
def _available_models() -> list:
    out = [("sklearn", "baseline B (sklearn)")]
    try:
        import lightgbm  # noqa: F401
        out.append(("lightgbm", "baseline B (lightgbm)"))
    except Exception:
        pass
    try:
        import xgboost  # noqa: F401
        out.append(("xgboost", "baseline B (xgboost)"))
    except Exception:
        pass
    return out


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
    parser.add_argument("--models", type=str, default=None,
                        help="Comma-separated model types, e.g. sklearn,lightgbm,xgboost")
    parser.add_argument("--use-extended-features", action="store_true",
                        help="Use extended features (KYOTEI_USE_MOTOR_WIN_PROXY=1)")
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    prev_env = os.environ.get(ENV_MOTOR_PROXY)
    if args.use_extended_features:
        os.environ[ENV_MOTOR_PROXY] = "1"
    try:
        raw_dir = args.data_dir or _PROJECT_ROOT / "kyotei_predictor" / "data" / "raw"
        if not raw_dir.is_dir():
            raw_dir = Path("kyotei_predictor/data/raw")
        if not raw_dir.is_dir():
            print("data_dir not found:", raw_dir, file=sys.stderr)
            return 1

        if args.models:
            model_list = [(m.strip(), m.strip()) for m in args.models.split(",") if m.strip()]
        else:
            model_list = _available_models()

        args.output_dir.mkdir(parents=True, exist_ok=True)
        results = []
        for model_type, model_label in model_list:
            sub_dir = args.output_dir / f"model_{model_type}"
            sub_dir.mkdir(parents=True, exist_ok=True)
            try:
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
                    model_type=model_type,
                    seed=args.seed,
                )
            except Exception as e:
                print(f"Skip {model_type}: {e}", file=sys.stderr)
                results.append({
                    "model_type": model_type,
                    "model_label": model_label,
                    "error": str(e),
                    "mean_roi_selected": None,
                    "median_roi_selected": None,
                    "std_roi_selected": None,
                    "overall_roi_selected": None,
                    "total_selected_bets": None,
                    "mean_selected_bets_per_window": None,
                    "mean_log_loss": None,
                    "mean_brier_score": None,
                    "number_of_windows": None,
                })
                continue
            bets = [w["selected_bets_total_count"] for w in windows]
            results.append({
                "model_type": model_type,
                "model_label": model_label,
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

        out_path = args.output_dir / "model_comparison_summary.json"
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump({
                "model_types": [r["model_type"] for r in results],
                "strategy": {"top_n": args.top_n, "ev_threshold": args.ev_threshold},
                "calibration": args.calibration,
                "feature_set": "extended_features" if args.use_extended_features else "current_features",
                "n_windows": args.n_windows,
                "results": results,
            }, f, ensure_ascii=False, indent=2)
        print("Saved", out_path)
        return 0
    finally:
        if prev_env is not None:
            os.environ[ENV_MOTOR_PROXY] = prev_env
        elif ENV_MOTOR_PROXY in os.environ:
            os.environ.pop(ENV_MOTOR_PROXY, None)


if __name__ == "__main__":
    sys.exit(main())
