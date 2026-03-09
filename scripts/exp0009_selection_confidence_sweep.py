#!/usr/bin/env python3
"""
EXP-0009: selection strategy 比較（top_n_ev vs top_n_ev_confidence）。

- 現行: top_n_ev（top_n=3, ev_threshold=1.15 / 1.18 / 1.20）
- 新規: top_n_ev_confidence（同 ev × confidence_type: pred_prob / prob_gap / entropy_adjusted）

評価: mean_roi_selected, median_roi_selected, overall_roi_selected, total_selected_bets,
      hit_rate_rank1_pct, mean_log_loss, mean_brier_score。
n_windows=12, seed=42。リポジトリルートで実行。
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

from kyotei_predictor.tools.rolling_validation_roi import run_rolling_validation_roi

TRAIN_DAYS = 30
TEST_DAYS = 7
STEP_DAYS = 7
TOP_N = 3
EV_VALUES = [1.15, 1.18, 1.20]
CONFIDENCE_TYPES = ["pred_prob", "prob_gap", "entropy_adjusted"]


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

    strategies = []
    for ev in EV_VALUES:
        strategies.append((f"top_n_ev_ev{int(ev*100)}", "top_n_ev", TOP_N, ev))
    for ev in EV_VALUES:
        for c in CONFIDENCE_TYPES:
            strategies.append((
                f"top_n_ev_conf_{c}_ev{int(ev*100)}",
                "top_n_ev_confidence",
                TOP_N,
                ev,
                c,
            ))

    print("Running rolling validation (top_n_ev + top_n_ev_confidence sweep)...")
    summaries, _ = run_rolling_validation_roi(
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

    results = []
    for s in summaries:
        results.append({
            "strategy": s.get("strategy"),
            "strategy_name": s.get("strategy_name"),
            "top_n": s.get("top_n"),
            "ev_threshold": s.get("ev_threshold"),
            "confidence_type": s.get("confidence_type"),
            "mean_roi_selected": s.get("mean_roi_selected"),
            "median_roi_selected": s.get("median_roi_selected"),
            "overall_roi_selected": s.get("overall_roi_selected"),
            "total_selected_bets": s.get("total_selected_bets"),
            "hit_rate_rank1_pct": s.get("hit_rate_rank1_pct"),
            "mean_log_loss": s.get("mean_log_loss"),
            "mean_brier_score": s.get("mean_brier_score"),
        })
        print(
            f"  {s.get('strategy_name')} -> roi={s.get('overall_roi_selected')}% "
            f"mean_roi={s.get('mean_roi_selected')} median_roi={s.get('median_roi_selected')} "
            f"bets={s.get('total_selected_bets')} hit_rate_rank1={s.get('hit_rate_rank1_pct')}"
        )

    out = {
        "experiment_id": "EXP-0009",
        "model": "xgboost",
        "calibration": "sigmoid",
        "features": "extended_features",
        "n_windows": args.n_windows,
        "seed": args.seed,
        "results": results,
    }
    out_path = output_dir / "exp0009_selection_confidence_sweep.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    print(f"Saved {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
