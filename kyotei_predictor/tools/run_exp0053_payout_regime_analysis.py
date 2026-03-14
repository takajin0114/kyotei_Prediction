"""
EXP-0053: Payout / Odds Regime Analysis.

EXP-0052 で負けブロックは hit_rate が高く avg_ev も同水準なのに利益が悪化することが分かった。
「当たっても低配当に寄っている」可能性を検証するため、
的中時オッズ分布・払戻分布・hit 1件あたり利益を block/月別に算出する。

選抜: d_hi475。運用: switch_dd4000。比較: normal_only。n_windows=36, block_size=6。
"""

import argparse
import json
import os
import statistics
import sys
from collections import defaultdict
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

EV_LO, EV_HI, PROB_MIN = 4.30, 4.75, 0.05
TRAIN_DAYS = 30
TEST_DAYS = 7
STEP_DAYS = 7
N_WINDOWS = 36
BLOCK_SIZE = 6

VARIANTS: List[Tuple[str, str, Optional[int]]] = [
    ("normal_only", "normal_only", None),
    ("switch_dd4000", "switch_dd", 4000),
]


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


def _stake_schedule_dd(
    rule: str,
    dd_threshold: Optional[int],
    n_w: int,
    ref_profit: List[float],
) -> List[int]:
    schedule = [100] * n_w
    if rule == "normal_only":
        return schedule
    if rule == "switch_dd" and dd_threshold is not None:
        cum = 0.0
        peak = 0.0
        for wi in range(n_w):
            cum += ref_profit[wi]
            if cum > peak:
                peak = cum
            if peak - cum >= dd_threshold:
                schedule[wi] = 80
    return schedule


