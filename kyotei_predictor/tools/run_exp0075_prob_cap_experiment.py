"""
EXP-0075: probability cap experiment.

EXP-0074 で prob ≥ 0.12 が損失源であることが確認されたため、
主軸戦略 4.50 ≤ EV < 4.75, prob ≥ 0.05 に prob 上限フィルタを追加して比較する。

CASE0: baseline（4.50 ≤ EV < 4.75, prob ≥ 0.05、上限なし）
CASE1: 0.05 ≤ prob < 0.12
CASE2: 0.05 ≤ prob < 0.10
CASE3: 0.05 ≤ prob < 0.09
CASE4: 0.05 ≤ prob < 0.08

共通: calibration=sigmoid, risk_control=switch_dd4000, n_windows=36, skip_top20pct。
ref_profit は EXP-0070 と同一（4.30 ≤ EV < 4.75, prob ≥ 0.05）で算出し全 CASE で共通 schedule 使用。
"""

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

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

# (case_name, ev_lo, ev_hi, prob_min, prob_max). prob_max None = 上限なし（baseline）
CASES: List[Tuple[str, float, float, float, Optional[float]]] = [
    ("CASE0", 4.50, 4.75, 0.05, None),   # baseline
    ("CASE1", 4.50, 4.75, 0.05, 0.12),    # prob < 0.12
    ("CASE2", 4.50, 4.75, 0.05, 0.10),    # prob < 0.10
    ("CASE3", 4.50, 4.75, 0.05, 0.09),    # prob < 0.09
    ("CASE4", 4.50, 4.75, 0.05, 0.08),    # prob < 0.08
]

BetTuple = Tuple[float, float, float, bool]  # (ev, prob, odds, hit)


def _top1_probability_for_race(race: dict) -> float:
    all_comb = race.get("all_combinations") or []
    if not all_comb:
        return 0.0
    probs = [
        float(c.get("probability") or c.get("score", 0))
        for c in all_comb
        if c.get("probability") is not None or c.get("score") is not None
    ]
    return max(probs) if probs else 0.0


def _longest_losing_streak(window_profits: List[float]) -> int:
    best = cur = 0
    for w in window_profits:
        if w < 0:
            cur += 1
            if cur > best:
                best = cur
        else:
            cur = 0
    return best


def _filter_bets_prob_cap(
    bets: List[BetTuple],
    ev_lo: float,
    ev_hi: float,
    prob_min: float,
    prob_max: Optional[float],
) -> List[BetTuple]:
    """bets を selection 条件でフィルタ。prob_max が None のときは上限なし。"""
    out: List[BetTuple] = []
    for ev, prob, odds, hit in bets:
        if not (ev_lo <= ev < ev_hi):
            continue
        if prob < prob_min:
            continue
        if prob_max is not None and prob >= prob_max:
            continue
        out.append((ev, prob, odds, hit))
    return out


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


