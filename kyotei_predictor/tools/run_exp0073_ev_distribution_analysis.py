"""
EXP-0073: EV distribution analysis.

主軸戦略（4.50≤EV<4.75, prob≥0.05）の前提で、EV帯ごとの利益分布を分析し利益源EV帯を特定する。
分析対象 baseline: 4.30 ≤ EV < 6.00, prob ≥ 0.05, difficulty filter なし。
共通: calibration=sigmoid, switch_dd4000, n_windows=36, skip_top20pct。ref_profit は 4.30≤EV<4.75 で算出。

出力: outputs/ev_distribution/exp0073_ev_distribution.json, exp0073_ev_distribution.csv
"""

import argparse
import csv
import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Tuple

_THIS_DIR = Path(__file__).resolve().parent
_REPO_ROOT = _THIS_DIR.parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

os.environ["KYOTEI_USE_MOTOR_WIN_PROXY"] = os.environ.get("KYOTEI_USE_MOTOR_WIN_PROXY", "1")
os.environ["KYOTEI_FEATURE_SET"] = os.environ.get("KYOTEI_FEATURE_SET", "extended_features")

from kyotei_predictor.tools.rolling_validation_roi import (
    build_windows,
    get_db_date_range,
    run_rolling_validation_roi,
)
from kyotei_predictor.tools.rolling_validation_windows import _date_range
from kyotei_predictor.infrastructure.repositories.race_data_repository_factory import (
    get_race_data_repository,
)
from kyotei_predictor.tools.run_exp0042_selection_verified import (
    FIXED_STAKE,
    SKIP_TOP_PCT,
    STRATEGIES,
    STRATEGY_SUFFIX,
    _all_bets_for_race,
    _filter_bets_by_selection,
    _max_ev_for_race,
    _resolve_db_path,
)

TRAIN_DAYS = 30
TEST_DAYS = 7
STEP_DAYS = 7
N_WINDOWS = 36

# 分析対象 baseline: 4.30 ≤ EV < 6.00, prob ≥ 0.05
ANALYSIS_EV_LO = 4.30
ANALYSIS_EV_HI = 6.00
PROB_MIN = 0.05
# ref_profit 算出は EXP-0070 と同一
REF_EV_LO, REF_EV_HI, REF_PROB_MIN = 4.30, 4.75, 0.05

# EV bin 定義 (label, lo, hi) 左閉右開 [lo, hi)
EV_BINS: List[Tuple[str, float, float]] = [
    ("1.00-1.20", 1.00, 1.20),
    ("1.20-1.50", 1.20, 1.50),
    ("1.50-2.00", 1.50, 2.00),
    ("2.00-2.50", 2.00, 2.50),
    ("2.50-3.00", 2.50, 3.00),
    ("3.00-3.50", 3.00, 3.50),
    ("3.50-4.00", 3.50, 4.00),
    ("4.00-4.30", 4.00, 4.30),
    ("4.30-4.50", 4.30, 4.50),
    ("4.50-4.75", 4.50, 4.75),
    ("4.75-5.00", 4.75, 5.00),
    ("5.00-6.00", 5.00, 6.00),
]

BetTuple = Tuple[float, float, float, bool]  # (ev, prob, odds, hit)


def _ev_to_bin(ev: float) -> str:
    for label, lo, hi in EV_BINS:
        if lo <= ev < hi:
            return label
    return "other"


