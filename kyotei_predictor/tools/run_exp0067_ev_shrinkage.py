"""
EXP-0067: EV Shrinkage Experiment.

EV 過大評価を抑えるため EV_adj = EV^alpha で shrinkage をかけ、selection に EV_adj を使用する。

EV: baseline EV = prob × odds
CASE0: baseline (alpha=1)
CASE1: EV_adj = EV^0.5
CASE2: EV_adj = EV^0.7
CASE3: EV_adj = EV^0.8
CASE4: EV_adj = EV^0.9

Selection: d_hi475（EV_adj で 4.30^alpha <= EV_adj < 4.75^alpha, prob>=0.05）
Risk control: switch_dd4000
n_windows = 36
"""

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

_THIS_DIR = Path(__file__).resolve().parent
_REPO_ROOT = _THIS_DIR.parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

os.environ["KYOTEI_USE_MOTOR_WIN_PROXY"] = os.environ.get("KYOTEI_USE_MOTOR_WIN_PROXY", "1")
os.environ["KYOTEI_FEATURE_SET"] = os.environ.get("KYOTEI_FEATURE_SET", "extended_features")

from kyotei_predictor.tools.rolling_validation_roi import build_windows, get_db_date_range
from kyotei_predictor.tools.rolling_validation_windows import _date_range
from kyotei_predictor.infrastructure.repositories.race_data_repository_factory import (
    get_race_data_repository,
)
from kyotei_predictor.tools.run_exp0042_selection_verified import (
    FIXED_STAKE,
    SKIP_TOP_PCT,
    STRATEGY_SUFFIX,
    _all_bets_for_race,
    _max_ev_for_race,
    _resolve_db_path,
)

EV_LO_BASELINE, EV_HI, PROB_MIN = 4.30, 4.75, 0.05
TRAIN_DAYS = 30
TEST_DAYS = 7
STEP_DAYS = 7
N_WINDOWS = 36

