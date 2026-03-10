"""
EXP-0016: EXP-0015 ベスト近傍の局所探索。top_n_ev_gap_filter。

ev_threshold × ev_gap_threshold の追加グリッド（1.19/1.20/1.21 × 0.06/0.07/0.08）を n_w=12 で検証。
ベースライン（EXP-0015 ベスト）: ev=1.20, ev_gap=0.07, overall_roi=-12.71%
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
TOP_N = 3

# EXP-0015 ベスト近傍の追加グリッド
EV_THRESHOLDS = [1.19, 1.20, 1.21]
EV_GAP_THRESHOLDS = [0.06, 0.07, 0.08]

# EXP-0015 ベスト（比較基準）
EXP0015_BEST_EV = 1.20
EXP0015_BEST_EV_GAP = 0.07
EXP0015_BEST_ROI = -12.71


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
    for ev_th in EV_THRESHOLDS:
        for ev_gap in EV_GAP_THRESHOLDS:
            name = (
                f"evgap_{str(ev_gap).replace('.', 'x')}_top{TOP_N}ev{int(ev_th * 100)}"
            )
            strategies.append((
                name,
                "top_n_ev_gap_filter",
                TOP_N,
                ev_th,
                None,
                None,
                None,
                ev_gap,
            ))

    print(
        f"Running rolling validation: {len(strategies)} strategies, n_windows={args.n_windows}..."
    )
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
        roi = s.get("overall_roi_selected")
        baseline_diff_roi = (
            round(roi - EXP0015_BEST_ROI, 2)
            if roi is not None
            else None
        )
        row = {
            "strategy_name": s.get("strategy_name"),
            "strategy": s.get("strategy"),
            "ev_threshold": s.get("ev_threshold"),
            "ev_gap_threshold": s.get("ev_gap_threshold"),
            "overall_roi_selected": roi,
            "total_selected_bets": s.get("total_selected_bets"),
            "hit_rate_rank1_pct": s.get("hit_rate_rank1_pct"),
            "baseline_diff_roi": baseline_diff_roi,
        }
        results.append(row)

    out_path = output_dir / "exp0016_ev_gap_near_local_search_results.json"
    payload = {
        "experiment_id": "EXP-0016",
        "n_windows": args.n_windows,
        "seed": args.seed,
        "baseline_exp0015": {
            "ev_threshold": EXP0015_BEST_EV,
            "ev_gap_threshold": EXP0015_BEST_EV_GAP,
            "overall_roi_selected": EXP0015_BEST_ROI,
        },
        "results": results,
    }
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    print(f"Saved {out_path}")

    print(
        "\n--- Summary: strategy_name, ev_threshold, ev_gap_threshold, "
        "overall_roi_selected, total_selected_bets, hit_rate_rank1_pct, baseline_diff_roi ---"
    )
    for r in results:
        print(
            f"  {r.get('strategy_name')} ev={r.get('ev_threshold')} gap={r.get('ev_gap_threshold')} "
            f"-> roi={r.get('overall_roi_selected')}% bets={r.get('total_selected_bets')} "
            f"hit_rate_rank1={r.get('hit_rate_rank1_pct')}% diff={r.get('baseline_diff_roi')}%"
        )

    best = max(
        [r for r in results if r.get("overall_roi_selected") is not None],
        key=lambda x: x["overall_roi_selected"],
    )
    print(
        f"\nBest by overall_roi_selected: {best['strategy_name']} "
        f"ev={best['ev_threshold']} gap={best['ev_gap_threshold']} "
        f"roi={best.get('overall_roi_selected')}% (baseline_diff={best.get('baseline_diff_roi')}%)"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