def _stake_schedule_dd(n_w: int, ref_profit: List[float], dd_threshold: int = 4000) -> List[int]:
    schedule = [100] * n_w
    cum = peak = 0.0
    for wi in range(n_w):
        cum += ref_profit[wi]
        if cum > peak:
            peak = cum
        if peak - cum >= dd_threshold:
            schedule[wi] = 80
    return schedule


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db-path", type=str, default=None)
    parser.add_argument("--output-dir", type=Path, default=None)
    parser.add_argument("--predictions-dir", type=Path, default=None)
    parser.add_argument("--n-windows", type=int, default=N_WINDOWS)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    n_w = args.n_windows
    if n_w <= 0:
        n_w = N_WINDOWS

    db_path_resolved = _resolve_db_path(args.db_path)
    if not db_path_resolved.exists():
        print("[EXP-0073] ERROR: DB not found: {}".format(db_path_resolved), file=sys.stderr)
        return 1
    db_path_str = str(db_path_resolved)
    print("[EXP-0073] DB found: {}".format(db_path_str))

    raw_dir = _REPO_ROOT / "kyotei_predictor" / "data" / "raw"
    if not raw_dir.is_dir():
        raw_dir = Path("kyotei_predictor/data/raw")

    output_dir = args.output_dir or _REPO_ROOT / "outputs" / "ev_distribution"
    output_dir.mkdir(parents=True, exist_ok=True)

    pred_parent = args.predictions_dir or _REPO_ROOT / "outputs" / "ev_cap_experiments"
    out_pred_dir = pred_parent / "rolling_roi_predictions"

    min_date, max_date = get_db_date_range(db_path_str)
    window_list_full = build_windows(
        min_date, max_date, TRAIN_DAYS, TEST_DAYS, STEP_DAYS, n_w
    )
    if len(window_list_full) < n_w:
        n_w = len(window_list_full)
    window_list = list(window_list_full[:n_w])

    need_days = set()
    for _ts, _te, tst, tend in window_list:
        for d in _date_range(tst, tend):
            need_days.add(d)
    existing = set()
    if out_pred_dir.exists():
        for p in out_pred_dir.glob("predictions_baseline_*" + STRATEGY_SUFFIX + ".json"):
            stem = p.stem
            date_part = stem.replace("predictions_baseline_", "").replace(STRATEGY_SUFFIX, "")
            if len(date_part) == 10 and date_part[4] == "-" and date_part[7] == "-":
                existing.add(date_part)
    if need_days and not need_days.issubset(existing):
        print("EXP-0073: Running rolling validation (n_windows={})...".format(n_w))
        run_rolling_validation_roi(
            db_path=db_path_str,
            output_dir=pred_parent,
            data_dir_raw=raw_dir,
            train_days=TRAIN_DAYS,
            test_days=TEST_DAYS,
            step_days=STEP_DAYS,
            n_windows=n_w,
            strategies=STRATEGIES,
            model_type="xgboost",
            calibration="sigmoid",
            feature_set="extended_features",
            seed=args.seed,
        )
    else:
        print("EXP-0073: Using existing predictions in {}.".format(out_pred_dir))

    repo = get_race_data_repository("db", data_dir=raw_dir, db_path=db_path_str)

    day_races_raw: Dict[str, List[Tuple[float, List[BetTuple]]]] = {}
    for wi, (_ts, _te, tst, tend) in enumerate(window_list):
        for day in _date_range(tst, tend):
            path = out_pred_dir / f"predictions_baseline_{day}{STRATEGY_SUFFIX}.json"
            if not path.exists():
                continue
            try:
                with open(path, encoding="utf-8") as f:
                    pred = json.load(f)
            except Exception:
                continue
            prediction_date = pred.get("prediction_date") or day
            predictions_list = pred.get("predictions") or []
            races_data = []
            for race in predictions_list:
                max_ev = _max_ev_for_race(race)
                bets = _all_bets_for_race(race, prediction_date, repo)
                if bets is not None:
                    races_data.append((max_ev, bets))
            if races_data:
                day_races_raw[day] = races_data

    day_to_wi: Dict[str, int] = {}
    for wi, (_ts, _te, tst, tend) in enumerate(window_list):
        if wi >= n_w:
            break
        for day in _date_range(tst, tend):
            day_to_wi[day] = wi

    ref_profit = [0.0] * n_w
    for day, races_data in day_races_raw.items():
        wi = day_to_wi.get(day, -1)
        if wi < 0 or wi >= n_w:
            continue
        races_sorted = sorted(races_data, key=lambda x: -x[0])
        n = len(races_sorted)
        k_skip = int(n * SKIP_TOP_PCT)
        idx_start = min(k_skip, n)
        for max_ev, bets in races_sorted[idx_start:]:
            for _ev, _prob, odds, hit in _filter_bets_by_selection(bets, REF_EV_LO, REF_EV_HI, REF_PROB_MIN):
                ref_profit[wi] += (FIXED_STAKE * odds if hit else 0.0) - FIXED_STAKE
    schedule = _stake_schedule_dd(n_w, ref_profit, 4000)

    # EV bin ごとに集計: stake, payout, bet_count, hit_count, sum_odds
    bin_agg: Dict[str, Dict] = {label: {"stake": 0.0, "payout": 0.0, "bet_count": 0, "hit_count": 0, "sum_odds": 0.0} for label, _, _ in EV_BINS}
    bin_agg["other"] = {"stake": 0.0, "payout": 0.0, "bet_count": 0, "hit_count": 0, "sum_odds": 0.0}

    window_set = {wi for wi in range(n_w)}
    for day, races_data in day_races_raw.items():
        wi = day_to_wi.get(day, -1)
        if wi not in window_set or wi >= len(schedule):
            continue
        st = schedule[wi]
        races_sorted = sorted(races_data, key=lambda x: -x[0])
        n = len(races_sorted)
        k_skip = int(n * SKIP_TOP_PCT)
        idx_start = min(k_skip, n)
        for max_ev, bets in races_sorted[idx_start:]:
            filtered = _filter_bets_by_selection(bets, ANALYSIS_EV_LO, ANALYSIS_EV_HI, PROB_MIN)
            for ev, _prob, odds, hit in filtered:
                b = _ev_to_bin(ev)
                bin_agg[b]["stake"] += st
                bin_agg[b]["payout"] += st * odds if hit else 0.0
                bin_agg[b]["bet_count"] += 1
                if hit:
                    bin_agg[b]["hit_count"] += 1
                bin_agg[b]["sum_odds"] += odds

    rows: List[Dict] = []
    for label, _lo, _hi in EV_BINS:
        d = bin_agg[label]
        bc = d["bet_count"]
        stake = d["stake"]
        payout = d["payout"]
        total_profit = round(payout - stake, 2)
        roi = round((payout / stake - 1) * 100, 2) if stake else None
        hit_rate = round(d["hit_count"] / bc * 100, 2) if bc else None
        avg_odds = round(d["sum_odds"] / bc, 2) if bc else None
        profit_per_1000 = round(1000.0 * (payout - stake) / bc, 2) if bc else None
        rows.append({
            "ev_bin": label,
            "ROI": roi,
            "total_profit": total_profit,
            "bet_count": bc,
            "hit_rate": hit_rate,
            "avg_odds": avg_odds,
            "profit_per_1000_bets": profit_per_1000,
        })
    if bin_agg["other"]["bet_count"]:
        d = bin_agg["other"]
        bc = d["bet_count"]
        stake = d["stake"]
        payout = d["payout"]
        rows.append({
            "ev_bin": "other",
            "ROI": round((payout / stake - 1) * 100, 2) if stake else None,
            "total_profit": round(payout - stake, 2),
            "bet_count": bc,
            "hit_rate": round(d["hit_count"] / bc * 100, 2) if bc else None,
            "avg_odds": round(d["sum_odds"] / bc, 2) if bc else None,
            "profit_per_1000_bets": round(1000.0 * (payout - stake) / bc, 2) if bc else None,
        })

    payload = {
        "experiment_id": "EXP-0073",
        "purpose": "EV distribution analysis: baseline 4.30<=EV<6.00, prob>=0.05, n_w=36",
        "db_path_used": db_path_str,
        "n_windows": n_w,
        "calibration": "sigmoid",
        "risk_control": "switch_dd4000",
        "selection": {"ev_lo": ANALYSIS_EV_LO, "ev_hi": ANALYSIS_EV_HI, "prob_min": PROB_MIN},
        "ref_profit": "4.30<=EV<4.75",
        "skip_top20pct": SKIP_TOP_PCT,
        "ev_bins": [{"label": lb, "lo": lo, "hi": hi} for lb, lo, hi in EV_BINS],
        "by_ev_bin": rows,
    }

    out_json = output_dir / "exp0073_ev_distribution.json"
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    print("Saved {}".format(out_json))

    out_csv = output_dir / "exp0073_ev_distribution.csv"
    with open(out_csv, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["ev_bin", "ROI", "total_profit", "bet_count", "hit_rate", "avg_odds", "profit_per_1000_bets"])
        w.writeheader()
        w.writerows(rows)
    print("Saved {}".format(out_csv))

    print("\n--- EXP-0073 EV distribution (n_windows={}, baseline 4.30<=EV<6.00) ---".format(n_w))
    print("ev_bin      | ROI     | total_profit | bet_count | hit_rate | avg_odds | profit_per_1000_bets")
    print("-" * 95)
    for r in rows:
        if r["bet_count"] == 0:
            continue
        print("  {:10} | {:6}% | {:12} | {:9} | {:7}% | {:8} | {:20}".format(
            r["ev_bin"],
            r["ROI"] if r["ROI"] is not None else "—",
            r["total_profit"],
            r["bet_count"],
            r["hit_rate"] if r["hit_rate"] is not None else "—",
            r["avg_odds"] if r["avg_odds"] is not None else "—",
            r["profit_per_1000_bets"] if r["profit_per_1000_bets"] is not None else "—",
        ))

    return 0


if __name__ == "__main__":
    sys.exit(main())
