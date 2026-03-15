"""
EXP-0072: race difficulty filter.

CASE2（4.50 ≤ EV < 4.75, prob ≥ 0.05）をベースに、レース単位の難易度フィルタを導入し
ROI / total_profit / max_drawdown の改善を狙う。

共通: calibration=sigmoid, risk_control=switch_dd4000, n_windows=36, skip_top20pct。
selection: 4.50 ≤ EV < 4.75, prob ≥ 0.05（固定）。
難易度指標: top1_prob, entropy, prob_gap（および prob_std, prob_max）をレース単位で算出。

CASE0: difficulty filter なし（baseline）
CASE1: top1_prob ≥ 0.35
CASE2: top1_prob ≥ 0.40
CASE3: prob_gap ≥ 0.05
CASE4: entropy ≤ 1.50
CASE5: entropy ≤ 1.30
"""

import argparse
import json
import math
import os
import sys
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

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

# ベース selection: CASE2（EXP-0070 採用）
EV_LO = 4.50
EV_HI = 4.75
PROB_MIN = 0.05

# (variant_name, filter_fn). filter_fn(race_difficulty) -> True ならレースを採用
def _no_filter(_: Dict[str, float]) -> bool:
    return True


def _top1_ge(threshold: float) -> Callable[[Dict[str, float]], bool]:
    def fn(d: Dict[str, float]) -> bool:
        return (d.get("top1_prob") or 0.0) >= threshold
    return fn


def _prob_gap_ge(threshold: float) -> Callable[[Dict[str, float]], bool]:
    def fn(d: Dict[str, float]) -> bool:
        return (d.get("prob_gap") or 0.0) >= threshold
    return fn


def _entropy_le(threshold: float) -> Callable[[Dict[str, float]], bool]:
    def fn(d: Dict[str, float]) -> bool:
        e = d.get("entropy")
        if e is None:
            return True
        return e <= threshold
    return fn


DIFFICULTY_CASES: List[Tuple[str, Callable[[Dict[str, float]], bool]]] = [
    ("CASE0", _no_filter),
    ("CASE1", _top1_ge(0.35)),
    ("CASE2", _top1_ge(0.40)),
    ("CASE3", _prob_gap_ge(0.05)),
    ("CASE4", _entropy_le(1.50)),
    ("CASE5", _entropy_le(1.30)),
]

BetTuple = Tuple[float, float, float, bool]  # (ev, prob, odds, hit)


def _race_difficulty(race: dict) -> Dict[str, float]:
    """レースの all_combinations から top1_prob, entropy, prob_gap, prob_std, prob_max を算出。"""
    all_comb = race.get("all_combinations") or []
    probs = [
        float(c.get("probability") or c.get("score", 0))
        for c in all_comb
        if c.get("probability") is not None or c.get("score") is not None
    ]
    out: Dict[str, float] = {
        "top1_prob": 0.0,
        "entropy": 0.0,
        "prob_gap": 0.0,
        "prob_std": 0.0,
        "prob_max": 0.0,
    }
    if not probs:
        return out
    out["prob_max"] = max(probs)
    out["top1_prob"] = out["prob_max"]
    if len(probs) >= 2:
        sorted_p = sorted(probs, reverse=True)
        out["prob_gap"] = sorted_p[0] - sorted_p[1]
    n = len(probs)
    total = sum(probs)
    if total > 0:
        h = 0.0
        for p in probs:
            if p > 0:
                q = p / total
                h -= q * math.log(q + 1e-12)
        out["entropy"] = round(h, 6)
    if n > 0:
        mean = total / n
        var = sum((p - mean) ** 2 for p in probs) / n
        out["prob_std"] = math.sqrt(var) if var >= 0 else 0.0
    return out


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