def _run_one_case(
    n_w: int,
    window_list: List[Tuple[str, str, str, str]],
    day_races_raw: Dict[str, List[Tuple[float, List[BetTuple], float]]],
    ev_lo: float,
    ev_hi: float,
    prob_min: float,
    prob_max: Optional[float],
    schedule: List[int],
) -> Dict:
    """指定 (ev_lo, ev_hi, prob_min, prob_max) でフィルタし、switch_dd4000 スケジュールで集計。"""
    window_set = {wi for wi in range(n_w)}
    day_to_wi: Dict[str, int] = {}
    for wi, (_ts, _te, tst, tend) in enumerate(window_list):
        if wi >= n_w:
            break
        for day in _date_range(tst, tend):
            day_to_wi[day] = wi

    total_stake = 0.0
    total_payout = 0.0
    bet_count = 0
    hit_count = 0
    window_profits = [0.0] * n_w

    for day, races_data in day_races_raw.items():
        wi = day_to_wi.get(day, -1)
        if wi not in window_set or wi >= len(schedule):
            continue
        st = schedule[wi]
        races_sorted = sorted(races_data, key=lambda x: -x[0])
        n = len(races_sorted)
        k_skip = int(n * SKIP_TOP_PCT)
        idx_start = min(k_skip, n)
        for max_ev, bets, _top1 in races_sorted[idx_start:]:
            filtered = _filter_bets_prob_cap(bets, ev_lo, ev_hi, prob_min, prob_max)
            for _ev, _prob, odds, hit in filtered:
                total_stake += st
                total_payout += st * odds if hit else 0.0
                bet_count += 1
                if hit:
                    hit_count += 1
                window_profits[wi] += (st * odds if hit else 0.0) - st

    total_profit = round(total_payout - total_stake, 2)
    roi = round((total_payout / total_stake - 1) * 100, 2) if total_stake else None
    profit_per_1000 = round(1000.0 * (total_payout - total_stake) / bet_count, 2) if bet_count else 0.0
    cum = peak = dd = 0.0
    for wprof in window_profits:
        cum += wprof
        if cum > peak:
            peak = cum
        if peak - cum > dd:
            dd = peak - cum
    longest_losing_streak = _longest_losing_streak(window_profits)

    return {
        "ROI": roi,
        "total_profit": total_profit,
        "max_drawdown": round(dd, 2),
        "profit_per_1000_bets": profit_per_1000,
        "bet_count": bet_count,
        "longest_losing_streak": longest_losing_streak,
        "total_stake": round(total_stake, 2),
        "total_payout": round(total_payout, 2),
        "hit_count": hit_count,
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
        print("[EXP-0075] ERROR: DB not found: {}".format(db_path_resolved), file=sys.stderr)
        return 1
    db_path_str = str(db_path_resolved)
    print("[EXP-0075] DB found: {}".format(db_path_str))

    raw_dir = _REPO_ROOT / "kyotei_predictor" / "data" / "raw"
    if not raw_dir.is_dir():
        raw_dir = Path("kyotei_predictor/data/raw")

    output_dir = args.output_dir or _REPO_ROOT / "outputs" / "prob_cap"
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
        print("EXP-0075: Running rolling validation (n_windows={})...".format(n_w))
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
        print("EXP-0075: Using existing predictions in {}.".format(out_pred_dir))

    repo = get_race_data_repository("db", data_dir=raw_dir, db_path=db_path_str)

    day_races_raw: Dict[str, List[Tuple[float, List[BetTuple], float]]] = {}
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
                top1_prob = _top1_probability_for_race(race)
                if bets is not None:
                    races_data.append((max_ev, bets, top1_prob))
            if races_data:
                day_races_raw[day] = races_data

    # ref_profit: EXP-0070 と同一（4.30 ≤ EV < 4.75, prob ≥ 0.05）で算出し全 CASE で共通 schedule
    ev_lo_ref, ev_hi_ref, prob_min_ref = 4.30, 4.75, 0.05
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
        for max_ev, bets, _ in races_sorted[idx_start:]:
            for _ev, _prob, odds, hit in _filter_bets_by_selection(bets, ev_lo_ref, ev_hi_ref, prob_min_ref):
                ref_profit[wi] += (FIXED_STAKE * odds if hit else 0.0) - FIXED_STAKE
    schedule = _stake_schedule_dd(n_w, ref_profit, 4000)

    results_by_case: Dict[str, Dict] = {}
    for case_name, ev_lo, ev_hi, prob_min, prob_max in CASES:
        res = _run_one_case(
            n_w, window_list, day_races_raw, ev_lo, ev_hi, prob_min, prob_max, schedule
        )
        results_by_case[case_name] = res

    summary_list = []
    for case_name, ev_lo, ev_hi, prob_min, prob_max in CASES:
        r = results_by_case[case_name]
        summary_list.append({
            "variant": case_name,
            "ev_lo": ev_lo,
            "ev_hi": ev_hi,
            "prob_min": prob_min,
            "prob_max": prob_max,
            "ROI": r["ROI"],
            "total_profit": r["total_profit"],
            "max_drawdown": r["max_drawdown"],
            "profit_per_1000_bets": r["profit_per_1000_bets"],
            "bet_count": r["bet_count"],
            "longest_losing_streak": r["longest_losing_streak"],
            "total_stake": r["total_stake"],
            "total_payout": r["total_payout"],
            "hit_count": r["hit_count"],
        })

    payload = {
        "experiment_id": "EXP-0075",
        "purpose": "probability cap experiment: prob upper limit filter, n_w=36",
        "db_path_used": db_path_str,
        "n_windows": n_w,
        "calibration": "sigmoid",
        "risk_control": "switch_dd4000",
        "ref_profit": "4.30<=EV<4.75, prob>=0.05 (EXP-0070 same)",
        "cases": [
            {"name": c[0], "ev_lo": c[1], "ev_hi": c[2], "prob_min": c[3], "prob_max": c[4]}
            for c in CASES
        ],
        "summary": summary_list,
        "results_by_case": results_by_case,
    }

    out_path = output_dir / "exp0075_prob_cap.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    print("Saved {}".format(out_path))

    print("\n--- EXP-0075 probability cap (n_windows={}) ---".format(n_w))
    print("variant  | ev_lo | ev_hi | prob     | ROI     | total_profit | max_drawdown | profit/1k   | bet_count | longest_lose")
    print("-" * 130)
    for s in summary_list:
        prob_str = "{}-{}".format(s["prob_min"], s["prob_max"] if s["prob_max"] is not None else "—")
        print("  {:7} | {:5} | {:5} | {:8} | {:6}% | {:12} | {:12} | {:11} | {:9} | {:12}".format(
            s["variant"],
            s["ev_lo"],
            s["ev_hi"],
            prob_str,
            s["ROI"] if s["ROI"] is not None else "—",
            s["total_profit"],
            s["max_drawdown"],
            s["profit_per_1000_bets"],
            s["bet_count"],
            s["longest_losing_streak"],
        ))

    return 0


if __name__ == "__main__":
    sys.exit(main())
