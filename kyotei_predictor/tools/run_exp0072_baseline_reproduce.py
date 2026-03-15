"""
EXP-0072 baseline reproducibility check.

EXP-0070 CASE2 と EXP-0072 CASE0 を同条件で再計算し、baseline の一致を検証する。
一致しない場合の原因特定のため、ref_profit 算出を両方式で行い比較する。

共通条件:
  selection: 4.50 <= EV < 4.75, prob >= 0.05
  calibration = sigmoid, risk_control = switch_dd4000, n_windows = 36, skip_top20pct
"""

import argparse
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

# EXP-0070 CASE0 (baseline d_hi475) → ref_profit 用
REF_EV_LO, REF_EV_HI, REF_PROB_MIN = 4.30, 4.75, 0.05
# EXP-0070 CASE2 = EXP-0072 baseline selection
CASE2_EV_LO, CASE2_EV_HI, CASE2_PROB_MIN = 4.50, 4.75, 0.05

BetTuple = Tuple[float, float, float, bool]


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


def _run_with_schedule(
    n_w: int,
    window_list: List[Tuple[str, str, str, str]],
    day_races_raw: Dict[str, List[Tuple[float, List[BetTuple], float]]],
    ev_lo: float,
    ev_hi: float,
    prob_min: float,
    schedule: List[int],
) -> Dict:
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
        for max_ev, bets, _ in races_sorted[idx_start:]:
            filtered = _filter_bets_by_selection(bets, ev_lo, ev_hi, prob_min)
            for _ev, _prob, odds, hit in filtered:
                total_stake += st
                total_payout += st * odds if hit else 0.0
                bet_count += 1
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
    return {
        "ROI": roi,
        "total_profit": total_profit,
        "max_drawdown": round(dd, 2),
        "profit_per_1000_bets": profit_per_1000,
        "bet_count": bet_count,
        "longest_losing_streak": _longest_losing_streak(window_profits),
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
        print("[EXP-0072 baseline] ERROR: DB not found: {}".format(db_path_resolved), file=sys.stderr)
        return 1
    db_path_str = str(db_path_resolved)

    raw_dir = _REPO_ROOT / "kyotei_predictor" / "data" / "raw"
    if not raw_dir.is_dir():
        raw_dir = Path("kyotei_predictor/data/raw")
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
                if bets is not None:
                    races_data.append((max_ev, bets, 0.0))
            if races_data:
                day_races_raw[day] = races_data

    day_to_wi: Dict[str, int] = {}
    for wi, (_ts, _te, tst, tend) in enumerate(window_list):
        if wi >= n_w:
            break
        for day in _date_range(tst, tend):
            day_to_wi[day] = wi

    # --- EXP-0070 方式: ref_profit を CASE0 (4.30, 4.75, 0.05) で算出 ---
    ref_profit_0070 = [0.0] * n_w
    for day, races_data in day_races_raw.items():
        wi = day_to_wi.get(day, -1)
        if wi < 0 or wi >= n_w:
            continue
        races_sorted = sorted(races_data, key=lambda x: -x[0])
        n = len(races_sorted)
        k_skip = int(n * SKIP_TOP_PCT)
        idx_start = min(k_skip, n)
        for max_ev, bets, _ in races_sorted[idx_start:]:
            for _ev, _prob, odds, hit in _filter_bets_by_selection(bets, REF_EV_LO, REF_EV_HI, REF_PROB_MIN):
                ref_profit_0070[wi] += (FIXED_STAKE * odds if hit else 0.0) - FIXED_STAKE
    schedule_0070 = _stake_schedule_dd(n_w, ref_profit_0070, 4000)

    # --- EXP-0072 方式: ref_profit を CASE2 selection (4.50, 4.75, 0.05) で算出 ---
    ref_profit_0072 = [0.0] * n_w
    for day, races_data in day_races_raw.items():
        wi = day_to_wi.get(day, -1)
        if wi < 0 or wi >= n_w:
            continue
        races_sorted = sorted(races_data, key=lambda x: -x[0])
        n = len(races_sorted)
        k_skip = int(n * SKIP_TOP_PCT)
        idx_start = min(k_skip, n)
        for max_ev, bets, _ in races_sorted[idx_start:]:
            for _ev, _prob, odds, hit in _filter_bets_by_selection(bets, CASE2_EV_LO, CASE2_EV_HI, CASE2_PROB_MIN):
                ref_profit_0072[wi] += (FIXED_STAKE * odds if hit else 0.0) - FIXED_STAKE
    schedule_0072 = _stake_schedule_dd(n_w, ref_profit_0072, 4000)

    # EXP-0070 CASE2: selection (4.50, 4.75, 0.05) + schedule from ref(CASE0)
    result_0070_case2 = _run_with_schedule(
        n_w, window_list, day_races_raw,
        CASE2_EV_LO, CASE2_EV_HI, CASE2_PROB_MIN,
        schedule_0070,
    )

    # EXP-0072 CASE0: selection (4.50, 4.75, 0.05) + schedule from ref(CASE2)
    result_0072_case0 = _run_with_schedule(
        n_w, window_list, day_races_raw,
        CASE2_EV_LO, CASE2_EV_HI, CASE2_PROB_MIN,
        schedule_0072,
    )

    # 同一 schedule (EXP-0070 方式) で EXP-0072 CASE0 相当も計算 → selection だけ同じなら bet 集合は同じなので schedule 差が効く
    result_0072_with_0070_schedule = _run_with_schedule(
        n_w, window_list, day_races_raw,
        CASE2_EV_LO, CASE2_EV_HI, CASE2_PROB_MIN,
        schedule_0070,
    )

    output_dir = args.output_dir or _REPO_ROOT / "outputs" / "race_difficulty"
    output_dir.mkdir(parents=True, exist_ok=True)
    out = {
        "experiment_id": "EXP-0072-baseline-reproduce",
        "n_windows": n_w,
        "ref_profit_0070": [round(x, 2) for x in ref_profit_0070],
        "ref_profit_0072": [round(x, 2) for x in ref_profit_0072],
        "schedule_0070": schedule_0070,
        "schedule_0072": schedule_0072,
        "EXP0070_CASE2": result_0070_case2,
        "EXP0072_CASE0": result_0072_case0,
        "EXP0072_CASE0_with_0070_schedule": result_0072_with_0070_schedule,
    }
    out_path = output_dir / "exp0072_baseline_reproduce.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    print("Saved {}".format(out_path))

    print("\n--- Baseline reproducibility (n_windows={}) ---".format(n_w))
    print("EXP-0070 CASE2 (ref=CASE0 4.30~4.75): ROI={}% profit={} max_dd={} bet_count={}".format(
        result_0070_case2["ROI"], result_0070_case2["total_profit"],
        result_0070_case2["max_drawdown"], result_0070_case2["bet_count"]))
    print("EXP-0072 CASE0 (ref=CASE2 4.50~4.75): ROI={}% profit={} max_dd={} bet_count={}".format(
        result_0072_case0["ROI"], result_0072_case0["total_profit"],
        result_0072_case0["max_drawdown"], result_0072_case0["bet_count"]))
    print("EXP-0072 CASE0 with EXP-0070 schedule: ROI={}% profit={} max_dd={} bet_count={}".format(
        result_0072_with_0070_schedule["ROI"], result_0072_with_0070_schedule["total_profit"],
        result_0072_with_0070_schedule["max_drawdown"], result_0072_with_0070_schedule["bet_count"]))
    if result_0070_case2["bet_count"] == result_0072_with_0070_schedule["bet_count"]:
        print("-> bet_count match when using same schedule. Difference was due to ref_profit/schedule.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
