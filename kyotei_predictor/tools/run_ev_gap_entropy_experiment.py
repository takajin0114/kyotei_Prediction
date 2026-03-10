"""
EXP-0017: EV gap + entropy filter。top_n_ev_gap_filter に skip if race_entropy > threshold を追加。

entropy_threshold 候補 1.2, 1.3, 1.4, 1.5 で sweep。n_w=12。
ベースライン: top_n_ev_gap_filter（ev=1.20, ev_gap=0.07, entropy なし）= EXP-0015 ベスト -12.71%
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
EV_THRESHOLD = 1.20
EV_GAP_THRESHOLD = 0.07

# ベースライン（EXP-0015 ベスト）
BASELINE_ROI = -12.71

# entropy_threshold 候補（skip if race_entropy > threshold）
ENTROPY_THRESHOLDS = [1.2, 1.3, 1.4, 1.5]


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
    # ベースライン: top_n_ev_gap_filter（entropy なし）
    strategies.append((
        "baseline_evgap_top3ev120_evgap0x07",
        "top_n_ev_gap_filter",
        TOP_N,
        EV_THRESHOLD,
        None,
        None,
        None,
        EV_GAP_THRESHOLD,
    ))
    for ent in ENTROPY_THRESHOLDS:
        name = f"evgap_ent_{str(ent).replace('.', 'x')}_top{TOP_N}ev{int(EV_THRESHOLD * 100)}_evgap0x07"
        # (name, strategy, top_n, ev_th, confidence_type, prob_gap_min, entropy_threshold, ev_gap_th)
        strategies.append((
            name,
            "top_n_ev_gap_filter_entropy",
            TOP_N,
            EV_THRESHOLD,
            None,
            None,
            ent,
            EV_GAP_THRESHOLD,
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

    baseline_roi = None
    for s in summaries:
        if s.get("strategy") == "top_n_ev_gap_filter":
            baseline_roi = s.get("overall_roi_selected")
            break

    results = []
    for s in summaries:
        roi = s.get("overall_roi_selected")
        baseline_diff_roi = (
            round(roi - baseline_roi, 2) if roi is not None and baseline_roi is not None else None
        )
        row = {
            "strategy_name": s.get("strategy_name"),
            "strategy": s.get("strategy"),
            "entropy_threshold": s.get("entropy_threshold"),
            "ev_threshold": s.get("ev_threshold"),
            "ev_gap_threshold": s.get("ev_gap_threshold"),
            "overall_roi_selected": roi,
            "total_selected_bets": s.get("total_selected_bets"),
            "hit_rate_rank1_pct": s.get("hit_rate_rank1_pct"),
            "baseline_diff_roi": baseline_diff_roi,
        }
        results.append(row)

    out_path = output_dir / "exp0017_ev_gap_entropy_results.json"
    payload = {
        "experiment_id": "EXP-0017",
        "n_windows": args.n_windows,
        "seed": args.seed,
        "baseline": {
            "strategy": "top_n_ev_gap_filter",
            "ev_threshold": EV_THRESHOLD,
            "ev_gap_threshold": EV_GAP_THRESHOLD,
            "overall_roi_selected": baseline_roi,
        },
        "results": results,
    }
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    print(f"Saved {out_path}")

    print(
        "\n--- Summary: strategy_name, entropy_threshold, ev_threshold, ev_gap_threshold, "
        "overall_roi_selected, total_selected_bets, hit_rate_rank1_pct, baseline_diff_roi ---"
    )
    for r in results:
        print(
            f"  {r.get('strategy_name')} ent={r.get('entropy_threshold')} ev={r.get('ev_threshold')} "
            f"gap={r.get('ev_gap_threshold')} -> roi={r.get('overall_roi_selected')}% "
            f"bets={r.get('total_selected_bets')} hit_rate_rank1={r.get('hit_rate_rank1_pct')}% "
            f"diff={r.get('baseline_diff_roi')}%"
        )

    ev_ent_results = [r for r in results if r.get("entropy_threshold") is not None]
    if ev_ent_results:
        best = max(
            ev_ent_results,
            key=lambda x: x["overall_roi_selected"] if x.get("overall_roi_selected") is not None else -999,
        )
        print(
            f"\nBest with entropy filter: {best['strategy_name']} "
            f"ent={best['entropy_threshold']} roi={best.get('overall_roi_selected')}% "
            f"(baseline_diff={best.get('baseline_diff_roi')}%)"
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
