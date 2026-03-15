"""
EXP-0062: Race EV Filter Experiment.

レース単位で race_ev = Σ(probability × odds) を計算し、
race_ev 閾値でレースをフィルタした場合の ROI・利益・リスク指標を評価する。

CASE0: baseline（フィルタなし）
CASE1: race_ev ≥ 1.00
CASE2: race_ev ≥ 1.02
CASE3: race_ev ≥ 1.05
CASE4: race_ev ≥ 1.10

既存戦略: d_hi475 + switch_dd4000 を全 CASE に同一適用。
rolling validation: n_windows=12。
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
from kyotei_predictor.domain.verification_models import get_odds_for_combination
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

EV_LO_BASELINE, EV_HI, PROB_MIN = 4.30, 4.75, 0.05
TRAIN_DAYS = 30
TEST_DAYS = 7
STEP_DAYS = 7
N_WINDOWS = 12

# (case_name, race_ev_min). None = no filter
RACE_EV_CASES: List[Tuple[str, Optional[float]]] = [
    ("CASE0_baseline", None),
    ("CASE1_race_ev_ge_100", 1.00),
    ("CASE2_race_ev_ge_102", 1.02),
    ("CASE3_race_ev_ge_105", 1.05),
    ("CASE4_race_ev_ge_110", 1.10),
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


def _race_ev_for_race(race: dict, prediction_date: str, repo) -> Optional[float]:
    """
    レースごとに 120 通りの EV を合計: race_ev = Σ(probability × odds).
    オッズが取れない combination は 0 として加算。オッズが全く取れない場合は None を返す。
    """
    all_comb = race.get("all_combinations") or []
    if not all_comb:
        return None
    venue = race.get("venue") or ""
    rno = int(race.get("race_number") or 0)
    if not venue or rno <= 0:
        return None
    odds_data = repo.get_odds(prediction_date, venue, rno) if hasattr(repo, "get_odds") else None
    if odds_data is None:
        return None
    total = 0.0
    has_any = False
    for c in all_comb:
        comb_raw = (c.get("combination") or "").strip()
        if not comb_raw:
            continue
        prob = float(c.get("probability", c.get("score", 0.0)))
        od = get_odds_for_combination(odds_data, comb_raw)
        if od is not None and float(od) > 0:
            total += prob * float(od)
            has_any = True
    return total if has_any else None


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


def _filter_bets_d_hi475(bets: List[BetTuple], top1: Optional[float]) -> List[BetTuple]:
    """d_hi475: 4.30≤EV<4.75, prob≥0.05, top1_prob≤0.35 は別扱いしない（CASE6 と異なりここでは使わない）。"""
    return _filter_bets_by_selection(bets, EV_LO_BASELINE, EV_HI, PROB_MIN)


def _run_one_n_windows(
    n_w: int,
    window_list: List[Tuple[str, str, str, str]],
    day_races_raw: Dict[str, List[Tuple[float, List[BetTuple], float, Optional[float]]]],
    race_ev_min: Optional[float],
) -> Dict:
    """
    day_races_raw: day -> [(max_ev, bets, top1_prob, race_ev), ...]
    race_ev_min: None なら全レース通過、否则 race_ev >= race_ev_min のレースのみ。
    d_hi475 + switch_dd4000 を適用して 1 つの結果 dict を返す。
    """
    window_set = {wi for wi in range(n_w)}
    day_to_wi: Dict[str, int] = {}
    for wi, (_ts, _te, tst, tend) in enumerate(window_list):
        if wi >= n_w:
            break
        for day in _date_range(tst, tend):
            day_to_wi[day] = wi

    # レースフィルタ: race_ev 条件
    day_races_filtered: Dict[str, List[Tuple[float, List[BetTuple], float]]] = {}
    for day, races_data in day_races_raw.items():
        wi = day_to_wi.get(day, -1)
        if wi not in window_set:
            continue
        filtered = []
        for max_ev, bets, top1_prob, race_ev in races_data:
            if race_ev_min is not None:
                if race_ev is None or race_ev < race_ev_min:
                    continue
            filtered.append((max_ev, bets, top1_prob))
        if filtered:
            day_races_filtered[day] = filtered

    # ref_profit: baseline (d_hi475) で 100 円ベットの window 別利益 → switch スケジュール用
    ref_profit: List[float] = [0.0] * n_w
    for day, races_data in day_races_filtered.items():
        wi = day_to_wi.get(day, -1)
        if wi < 0 or wi >= n_w:
            continue
        races_sorted = sorted(races_data, key=lambda x: -x[0])
        n = len(races_sorted)
        k_skip = int(n * SKIP_TOP_PCT)
        idx_start = min(k_skip, n)
        for max_ev, bets, top1_prob in races_sorted[idx_start:]:
            for _ev, _prob, odds, hit in _filter_bets_d_hi475(bets, top1_prob):
                ref_profit[wi] += (FIXED_STAKE * odds if hit else 0.0) - FIXED_STAKE
    schedule = _stake_schedule_dd(n_w, ref_profit, 4000)

    # 集計: stake=schedule[wi], d_hi475 フィルタ
    total_stake = 0.0
    total_payout = 0.0
    bet_count = 0
    hit_count = 0
    window_profits = [0.0] * n_w
    window_stake = [0.0] * n_w
    window_payout = [0.0] * n_w
    window_bet_count = [0] * n_w

    for day, races_data in day_races_filtered.items():
        wi = day_to_wi.get(day, -1)
        if wi not in window_set:
            continue
        st = schedule[wi]
        races_sorted = sorted(races_data, key=lambda x: -x[0])
        n = len(races_sorted)
        k_skip = int(n * SKIP_TOP_PCT)
        idx_start = min(k_skip, n)
        for max_ev, bets, top1_prob in races_sorted[idx_start:]:
            for _ev, _prob, odds, hit in _filter_bets_d_hi475(bets, top1_prob):
                total_stake += st
                total_payout += st * odds if hit else 0.0
                bet_count += 1
                if hit:
                    hit_count += 1
                window_profits[wi] += (st * odds if hit else 0.0) - st
                window_stake[wi] += st
                window_payout[wi] += st * odds if hit else 0.0
                window_bet_count[wi] += 1

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
        "window_profits": window_profits,
        "window_stake": window_stake,
        "window_payout": window_payout,
        "window_bet_count": window_bet_count,
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
        print("[EXP-0062] ERROR: DB not found: {}".format(db_path_resolved), file=sys.stderr)
        return 1
    db_path_str = str(db_path_resolved)
    print("[EXP-0062] DB found: {}".format(db_path_str))

    raw_dir = _REPO_ROOT / "kyotei_predictor" / "data" / "raw"
    if not raw_dir.is_dir():
        raw_dir = Path("kyotei_predictor/data/raw")

    output_dir = args.output_dir or _REPO_ROOT / "outputs" / "race_ev_filter"
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
        print("EXP-0062: Running rolling validation (n_windows={})...".format(n_w))
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
        print("EXP-0062: Using existing predictions in {}.".format(out_pred_dir))

    repo = get_race_data_repository("db", data_dir=raw_dir, db_path=db_path_str)

    # day -> [(max_ev, bets, top1_prob, race_ev), ...]
    day_races_raw: Dict[str, List[Tuple[float, List[BetTuple], float, Optional[float]]]] = {}
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
                race_ev = _race_ev_for_race(race, prediction_date, repo)
                if bets is not None:
                    races_data.append((max_ev, bets, top1_prob, race_ev))
            if races_data:
                day_races_raw[day] = races_data

    results_by_case: Dict[str, Dict] = {}
    for case_name, race_ev_min in RACE_EV_CASES:
        res = _run_one_n_windows(n_w, window_list, day_races_raw, race_ev_min)
        results_by_case[case_name] = res

    summary_list = []
    for case_name, _ in RACE_EV_CASES:
        r = results_by_case[case_name]
        summary_list.append({
            "variant": case_name,
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
        "experiment_id": "EXP-0062",
        "purpose": "Race EV filter: filter races by race_ev = sum(prob*odds), then apply d_hi475 + switch_dd4000",
        "db_path_used": db_path_str,
        "n_windows": n_w,
        "race_ev_cases": [{"name": c[0], "race_ev_min": c[1]} for c in RACE_EV_CASES],
        "strategy": "d_hi475 + switch_dd4000",
        "summary": summary_list,
        "results_by_case": {k: {kk: vv for kk, vv in v.items() if kk not in ("window_profits", "window_stake", "window_payout", "window_bet_count")} for k, v in results_by_case.items()},
    }

    out_path = output_dir / "exp0062_race_ev_filter_results.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    print("Saved {}".format(out_path))

    print("\n--- EXP-0062 Race EV Filter (n_windows={}) ---".format(n_w))
    print("variant              | ROI     | total_profit | max_drawdown | profit/1k   | bet_count | longest_lose")
    print("-" * 105)
    for s in summary_list:
        print("  {:18} | {:6}% | {:12} | {:12} | {:11} | {:9} | {:12}".format(
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
