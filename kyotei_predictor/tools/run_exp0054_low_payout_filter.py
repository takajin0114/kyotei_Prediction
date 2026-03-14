"""
EXP-0054: Low Payout Regime Filter Experiment.

EXP-0053 で「利益悪化は低配当ヒット偏重で説明できる」と確認された。
本実験では baseline（d_hi475 + switch_dd4000）に加え、
低配当寄りを避けるフィルタ（EV底上げ・予想オッズ下限・堅いレース回避）を検証する。

CASE1: EV >= 4.50
CASE2: EV >= 4.60
CASE3: predicted_odds >= 10
CASE4: predicted_odds >= 12
CASE5: predicted_odds >= 15
CASE6: top1_probability <= 0.35（堅いレース回避）
"""

import argparse
import json
import os
import statistics
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

EV_LO_BASELINE, EV_HI, PROB_MIN = 4.30, 4.75, 0.05
TRAIN_DAYS = 30
TEST_DAYS = 7
STEP_DAYS = 7
N_WINDOWS = 36
BLOCK_SIZE = 6


def _top1_probability_for_race(race: dict) -> float:
    """レース内の最大予想確率（all_combinations の probability の最大値）。"""
    all_comb = race.get("all_combinations") or []
    if not all_comb:
        return 0.0
    probs = []
    for c in all_comb:
        p = c.get("probability") or c.get("score")
        if p is not None:
            try:
                probs.append(float(p))
            except (TypeError, ValueError):
                pass
    return max(probs) if probs else 0.0


def _longest_losing_streak(window_profits: List[float]) -> int:
    best = 0
    cur = 0
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
    cum = 0.0
    peak = 0.0
    for wi in range(n_w):
        cum += ref_profit[wi]
        if cum > peak:
            peak = cum
        if peak - cum >= dd_threshold:
            schedule[wi] = 80
    return schedule


# (variant_name, filter_fn). filter_fn(bets, top1_prob|None) -> list of (ev, prob, odds, hit)
BetTuple = Tuple[float, float, float, bool]
FilterFn = Callable[[List[BetTuple], Optional[float]], List[BetTuple]]


def _make_filter_baseline() -> FilterFn:
    def _f(bets: List[BetTuple], _top1: Optional[float]) -> List[BetTuple]:
        return _filter_bets_by_selection(bets, EV_LO_BASELINE, EV_HI, PROB_MIN)
    return _f


def _make_filter_ev_min(ev_lo: float) -> FilterFn:
    def _f(bets: List[BetTuple], _top1: Optional[float]) -> List[BetTuple]:
        return _filter_bets_by_selection(bets, ev_lo, EV_HI, PROB_MIN)
    return _f


def _make_filter_odds_min(odds_min: float) -> FilterFn:
    def _f(bets: List[BetTuple], _top1: Optional[float]) -> List[BetTuple]:
        base = _filter_bets_by_selection(bets, EV_LO_BASELINE, EV_HI, PROB_MIN)
        return [(ev, prob, odds, hit) for ev, prob, odds, hit in base if odds >= odds_min]
    return _f


def _make_filter_top1_prob_max(threshold: float) -> FilterFn:
    def _f(bets: List[BetTuple], top1: Optional[float]) -> List[BetTuple]:
        if top1 is not None and top1 > threshold:
            return []
        return _filter_bets_by_selection(bets, EV_LO_BASELINE, EV_HI, PROB_MIN)
    return _f