def _run_one_variant(
    n_w: int,
    window_list: List[Tuple[str, str, str, str]],
    day_races_raw: Dict[str, List[Tuple[float, List[BetTuple], Dict[str, float]]]],
    schedule: List[int],
    filter_fn: Callable[[Dict[str, float]], bool],
) -> Dict[str, Any]:
    """指定 difficulty filter でレースを絞り、CASE2 selection + switch_dd4000 で集計。"""
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
        for max_ev, bets, difficulty in races_sorted[idx_start:]:
            if not filter_fn(difficulty):
                continue
            filtered = _filter_bets_by_selection(bets, EV_LO, EV_HI, PROB_MIN)
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

    return {
        "ROI": roi,
        "total_profit": total_profit,
        "max_drawdown": round(dd, 2),
        "profit_per_1000_bets": profit_per_1000,
        "bet_count": bet_count,
        "longest_losing_streak": longest_losing_streak,
        "block_profit": block_profit,
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
        print("[EXP-0072] ERROR: DB not found: {}".format(db_path_resolved), file=sys.stderr)
        return 1
    db_path_str = str(db_path_resolved)
    print("[EXP-0072] DB found: {}".format(db_path_str))

    raw_dir = _REPO_ROOT / "kyotei_predictor" / "data" / "raw"
    if not raw_dir.is_dir():
        raw_dir = Path("kyotei_predictor/data/raw")

    output_dir = args.output_dir or _REPO_ROOT / "outputs" / "race_difficulty"
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
        print("EXP-0072: Running rolling validation (n_windows={})...".format(n_w))
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
        print("EXP-0072: Using existing predictions in {}.".format(out_pred_dir))

    repo = get_race_data_repository("db", data_dir=raw_dir, db_path=db_path_str)

    day_races_raw: Dict[str, List[Tuple[float, List[BetTuple], Dict[str, float]]]] = {}
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
                difficulty = _race_difficulty(race)
                if bets is not None:
                    races_data.append((max_ev, bets, difficulty))
            if races_data:
                day_races_raw[day] = races_data

    # Reference schedule: CASE0（difficulty filter なし）で ref_profit を計算
    day_to_wi_ref: Dict[str, int] = {}
    for wi, (_ts, _te, tst, tend) in enumerate(window_list):
        if wi >= n_w:
            break
        for day in _date_range(tst, tend):
            day_to_wi_ref[day] = wi
    ref_profit = [0.0] * n_w
    for day, races_data in day_races_raw.items():
        wi = day_to_wi_ref.get(day, -1)
        if wi < 0 or wi >= n_w:
            continue
        races_sorted = sorted(races_data, key=lambda x: -x[0])
        n = len(races_sorted)
        k_skip = int(n * SKIP_TOP_PCT)
        idx_start = min(k_skip, n)
        for max_ev, bets, _ in races_sorted[idx_start:]:
            for _ev, _prob, odds, hit in _filter_bets_by_selection(bets, EV_LO, EV_HI, PROB_MIN):
                ref_profit[wi] += (FIXED_STAKE * odds if hit else 0.0) - FIXED_STAKE
    schedule = _stake_schedule_dd(n_w, ref_profit, 4000)

    results_by_case: Dict[str, Dict] = {}
    summary_list: List[Dict] = []
    for variant_name, filter_fn in DIFFICULTY_CASES:
        res = _run_one_variant(n_w, window_list, day_races_raw, schedule, filter_fn)
        results_by_case[variant_name] = res
        summary_list.append({
            "variant": variant_name,
            "ROI": res["ROI"],
            "total_profit": res["total_profit"],
            "max_drawdown": res["max_drawdown"],
            "profit_per_1000_bets": res["profit_per_1000_bets"],
            "bet_count": res["bet_count"],
            "longest_losing_streak": res["longest_losing_streak"],
            "block_profit": res.get("block_profit"),
        })

    payload = {
        "experiment_id": "EXP-0072",
        "purpose": "race difficulty filter on CASE2 (4.50<=EV<4.75, prob>=0.05), n_w=36",
        "db_path_used": db_path_str,
        "n_windows": n_w,
        "calibration": "sigmoid",
        "risk_control": "switch_dd4000",
        "selection": {"ev_lo": EV_LO, "ev_hi": EV_HI, "prob_min": PROB_MIN},
        "skip_top20pct": SKIP_TOP_PCT,
        "difficulty_cases": [
            {"name": name, "description": _case_description(name)}
            for name, _ in DIFFICULTY_CASES
        ],
        "summary": summary_list,
        "results_by_case": results_by_case,
    }

    out_path = output_dir / "exp0072_race_difficulty.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    print("Saved {}".format(out_path))

    print("\n--- EXP-0072 race difficulty filter (n_windows={}) ---".format(n_w))
    print("variant  | ROI     | total_profit | max_drawdown | profit/1k   | bet_count | longest_lose")
    print("-" * 95)
    for s in summary_list:
        print("  {:7} | {:6}% | {:12} | {:12} | {:11} | {:9} | {:12}".format(
            s["variant"],
            s["ROI"] if s["ROI"] is not None else "—",
            s["total_profit"],
            s["max_drawdown"],
            s["profit_per_1000_bets"],
            s["bet_count"],
            s["longest_losing_streak"],
        ))

    return 0


def _case_description(name: str) -> str:
    if name == "CASE0":
        return "no difficulty filter (baseline)"
    if name == "CASE1":
        return "top1_prob >= 0.35"
    if name == "CASE2":
        return "top1_prob >= 0.40"
    if name == "CASE3":
        return "prob_gap >= 0.05"
    if name == "CASE4":
        return "entropy <= 1.50"
    if name == "CASE5":
        return "entropy <= 1.30"
    return name


if __name__ == "__main__":
    sys.exit(main())
