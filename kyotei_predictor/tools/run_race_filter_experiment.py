"""
EXP-0010: race_filtered_top_n_ev のグリッド実験。

実験パラメータ:
  top_n = 2, 3
  ev_threshold = 1.15, 1.18, 1.20
  prob_gap_min = 0.03, 0.05, 0.07
  entropy_max = 1.5, 1.7

ベースライン top_n_ev も含めて比較。結果は outputs/race_filter_experiments/ に保存。
"""

import argparse
import json
import os
import sys
from pathlib import Path

_THIS_DIR = Path(__file__).resolve().parent
# リポジトリルート = kyotei_predictor/tools の2つ上
_REPO_ROOT = _THIS_DIR.parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

os.environ["KYOTEI_USE_MOTOR_WIN_PROXY"] = os.environ.get("KYOTEI_USE_MOTOR_WIN_PROXY", "1")
os.environ["KYOTEI_FEATURE_SET"] = os.environ.get("KYOTEI_FEATURE_SET", "extended_features")

from kyotei_predictor.tools.rolling_validation_roi import run_rolling_validation_roi

TRAIN_DAYS = 30
TEST_DAYS = 7
STEP_DAYS = 7
TOP_N_VALUES = [2, 3]
EV_VALUES = [1.15, 1.18, 1.20]
PROB_GAP_VALUES = [0.03, 0.05, 0.07]
ENTROPY_MAX_VALUES = [1.5, 1.7]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db-path", required=True, help="SQLite DB path")
    parser.add_argument("--output-dir", type=Path, default=None)
    parser.add_argument("--n-windows", type=int, default=12)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--quick", action="store_true", help="小さいグリッドのみ（top_n=3, ev=1.18, pg=0.05, ent=1.7）")
    args = parser.parse_args()

    raw_dir = _REPO_ROOT / "kyotei_predictor" / "data" / "raw"
    if not raw_dir.is_dir():
        raw_dir = Path("kyotei_predictor/data/raw")
    output_dir = args.output_dir or _REPO_ROOT / "outputs" / "race_filter_experiments"
    output_dir.mkdir(parents=True, exist_ok=True)

    strategies: list = []
    # ベースライン: top_n_ev
    for ev in EV_VALUES:
        strategies.append((f"top_n_ev_ev{int(ev*100)}", "top_n_ev", 3, ev))
    # race_filtered_top_n_ev グリッド (name, strategy, top_n, ev_threshold, confidence_type, prob_gap_min, entropy_max)
    if args.quick:
        strategies.append((
            "racefilter_top3_ev118_pg5_ent17",
            "race_filtered_top_n_ev",
            3,
            1.18,
            None,
            0.05,
            1.7,
        ))
    else:
        for top_n in TOP_N_VALUES:
            for ev in EV_VALUES:
                for pg in PROB_GAP_VALUES:
                    for ent in ENTROPY_MAX_VALUES:
                        name = f"racefilter_top{top_n}_ev{int(ev*100)}_pg{int(pg*100)}_ent{int(ent*10)}"
                        strategies.append((name, "race_filtered_top_n_ev", top_n, ev, None, pg, ent))

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

    # ベースライン ROI（top_n_ev ev=1.18）を取得
    baseline_roi = None
    for s in summaries:
        if s.get("strategy") == "top_n_ev" and s.get("ev_threshold") == 1.18:
            baseline_roi = s.get("overall_roi_selected")
            break
    if baseline_roi is None:
        baseline_roi = next(
            (s.get("overall_roi_selected") for s in summaries if "top_n_ev" in (s.get("strategy_name") or "") and s.get("ev_threshold") == 1.18),
            None,
        )

    results = []
    for s in summaries:
        roi = s.get("overall_roi_selected")
        baseline_diff_roi = (round(roi - baseline_roi, 2) if roi is not None and baseline_roi is not None else None)
        row = {
            "strategy": s.get("strategy"),
            "strategy_name": s.get("strategy_name"),
            "top_n": s.get("top_n"),
            "ev_threshold": s.get("ev_threshold"),
            "prob_gap_min": s.get("prob_gap_min"),
            "entropy_max": s.get("entropy_max"),
            "mean_roi_selected": s.get("mean_roi_selected"),
            "median_roi_selected": s.get("median_roi_selected"),
            "overall_roi_selected": roi,
            "total_selected_bets": s.get("total_selected_bets"),
            "hit_rate_rank1_pct": s.get("hit_rate_rank1_pct"),
            "selected_race_count": s.get("selected_race_count"),
            "selected_race_ratio": s.get("selected_race_ratio"),
            "avg_bets_per_selected_race": s.get("avg_bets_per_selected_race"),
            "total_evaluated_races": s.get("total_evaluated_races"),
            "baseline_roi_selected": baseline_roi,
            "baseline_diff_roi": baseline_diff_roi,
            "mean_log_loss": s.get("mean_log_loss"),
            "mean_brier_score": s.get("mean_brier_score"),
        }
        results.append(row)
        print(
            f"  {s.get('strategy_name')} -> roi={roi}% diff_baseline={baseline_diff_roi}% "
            f"bets={s.get('total_selected_bets')} races_sel={s.get('selected_race_count')} "
            f"hit_rate_rank1={s.get('hit_rate_rank1_pct')}"
        )

    out = {
        "experiment_id": "EXP-0010",
        "full_grid": not args.quick,
        "model": "xgboost",
        "calibration": "sigmoid",
        "features": "extended_features",
        "n_windows": args.n_windows,
        "seed": args.seed,
        "baseline_roi_selected": baseline_roi,
        "results": results,
    }
    out_name = "exp0010_race_filter_full_results.json" if not args.quick else "exp0010_race_filter_results.json"
    out_path = output_dir / out_name
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    print(f"Saved {out_path}")

    # 診断用サマリ表（全項目）
    print("\n--- Summary table (all strategies) ---")
    print(
        f"{'strategy_name':<35} {'roi%':>8} {'diff_base':>9} {'bets':>7} "
        f"{'races_sel':>9} {'sel_ratio':>9} {'avg_bet/race':>11} {'hit_r1%':>8}"
    )
    for r in results:
        print(
            f"{str(r.get('strategy_name') or ''):<35} "
            f"{r.get('overall_roi_selected') or 0:>7.2f}% "
            f"{r.get('baseline_diff_roi') or 0:>+8.2f}% "
            f"{r.get('total_selected_bets') or 0:>7} "
            f"{r.get('selected_race_count') or 0:>9} "
            f"{r.get('selected_race_ratio') or 0:>9.4f} "
            f"{r.get('avg_bets_per_selected_race') or 0:>11.2f} "
            f"{r.get('hit_rate_rank1_pct') or 0:>7.2f}%"
        )

    # ROI ランキング（overall_roi_selected の良い順）
    by_roi = sorted(
        [r for r in results if r.get("overall_roi_selected") is not None],
        key=lambda x: x["overall_roi_selected"],
        reverse=True,
    )
    print("\nTop 5 by overall_roi_selected:")
    for i, r in enumerate(by_roi[:5], 1):
        print(f"  {i}. {r['strategy_name']} {r['overall_roi_selected']}% bets={r['total_selected_bets']} diff={r.get('baseline_diff_roi')}%")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