VARIANTS: List[Tuple[str, FilterFn]] = [
    ("baseline", _make_filter_baseline()),
    ("CASE1_ev_ge_450", _make_filter_ev_min(4.50)),
    ("CASE2_ev_ge_460", _make_filter_ev_min(4.60)),
    ("CASE3_odds_ge_10", _make_filter_odds_min(10)),
    ("CASE4_odds_ge_12", _make_filter_odds_min(12)),
    ("CASE5_odds_ge_15", _make_filter_odds_min(15)),
    ("CASE6_top1_prob_le_035", _make_filter_top1_prob_max(0.35)),
]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db-path", type=str, default=None)
    parser.add_argument("--output-dir", type=Path, default=None)
    parser.add_argument("--predictions-dir", type=Path, default=None)
    parser.add_argument("--n-windows", type=int, default=N_WINDOWS)
    parser.add_argument("--block-size", type=int, default=BLOCK_SIZE)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    n_w = args.n_windows
    block_size = args.block_size
    n_blocks = n_w // block_size if block_size else 0

    db_path_resolved = _resolve_db_path(args.db_path)
    if not db_path_resolved.exists():
        print(f"[ERROR] DB not found: {db_path_resolved}", file=sys.stderr)
        return 1
    db_path_str = str(db_path_resolved)
    print(f"[EXP-0054] DB found: {db_path_str}")

    raw_dir = _REPO_ROOT / "kyotei_predictor" / "data" / "raw"
    if not raw_dir.is_dir():
        raw_dir = Path("kyotei_predictor/data/raw")

    output_dir = args.output_dir or _REPO_ROOT / "outputs" / "selection_verified"
    output_dir.mkdir(parents=True, exist_ok=True)

    pred_parent = args.predictions_dir or _REPO_ROOT / "outputs" / "ev_cap_experiments"
    out_pred_dir = pred_parent / "rolling_roi_predictions"

    min_date, max_date = get_db_date_range(db_path_str)
    window_list = build_windows(
        min_date, max_date, TRAIN_DAYS, TEST_DAYS, STEP_DAYS, n_w
    )
    if len(window_list) < n_w:
        n_w = len(window_list)
        n_blocks = n_w // block_size if block_size else 0

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
        print("EXP-0054: Running rolling validation (n_windows={})...".format(n_w))
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
        print("EXP-0054: Using existing predictions in {}.".format(out_pred_dir))

    repo = get_race_data_repository("db", data_dir=raw_dir, db_path=db_path_str)

    day_to_wi: Dict[str, int] = {}
    for wi, (_ts, _te, tst, tend) in enumerate(window_list):
        for day in _date_range(tst, tend):
            day_to_wi[day] = wi

    # day -> list of (max_ev, bets, top1_prob)
    day_races_raw: Dict[str, List[Tuple[float, List[Tuple[float, float, float, bool]], float]]] = {}
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

    half = n_w // 2
    window_set = {wi for wi in range(n_w)}

    # Per-variant: day -> (wi, s100, p100, s80, p80, bet_count, hit_count)
    day_data_by_variant: Dict[str, Dict[str, Tuple[int, float, float, float, float, int, int]]] = {
        name: {} for name, _ in VARIANTS
    }

    for day, races_data in day_races_raw.items():
        wi = day_to_wi.get(day, -1)
        if wi not in window_set:
            continue
        races_sorted = sorted(races_data, key=lambda x: -x[0])
        n = len(races_sorted)
        k_skip = int(n * SKIP_TOP_PCT)
        idx_start = min(k_skip, n)

        for vname, filter_fn in VARIANTS:
            s100, p100, s80, p80 = 0.0, 0.0, 0.0, 0.0
            bet_count = 0
            hit_count = 0
            for max_ev, bets, top1_prob in races_sorted[idx_start:]:
                filtered = filter_fn(bets, top1_prob)
                for ev, prob, odds, hit in filtered:
                    s100 += FIXED_STAKE
                    s80 += 80
                    bet_count += 1
                    if hit:
                        p100 += FIXED_STAKE * odds
                        p80 += 80 * odds
                        hit_count += 1
            if bet_count > 0 or vname == "baseline":
                day_data_by_variant[vname][day] = (wi, s100, p100, s80, p80, bet_count, hit_count)

    # ref_profit from baseline for switch_dd4000 schedule for switch_dd4000 schedule
    ref_profit: List[float] = [0.0] * n_w
    for day, (wi, s100, p100, _s80, _p80, _bc, _hc) in day_data_by_variant["baseline"].items():
        if 0 <= wi < n_w:
            ref_profit[wi] += p100 - s100

    schedule = _stake_schedule_dd(n_w, ref_profit, 4000)

    results: Dict[str, Dict] = {}
    for vname, _ in VARIANTS:
        results[vname] = {
            "total_stake": 0.0,
            "total_payout": 0.0,
            "bet_count": 0,
            "hit_count": 0,
            "window_profits": [0.0] * n_w,
            "window_stake": [0.0] * n_w,
            "window_payout": [0.0] * n_w,
            "window_bet_count": [0] * n_w,
            "window_hit_count": [0] * n_w,
            "schedule": schedule,
        }

    for vname, _ in VARIANTS:
        for day, (wi, s100, p100, s80, p80, bet_count, hit_count) in day_data_by_variant[vname].items():
            if wi < 0 or wi >= n_w:
                continue
            st = schedule[wi]
            stake = s100 if st == 100 else s80
            payout = p100 if st == 100 else p80
            results[vname]["total_stake"] += stake
            results[vname]["total_payout"] += payout
            results[vname]["bet_count"] += bet_count
            results[vname]["hit_count"] += hit_count
            results[vname]["window_profits"][wi] += payout - stake
            results[vname]["window_stake"][wi] += stake
            results[vname]["window_payout"][wi] += payout
            results[vname]["window_bet_count"][wi] += bet_count
            results[vname]["window_hit_count"][wi] += hit_count

    summary_list: List[Dict] = []
    block_metrics: Dict[str, List[Dict]] = {vname: [] for vname, _ in VARIANTS}

    for vname, _ in VARIANTS:
        r = results[vname]
        wp = r["window_profits"]
        ts = r["total_stake"]
        tp = r["total_payout"]
        cnt = r["bet_count"]
        hit_count = r["hit_count"]
        total_profit = round(tp - ts, 2)
        roi = round((tp / ts - 1) * 100, 2) if ts else None
        profit_per_1000 = round(1000.0 * (tp - ts) / cnt, 2) if cnt else 0.0
        cum = 0.0
        peak = 0.0
        dd = 0.0
        for wprof in wp:
            cum += wprof
            if cum > peak:
                peak = cum
            if peak - cum > dd:
                dd = peak - cum
        profitable_windows = sum(1 for w in wp if w > 0)
        losing_windows = sum(1 for w in wp if w < 0)
        longest_losing_streak = _longest_losing_streak(wp)
        worst_window_profit = round(min(wp), 2) if wp else None
        median_window_profit = round(statistics.median(wp), 2) if wp else None
        window_profit_std = round(statistics.stdev(wp), 2) if len(wp) >= 2 else None
        early_half_profit = round(sum(wp[:half]), 2) if half else 0.0
        late_half_profit = round(sum(wp[half:]), 2) if half < n_w else 0.0

        summary_list.append({
            "variant": vname,
            "ROI": roi,
            "total_profit": total_profit,
            "max_drawdown": round(dd, 2),
            "profit_per_1000_bets": profit_per_1000,
            "bet_count": cnt,
            "hit_count": hit_count,
            "total_stake": round(ts, 2),
            "profitable_windows": profitable_windows,
            "losing_windows": losing_windows,
            "longest_losing_streak": longest_losing_streak,
            "worst_window_profit": worst_window_profit,
            "median_window_profit": median_window_profit,
            "window_profit_std": window_profit_std,
            "early_half_profit": early_half_profit,
            "late_half_profit": late_half_profit,
        })
        r.update(summary_list[-1])

        for bi in range(n_blocks):
            start_wi = bi * block_size
            end_wi = min((bi + 1) * block_size, n_w)
            b_profits = wp[start_wi:end_wi]
            b_stake = sum(r["window_stake"][start_wi:end_wi])
            b_payout = sum(r["window_payout"][start_wi:end_wi])
            b_bet = sum(r["window_bet_count"][start_wi:end_wi])
            b_hit = sum(r["window_hit_count"][start_wi:end_wi])
            b_profit = sum(b_profits)
            b_roi = round((b_payout / b_stake - 1) * 100, 2) if b_stake else None
            block_metrics[vname].append({
                "block_index": bi,
                "window_range": f"w{start_wi}-w{end_wi - 1}",
                "test_start": window_list[start_wi][2] if start_wi < len(window_list) else "",
                "test_end": window_list[end_wi - 1][3] if end_wi <= len(window_list) else "",
                "block_profit": round(b_profit, 2),
                "block_roi": b_roi,
                "block_bet_count": b_bet,
                "block_hit_count": b_hit,
            })

    payload = {
        "experiment_id": "EXP-0054",
        "purpose": "Low Payout Regime Filter (d_hi475 + switch_dd4000 + extra filter)",
        "db_path_used": db_path_str,
        "selection_baseline": "d_hi475: skip_top20pct, 4.30<=EV<4.75, prob>=0.05",
        "n_windows": n_w,
        "block_size": block_size,
        "variants": [{"name": vname, "description": vname} for vname, _ in VARIANTS],
        "summary": summary_list,
        "block_metrics": block_metrics,
    }

    out_path = output_dir / "exp0054_low_payout_filter_results.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    print("Saved {}".format(out_path))

    print("\n--- EXP-0054 Summary (n_windows={}) ---".format(n_w))
    print("variant                | ROI     | total_profit | max_dd    | profit/1k   | bet_count | longest_lose")
    print("-" * 95)
    for vname, _ in VARIANTS:
        r = results[vname]
        print(
            "  {:22} | {:6}% | {:12} | {:9} | {:11} | {:9} | {:12}".format(
                vname,
                r["ROI"] if r["ROI"] is not None else "—",
                r["total_profit"],
                r["max_drawdown"],
                r["profit_per_1000_bets"],
                r["bet_count"],
                r["longest_losing_streak"],
            )
        )

    print("\n--- Block-level (block_size={}) ---".format(block_size))
    for vname, _ in VARIANTS:
        print("\n  [{}]".format(vname))
        for b in block_metrics[vname]:
            print("    block {} {} | profit {} | roi {}% | bets {} | hits {}".format(
                b["block_index"], b["window_range"], b["block_profit"], b["block_roi"] or 0, b["block_bet_count"], b["block_hit_count"]
            ))

    return 0


if __name__ == "__main__":
    sys.exit(main())
