"""
EXP-0059: CASE2 フィルタ改善（ノイズ削減）。

CASE2_base（EV≥4.60）をベースに、prob・predicted_odds・top1_prob を追加した
5 条件を比較し、profit 維持・longest_losing_streak 短縮・profit/max_drawdown 改善を評価する。
同一予測・窓・switch_dd4000 を EXP-0058 と同一に使用。
"""

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Callable, Dict, List, Optional, Tuple

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

EV_HI = 4.75
TRAIN_DAYS = 30
TEST_DAYS = 7
STEP_DAYS = 7
BLOCK_SIZE = 6

VARIANT_NAMES = [
    "CASE2_base",
    "CASE2_prob",
    "CASE2_odds",
    "CASE2_prob_odds",
    "CASE2_full",
]

BetTuple = Tuple[float, float, float, bool]
FilterFn = Callable[[List[BetTuple], Optional[float]], List[BetTuple]]


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


def _make_filter_baseline() -> FilterFn:
    def _f(bets: List[BetTuple], _top1: Optional[float]) -> List[BetTuple]:
        return _filter_bets_by_selection(bets, 4.30, EV_HI, 0.05)
    return _f


# CASE2_base: EV ≥ 4.60 (prob_min=0.05 は既存 CASE2 と同一)
def _make_filter_case2_base() -> FilterFn:
    def _f(bets: List[BetTuple], _top1: Optional[float]) -> List[BetTuple]:
        return _filter_bets_by_selection(bets, 4.60, EV_HI, 0.05)
    return _f


# CASE2_prob: EV ≥ 4.60, prob ≥ 0.06
def _make_filter_case2_prob() -> FilterFn:
    def _f(bets: List[BetTuple], _top1: Optional[float]) -> List[BetTuple]:
        return _filter_bets_by_selection(bets, 4.60, EV_HI, 0.06)
    return _f


# CASE2_odds: EV ≥ 4.60, predicted_odds ≥ 12
def _make_filter_case2_odds() -> FilterFn:
    def _f(bets: List[BetTuple], _top1: Optional[float]) -> List[BetTuple]:
        base = _filter_bets_by_selection(bets, 4.60, EV_HI, 0.05)
        return [(ev, prob, odds, hit) for ev, prob, odds, hit in base if odds >= 12]

    return _f


# CASE2_prob_odds: EV ≥ 4.60, prob ≥ 0.06, predicted_odds ≥ 12
def _make_filter_case2_prob_odds() -> FilterFn:
    def _f(bets: List[BetTuple], _top1: Optional[float]) -> List[BetTuple]:
        base = _filter_bets_by_selection(bets, 4.60, EV_HI, 0.06)
        return [(ev, prob, odds, hit) for ev, prob, odds, hit in base if odds >= 12]

    return _f


# CASE2_full: EV ≥ 4.60, prob ≥ 0.06, predicted_odds ≥ 12, top1_probability ≤ 0.35
def _make_filter_case2_full() -> FilterFn:
    def _f(bets: List[BetTuple], top1: Optional[float]) -> List[BetTuple]:
        if top1 is not None and top1 > 0.35:
            return []
        base = _filter_bets_by_selection(bets, 4.60, EV_HI, 0.06)
        return [(ev, prob, odds, hit) for ev, prob, odds, hit in base if odds >= 12]

    return _f


FILTER_BASELINE = _make_filter_baseline()
FILTERS: Dict[str, FilterFn] = {
    "CASE2_base": _make_filter_case2_base(),
    "CASE2_prob": _make_filter_case2_prob(),
    "CASE2_odds": _make_filter_case2_odds(),
    "CASE2_prob_odds": _make_filter_case2_prob_odds(),
    "CASE2_full": _make_filter_case2_full(),
}


