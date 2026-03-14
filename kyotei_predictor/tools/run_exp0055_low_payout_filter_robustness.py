"""
EXP-0055: Low Payout Filter Robustness Comparison.

EXP-0054 で低配当回避フィルタが有効と分かった。本実験では
baseline / CASE2 / CASE4 / CASE5 / CASE6 を n_windows=24,30,36 で比較し、
長期で強い候補と実運用向き安定候補を切り分ける。
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
BLOCK_SIZE = 6

# 主分析: 5 条件
BetTuple = Tuple[float, float, float, bool]
FilterFn = Callable[[List[BetTuple], Optional[float]], List[BetTuple]]


def _top1_probability_for_race(race: dict) -> float:
    all_comb = race.get("all_combinations") or []
    if not all_comb:
        return 0.0
    probs = [float(c.get("probability") or c.get("score", 0)) for c in all_comb if c.get("probability") is not None or c.get("score") is not None]
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
    ("CASE2_ev_ge_460", _make_filter_ev_min(4.60)),
    ("CASE4_odds_ge_12", _make_filter_odds_min(12)),
    ("CASE5_odds_ge_15", _make_filter_odds_min(15)),
    ("CASE6_top1_prob_le_035", _make_filter_top1_prob_max(0.35)),
]


def _run_one_n_windows(
    n_w: int,
    window_list: List[Tuple[str, str, str, str]],
    day_races_raw: Dict[str, List[Tuple[float, List[BetTuple], float]]],
) -> Tuple[Dict[str, Dict], List[Dict], Dict[str, List[Dict]]]:
    block_size = BLOCK_SIZE
    n_blocks = n_w // block_size if block_size else 0
    half = n_w // 2
    window_set = {wi for wi in range(n_w)}
    day_to_wi: Dict[str, int] = {}
    for wi, (_ts, _te, tst, tend) in enumerate(window_list):
        if wi >= n_w:
            break
        for day in _date_range(tst, tend):
            day_to_wi[day] = wi

    day_data_by_variant: Dict[str, Dict[str, Tuple[int, float, float, float, float, int, int]]] = {
        vname: {} for vname, _ in VARIANTS
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
            bet_count = hit_count = 0
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
        cum = peak = dd = 0.0
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
            b_cum = b_peak = b_dd = 0.0
            for p in b_profits:
                b_cum += p
                if b_cum > b_peak:
                    b_peak = b_cum
                if b_peak - b_cum > b_dd:
                    b_dd = b_peak - b_cum
            block_metrics[vname].append({
                "block_index": bi,
                "window_range": f"w{start_wi}-w{end_wi - 1}",
                "test_start": window_list[start_wi][2] if start_wi < len(window_list) else "",
                "test_end": window_list[end_wi - 1][3] if end_wi <= len(window_list) else "",
                "block_profit": round(b_profit, 2),
                "block_roi": b_roi,
                "block_drawdown": round(b_dd, 2),
                "block_bet_count": b_bet,
                "block_hit_count": b_hit,
            })

    return results, summary_list, block_metrics


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db-path", type=str, default=None)
    parser.add_argument("--output-dir", type=Path, default=None)
    parser.add_argument("--predictions-dir", type=Path, default=None)
    parser.add_argument("--n-windows-list", type=str, default="24,30,36", help="Comma-separated, e.g. 24,30,36")
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    n_windows_list = [int(x.strip()) for x in args.n_windows_list.split(",") if x.strip()]
    if not n_windows_list:
        n_windows_list = [24, 30, 36]
    max_n_w = max(n_windows_list)

    db_path_resolved = _resolve_db_path(args.db_path)
    if not db_path_resolved.exists():
        print("[ERROR] DB not found: {}".format(db_path_resolved), file=sys.stderr)
        return 1
    db_path_str = str(db_path_resolved)
    print("[EXP-0055] DB found: {}".format(db_path_str))

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
        print("EXP-0055: Running rolling validation (n_windows={})...".format(max_n_w))
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
        print("EXP-0055: Using existing predictions in {}.".format(out_pred_dir))

    repo = get_race_data_repository("db", data_dir=raw_dir, db_path=db_path_str)

    # day -> list of (max_ev, bets, top1_prob) for all days in max_n_w windows
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
        results, summary_list, block_metrics = _run_one_n_windows(
            n_w, window_list_n, day_races_raw
        )
        results_by_n_w[n_w] = {
            "summary": summary_list,
            "block_metrics": block_metrics,
        }

    # Robustness: rank by total_profit at each n_w
    robustness_profit: Dict[int, List[Tuple[str, float]]] = {}
    robustness_roi: Dict[int, List[Tuple[str, float]]] = {}
    robustness_max_dd: Dict[int, List[Tuple[str, float]]] = {}
    for n_w, data in results_by_n_w.items():
        summary = data["summary"]
        robustness_profit[n_w] = sorted([(s["variant"], s["total_profit"]) for s in summary], key=lambda x: -x[1])
        robustness_roi[n_w] = sorted([(s["variant"], s["ROI"] or -999) for s in summary], key=lambda x: -x[1])
        robustness_max_dd[n_w] = sorted([(s["variant"], s["max_drawdown"]) for s in summary], key=lambda x: x[1])

    # CASE2 sharpness at n_w=36
    case2_sharpness: Optional[Dict] = None
    if 36 in results_by_n_w:
        s36 = next((s for s in results_by_n_w[36]["summary"] if s["variant"] == "CASE2_ev_ge_460"), None)
        bm36 = results_by_n_w[36]["block_metrics"].get("CASE2_ev_ge_460", [])
        if s36 and bm36:
            total_p = s36["total_profit"]
            block_profits = [b["block_profit"] for b in bm36]
            block_share = [round(100.0 * b / total_p, 1) if total_p and total_p != 0 else 0 for b in block_profits]
            max_block_share = max(abs(s) for s in block_share) if block_share else 0
            case2_sharpness = {
                "bet_count": s36["bet_count"],
                "longest_losing_streak": s36["longest_losing_streak"],
                "block_profits": block_profits,
                "block_profit_share_pct": block_share,
                "max_absolute_block_share_pct": max_block_share,
            }

    # Classification
    if 36 in results_by_n_w:
        summary36 = results_by_n_w[36]["summary"]
        by_profit = sorted(summary36, key=lambda s: -s["total_profit"])
        by_dd = sorted(summary36, key=lambda s: s["max_drawdown"])
        high_return = [s["variant"] for s in by_profit if s["total_profit"] > 5000 and s["variant"] != "baseline"][:2]
        stable = [s["variant"] for s in summary36 if s["longest_losing_streak"] <= 6 and s["bet_count"] >= 400 and s["variant"] != "baseline"]
        reject = [s["variant"] for s in summary36 if s["total_profit"] < 0 or s["bet_count"] < 200]
    else:
        high_return = stable = reject = []

    payload = {
        "experiment_id": "EXP-0055",
        "purpose": "Low Payout Filter Robustness (n_w=24/30/36)",
        "db_path_used": db_path_str,
        "selection_baseline": "d_hi475 + switch_dd4000",
        "n_windows_list": n_windows_list,
        "block_size": BLOCK_SIZE,
        "variants": [vname for vname, _ in VARIANTS],
        "results_by_n_windows": {
            str(n_w): {
                "summary": data["summary"],
                "block_metrics": data["block_metrics"],
            }
            for n_w, data in results_by_n_w.items()
        },
        "robustness": {
            "rank_by_total_profit": {str(k): [x[0] for x in v] for k, v in robustness_profit.items()},
            "rank_by_ROI": {str(k): [x[0] for x in v] for k, v in robustness_roi.items()},
            "rank_by_max_drawdown_best": {str(k): [x[0] for x in v] for k, v in robustness_max_dd.items()},
        },
        "case2_sharpness": case2_sharpness,
        "classification": {
            "high_return_candidates": high_return,
            "stable_candidates": stable,
            "reject_candidates": reject,
        },
    }

    out_path = output_dir / "exp0055_low_payout_filter_robustness_results.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    print("Saved {}".format(out_path))

    print("\n--- EXP-0055 Overall (n_windows=36) ---")
    if 36 in results_by_n_w:
        summary = results_by_n_w[36]["summary"]
        print("variant                | ROI     | total_profit | max_dd    | profit/1k   | bet_count | lose_w | longest_lose")
        print("-" * 100)
        for s in summary:
            print("  {:22} | {:6}% | {:12} | {:9} | {:11} | {:9} | {:6} | {:12}".format(
                s["variant"],
                s["ROI"] if s["ROI"] is not None else "—",
                s["total_profit"],
                s["max_drawdown"],
                s["profit_per_1000_bets"],
                s["bet_count"],
                s["losing_windows"],
                s["longest_losing_streak"],
            ))

    print("\n--- Robustness (rank by total_profit) ---")
    for n_w in sorted(robustness_profit.keys()):
        print("  n_w={}: {}".format(n_w, " > ".join(x[0] for x in robustness_profit[n_w])))

    if case2_sharpness:
        print("\n--- CASE2 sharpness (n_w=36) ---")
        print("  bet_count={} longest_losing_streak={} block_profits={}".format(
            case2_sharpness["bet_count"], case2_sharpness["longest_losing_streak"], case2_sharpness["block_profits"]
        ))

    print("\n--- Classification ---")
    print("  high_return: {}  stable: {}  reject: {}".format(high_return, stable, reject))

    return 0


if __name__ == "__main__":
    sys.exit(main())
