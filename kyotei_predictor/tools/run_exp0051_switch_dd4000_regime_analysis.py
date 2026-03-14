"""
EXP-0051: switch_dd4000 の期間安定性・regime 差分析。

EXP-0050 で実運用標準候補となった switch_dd4000 について、
n_windows=36 を主対象に「どの期間で強く・どの期間で弱いか」を把握し、
ブロック別 profit/ROI/DD・switch 発動回数・発動 window を集計する。
実運用での注意点を明文化する。

選抜: d_hi475 固定（skip_top20pct + 4.30≤EV<4.75 + prob≥0.05）。
比較: normal_only, switch_dd4000, 参考で conservative_only。
"""

import argparse
import json
import os
import statistics
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

EV_LO, EV_HI, PROB_MIN = 4.30, 4.75, 0.05
TRAIN_DAYS = 30
TEST_DAYS = 7
STEP_DAYS = 7
N_WINDOWS = 36
BLOCK_SIZE = 6  # 36 / 6 = 6 blocks

REGIME_VARIANTS: List[Tuple[str, str, Optional[int]]] = [
    ("normal_only", "normal_only", None),
    ("switch_dd4000", "switch_dd", 4000),
    ("conservative_only", "conservative_only", None),
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
    """各 window の stake (100 or 80)。"""
    schedule = [100] * n_w
    if rule == "normal_only":
        return schedule
    if rule == "conservative_only":
        return [80] * n_w
    if rule == "switch_dd" and dd_threshold is not None:
        cum = 0.0
        peak = 0.0
        for wi in range(n_w):
            cum += ref_profit[wi]
            if cum > peak:
                peak = cum
            dd = peak - cum
            if dd >= dd_threshold:
                schedule[wi] = 80
    return schedule


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
    print(f"[EXP-0051] DB found: {db_path_str}")

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
        print(f"[WARN] Requested n_windows={n_w}, got {len(window_list)}.", file=sys.stderr)
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
    if need_days and need_days.issubset(existing):
        print(f"EXP-0051: Using existing predictions in {out_pred_dir} ({len(existing)} files).")
    else:
        print(f"EXP-0051: Running rolling validation (n_windows={n_w})...")
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

    repo = get_race_data_repository(
        "db",
        data_dir=raw_dir,
        db_path=db_path_str,
    )

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
            day_races: List[Tuple[float, List[Tuple[float, float, float, bool]]]] = []
            for race in predictions_list:
                max_ev = _max_ev_for_race(race)
                bets = _all_bets_for_race(race, prediction_date, repo)
                if not bets:
                    continue
                day_races.append((max_ev, bets))
            if day_races:
                races_per_date[day] = day_races

    half = n_w // 2
    day_data: Dict[str, Tuple[int, float, float, float, float, int, int, float, float, float]] = {}
    window_set = {wi for wi in range(n_w)}
    for day, day_races in races_per_date.items():
        wi = day_to_wi.get(day, -1)
        if wi not in window_set:
            continue
        day_races_sorted = sorted(day_races, key=lambda x: -x[0])
        n = len(day_races_sorted)
        k_skip = int(n * SKIP_TOP_PCT)
        idx_start = min(k_skip, n)
        s100, p100, s80, p80 = 0.0, 0.0, 0.0, 0.0
        bet_count = 0
        hit_count = 0
        sum_odds, sum_ev, sum_prob = 0.0, 0.0, 0.0
        for max_ev, bets in day_races_sorted[idx_start:]:
            filtered = _filter_bets_by_selection(bets, EV_LO, EV_HI, PROB_MIN)
            if not filtered:
                continue
            cnt = len(filtered)
            bet_count += cnt
            s100 += FIXED_STAKE * cnt
            s80 += 80 * cnt
            for ev, prob, odds, hit in filtered:
                if hit:
                    p100 += FIXED_STAKE * odds
                    p80 += 80 * odds
                hit_count += 1 if hit else 0
                sum_odds += odds
                sum_ev += ev
                sum_prob += prob
        if bet_count > 0:
            day_data[day] = (wi, s100, p100, s80, p80, bet_count, hit_count, sum_odds, sum_ev, sum_prob)

    ref_profit: List[float] = [0.0] * n_w
    for day, (wi, s100, p100, _s80, _p80, _bc, _hc, _so, _se, _sp) in day_data.items():
        if 0 <= wi < n_w:
            ref_profit[wi] += p100 - s100

    # Per-variant: per-window stake, payout, bet_count, hit_count, profit
    results: Dict[str, Dict] = {}
    for name, rule, dd_thr in REGIME_VARIANTS:
        schedule = _stake_schedule_dd(rule, dd_thr, n_w, ref_profit)
        results[name] = {
            "total_stake": 0.0,
            "total_payout": 0.0,
            "bet_count": 0,
            "hit_count": 0,
            "race_count": 0,
            "window_profits": [0.0] * n_w,
            "window_stake": [0.0] * n_w,
            "window_payout": [0.0] * n_w,
            "window_bet_count": [0] * n_w,
            "window_hit_count": [0] * n_w,
            "schedule": schedule,
            "sum_odds": 0.0,
            "sum_ev": 0.0,
            "sum_prob": 0.0,
        }
        for day, (wi, s100, p100, s80, p80, bet_count, hit_count, sum_odds, sum_ev, sum_prob) in day_data.items():
            if wi < 0 or wi >= n_w:
                continue
            st = schedule[wi]
            if st == 100:
                stake, payout = s100, p100
            else:
                stake, payout = s80, p80
            results[name]["total_stake"] += stake
            results[name]["total_payout"] += payout
            results[name]["bet_count"] += bet_count
            results[name]["hit_count"] += hit_count
            results[name]["race_count"] += 1
            results[name]["window_profits"][wi] += payout - stake
            results[name]["window_stake"][wi] += stake
            results[name]["window_payout"][wi] += payout
            results[name]["window_bet_count"][wi] += bet_count
            results[name]["window_hit_count"][wi] += hit_count
            results[name]["sum_odds"] += sum_odds
            results[name]["sum_ev"] += sum_ev
            results[name]["sum_prob"] += sum_prob

    # Switch trigger for switch_dd4000
    switch_schedule = results["switch_dd4000"]["schedule"]
    switch_triggered_windows = [wi for wi in range(n_w) if switch_schedule[wi] == 80]
    switch_trigger_count = len(switch_triggered_windows)

    # Block-level metrics (block = consecutive block_size windows)
    block_info: List[Dict] = []
    for bi in range(n_blocks):
        start_wi = bi * block_size
        end_wi = min((bi + 1) * block_size, n_w)
        test_start = window_list[start_wi][2] if start_wi < len(window_list) else ""
        test_end = window_list[end_wi - 1][3] if end_wi <= len(window_list) else ""
        block_info.append({
            "block_index": bi,
            "window_range": f"w{start_wi}-w{end_wi - 1}",
            "test_start": test_start,
            "test_end": test_end,
        })

    # Overall metrics and block metrics per variant
    summary_list: List[Dict] = []
    block_metrics: Dict[str, List[Dict]] = {name: [] for name, _, _ in REGIME_VARIANTS}

    for name, _rule, _thr in REGIME_VARIANTS:
        r = results[name]
        wp = r["window_profits"]
        ts = r["total_stake"]
        tp = r["total_payout"]
        cnt = r["bet_count"]
        rc = r["race_count"]
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
            "variant": name,
            "ROI": roi,
            "total_profit": total_profit,
            "max_drawdown": round(dd, 2),
            "profit_per_1000_bets": profit_per_1000,
            "bet_count": cnt,
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

        # Block-level
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
            b_cum = 0.0
            b_peak = 0.0
            b_dd = 0.0
            for p in b_profits:
                b_cum += p
                if b_cum > b_peak:
                    b_peak = b_cum
                if b_peak - b_cum > b_dd:
                    b_dd = b_peak - b_cum
            block_metrics[name].append({
                "block_index": bi,
                "window_range": f"w{start_wi}-w{end_wi - 1}",
                "test_start": block_info[bi]["test_start"],
                "test_end": block_info[bi]["test_end"],
                "block_profit": round(b_profit, 2),
                "block_roi": b_roi,
                "block_drawdown": round(b_dd, 2),
                "block_bet_count": b_bet,
                "block_hit_count": b_hit,
                "block_stake": round(b_stake, 2),
            })

    # Output
    payload = {
        "experiment_id": "EXP-0051",
        "purpose": "switch_dd4000 period stability and regime analysis (n_windows=36)",
        "db_path_used": db_path_str,
        "selection": "d_hi475: skip_top20pct, 4.30<=EV<4.75, prob>=0.05",
        "n_windows": n_w,
        "block_size": block_size,
        "n_blocks": n_blocks,
        "variants": [{"name": n, "rule": r, "dd_threshold": t} for n, r, t in REGIME_VARIANTS],
        "summary": summary_list,
        "block_metrics": block_metrics,
        "window_list_date_ranges": [
            {"window_index": wi, "test_start": window_list[wi][2], "test_end": window_list[wi][3]}
            for wi in range(min(n_w, len(window_list)))
        ],
        "switch_dd4000_trigger": {
            "trigger_count": switch_trigger_count,
            "triggered_windows": switch_triggered_windows,
            "triggered_ratio": round(switch_trigger_count / n_w * 100, 1) if n_w else 0,
        },
    }
    out_path = output_dir / "exp0051_switch_dd4000_regime_analysis_results.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    print(f"Saved {out_path}")

    # Console output
    print("\n--- EXP-0051 Overall (n_windows={}) ---".format(n_w))
    print(
        "variant             | ROI     | total_profit | max_dd   | profit/1k   | bet_count | prof_w | lose_w | longest_lose | worst_w  | early_half | late_half"
    )
    print("-" * 150)
    for name, _, _ in REGIME_VARIANTS:
        r = results[name]
        print(
            f"  {name:18} | {r['ROI']:6}% | {r['total_profit']:12} | {r['max_drawdown']:8} | {r['profit_per_1000_bets']:10} | {r['bet_count']:9} | {r['profitable_windows']:6} | {r['losing_windows']:6} | {r['longest_losing_streak']:12} | {r.get('worst_window_profit') or 0:8} | {r['early_half_profit']:10} | {r['late_half_profit']:10}"
        )

    print("\n--- switch_dd4000 trigger ---")
    print(f"  trigger_count: {switch_trigger_count} / {n_w} windows ({payload['switch_dd4000_trigger']['triggered_ratio']}%)")
    print(f"  triggered_windows: {switch_triggered_windows}")

    print("\n--- Block-level (block_size={}) ---".format(block_size))
    for name, _, _ in REGIME_VARIANTS:
        print(f"\n  [{name}]")
        print("  block | w_range   | test_start   | test_end     | profit    | roi     | dd      | bet_count | hit_count")
        print("  " + "-" * 95)
        for b in block_metrics[name]:
            print(
                f"  {b['block_index']:5} | {b['window_range']:10} | {b['test_start']:12} | {b['test_end']:12} | {b['block_profit']:9} | {b['block_roi'] or 0:6}% | {b['block_drawdown']:7} | {b['block_bet_count']:9} | {b['block_hit_count']:9}"
            )

    return 0


if __name__ == "__main__":
    sys.exit(main())