def _run_one_n_windows(
    n_w: int,
    window_list: List[Tuple[str, str, str, str]],
    day_races_raw: Dict[str, List[Tuple[float, List[BetTuple], float]]],
) -> Tuple[Dict[str, Dict], List[Dict]]:
    window_set = {wi for wi in range(n_w)}
    day_to_wi: Dict[str, int] = {}
    for wi, (_ts, _te, tst, tend) in enumerate(window_list):
        if wi >= n_w:
            break
        for day in _date_range(tst, tend):
            day_to_wi[day] = wi

    # Baseline for ref_profit and schedule
    day_data_baseline: Dict[str, Tuple[int, float, float]] = {}
    for day, races_data in day_races_raw.items():
        wi = day_to_wi.get(day, -1)
        if wi not in window_set:
            continue
        races_sorted = sorted(races_data, key=lambda x: -x[0])
        n = len(races_sorted)
        k_skip = int(n * SKIP_TOP_PCT)
        idx_start = min(k_skip, n)
        s100, p100 = 0.0, 0.0
        for max_ev, bets, top1_prob in races_sorted[idx_start:]:
            filtered = FILTER_BASELINE(bets, top1_prob)
            for _ev, _prob, odds, hit in filtered:
                s100 += FIXED_STAKE
                if hit:
                    p100 += FIXED_STAKE * odds
        day_data_baseline[day] = (wi, s100, p100)

    ref_profit: List[float] = [0.0] * n_w
    for day, (wi, s100, p100) in day_data_baseline.items():
        if 0 <= wi < n_w:
            ref_profit[wi] += p100 - s100
    schedule = _stake_schedule_dd(n_w, ref_profit, 4000)

    day_data_by_variant: Dict[str, Dict[str, Tuple[int, float, float, int, int]]] = {
        v: {} for v in VARIANT_NAMES
    }

    for day, races_data in day_races_raw.items():
        wi = day_to_wi.get(day, -1)
        if wi not in window_set:
            continue
        st = schedule[wi]
        races_sorted = sorted(races_data, key=lambda x: -x[0])
        n = len(races_sorted)
        k_skip = int(n * SKIP_TOP_PCT)
        idx_start = min(k_skip, n)
        races_sub = races_sorted[idx_start:]

        for vname, filter_fn in FILTERS.items():
            stake_day = 0.0
            payout_day = 0.0
            bet_count = 0
            hit_count = 0
            for max_ev, bets, top1_prob in races_sub:
                filtered = filter_fn(bets, top1_prob)
                for _ev, _prob, odds, hit in filtered:
                    stake_day += st
                    if hit:
                        payout_day += st * odds
                    bet_count += 1
                    if hit:
                        hit_count += 1
            if bet_count > 0:
                day_data_by_variant[vname][day] = (wi, stake_day, payout_day, bet_count, hit_count)

    results: Dict[str, Dict] = {}
    for vname in VARIANT_NAMES:
        results[vname] = {
            "total_stake": 0.0,
            "total_payout": 0.0,
            "bet_count": 0,
            "hit_count": 0,
            "window_profits": [0.0] * n_w,
        }

    for vname in VARIANT_NAMES:
        for day, tup in day_data_by_variant[vname].items():
            wi, stake, payout, bet_count, hit_count = tup
            if wi < 0 or wi >= n_w:
                continue
            results[vname]["total_stake"] += stake
            results[vname]["total_payout"] += payout
            results[vname]["bet_count"] += bet_count
            results[vname]["hit_count"] += hit_count
            results[vname]["window_profits"][wi] += payout - stake

    summary_list: List[Dict] = []
    for vname in VARIANT_NAMES:
        r = results[vname]
        wp = r["window_profits"]
        ts = r["total_stake"]
        tp = r["total_payout"]
        cnt = r["bet_count"]
        total_profit = round(tp - ts, 2)
        roi = round((tp / ts - 1) * 100, 2) if ts else None
        profit_per_1000 = round(1000.0 * (tp - ts) / cnt, 2) if cnt else 0.0
        cum = peak = dd = 0.0
        for wprof in wp:
            cum += wprof
            if cum > peak:
                peak = cum
            if peak - cum > dd:
                dd = peak - cum
        max_drawdown = round(dd, 2)
        longest_losing_streak = _longest_losing_streak(wp)
        profit_per_drawdown = round(total_profit / max_drawdown, 4) if max_drawdown > 0 else None

        summary_list.append({
            "variant": vname,
            "ROI": roi,
            "total_profit": total_profit,
            "max_drawdown": max_drawdown,
            "profit_per_1000_bets": profit_per_1000,
            "bet_count": cnt,
            "longest_losing_streak": longest_losing_streak,
            "total_stake": round(ts, 2),
            "profit_per_drawdown": profit_per_drawdown,
        })
        r.update(summary_list[-1])

    return results, summary_list


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db-path", type=str, default=None)
    parser.add_argument("--output-dir", type=Path, default=None)
    parser.add_argument("--predictions-dir", type=Path, default=None)
    parser.add_argument("--n-windows-list", type=str, default="24,30,36")
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    n_windows_list = [int(x.strip()) for x in args.n_windows_list.split(",") if x.strip()]
    if not n_windows_list:
        n_windows_list = [24, 30, 36]
    max_n_w = max(n_windows_list)

    db_path_resolved = _resolve_db_path(args.db_path)
    if not db_path_resolved.exists():
        print("[EXP-0059] ERROR: DB not found: {}".format(db_path_resolved), file=sys.stderr)
        return 1
    db_path_str = str(db_path_resolved)
    print("[EXP-0059] DB found: {}".format(db_path_str))

    raw_dir = _REPO_ROOT / "kyotei_predictor" / "data" / "raw"
    if not raw_dir.is_dir():
        raw_dir = Path("kyotei_predictor/data/raw")

    output_dir = args.output_dir or _REPO_ROOT / "outputs" / "selection_verified"
    output_dir.mkdir(parents=True, exist_ok=True)

    pred_parent = args.predictions_dir or _REPO_ROOT / "outputs" / "ev_cap_experiments"
    out_pred_dir = pred_parent / "rolling_roi_predictions"

    min_date, max_date = get_db_date_range(db_path_str)
    window_list_full = build_windows(
        min_date, max_date, TRAIN_DAYS, TEST_DAYS, STEP_DAYS, max_n_w
    )
    if len(window_list_full) < max_n_w:
        max_n_w = len(window_list_full)
        n_windows_list = [n for n in n_windows_list if n <= max_n_w]

    need_days = set()
    for _ts, _te, tst, tend in window_list_full:
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
        print("EXP-0059: Running rolling validation (n_windows={})...".format(max_n_w))
        run_rolling_validation_roi(
            db_path=db_path_str,
            output_dir=pred_parent,
            data_dir_raw=raw_dir,
            train_days=TRAIN_DAYS,
            test_days=TEST_DAYS,
            step_days=STEP_DAYS,
            n_windows=max_n_w,
            strategies=STRATEGIES,
            model_type="xgboost",
            calibration="sigmoid",
            feature_set="extended_features",
            seed=args.seed,
        )
    else:
        print("EXP-0059: Using existing predictions in {}.".format(out_pred_dir))

    repo = get_race_data_repository("db", data_dir=raw_dir, db_path=db_path_str)

    day_races_raw: Dict[str, List[Tuple[float, List[BetTuple], float]]] = {}
    for wi, (_ts, _te, tst, tend) in enumerate(window_list_full):
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

    results_by_n_w: Dict[int, Dict] = {}
    for n_w in n_windows_list:
        if n_w > len(window_list_full):
            continue
        window_list_n = list(window_list_full[:n_w])
        results, summary_list = _run_one_n_windows(n_w, window_list_n, day_races_raw)
        results_by_n_w[n_w] = {"summary": summary_list}

    evaluation = {}
    if 36 in results_by_n_w:
        summary = results_by_n_w[36]["summary"]
        base_row = next(s for s in summary if s["variant"] == "CASE2_base")
        evaluation = {
            "reference_CASE2_base": {
                "total_profit": base_row["total_profit"],
                "longest_losing_streak": base_row["longest_losing_streak"],
                "profit_per_drawdown": base_row["profit_per_drawdown"],
            },
            "vs_base": [],
        }
        for s in summary:
            if s["variant"] == "CASE2_base":
                continue
            evaluation["vs_base"].append({
                "variant": s["variant"],
                "profit_maintained": s["total_profit"] >= base_row["total_profit"] * 0.95,
                "longest_lose_shortened": s["longest_losing_streak"] < base_row["longest_losing_streak"],
                "profit_dd_improved": (
                    s["profit_per_drawdown"] is not None
                    and base_row["profit_per_drawdown"] is not None
                    and s["profit_per_drawdown"] > base_row["profit_per_drawdown"]
                ),
                "total_profit": s["total_profit"],
                "longest_losing_streak": s["longest_losing_streak"],
                "profit_per_drawdown": s["profit_per_drawdown"],
            })

    payload = {
        "experiment_id": "EXP-0059",
        "purpose": "CASE2 filter refinement (noise reduction for standalone attack)",
        "db_path_used": db_path_str,
        "n_windows_list": n_windows_list,
        "variants": VARIANT_NAMES,
        "results_by_n_windows": {
            str(n_w): {"summary": data["summary"]}
            for n_w, data in results_by_n_w.items()
        },
        "evaluation_n_w36": evaluation,
    }

    out_path = output_dir / "exp0059_case2_filter_refinement_results.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    print("Saved {}".format(out_path))

    print("\n--- EXP-0059 Summary (n_windows=36) ---")
    if 36 in results_by_n_w:
        summary = results_by_n_w[36]["summary"]
        print("variant         | ROI     | total_profit | max_dd   | profit/1k   | bet_count | longest_lose | total_stake | profit/dd")
        print("-" * 125)
        for s in summary:
            pd = s.get("profit_per_drawdown")
            print("  {:13} | {:6}% | {:12} | {:8} | {:11} | {:9} | {:13} | {:11} | {}".format(
                s["variant"],
                s["ROI"] if s["ROI"] is not None else "—",
                s["total_profit"],
                s["max_drawdown"],
                s["profit_per_1000_bets"],
                s["bet_count"],
                s["longest_losing_streak"],
                int(s["total_stake"]),
                pd if pd is not None else "—",
            ))

    print("\n--- Evaluation vs CASE2_base (n_w=36) ---")
    if evaluation and "vs_base" in evaluation:
        base = evaluation["reference_CASE2_base"]
        print("  CASE2_base: profit={}, longest_lose={}, profit/dd={}".format(
            base["total_profit"], base["longest_losing_streak"], base["profit_per_drawdown"],
        ))
        for v in evaluation["vs_base"]:
            print("  {}: profit_ok={}, lose_shortened={}, profit_dd_improved={}".format(
                v["variant"],
                v["profit_maintained"],
                v["longest_lose_shortened"],
                v["profit_dd_improved"],
            ))

    return 0


if __name__ == "__main__":
    sys.exit(main())
