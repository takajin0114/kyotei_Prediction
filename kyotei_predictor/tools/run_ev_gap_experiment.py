"""
EXP-0013: EV gap strategy（top_n_ev_gap_filter）の評価。

ロジック: ev_gap = ev_rank1 - ev_rank2。ev_gap < threshold ならそのレースを skip。
ベースライン top_n_ev (top_n=3, ev=1.18) と比較。結果は outputs/ev_gap_experiments/ に保存。
"""

import argparse
import json
import os
import sys
from pathlib import Path

_THIS_DIR = Path(__file__).resolve().parent
_REPO_ROOT = _THIS_DIR.parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

os.environ["KYOTEI_USE_MOTOR_WIN_PROXY"] = os.environ.get("KYOTEI_USE_MOTOR_WIN_PROXY", "1")
os.environ["KYOTEI_FEATURE_SET"] = os.environ.get("KYOTEI_FEATURE_SET", "extended_features")

from kyotei_predictor.tools.rolling_validation_roi import run_rolling_validation_roi

TRAIN_DAYS = 30
TEST_DAYS = 7
STEP_DAYS = 7
EV_GAP_THRESHOLDS = [0.02, 0.03, 0.05, 0.07]
BASELINE_TOP_N = 3
BASELINE_EV = 1.18


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
    output_dir = args.output_dir or _REPO_ROOT / "outputs" / "ev_gap_experiments"
    output_dir.mkdir(parents=True, exist_ok=True)

    strategies: list = []
    # ベースライン: top_n_ev (top_n=3, ev=1.18)
    strategies.append(("baseline_top_n_ev", "top_n_ev", BASELINE_TOP_N, BASELINE_EV))
    for ev_gap in EV_GAP_THRESHOLDS:
        name = f"evgap_{str(ev_gap).replace('.', 'x')}_top{BASELINE_TOP_N}ev{int(BASELINE_EV * 100)}"
        strategies.append((
            name,
            "top_n_ev_gap_filter",
            BASELINE_TOP_N,
            BASELINE_EV,
            None,
            None,
            None,
            ev_gap,
        ))

    print(f"Running rolling validation: {len(strategies)} strategies, n_windows={args.n_windows}...")
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

    baseline_roi = None
    for s in summaries:
        if s.get("strategy") == "top_n_ev" and s.get("ev_threshold") == BASELINE_EV:
            baseline_roi = s.get("overall_roi_selected")
            break

    results = []
    for s in summaries:
        roi = s.get("overall_roi_selected")
        baseline_diff_roi = (
            round(roi - baseline_roi, 2) if roi is not None and baseline_roi is not None else None
        )
        row = {
            "strategy": s.get("strategy"),
            "strategy_name": s.get("strategy_name"),
            "top_n": s.get("top_n"),
            "ev_threshold": s.get("ev_threshold"),
            "ev_gap_threshold": s.get("ev_gap_threshold"),
            "mean_roi_selected": s.get("mean_roi_selected"),
            "median_roi_selected": s.get("median_roi_selected"),
            "overall_roi_selected": roi,
            "total_selected_bets": s.get("total_selected_bets"),
            "hit_rate_rank1_pct": s.get("hit_rate_rank1_pct"),
            "baseline_diff_roi": baseline_diff_roi,
        }
        results.append(row)

    out_path = output_dir / "exp0013_ev_gap_results.json"
    payload = {
        "experiment_id": "EXP-0013",
        "n_windows": args.n_windows,
        "seed": args.seed,
        "baseline": {"strategy": "top_n_ev", "top_n": BASELINE_TOP_N, "ev_threshold": BASELINE_EV},
        "baseline_roi": baseline_roi,
        "results": results,
    }
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    print(f"Saved {out_path}")

    print("\n--- Summary: strategy_name, overall_roi_selected, total_selected_bets, hit_rate_rank1_pct, baseline_diff_roi ---")
    for r in results:
        print(
            f"  {r.get('strategy_name')} -> roi={r.get('overall_roi_selected')}% "
            f"bets={r.get('total_selected_bets')} hit_rate_rank1={r.get('hit_rate_rank1_pct')}% "
            f"diff={r.get('baseline_diff_roi')}%"
        )
    best = max(
        [r for r in results if r.get("overall_roi_selected") is not None],
        key=lambda x: x["overall_roi_selected"],
    )
    print(f"\nBest by overall_roi_selected: {best['strategy_name']} {best.get('overall_roi_selected')}%")
    return 0


if __name__ == "__main__":
    sys.exit(main())
