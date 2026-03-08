#!/usr/bin/env python3
"""
EV threshold sweep: ev_threshold_only 戦略で threshold 1.05〜1.25 を比較。
各 threshold で ROI, bet_count, profit を計算。scripts/ から実行（リポジトリルートで実行すること）。
"""

import argparse
import json
import statistics
import sys
from pathlib import Path

_SCRIPT_DIR = Path(__file__).resolve().parent
_PROJECT_ROOT = _SCRIPT_DIR.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from kyotei_predictor.tools.rolling_validation_roi import run_rolling_validation_roi

EV_THRESHOLDS = [1.05, 1.10, 1.15, 1.20, 1.25]


def main() -> int:
    parser = argparse.ArgumentParser(description="EV threshold sweep with ev_threshold_only strategy")
    parser.add_argument("--db-path", required=True, help="SQLite DB path (races)")
    parser.add_argument("--output-dir", type=Path, default=None)
    parser.add_argument("--data-dir", type=Path, default=None)
    parser.add_argument("--n-windows", type=int, default=12)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    raw_dir = args.data_dir or _PROJECT_ROOT / "kyotei_predictor" / "data" / "raw"
    if not raw_dir.is_dir():
        raw_dir = Path("kyotei_predictor/data/raw")
    output_dir = args.output_dir or _PROJECT_ROOT / "outputs"
    output_dir.mkdir(parents=True, exist_ok=True)

    strategies = [(f"ev_{ev}", "ev_threshold_only", 0, ev) for ev in EV_THRESHOLDS]
    summaries, per_strategy_windows = run_rolling_validation_roi(
        db_path=args.db_path,
        output_dir=output_dir,
        data_dir_raw=raw_dir,
        train_days=30,
        test_days=7,
        step_days=7,
        n_windows=args.n_windows,
        strategies=strategies,
        seed=args.seed,
    )

    results = []
    for s, windows in zip(summaries, per_strategy_windows):
        total_bet = s.get("total_bet_selected") or 0
        total_payout = s.get("total_payout_selected") or 0
        bet_count = s.get("total_selected_bets") or 0
        roi = s.get("overall_roi_selected")
        profit = round(total_payout - total_bet, 2) if total_bet else 0.0
        rois = [w["roi_selected"] for w in windows]
        max_dd = _max_drawdown(windows)
        results.append({
            "ev_threshold": s["ev_threshold"],
            "roi": roi,
            "mean_roi": s.get("mean_roi_selected"),
            "median_roi": s.get("median_roi_selected"),
            "overall_roi": roi,
            "bet_count": bet_count,
            "profit": profit,
            "max_drawdown": max_dd,
        })

    out_path = output_dir / "ev_threshold_sweep_results.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump({"ev_thresholds": EV_THRESHOLDS, "results": results}, f, ensure_ascii=False, indent=2)
    print(f"Saved {out_path}")
    for r in results:
        print(f"  ev={r['ev_threshold']}: roi={r.get('roi')}% bet_count={r['bet_count']} profit={r['profit']}")
    return 0


def _max_drawdown(windows: list) -> float:
    """window 単位の ROI から簡易 max drawdown（累積利益の最大下落幅）を計算。"""
    if not windows:
        return 0.0
    cum = 0.0
    peak = 0.0
    max_dd = 0.0
    for w in windows:
        total_bet = w.get("total_bet_selected") or 0
        total_payout = w.get("total_payout_selected") or 0
        cum += (total_payout - total_bet) if total_bet else 0
        if cum > peak:
            peak = cum
        dd = peak - cum
        if dd > max_dd:
            max_dd = dd
    return round(max_dd, 2)


if __name__ == "__main__":
    raise SystemExit(main())
