"""
EXP-0019: EV gap + odds band + max bets per race。top_n_ev_gap_filter_odds_band に 1 レースあたり最大購入点数を追加。

max_bets_per_race 候補 1, 2。ベースラインは odds_band のみ（制限なし＝最大3点/レース）。n_w=12。
条件: top_n=3, ev=1.20, ev_gap=0.07, odds_low=1.3, odds_high=25。
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
ODDS_LOW = 1.3
ODDS_HIGH = 25

MAX_BETS_PER_RACE_CANDIDATES = [1, 2]


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
    # ベースライン: odds_band のみ（max_bets_per_race 制限なし＝最大3点/レース）
    strategies.append((
        "baseline_odds1x3_25_top3ev120_evgap0x07",
        "top_n_ev_gap_filter_odds_band",
        TOP_N,
        EV_THRESHOLD,
        None,
        None,
        None,
        EV_GAP_THRESHOLD,
        ODDS_LOW,
        ODDS_HIGH,
    ))
    for mx in MAX_BETS_PER_RACE_CANDIDATES:
        name = f"odds1x3_25_max{mx}_top3ev120_evgap0x07"
        strategies.append((
            name,
            "top_n_ev_gap_filter_odds_band_bet_limit",
            TOP_N,
            EV_THRESHOLD,
            None,
            None,
            None,
            EV_GAP_THRESHOLD,
            ODDS_LOW,
            ODDS_HIGH,
            mx,
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
        if s.get("strategy") == "top_n_ev_gap_filter_odds_band":
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
            "max_bets_per_race": s.get("max_bets_per_race"),
            "overall_roi_selected": roi,
            "total_selected_bets": s.get("total_selected_bets"),
            "hit_rate_rank1_pct": s.get("hit_rate_rank1_pct"),
            "baseline_diff_roi": baseline_diff_roi,
        }
        results.append(row)

    out_path = output_dir / "exp0019_ev_gap_odds_band_bet_limit_results.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(
            {"n_windows": args.n_windows, "seed": args.seed, "results": results},
            f,
            ensure_ascii=False,
            indent=2,
        )
    print(f"Wrote {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