def _safe_percentile(sorted_list: List[float], p: float) -> Optional[float]:
    if not sorted_list:
        return None
    k = (len(sorted_list) - 1) * p / 100.0
    i = int(k)
    if i >= len(sorted_list) - 1:
        return round(sorted_list[-1], 2)
    return round(sorted_list[i] + (k - i) * (sorted_list[i + 1] - sorted_list[i]), 2)


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
    print(f"[EXP-0053] DB found: {db_path_str}")

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
        print(f"EXP-0053: Running rolling validation (n_windows={n_w})...")
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
        print(f"EXP-0053: Using existing predictions in {out_pred_dir}.")

    repo = get_race_data_repository("db", data_dir=raw_dir, db_path=db_path_str)

    races_per_date: Dict[str, List[Tuple[float, List[Tuple[float, float, float, bool]]]]] = {}
    day_to_wi: Dict[str, int] = {}
    for wi, (_ts, _te, tst, tend) in enumerate(window_list):
        for day in _date_range(tst, tend):
            day_to_wi[day] = wi

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
            day_races = []
            for race in predictions_list:
                max_ev = _max_ev_for_race(race)
                bets = _all_bets_for_race(race, prediction_date, repo)
                if bets:
                    day_races.append((max_ev, bets))
            if day_races:
                races_per_date[day] = day_races

    half = n_w // 2
    window_set = {wi for wi in range(n_w)}

    # day -> list of (odds, hit, ev) for each selected bet
    day_bet_details: Dict[str, List[Tuple[float, bool, float]]] = {}
    day_data: Dict[str, Tuple[int, float, float, float, float, int, int, float, float]] = {}
    for day, day_races in races_per_date.items():
        wi = day_to_wi.get(day, -1)
        if wi not in window_set:
            continue
        day_races_sorted = sorted(day_races, key=lambda x: -x[0])
        n = len(day_races_sorted)
        k_skip = int(n * SKIP_TOP_PCT)
        idx_start = min(k_skip, n)
        details = []
        s100, p100, s80, p80 = 0.0, 0.0, 0.0, 0.0
        sum_odds, sum_ev = 0.0, 0.0
        for max_ev, bets in day_races_sorted[idx_start:]:
            filtered = _filter_bets_by_selection(bets, EV_LO, EV_HI, PROB_MIN)
            for ev, prob, odds, hit in filtered:
                details.append((odds, hit, ev))
                s100 += FIXED_STAKE
                s80 += 80
                if hit:
                    p100 += FIXED_STAKE * odds
                    p80 += 80 * odds
                sum_odds += odds
                sum_ev += ev
        if details:
            day_bet_details[day] = details
            day_data[day] = (wi, s100, p100, s80, p80, len(details), sum(1 for _, h, _ in details if h), sum_odds, sum_ev)

    ref_profit: List[float] = [0.0] * n_w
    for day, (wi, s100, p100, _s80, _p80, _bc, _hc, _so, _se) in day_data.items():
        if 0 <= wi < n_w:
            ref_profit[wi] += p100 - s100

    results: Dict[str, Dict] = {}
    for name, rule, dd_thr in VARIANTS:
        schedule = _stake_schedule_dd(rule, dd_thr, n_w, ref_profit)
        results[name] = {
            "total_stake": 0.0,
            "total_payout": 0.0,
            "bet_count": 0,
            "hit_count": 0,
            "window_profits": [0.0] * n_w,
            "window_stake": [0.0] * n_w,
            "window_payout": [0.0] * n_w,
            "window_bet_count": [0] * n_w,
            "window_hit_count": [0] * n_w,
            "window_sum_ev": [0.0] * n_w,
            "window_sum_odds": [0.0] * n_w,
            "window_hit_odds": [[] for _ in range(n_w)],
            "window_payouts": [[] for _ in range(n_w)],
            "window_stakes_per_bet": [[] for _ in range(n_w)],
            "schedule": schedule,
        }
        for day in day_bet_details:
            wi = day_to_wi.get(day, -1)
            if wi < 0 or wi >= n_w:
                continue
            stake = schedule[wi]
            for odds, hit, ev in day_bet_details[day]:
                payout = stake * odds if hit else 0.0
                results[name]["total_stake"] += stake
                results[name]["total_payout"] += payout
                results[name]["bet_count"] += 1
                results[name]["hit_count"] += 1 if hit else 0
                results[name]["window_profits"][wi] += payout - stake
                results[name]["window_stake"][wi] += stake
                results[name]["window_payout"][wi] += payout
                results[name]["window_bet_count"][wi] += 1
                results[name]["window_hit_count"][wi] += 1 if hit else 0
                results[name]["window_sum_ev"][wi] += ev
                results[name]["window_sum_odds"][wi] += odds
                results[name]["window_payouts"][wi].append(payout)
                results[name]["window_stakes_per_bet"][wi].append(stake)
                if hit:
                    results[name]["window_hit_odds"][wi].append(odds)

    # Summary with payout/odds metrics
    summary_list: List[Dict] = []
    for name, _, _ in VARIANTS:
        r = results[name]
        ts = r["total_stake"]
        tp = r["total_payout"]
        cnt = r["bet_count"]
        hit_count = r["hit_count"]
        all_hit_odds: List[float] = []
        for wi in range(n_w):
            all_hit_odds.extend(r["window_hit_odds"][wi])
        all_payouts: List[float] = []
        hit_stakes: List[float] = []
        for wi in range(n_w):
            all_payouts.extend(r["window_payouts"][wi])
            for i, p in enumerate(r["window_payouts"][wi]):
                if p > 0:
                    hit_stakes.append(r["window_stakes_per_bet"][wi][i])
        hit_payouts = [p for p in all_payouts if p > 0]

        total_profit = tp - ts
        roi = round((tp / ts - 1) * 100, 2) if ts else None
        profit_per_1000 = round(1000.0 * total_profit / cnt, 2) if cnt else 0.0
        wp = r["window_profits"]
        cum, peak, dd = 0.0, 0.0, 0.0
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

        hit_odds_mean = round(statistics.mean(all_hit_odds), 2) if all_hit_odds else None
        hit_odds_median = round(statistics.median(all_hit_odds), 2) if all_hit_odds else None
        payout_per_hit_mean = round(statistics.mean(hit_payouts), 2) if hit_payouts else None
        payout_per_hit_median = round(statistics.median(hit_payouts), 2) if hit_payouts else None
        default_stake = r["schedule"][0] if r["schedule"] else 100
        profit_per_hit_mean = round(statistics.mean([p - s for p, s in zip(hit_payouts, hit_stakes)]), 2) if hit_payouts and hit_stakes and len(hit_payouts) == len(hit_stakes) else (round(statistics.mean(hit_payouts) - default_stake, 2) if hit_payouts else None)
        avg_odds_all = round(sum(r["window_sum_odds"][wi] for wi in range(n_w)) / cnt, 2) if cnt else None
        avg_ev_all = round(sum(r["window_sum_ev"][wi] for wi in range(n_w)) / cnt, 4) if cnt else None

        summary_list.append({
            "variant": name,
            "ROI": roi,
            "total_profit": round(total_profit, 2),
            "max_drawdown": round(dd, 2),
            "profit_per_1000_bets": profit_per_1000,
            "bet_count": cnt,
            "total_stake": round(ts, 2),
            "total_payout": round(tp, 2),
            "profitable_windows": profitable_windows,
            "losing_windows": losing_windows,
            "longest_losing_streak": longest_losing_streak,
            "worst_window_profit": worst_window_profit,
            "median_window_profit": median_window_profit,
            "window_profit_std": window_profit_std,
            "early_half_profit": early_half_profit,
            "late_half_profit": late_half_profit,
            "hit_odds_mean": hit_odds_mean,
            "hit_odds_median": hit_odds_median,
            "payout_per_hit_mean": payout_per_hit_mean,
            "payout_per_hit_median": payout_per_hit_median,
            "profit_per_hit_mean": profit_per_hit_mean,
            "avg_odds_all_bets": avg_odds_all,
            "avg_ev_all_bets": avg_ev_all,
        })
        r.update(summary_list[-1])

    # Block-level payout/odds
    block_metrics: Dict[str, List[Dict]] = {name: [] for name, _, _ in VARIANTS}
    for bi in range(n_blocks):
        start_wi = bi * block_size
        end_wi = min((bi + 1) * block_size, n_w)
        test_start = window_list[start_wi][2] if start_wi < len(window_list) else ""
        test_end = window_list[end_wi - 1][3] if end_wi <= len(window_list) else ""
        for name, _, _ in VARIANTS:
            r = results[name]
            b_hit_odds: List[float] = []
            b_payouts: List[float] = []
            b_stakes: List[float] = []
            b_profits = []
            b_bet = 0
            b_hit = 0
            b_stake = 0.0
            b_payout = 0.0
            b_sum_ev = 0.0
            b_sum_odds = 0.0
            for wi in range(start_wi, end_wi):
                b_hit_odds.extend(r["window_hit_odds"][wi])
                b_payouts.extend(r["window_payouts"][wi])
                b_stakes.extend(r["window_stakes_per_bet"][wi])
                b_profits.append(r["window_profits"][wi])
                b_bet += r["window_bet_count"][wi]
                b_hit += r["window_hit_count"][wi]
                b_stake += r["window_stake"][wi]
                b_payout += r["window_payout"][wi]
                b_sum_ev += r["window_sum_ev"][wi]
                b_sum_odds += r["window_sum_odds"][wi]
            b_profit = sum(b_profits)
            b_roi = round((b_payout / b_stake - 1) * 100, 2) if b_stake else None
            hit_payouts_b = [p for p in b_payouts if p > 0]
            hit_stakes_b = [s for p, s in zip(b_payouts, b_stakes) if p > 0]
            block_metrics[name].append({
                "block_id": bi,
                "window_range": f"w{start_wi}-w{end_wi - 1}",
                "test_start": test_start,
                "test_end": test_end,
                "block_profit": round(b_profit, 2),
                "block_roi": b_roi,
                "block_bets": b_bet,
                "block_hit_count": b_hit,
                "block_hit_rate": round(100.0 * b_hit / b_bet, 2) if b_bet else None,
                "block_hit_odds_mean": round(statistics.mean(b_hit_odds), 2) if b_hit_odds else None,
                "block_hit_odds_median": round(statistics.median(b_hit_odds), 2) if b_hit_odds else None,
                "block_hit_odds_p25": _safe_percentile(sorted(b_hit_odds), 25) if b_hit_odds else None,
                "block_hit_odds_p75": _safe_percentile(sorted(b_hit_odds), 75) if b_hit_odds else None,
                "block_hit_odds_max": round(max(b_hit_odds), 2) if b_hit_odds else None,
                "block_total_payout": round(b_payout, 2),
                "block_payout_per_hit_mean": round(statistics.mean(hit_payouts_b), 2) if hit_payouts_b else None,
                "block_payout_per_hit_median": round(statistics.median(hit_payouts_b), 2) if hit_payouts_b else None,
                "block_payout_per_bet": round(b_payout / b_bet, 2) if b_bet else None,
                "block_profit_per_hit_mean": round(statistics.mean([p - s for p, s in zip(hit_payouts_b, hit_stakes_b)]), 2) if hit_payouts_b and hit_stakes_b and len(hit_payouts_b) == len(hit_stakes_b) else None,
                "block_avg_odds_all": round(b_sum_odds / b_bet, 2) if b_bet else None,
                "block_avg_ev_all": round(b_sum_ev / b_bet, 4) if b_bet else None,
            })

    # Winning vs losing block comparison (switch_dd4000)
    switch_blocks = block_metrics["switch_dd4000"]
    winning_blocks = [b for b in switch_blocks if b["block_profit"] > 0]
    losing_blocks = [b for b in switch_blocks if b["block_profit"] < 0]
    win_lose_compare = {
        "winning_blocks": {
            "count": len(winning_blocks),
            "avg_hit_odds": round(statistics.mean([b["block_hit_odds_mean"] or 0 for b in winning_blocks]), 2) if winning_blocks else None,
            "median_hit_odds": round(statistics.median([b["block_hit_odds_median"] or 0 for b in winning_blocks]), 2) if winning_blocks else None,
            "avg_payout_per_hit": round(statistics.mean([b["block_payout_per_hit_mean"] or 0 for b in winning_blocks]), 2) if winning_blocks else None,
            "avg_profit_per_hit": round(statistics.mean([b["block_profit_per_hit_mean"] or 0 for b in winning_blocks]), 2) if winning_blocks else None,
            "avg_bet_count": round(statistics.mean([b["block_bets"] for b in winning_blocks]), 1) if winning_blocks else None,
            "avg_hit_rate": round(statistics.mean([b["block_hit_rate"] or 0 for b in winning_blocks]), 2) if winning_blocks else None,
            "avg_ev": round(statistics.mean([b["block_avg_ev_all"] or 0 for b in winning_blocks]), 4) if winning_blocks else None,
        },
        "losing_blocks": {
            "count": len(losing_blocks),
            "avg_hit_odds": round(statistics.mean([b["block_hit_odds_mean"] or 0 for b in losing_blocks]), 2) if losing_blocks else None,
            "median_hit_odds": round(statistics.median([b["block_hit_odds_median"] or 0 for b in losing_blocks]), 2) if losing_blocks else None,
            "avg_payout_per_hit": round(statistics.mean([b["block_payout_per_hit_mean"] or 0 for b in losing_blocks]), 2) if losing_blocks else None,
            "avg_profit_per_hit": round(statistics.mean([b["block_profit_per_hit_mean"] or 0 for b in losing_blocks]), 2) if losing_blocks else None,
            "avg_bet_count": round(statistics.mean([b["block_bets"] for b in losing_blocks]), 1) if losing_blocks else None,
            "avg_hit_rate": round(statistics.mean([b["block_hit_rate"] or 0 for b in losing_blocks]), 2) if losing_blocks else None,
            "avg_ev": round(statistics.mean([b["block_avg_ev_all"] or 0 for b in losing_blocks]), 4) if losing_blocks else None,
        },
    }

    # Monthly (switch_dd4000) with odds/payout
    month_to_windows: Dict[str, List[int]] = defaultdict(list)
    for wi in range(min(n_w, len(window_list))):
        month_to_windows[window_list[wi][2][:7]].append(wi)
    monthly_metrics: List[Dict] = []
    for month in sorted(month_to_windows.keys()):
        windices = month_to_windows[month]
        r = results["switch_dd4000"]
        m_hit_odds = []
        m_payouts = []
        m_stake = sum(r["window_stake"][wi] for wi in windices)
        m_payout = sum(r["window_payout"][wi] for wi in windices)
        m_bet = sum(r["window_bet_count"][wi] for wi in windices)
        m_hit = sum(r["window_hit_count"][wi] for wi in windices)
        for wi in windices:
            m_hit_odds.extend(r["window_hit_odds"][wi])
            m_payouts.extend(r["window_payouts"][wi])
        hit_payouts_m = [p for p in m_payouts if p > 0]
        monthly_metrics.append({
            "month": month,
            "hit_count": m_hit,
            "mean_hit_odds": round(statistics.mean(m_hit_odds), 2) if m_hit_odds else None,
            "payout_per_hit_mean": round(statistics.mean(hit_payouts_m), 2) if hit_payouts_m else None,
            "total_profit": round(m_payout - m_stake, 2),
            "roi": round((m_payout / m_stake - 1) * 100, 2) if m_stake else None,
        })

    # Chart-friendly JSON
    chart_data = {
        "block_mean_hit_odds": [block_metrics["switch_dd4000"][bi]["block_hit_odds_mean"] for bi in range(n_blocks)],
        "block_payout_per_hit_mean": [block_metrics["switch_dd4000"][bi]["block_payout_per_hit_mean"] for bi in range(n_blocks)],
        "block_total_profit": [block_metrics["switch_dd4000"][bi]["block_profit"] for bi in range(n_blocks)],
    }

    payload = {
        "experiment_id": "EXP-0053",
        "purpose": "Payout / Odds Regime analysis (n_windows=36)",
        "db_path_used": db_path_str,
        "selection": "d_hi475: skip_top20pct, 4.30<=EV<4.75, prob>=0.05",
        "n_windows": n_w,
        "block_size": block_size,
        "variants": [{"name": n, "rule": r, "dd_threshold": t} for n, r, t in VARIANTS],
        "summary": summary_list,
        "block_metrics": block_metrics,
        "win_lose_compare": win_lose_compare,
        "monthly_metrics_switch": monthly_metrics,
        "chart_data": chart_data,
    }
    out_path = output_dir / "exp0053_payout_regime_analysis_results.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    print(f"Saved {out_path}")

    # Console
    print("\n--- EXP-0053 Summary ---")
    for name, _, _ in VARIANTS:
        s = summary_list[[i for i, (n, _, _) in enumerate(VARIANTS) if n == name][0]]
        print(f"  [{name}] ROI={s['ROI']}% total_profit={s['total_profit']} total_payout={s['total_payout']} hit_odds_mean={s['hit_odds_mean']} payout_per_hit_mean={s['payout_per_hit_mean']} profit_per_hit_mean={s['profit_per_hit_mean']}")

    print("\n--- Block (switch_dd4000) odds/payout ---")
    print("block_id | block_profit | block_roi | hit_count | hit_odds_mean | hit_odds_median | payout_per_hit_mean | profit_per_hit_mean")
    print("-" * 110)
    for b in block_metrics["switch_dd4000"]:
        print(f"  {b['block_id']:7} | {b['block_profit']:11} | {b['block_roi'] or 0:8}% | {b['block_hit_count']:9} | {b['block_hit_odds_mean'] or 0:14} | {b['block_hit_odds_median'] or 0:16} | {b['block_payout_per_hit_mean'] or 0:19} | {b['block_profit_per_hit_mean'] or 0:18}")

    print("\n--- Monthly (switch_dd4000) ---")
    print("month    | hit_count | mean_hit_odds | payout_per_hit_mean | total_profit | roi")
    print("-" * 75)
    for m in monthly_metrics:
        print(f"  {m['month']} | {m['hit_count']:9} | {m['mean_hit_odds'] or 0:13} | {m['payout_per_hit_mean'] or 0:20} | {m['total_profit']:12} | {m['roi'] or 0:5}%")

    print("\n--- Win vs Lose blocks (switch_dd4000) ---")
    print("  winning:", win_lose_compare["winning_blocks"])
    print("  losing:", win_lose_compare["losing_blocks"])

    return 0


if __name__ == "__main__":
    sys.exit(main())
