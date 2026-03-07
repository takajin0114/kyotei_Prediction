"""
top_n sweep: 同じ rolling 条件で top_n を 3, 5, 10, 15 で比較。

出力: outputs/topn_sweep_summary.json
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

TOP_N_VALUES_DEFAULT = [3, 5, 10, 15]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db-path", required=True)
    parser.add_argument("--output-dir", type=Path, default=Path("outputs"))
    parser.add_argument("--data-dir", type=Path, default=None)
    parser.add_argument("--train-days", type=int, default=30)
    parser.add_argument("--test-days", type=int, default=7)
    parser.add_argument("--step-days", type=int, default=7)
    parser.add_argument("--n-windows", type=int, default=12)
    parser.add_argument("--ev-threshold", type=float, default=1.15)
    parser.add_argument("--top-n-values", type=str, default=None,
                        help="Comma-separated top_n, e.g. 4,5,6,8")
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    if args.top_n_values:
        top_n_values = [int(x.strip()) for x in args.top_n_values.split(",") if x.strip()]
    else:
        top_n_values = TOP_N_VALUES_DEFAULT

    raw_dir = args.data_dir or _PROJECT_ROOT / "kyotei_predictor" / "data" / "raw"
    if not raw_dir.is_dir():
        raw_dir = Path("kyotei_predictor/data/raw")
    if not raw_dir.is_dir():
        print("data_dir not found:", raw_dir, file=sys.stderr)
        return 1

    args.output_dir.mkdir(parents=True, exist_ok=True)
    strategies = [
        (f"top{n}", "top_n_ev", n, args.ev_threshold) for n in top_n_values
    ]
    summaries, per_strategy_windows = run_rolling_validation_roi(
        db_path=args.db_path,
        output_dir=args.output_dir,
        data_dir_raw=raw_dir,
        train_days=args.train_days,
        test_days=args.test_days,
        step_days=args.step_days,
        n_windows=args.n_windows,
        ev_threshold=args.ev_threshold,
        strategies=strategies,
        seed=args.seed,
    )
    results = []
    for s, windows in zip(summaries, per_strategy_windows):
        bets = [w["selected_bets_total_count"] for w in windows]
        results.append({
            "top_n": s["top_n"],
            "mean_roi_selected": s["mean_roi_selected"],
            "median_roi_selected": s.get("median_roi_selected"),
            "overall_roi_selected": s["overall_roi_selected"],
            "total_selected_bets": s["total_selected_bets"],
            "mean_selected_bets_per_window": round(statistics.mean(bets), 2) if bets else 0,
            "std_roi_selected": s["std_roi_selected"],
            "number_of_windows": s["number_of_windows"],
            "mean_log_loss": s.get("mean_log_loss"),
            "mean_brier_score": s.get("mean_brier_score"),
        })

    out_path = args.output_dir / "topn_sweep_summary.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump({"top_n_values": top_n_values, "ev_threshold": args.ev_threshold, "results": results}, f, ensure_ascii=False, indent=2)
    print("Saved", out_path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
