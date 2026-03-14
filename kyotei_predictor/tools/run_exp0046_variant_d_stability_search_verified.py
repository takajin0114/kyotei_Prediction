"""
EXP-0046: variant_d 近傍安定化探索。

EXP-0045 で主軸化した variant_d（skip_top20pct + 4.30≤EV<4.80 + prob≥0.05）を基準に、
ROI 維持または改善しつつ max_drawdown / longest_losing_streak / worst_window_profit を
悪化させない方向で実運用向け安定版を探す。

評価ロジックは EXP-0045 と同一（stake=100, payout=stake*odds if hit, profit=payout-stake）。
n_windows=24 を基本とし、全必須指標を出力する。
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

TRAIN_DAYS = 30
TEST_DAYS = 7
STEP_DAYS = 7

# variant_d 近傍: reference_2 + d_base と prob 強化・EV 軽微変更版
SELECTION_VARIANTS: List[Tuple[str, float, float, Optional[float]]] = [
    ("reference_2", 4.3, 4.9, 0.05),    # 4.3≤EV<4.9, prob≥0.05
    ("d_base", 4.30, 4.80, 0.05),       # 4.30≤EV<4.80, prob≥0.05 (EXP-0045 主軸)
    ("d_p055", 4.30, 4.80, 0.055),      # prob 強化
    ("d_p060", 4.30, 4.80, 0.06),       # prob 強化
    ("d_hi475", 4.30, 4.75, 0.05),      # EV 上限を少し絞る
    ("d_lo435", 4.35, 4.80, 0.05),      # EV 下限を少し上げる
    ("d_mid", 4.35, 4.75, 0.05),        # 帯を中央に
    ("d_mid_p055", 4.35, 4.75, 0.055), # 帯中央 + prob 強化
]


def _longest_losing_streak(window_profits: List[float]) -> int:
    """連続で赤字の window の最大個数。"""
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


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--db-path",
        type=str,
        default=None,
        help="SQLite DB path. Default: kyotei_predictor/data/kyotei_races.sqlite (repo root relative)",
    )
    parser.add_argument("--output-dir", type=Path, default=None)
    parser.add_argument("--predictions-dir", type=Path, default=None)
    parser.add_argument("--n-windows", type=int, default=24)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    db_path_resolved = _resolve_db_path(args.db_path)
    if not db_path_resolved.exists():
        print(f"[ERROR] DB not found: {db_path_resolved}", file=sys.stderr)
        print("  Resolved from: --db-path={}".format(args.db_path or "(default)"), file=sys.stderr)
        print("  REPO_ROOT: {}".format(_REPO_ROOT), file=sys.stderr)
        return 1
    db_path_str = str(db_path_resolved)
    print(f"[EXP-0046] DB found: {db_path_str}")

    raw_dir = _REPO_ROOT / "kyotei_predictor" / "data" / "raw"
    if not raw_dir.is_dir():
        raw_dir = Path("kyotei_predictor/data/raw")

    output_dir = args.output_dir or _REPO_ROOT / "outputs" / "selection_verified"
    output_dir.mkdir(parents=True, exist_ok=True)

    pred_parent = args.predictions_dir or _REPO_ROOT / "outputs" / "ev_cap_experiments"
    out_pred_dir = pred_parent / "rolling_roi_predictions"

    min_date, max_date = get_db_date_range(db_path_str)
    window_list = build_windows(
        min_date, max_date, TRAIN_DAYS, TEST_DAYS, STEP_DAYS, args.n_windows
    )
    if len(window_list) < args.n_windows:
        print(f"[WARN] Requested n_windows={args.n_windows}, got {len(window_list)} (data range limit).", file=sys.stderr)

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
        print(f"EXP-0046: Using existing predictions in {out_pred_dir} ({len(existing)} files).")
    else:
        print(f"EXP-0046: Running rolling validation (n_windows={args.n_windows})...")
        run_rolling_validation_roi(
            db_path=db_path_str,
            output_dir=pred_parent,
            data_dir_raw=raw_dir,
            train_days=TRAIN_DAYS,
            test_days=TEST_DAYS,
            step_days=STEP_DAYS,
            n_windows=args.n_windows,
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
    for wi, (ts, te, tst, tend) in enumerate(window_list):
        test_dates = _date_range(tst, tend)
        for day in test_dates:
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

    results: Dict[str, Dict] = {}
    for name, ev_lo, ev_hi, prob_min in SELECTION_VARIANTS:
        results[name] = {
            "total_stake": 0.0,
            "total_payout": 0.0,
            "bet_count": 0,
            "hit_count": 0,
            "race_count": 0,
            "window_profits": [0.0] * len(window_list),
            "sum_odds": 0.0,
            "sum_ev": 0.0,
            "sum_prob": 0.0,
        }

    for day, day_races in races_per_date.items():
        day_races_sorted = sorted(day_races, key=lambda x: -x[0])
        n = len(day_races_sorted)
        k_skip = int(n * SKIP_TOP_PCT)
        idx_start = min(k_skip, n)
        races_after_skip = day_races_sorted[idx_start:]

        wi = next((i for i, (_, _, tst, tend) in enumerate(window_list) if tst <= day <= tend), 0)
        for max_ev, bets in races_after_skip:
            for name, ev_lo, ev_hi, prob_min in SELECTION_VARIANTS:
                filtered = _filter_bets_by_selection(bets, ev_lo, ev_hi, prob_min)
                if not filtered:
                    continue
                race_stake = FIXED_STAKE * len(filtered)
                race_payout = 0.0
                for ev, prob, odds, hit in filtered:
                    race_payout += FIXED_STAKE * odds if hit else 0.0
                results[name]["total_stake"] += race_stake
                results[name]["total_payout"] += race_payout
                results[name]["bet_count"] += len(filtered)
                results[name]["hit_count"] += sum(1 for _, _, _, h in filtered if h)
                results[name]["race_count"] += 1
                results[name]["window_profits"][wi] += race_payout - race_stake
                for ev, prob, odds, _ in filtered:
                    results[name]["sum_odds"] += odds
                    results[name]["sum_ev"] += ev
                    results[name]["sum_prob"] += prob

    n_w = len(window_list)
    half = n_w // 2
    results_list: List[Dict] = []
    for name, ev_lo, ev_hi, prob_min in SELECTION_VARIANTS:
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
        avg_bet = round(ts / cnt, 2) if cnt else 0.0
        avg_stake_per_race = round(ts / rc, 2) if rc else 0.0
        hit_rate = round(100.0 * hit_count / cnt, 2) if cnt else 0.0
        avg_odds = round(r["sum_odds"] / cnt, 2) if cnt else None
        avg_ev = round(r["sum_ev"] / cnt, 4) if cnt else None
        avg_prob = round(r["sum_prob"] / cnt, 4) if cnt else None
        out = {
            "variant": name,
            "ROI": roi,
            "total_profit": total_profit,
            "max_drawdown": round(dd, 2),
            "profit_per_1000_bets": profit_per_1000,
            "bet_count": cnt,
            "race_count": rc,
            "hit_count": hit_count,
            "hit_rate": hit_rate,
            "total_stake": round(ts, 2),
            "average_bet_size": avg_bet,
            "average_stake_per_race": avg_stake_per_race,
            "average_odds": avg_odds,
            "average_ev": avg_ev,
            "average_prob": avg_prob,
            "profitable_windows": profitable_windows,
            "losing_windows": losing_windows,
            "longest_losing_streak": longest_losing_streak,
            "worst_window_profit": worst_window_profit,
            "median_window_profit": median_window_profit,
            "window_profit_std": window_profit_std,
            "early_half_profit": early_half_profit,
            "late_half_profit": late_half_profit,
        }
        r.update(out)
        results_list.append(out)

    out_path = output_dir / "exp0046_variant_d_stability_search_verified_results.json"
    payload = {
        "experiment_id": "EXP-0046",
        "n_windows": n_w,
        "db_path_used": db_path_str,
        "stake_fixed": FIXED_STAKE,
        "evaluation_logic": "Same as EXP-0045: stake=100, payout=stake*odds if hit, profit=payout-stake",
        "selection_variants": [
            {"name": n, "ev_lo": e0, "ev_hi": e1, "prob_min": p}
            for n, e0, e1, p in SELECTION_VARIANTS
        ],
        "results": results_list,
    }
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    print(f"Saved {out_path}")

    print("\n--- EXP-0046 variant_d stability search (stake=100, n_windows={}) ---".format(n_w))
    print("variant      | ROI     | total_profit | max_dd   | profit/1k  | bet_count | prof_w | lose_w | longest_lose | worst_w | median_w | early_half | late_half")
    print("-" * 150)
    for name, _, _, _ in SELECTION_VARIANTS:
        r = results[name]
        print(
            f"  {name:12} | {r['ROI']:6}% | {r['total_profit']:12} | {r['max_drawdown']:8} | {r['profit_per_1000_bets']:10} | {r['bet_count']:9} | {r['profitable_windows']:6} | {r['losing_windows']:6} | {r['longest_losing_streak']:12} | {r.get('worst_window_profit') or 0:7} | {r.get('median_window_profit') or 0:7} | {r['early_half_profit']:11} | {r['late_half_profit']:10}"
        )

    return 0


if __name__ == "__main__":
    sys.exit(main())
