"""
EXP-0012: EV スコア再設計（top_n_ev_power_prob）のグリッド実験。

EV_adj = (pred_prob ** alpha) * odds でスコア化し、ev_threshold 以上から top_n 選抜。

実験パラメータ:
  alpha: 0.7, 0.8, 0.9, 1.0, 1.1
  top_n: 2, 3
  ev_threshold: 1.15, 1.17, 1.18, 1.19, 1.20

ベースライン: top_n_ev top_n=3 ev=1.18
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
ALPHA_VALUES = [0.7, 0.8, 0.9, 1.0, 1.1]
TOP_N_VALUES = [2, 3]
EV_VALUES = [1.15, 1.17, 1.18, 1.19, 1.20]


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
    output_dir = args.output_dir or _REPO_ROOT / "outputs" / "power_prob_experiments"
    output_dir.mkdir(parents=True, exist_ok=True)

    strategies: list = []
    # ベースライン: top_n_ev top_n=3 ev=1.18
    strategies.append(("top_n_ev_ev118", "top_n_ev", 3, 1.18))
    # top_n_ev_power_prob: (name, strategy, top_n, ev_threshold, None, alpha, None)
    for alpha in ALPHA_VALUES:
        for tn in TOP_N_VALUES:
            for ev in EV_VALUES:
                name = f"powerprob_a{str(alpha).replace('.', 'x')}_top{tn}_ev{int(ev*100)}"
                strategies.append((name, "top_n_ev_power_prob", tn, ev, None, alpha, None))

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
        if s.get("strategy") == "top_n_ev" and s.get("ev_threshold") == 1.18:
            baseline_roi = s.get("overall_roi_selected")
            break

    results = []
    for s in summaries:
        roi = s.get("overall_roi_selected")
        results.append({
            "strategy": s.get("strategy"),
            "strategy_name": s.get("strategy_name"),
            "alpha": s.get("alpha"),
            "top_n": s.get("top_n"),
            "ev_threshold": s.get("ev_threshold"),
            "overall_roi_selected": roi,
            "total_selected_bets": s.get("total_selected_bets"),
            "hit_rate_rank1_pct": s.get("hit_rate_rank1_pct"),
            "baseline_roi_selected": baseline_roi,
            "baseline_diff_roi": round(roi - baseline_roi, 2) if roi is not None and baseline_roi is not None else None,
        })
        print(
            f"  {s.get('strategy_name')} alpha={s.get('alpha')} top_n={s.get('top_n')} ev={s.get('ev_threshold')} "
            f"-> roi={roi}% diff={round(roi - baseline_roi, 2) if (roi is not None and baseline_roi is not None) else None}% "
            f"bets={s.get('total_selected_bets')}"
        )

    out = {
        "experiment_id": "EXP-0012",
        "model": "xgboost",
        "calibration": "sigmoid",
        "features": "extended_features",
        "n_windows": args.n_windows,
        "seed": args.seed,
        "baseline_roi_selected": baseline_roi,
        "results": results,
    }
    out_path = output_dir / "exp0012_power_prob_results.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    print(f"Saved {out_path}")

    print("\n--- Summary: strategy, alpha, top_n, ev_threshold, overall_roi_selected, total_selected_bets, hit_rate_rank1_pct ---")
    for r in results:
        print(
            f"  {r.get('strategy_name')} | alpha={r.get('alpha')} top_n={r.get('top_n')} ev={r.get('ev_threshold')} | "
            f"roi={r.get('overall_roi_selected')}% | bets={r.get('total_selected_bets')} | hit_r1={r.get('hit_rate_rank1_pct')}%"
        )

    by_roi = sorted(
        [r for r in results if r.get("overall_roi_selected") is not None],
        key=lambda x: x["overall_roi_selected"],
        reverse=True,
    )
    print("\nTop 5 by overall_roi_selected:")
    for i, r in enumerate(by_roi[:5], 1):
        print(f"  {i}. {r['strategy_name']} {r['overall_roi_selected']}% (diff={r.get('baseline_diff_roi')}%)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
