"""
EXP-0074: profit zone decomposition analysis.

利益源EV帯（4.50≤EV<4.75, prob≥0.05）の内部構造を分析し、勝つ条件・負ける条件を特定する。
分析軸: odds_band, prob_band, top1_prob_band, venue, race_number_band。

共通: calibration=sigmoid, switch_dd4000, n_windows=36, skip_top20pct。ref_profit は 4.30≤EV<4.75 で算出。
出力: outputs/profit_zone/exp0074_profit_zone.json, exp0074_profit_zone.csv
"""

import argparse
import csv
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple

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

# 分析対象: 利益源EV帯のみ
ZONE_EV_LO, ZONE_EV_HI = 4.50, 4.75
PROB_MIN = 0.05
REF_EV_LO, REF_EV_HI, REF_PROB_MIN = 4.30, 4.75, 0.05

BetTuple = Tuple[float, float, float, bool]  # (ev, prob, odds, hit)


def _top1_prob_for_race(race: dict) -> float:
    all_comb = race.get("all_combinations") or []
    probs = [
        float(c.get("probability") or c.get("score", 0))
        for c in all_comb
        if c.get("probability") is not None or c.get("score") is not None
    ]
    return max(probs) if probs else 0.0


def _odds_band(odds: float) -> str:
    if odds < 10:
        return "0-10"
    if odds < 20:
        return "10-20"
    if odds < 30:
        return "20-30"
    if odds < 50:
        return "30-50"
    return "50+"


def _prob_band(prob: float) -> str:
    if prob < 0.07:
        return "0.05-0.07"
    if prob < 0.09:
        return "0.07-0.09"
    if prob < 0.12:
        return "0.09-0.12"
    return "0.12+"


def _top1_prob_band(top1: float) -> str:
    if top1 < 0.30:
        return "0-0.30"
    if top1 < 0.40:
        return "0.30-0.40"
    return "0.40+"


def _race_number_band(rno: int) -> str:
    if rno <= 3:
        return "1-3"
    if rno <= 6:
        return "4-6"
    if rno <= 9:
        return "7-9"
    return "10-12"


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


