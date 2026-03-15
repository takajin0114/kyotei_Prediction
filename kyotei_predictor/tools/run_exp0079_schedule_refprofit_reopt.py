"""
EXP-0079: schedule / ref_profit re-optimization for new main.

主軸戦略は new_main（4.50 ≤ EV < 4.90, 0.05 ≤ prob < 0.09）に更新されたが、
ref_profit と switch_dd4000 の基準は旧主軸ベースのままの可能性がある。
new_main に合わせた ref_profit へ再最適化したときに profit / drawdown / 安定性が
改善するかを確認する。risk control の基準も追随させるべきかを判断する。

対象ベットは常に new_main（4.50 ≤ EV < 4.90, 0.05 ≤ prob < 0.09）。
比較するのは ref_profit の定義と switch 閾値のみ。

CASE0_old_ref:     ref_profit = 4.30-4.75, prob≥0.05（旧基準）, dd4000
CASE1_new_ref:     ref_profit = 4.50-4.90, prob≥0.05（新基準）, dd4000
CASE2_new_ref_dd3000: ref_profit = 新基準, dd3000
CASE3_new_ref_dd5000: ref_profit = 新基準, dd5000
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

# 対象ベットは常に new_main
NEW_MAIN_EV_LO, NEW_MAIN_EV_HI = 4.50, 4.90
NEW_MAIN_PROB_MIN, NEW_MAIN_PROB_MAX = 0.05, 0.09

# (case_name, ref_ev_lo, ref_ev_hi, ref_prob_min, dd_threshold)
# ref_prob_min で ref_profit 計算時は prob >= ref_prob_min のベットで利益を集計
CASES: List[Tuple[str, float, float, float, int]] = [
    ("CASE0_old_ref", 4.30, 4.75, 0.05, 4000),
    ("CASE1_new_ref", 4.50, 4.90, 0.05, 4000),
    ("CASE2_new_ref_dd3000", 4.50, 4.90, 0.05, 3000),
    ("CASE3_new_ref_dd5000", 4.50, 4.90, 0.05, 5000),
]

N_WINDOWS_LIST = [24, 30, 36, 48]

BetTuple = Tuple[float, float, float, bool]


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


def _filter_bets_ev_prob(
    bets: List[BetTuple],
    ev_lo: float,
    ev_hi: float,
    prob_min: float,
    prob_max: float,
) -> List[BetTuple]:
    out: List[BetTuple] = []
    for ev, prob, odds, hit in bets:
        if not (ev_lo <= ev < ev_hi):
            continue
        if prob < prob_min:
            continue
        if prob >= prob_max:
            continue
        out.append((ev, prob, odds, hit))
    return out


def _stake_schedule_dd(n_w: int, ref_profit: List[float], dd_threshold: int) -> List[int]:
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
    schedule: List[int],
) -> Dict:
    """常に new_main（4.50-4.90, 0.05-0.09）でベットし、指定 schedule で集計。"""
    ev_lo, ev_hi = NEW_MAIN_EV_LO, NEW_MAIN_EV_HI
    prob_min, prob_max = NEW_MAIN_PROB_MIN, NEW_MAIN_PROB_MAX
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
            filtered = _filter_bets_ev_prob(bets, ev_lo, ev_hi, prob_min, prob_max)
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

    block_profit: List[float] = []
    if n_w >= 6:
        block_size = n_w // 6
        for i in range(6):
            start = i * block_size
            end = (i + 1) * block_size if i < 5 else n_w
            block_profit.append(round(sum(window_profits[start:end]), 2))
    else:
        block_profit = [round(w, 2) for w in window_profits]

    winning_blocks = sum(1 for b in block_profit if b > 0)
    losing_blocks = sum(1 for b in block_profit if b < 0)
    schedule_switch_count = sum(1 for s in schedule if s == 80)

    return {
        "ROI": roi,
        "total_profit": total_profit,
        "max_drawdown": round(dd, 2),
        "profit_per_1000_bets": profit_per_1000,
        "bet_count": bet_count,
        "longest_losing_streak": longest_losing_streak,
        "block_profit": block_profit,
        "winning_blocks": winning_blocks,
        "losing_blocks": losing_blocks,
        "schedule_switch_count": schedule_switch_count,
        "total_stake": round(total_stake, 2),
        "total_payout": round(total_payout, 2),
        "hit_count": hit_count,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db-path", type=str, default=None)
    parser.add_argument("--output-dir", type=Path, default=None)
    parser.add_argument("--predictions-dir", type=Path, default=None)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    db_path_resolved = _resolve_db_path(args.db_path)
    if not db_path_resolved.exists():
        print("[EXP-0079] ERROR: DB not found: {}".format(db_path_resolved), file=sys.stderr)
        return 1
    db_path_str = str(db_path_resolved)
    print("[EXP-0079] DB found: {}".format(db_path_str))

    raw_dir = _REPO_ROOT / "kyotei_predictor" / "data" / "raw"
    if not raw_dir.is_dir():
        raw_dir = Path("kyotei_predictor/data/raw")

    output_dir = args.output_dir or _REPO_ROOT / "outputs" / "schedule_refprofit_reopt"
    output_dir.mkdir(parents=True, exist_ok=True)

    pred_parent = args.predictions_dir or _REPO_ROOT / "outputs" / "ev_cap_experiments"
    out_pred_dir = pred_parent / "rolling_roi_predictions"

    min_date, max_date = get_db_date_range(db_path_str)
    repo = get_race_data_repository("db", data_dir=raw_dir, db_path=db_path_str)

    n_w_max = max(N_WINDOWS_LIST)
    window_list_full = build_windows(min_date, max_date, TRAIN_DAYS, TEST_DAYS, STEP_DAYS, n_w_max)
    if len(window_list_full) < n_w_max:
        n_w_max = len(window_list_full)
    need_days = set()
    for _ts, _te, tst, tend in window_list_full[:n_w_max]:
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
        print("[EXP-0079] Running rolling validation (n_windows={})...".format(n_w_max))
        run_rolling_validation_roi(
            db_path=db_path_str,
            output_dir=pred_parent,
            data_dir_raw=raw_dir,
            train_days=TRAIN_DAYS,
            test_days=TEST_DAYS,
            step_days=STEP_DAYS,
            n_windows=n_w_max,
            strategies=STRATEGIES,
            model_type="xgboost",
            calibration="sigmoid",
            feature_set="extended_features",
            seed=args.seed,
        )
    else:
        print("[EXP-0079] Using existing predictions.")

    summary_list: List[Dict] = []
    results_by_variant_horizon: Dict[str, Dict] = {}

    for n_w in N_WINDOWS_LIST:
        window_list_full_n = build_windows(min_date, max_date, TRAIN_DAYS, TEST_DAYS, STEP_DAYS, n_w)
        if len(window_list_full_n) < n_w:
            n_w_actual = len(window_list_full_n)
        else:
            n_w_actual = n_w
        window_list = list(window_list_full_n[:n_w_actual])

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

        day_to_wi: Dict[str, int] = {}
        for wi, (_ts, _te, tst, tend) in enumerate(window_list):
            if wi >= n_w_actual:
                break
            for day in _date_range(tst, tend):
                day_to_wi[day] = wi

        for case_name, ref_ev_lo, ref_ev_hi, ref_prob_min, dd_threshold in CASES:
            ref_profit = [0.0] * n_w_actual
            for day, races_data in day_races_raw.items():
                wi = day_to_wi.get(day, -1)
                if wi < 0 or wi >= n_w_actual:
                    continue
                races_sorted = sorted(races_data, key=lambda x: -x[0])
                n = len(races_sorted)
                k_skip = int(n * SKIP_TOP_PCT)
                idx_start = min(k_skip, n)
                for max_ev, bets, _ in races_sorted[idx_start:]:
                    for _ev, _prob, odds, hit in _filter_bets_by_selection(
                        bets, ref_ev_lo, ref_ev_hi, ref_prob_min
                    ):
                        ref_profit[wi] += (FIXED_STAKE * odds if hit else 0.0) - FIXED_STAKE
            schedule = _stake_schedule_dd(n_w_actual, ref_profit, dd_threshold)

            res = _run_one_case(n_w_actual, window_list, day_races_raw, schedule)
            key = "{}_nw{}".format(case_name, n_w_actual)
            results_by_variant_horizon[key] = res
            summary_list.append({
                "variant": case_name,
                "n_windows": n_w_actual,
                "ref_ev_lo": ref_ev_lo,
                "ref_ev_hi": ref_ev_hi,
                "ref_prob_min": ref_prob_min,
                "dd_threshold": dd_threshold,
                "ROI": res["ROI"],
                "total_profit": res["total_profit"],
                "max_drawdown": res["max_drawdown"],
                "profit_per_1000_bets": res["profit_per_1000_bets"],
                "bet_count": res["bet_count"],
                "longest_losing_streak": res["longest_losing_streak"],
                "block_profit": res["block_profit"],
                "winning_blocks": res["winning_blocks"],
                "losing_blocks": res["losing_blocks"],
                "schedule_switch_count": res["schedule_switch_count"],
            })

    payload = {
        "experiment_id": "EXP-0079",
        "purpose": "schedule and ref_profit re-optimization for new main (4.50-4.90, 0.05-0.09)",
        "db_path_used": db_path_str,
        "bet_target": "new_main: 4.50<=EV<4.90, 0.05<=prob<0.09",
        "n_windows_list": N_WINDOWS_LIST,
        "calibration": "sigmoid",
        "skip_top20pct": SKIP_TOP_PCT,
        "cases": [
            {
                "name": c[0],
                "ref_ev_lo": c[1],
                "ref_ev_hi": c[2],
                "ref_prob_min": c[3],
                "dd_threshold": c[4],
            }
            for c in CASES
        ],
        "summary": summary_list,
        "results_by_variant_horizon": results_by_variant_horizon,
    }

    out_path = output_dir / "exp0079_schedule_refprofit_reopt.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    print("Saved {}".format(out_path))

    print("\n--- EXP-0079 schedule/ref_profit reopt (variant × horizon) ---")
    print("variant            | n_w  | ROI     | total_profit | max_dd   | profit/1k   | bet_count | longest_lose | switch_cnt")
    print("-" * 135)
    for s in summary_list:
        v = s["variant"]
        if len(v) > 18:
            v = v[:15] + "..."
        print(" {:18} | {:4} | {:6}% | {:12} | {:8} | {:11} | {:9} | {:12} | {:9}".format(
            v,
            s["n_windows"],
            s["ROI"] if s["ROI"] is not None else "—",
            s["total_profit"],
            s["max_drawdown"],
            s["profit_per_1000_bets"],
            s["bet_count"],
            s["longest_losing_streak"],
            s["schedule_switch_count"],
        ))

    return 0


if __name__ == "__main__":
    sys.exit(main())