# (case_name, alpha). EV_adj = EV^alpha. alpha=1 is baseline.
EV_SHRINKAGE_CASES: List[Tuple[str, float]] = [
    ("CASE0_baseline", 1.0),
    ("CASE1_ev_power_0_5", 0.5),
    ("CASE2_ev_power_0_7", 0.7),
    ("CASE3_ev_power_0_8", 0.8),
    ("CASE4_ev_power_0_9", 0.9),
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


def _filter_bets_d_hi475_ev_adj(
    bets: List[BetTuple],
    alpha: float,
) -> List[BetTuple]:
    """EV_adj = EV^alpha で d_hi475 相当のフィルタ（4.30^a <= EV_adj < 4.75^a, prob>=0.05）。返すのは (ev_adj, prob, odds, hit)。"""
    if alpha <= 0:
        return []
    ev_lo_adj = EV_LO_BASELINE ** alpha
    ev_hi_adj = EV_HI ** alpha
    out: List[BetTuple] = []
    for ev, prob, odds, hit in bets:
        ev_adj = ev ** alpha
        if not (ev_lo_adj <= ev_adj < ev_hi_adj):
            continue
        if prob < PROB_MIN:
            continue
        out.append((ev_adj, prob, odds, hit))
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


def _build_day_races_ev_adj(
    day_races_raw: Dict[str, List[Tuple[float, List[BetTuple], float, Optional[float]]]],
    alpha: float,
) -> Dict[str, List[Tuple[float, List[BetTuple]]]]:
    """
    day_races_raw を EV_adj 空間に変換。各レースは (max_ev_adj, selected_bets) のみ残す。
    selected_bets は (ev_adj, prob, odds, hit) のリスト。
    """
    out: Dict[str, List[Tuple[float, List[BetTuple]]]] = {}
    for day, races_data in day_races_raw.items():
        filtered_races: List[Tuple[float, List[BetTuple]]] = []
        for _max_ev, bets, _top1_prob, _ in races_data:
            selected = _filter_bets_d_hi475_ev_adj(bets, alpha)
            if not selected:
                continue
            max_ev_adj = max(ev_adj for ev_adj, _p, _o, _h in selected)
            filtered_races.append((max_ev_adj, selected))
        if filtered_races:
            out[day] = filtered_races
    return out


def _run_one_n_windows_ev_shrinkage(
    n_w: int,
    window_list: List[Tuple[str, str, str, str]],
    day_races_ev_adj: Dict[str, List[Tuple[float, List[BetTuple]]]],
) -> Dict:
    """EV_adj でフィルタ済みの day_races_ev_adj に対して switch_dd4000 で集計。"""
    window_set = {wi for wi in range(n_w)}
    day_to_wi: Dict[str, int] = {}
    for wi, (_ts, _te, tst, tend) in enumerate(window_list):
        if wi >= n_w:
            break
        for day in _date_range(tst, tend):
            day_to_wi[day] = wi

    ref_profit: List[float] = [0.0] * n_w
    for day, races_data in day_races_ev_adj.items():
        wi = day_to_wi.get(day, -1)
        if wi < 0 or wi >= n_w:
            continue
        races_sorted = sorted(races_data, key=lambda x: -x[0])
        n = len(races_sorted)
        k_skip = int(n * SKIP_TOP_PCT)
        idx_start = min(k_skip, n)
        for _max_ev_adj, selected_bets in races_sorted[idx_start:]:
            for _ev_adj, _prob, odds, hit in selected_bets:
                ref_profit[wi] += (FIXED_STAKE * odds if hit else 0.0) - FIXED_STAKE
    schedule = _stake_schedule_dd(n_w, ref_profit, 4000)

    total_stake = 0.0
    total_payout = 0.0
    bet_count = 0
    hit_count = 0
    window_profits = [0.0] * n_w

    for day, races_data in day_races_ev_adj.items():
        wi = day_to_wi.get(day, -1)
        if wi not in window_set:
            continue
        st = schedule[wi]
        races_sorted = sorted(races_data, key=lambda x: -x[0])
        n = len(races_sorted)
        k_skip = int(n * SKIP_TOP_PCT)
        idx_start = min(k_skip, n)
        for _max_ev_adj, selected_bets in races_sorted[idx_start:]:
            for _ev_adj, _prob, odds, hit in selected_bets:
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


def _build_day_races_raw(
    out_pred_dir: Path,
    repo,
    need_days: Set[str],
) -> Dict[str, List[Tuple[float, List[BetTuple], float, Optional[float]]]]:
    day_races_raw: Dict[str, List[Tuple[float, List[BetTuple], float, Optional[float]]]] = {}
    for day in need_days:
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
                races_data.append((max_ev, bets, top1_prob, None))
        if races_data:
            day_races_raw[day] = races_data
    return day_races_raw


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db-path", type=str, default=None)
    parser.add_argument("--output-dir", type=Path, default=None)
    parser.add_argument("--predictions-dir", type=Path, default=None)
    parser.add_argument("--n-windows", type=int, default=N_WINDOWS)
    args = parser.parse_args()

    n_w = args.n_windows
    if n_w <= 0:
        n_w = N_WINDOWS

    db_path_resolved = _resolve_db_path(args.db_path)
    if not db_path_resolved.exists():
        print("[EXP-0067] ERROR: DB not found: {}".format(db_path_resolved), file=sys.stderr)
        return 1
    db_path_str = str(db_path_resolved)
    print("[EXP-0067] DB found: {}".format(db_path_str))

    raw_dir = _REPO_ROOT / "kyotei_predictor" / "data" / "raw"
    if not raw_dir.is_dir():
        raw_dir = Path("kyotei_predictor/data/raw")

    output_dir = args.output_dir or _REPO_ROOT / "outputs" / "ev_shrinkage"
    output_dir.mkdir(parents=True, exist_ok=True)

    pred_parent = args.predictions_dir or _REPO_ROOT / "outputs" / "calibration_comparison" / "calib_sigmoid"
    out_pred_dir = pred_parent / "rolling_roi_predictions"

    min_date, max_date = get_db_date_range(db_path_str)
    window_list_full = build_windows(min_date, max_date, TRAIN_DAYS, TEST_DAYS, STEP_DAYS, n_w)
    if len(window_list_full) < n_w:
        n_w = len(window_list_full)
    window_list = list(window_list_full[:n_w])

    need_days: Set[str] = set()
    for _ts, _te, tst, tend in window_list:
        for d in _date_range(tst, tend):
            need_days.add(d)

    if not out_pred_dir.exists():
        print("[EXP-0067] ERROR: Predictions dir not found: {}".format(out_pred_dir), file=sys.stderr)
        print("  Run EXP-0065 first (n_w=36).", file=sys.stderr)
        return 1

    repo = get_race_data_repository("db", data_dir=raw_dir, db_path=db_path_str)
    day_races_raw = _build_day_races_raw(out_pred_dir, repo, need_days)

    results_by_case: Dict[str, Dict] = {}
    for case_name, alpha in EV_SHRINKAGE_CASES:
        day_races_ev_adj = _build_day_races_ev_adj(day_races_raw, alpha)
        res = _run_one_n_windows_ev_shrinkage(n_w, window_list, day_races_ev_adj)
        results_by_case[case_name] = res

    summary_list = []
    for case_name, alpha in EV_SHRINKAGE_CASES:
        r = results_by_case[case_name]
        summary_list.append({
            "variant": case_name,
            "alpha": alpha,
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
        "experiment_id": "EXP-0067",
        "purpose": "EV shrinkage: EV_adj = EV^alpha, d_hi475 + switch_dd4000, n_w=36",
        "db_path_used": db_path_str,
        "n_windows": n_w,
        "predictions_source": str(out_pred_dir),
        "ev_definition_baseline": "EV = prob × odds",
        "shrinkage_cases": [{"name": c[0], "alpha": c[1], "formula": "EV_adj = EV^{}".format(c[1])} for c in EV_SHRINKAGE_CASES],
        "strategy": "d_hi475 (EV_adj), switch_dd4000",
        "summary": summary_list,
        "results_by_case": results_by_case,
    }

    out_path = output_dir / "exp0067_ev_shrinkage.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    print("Saved {}".format(out_path))

    print("\n--- EXP-0067 EV Shrinkage (n_windows={}) ---".format(n_w))
    print("variant                 | ROI     | total_profit | max_drawdown | profit/1k   | bet_count | longest_lose")
    print("-" * 110)
    for s in summary_list:
        print("  {:22} | {:6}% | {:12} | {:12} | {:11} | {:9} | {:12}".format(
            s["variant"],
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