def _agg_to_row(agg: Dict[str, Any]) -> Dict[str, Any]:
    bc = agg["bet_count"]
    stake = agg["stake"]
    payout = agg["payout"]
    total_profit = round(payout - stake, 2)
    roi = round((payout / stake - 1) * 100, 2) if stake else None
    hit_rate = round(agg["hit_count"] / bc * 100, 2) if bc else None
    avg_odds = round(agg["sum_odds"] / bc, 2) if bc else None
    profit_per_1000 = round(1000.0 * (payout - stake) / bc, 2) if bc else None
    return {
        "ROI": roi,
        "total_profit": total_profit,
        "bet_count": bc,
        "hit_rate": hit_rate,
        "avg_odds": avg_odds,
        "profit_per_1000_bets": profit_per_1000,
    }


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
        print("[EXP-0074] ERROR: DB not found: {}".format(db_path_resolved), file=sys.stderr)
        return 1
    db_path_str = str(db_path_resolved)
    print("[EXP-0074] DB found: {}".format(db_path_str))

    raw_dir = _REPO_ROOT / "kyotei_predictor" / "data" / "raw"
    if not raw_dir.is_dir():
        raw_dir = Path("kyotei_predictor/data/raw")
    output_dir = args.output_dir or _REPO_ROOT / "outputs" / "profit_zone"
    output_dir.mkdir(parents=True, exist_ok=True)
    pred_parent = args.predictions_dir or _REPO_ROOT / "outputs" / "ev_cap_experiments"
    out_pred_dir = pred_parent / "rolling_roi_predictions"

    min_date, max_date = get_db_date_range(db_path_str)
    window_list_full = build_windows(min_date, max_date, TRAIN_DAYS, TEST_DAYS, STEP_DAYS, n_w)
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
        print("EXP-0074: Running rolling validation (n_windows={})...".format(n_w))
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
        print("EXP-0074: Using existing predictions in {}.".format(out_pred_dir))

    repo = get_race_data_repository("db", data_dir=raw_dir, db_path=db_path_str)

    # (max_ev, bets, top1_prob, venue, race_number)
    day_races_raw: Dict[str, List[Tuple[float, List[BetTuple], float, str, int]]] = {}
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
                top1 = _top1_prob_for_race(race)
                venue = (race.get("venue") or "").strip()
                rno = int(race.get("race_number") or 0)
                if bets is not None:
                    races_data.append((max_ev, bets, top1, venue, rno))
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
        for max_ev, bets, _top1, _v, _r in races_sorted[idx_start:]:
            for _ev, _prob, odds, hit in _filter_bets_by_selection(bets, REF_EV_LO, REF_EV_HI, REF_PROB_MIN):
                ref_profit[wi] += (FIXED_STAKE * odds if hit else 0.0) - FIXED_STAKE
    schedule = _stake_schedule_dd(n_w, ref_profit, 4000)

    # dimension -> bin -> agg
    dims: Dict[str, Dict[str, Dict[str, Any]]] = {
        "odds_band": {},
        "prob_band": {},
        "top1_prob_band": {},
        "venue": {},
        "race_number_band": {},
    }
    for dim in dims:
        dims[dim] = {}

    def _get_agg(dimension: str, bin_name: str) -> Dict[str, Any]:
        if bin_name not in dims[dimension]:
            dims[dimension][bin_name] = {"stake": 0.0, "payout": 0.0, "bet_count": 0, "hit_count": 0, "sum_odds": 0.0}
        return dims[dimension][bin_name]

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
        for max_ev, bets, top1_prob, venue, race_number in races_sorted[idx_start:]:
            filtered = _filter_bets_by_selection(bets, ZONE_EV_LO, ZONE_EV_HI, PROB_MIN)
            for ev, prob, odds, hit in filtered:
                ob = _odds_band(odds)
                pb = _prob_band(prob)
                tb = _top1_prob_band(top1_prob)
                vb = venue or "unknown"
                rb = _race_number_band(race_number)

                for dimension_key, bin_value in [("odds_band", ob), ("prob_band", pb), ("top1_prob_band", tb), ("venue", vb), ("race_number_band", rb)]:
                    a = _get_agg(dimension_key, bin_value)
                    a["stake"] += st
                    a["payout"] += st * odds if hit else 0.0
                    a["bet_count"] += 1
                    if hit:
                        a["hit_count"] += 1
                    a["sum_odds"] += odds

    # Build output: dimension -> [ {bin, ROI, total_profit, ...}, ... ]
    result_by_dim: Dict[str, List[Dict]] = {}
    csv_rows: List[Dict] = []

    for dimension in ["odds_band", "prob_band", "top1_prob_band", "venue", "race_number_band"]:
        bins_sorted = sorted(dims[dimension].keys())
        rows = []
        for bin_name in bins_sorted:
            agg = dims[dimension][bin_name]
            if agg["bet_count"] == 0:
                continue
            row = {"dimension": dimension, "bin": bin_name, **_agg_to_row(agg)}
            rows.append(row)
            csv_rows.append(row)
        result_by_dim[dimension] = rows

    payload = {
        "experiment_id": "EXP-0074",
        "purpose": "profit zone (4.50<=EV<4.75, prob>=0.05) decomposition analysis, n_w=36",
        "db_path_used": db_path_str,
        "n_windows": n_w,
        "calibration": "sigmoid",
        "risk_control": "switch_dd4000",
        "zone": {"ev_lo": ZONE_EV_LO, "ev_hi": ZONE_EV_HI, "prob_min": PROB_MIN},
        "ref_profit": "4.30<=EV<4.75",
        "skip_top20pct": SKIP_TOP_PCT,
        "by_dimension": result_by_dim,
    }

    out_json = output_dir / "exp0074_profit_zone.json"
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    print("Saved {}".format(out_json))

    out_csv = output_dir / "exp0074_profit_zone.csv"
    if csv_rows:
        with open(out_csv, "w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=["dimension", "bin", "ROI", "total_profit", "bet_count", "hit_rate", "avg_odds", "profit_per_1000_bets"])
            w.writeheader()
            w.writerows(csv_rows)
        print("Saved {}".format(out_csv))

    print("\n--- EXP-0074 profit zone decomposition (4.50<=EV<4.75, n_windows={}) ---".format(n_w))
    for dimension, rows in result_by_dim.items():
        if not rows:
            continue
        print("\n[{}]".format(dimension))
        print("  bin           | ROI     | total_profit | bet_count | hit_rate | avg_odds | profit_per_1000_bets")
        print("  " + "-" * 90)
        for r in rows:
            print("  {:13} | {:6}% | {:12} | {:9} | {:7}% | {:8} | {:20}".format(
                r["bin"][:13],
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
