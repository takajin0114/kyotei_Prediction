"""
EXP-0047: d_hi475 運用制御の追加効果検証。

EXP-0046 で主軸化した d_hi475（skip_top20pct + 4.30≤EV<4.75 + prob≥0.05）に対し、
レースごとの点数制限・軽い防御ルールの効果を検証する。
- base: 現行 d_hi475（制御なし）
- cap1: 1レースあたり最大1点（EV 上位）
- cap2: 1レースあたり最大2点（EV 上位）
- top1_prob: 条件を満たす買い目のうち prob 上位1点のみ
- top1_ev: 条件を満たす買い目のうち EV 上位1点のみ（cap1 と同一ロジック）
- dd_guard_light: 前 window が赤字なら次 window は賭けなし

評価ロジック: stake=100（sizing_80 は 80）、payout=stake*odds if hit, profit=payout-stake。
n_windows=24 を基本。必須指標＋average_bets_per_race, race_count を出力。
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

# d_hi475 条件
EV_LO, EV_HI, PROB_MIN = 4.30, 4.75, 0.05

TRAIN_DAYS = 30
TEST_DAYS = 7
STEP_DAYS = 7

# 実行制御の種類: (名前, レースあたり最大点数, 選び方, dd_guard を使うか, stake)
# 選び方: "all" | "top1_ev" | "top1_prob" | "top2_ev"
CONTROL_VARIANTS: List[Tuple[str, Optional[int], str, bool, int]] = [
    ("base", None, "all", False, 100),
    ("cap1", 1, "top1_ev", False, 100),
    ("cap2", 2, "top2_ev", False, 100),
    ("top1_prob", 1, "top1_prob", False, 100),
    ("top1_ev", 1, "top1_ev", False, 100),
    ("dd_guard_light", None, "all", True, 100),
    ("sizing_80", None, "all", False, 80),
]


def _apply_cap(
    filtered: List[Tuple[float, float, float, bool]],
    max_per_race: Optional[int],
    order_by: str,
) -> List[Tuple[float, float, float, bool]]:
    """filtered を order_by でソートし、最大 max_per_race 件を返す。"""
    if not filtered:
        return []
    if order_by == "top1_ev" or order_by == "top2_ev":
        key = 0  # EV
        desc = True
    elif order_by == "top1_prob":
        key = 1  # prob
        desc = True
    else:
        key = 0
        desc = True
    sorted_bets = sorted(filtered, key=lambda x: x[key], reverse=desc)
    if max_per_race is None:
        return sorted_bets
    return sorted_bets[:max_per_race]


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
    parser.add_argument("--db-path", type=str, default=None)
    parser.add_argument("--output-dir", type=Path, default=None)
    parser.add_argument("--predictions-dir", type=Path, default=None)
    parser.add_argument("--n-windows", type=int, default=24)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    db_path_resolved = _resolve_db_path(args.db_path)
    if not db_path_resolved.exists():
        print(f"[ERROR] DB not found: {db_path_resolved}", file=sys.stderr)
        return 1
    db_path_str = str(db_path_resolved)
    print(f"[EXP-0047] DB found: {db_path_str}")

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
        print(
            f"[WARN] Requested n_windows={args.n_windows}, got {len(window_list)}.",
            file=sys.stderr,
        )

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
        print(f"EXP-0047: Using existing predictions in {out_pred_dir} ({len(existing)} files).")
    else:
        print(f"EXP-0047: Running rolling validation (n_windows={args.n_windows})...")
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

    # day -> [(max_ev, bets), ...] (skip_top20pct 適用前の日別レースリストは後でソートして skip)
    races_per_date: Dict[str, List[Tuple[float, List[Tuple[float, float, float, bool]]]]] = {}
    day_to_wi: Dict[str, int] = {}
    for wi, (ts, te, tst, tend) in enumerate(window_list):
        for day in _date_range(tst, tend):
            day_to_wi[day] = wi

    for wi, (_ts, _te, tst, tend) in enumerate(window_list):
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

    n_w = len(window_list)
    half = n_w // 2

    # まず base の window_profits を計算（dd_guard_light で参照）
    base_window_profits: List[float] = [0.0] * n_w
    for day, day_races in races_per_date.items():
        wi = day_to_wi.get(day, 0)
        day_races_sorted = sorted(day_races, key=lambda x: -x[0])
        n = len(day_races_sorted)
        k_skip = int(n * SKIP_TOP_PCT)
        idx_start = min(k_skip, n)
        for max_ev, bets in day_races_sorted[idx_start:]:
            filtered = _filter_bets_by_selection(bets, EV_LO, EV_HI, PROB_MIN)
            if not filtered:
                continue
            stake = FIXED_STAKE * len(filtered)
            payout = sum(FIXED_STAKE * odds if hit else 0.0 for ev, prob, odds, hit in filtered)
            base_window_profits[wi] += payout - stake

    # 各 variant の結果を集計
    results: Dict[str, Dict] = {}
    for name, max_per_race, order_by, use_dd_guard, stake in CONTROL_VARIANTS:
        results[name] = {
            "total_stake": 0.0,
            "total_payout": 0.0,
            "bet_count": 0,
            "hit_count": 0,
            "race_count": 0,
            "window_profits": [0.0] * n_w,
            "sum_odds": 0.0,
            "sum_ev": 0.0,
            "sum_prob": 0.0,
        }

    for day, day_races in races_per_date.items():
        wi = day_to_wi.get(day, 0)
        day_races_sorted = sorted(day_races, key=lambda x: -x[0])
        n = len(day_races_sorted)
        k_skip = int(n * SKIP_TOP_PCT)
        idx_start = min(k_skip, n)
        races_after_skip = day_races_sorted[idx_start:]

        for max_ev, bets in races_after_skip:
            filtered = _filter_bets_by_selection(bets, EV_LO, EV_HI, PROB_MIN)
            if not filtered:
                continue

            for name, max_per_race, order_by, use_dd_guard, stake in CONTROL_VARIANTS:
                if use_dd_guard and wi > 0 and base_window_profits[wi - 1] < 0:
                    continue
                chosen = _apply_cap(filtered, max_per_race, order_by)
                if not chosen:
                    continue
                race_stake = stake * len(chosen)
                race_payout = sum(stake * odds if hit else 0.0 for ev, prob, odds, hit in chosen)
                results[name]["total_stake"] += race_stake
                results[name]["total_payout"] += race_payout
                results[name]["bet_count"] += len(chosen)
                results[name]["hit_count"] += sum(1 for _, _, _, h in chosen if h)
                results[name]["race_count"] += 1
                results[name]["window_profits"][wi] += race_payout - race_stake
                for ev, prob, odds, _ in chosen:
                    results[name]["sum_odds"] += odds
                    results[name]["sum_ev"] += ev
                    results[name]["sum_prob"] += prob

    results_list: List[Dict] = []
    for name, _mp, _ob, _ud, stake in CONTROL_VARIANTS:
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
        avg_bets_per_race = round(cnt / rc, 2) if rc else None
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
            "average_bet_size": round(ts / cnt, 2) if cnt else 0.0,
            "average_stake_per_race": avg_stake_per_race,
            "average_odds": avg_odds,
            "average_ev": avg_ev,
            "average_prob": avg_prob,
            "average_bets_per_race": avg_bets_per_race,
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

    out_path = output_dir / "exp0047_d_hi475_execution_controls_verified_results.json"
    payload = {
        "experiment_id": "EXP-0047",
        "n_windows": n_w,
        "db_path_used": db_path_str,
        "selection": "d_hi475: skip_top20pct, 4.30<=EV<4.75, prob>=0.05",
        "evaluation_logic": "stake per variant (100 or 80), payout=stake*odds if hit, profit=payout-stake",
        "control_variants": [
            {
                "name": name,
                "max_per_race": mp,
                "order_by": ob,
                "dd_guard_light": ud,
                "stake": st,
            }
            for name, mp, ob, ud, st in CONTROL_VARIANTS
        ],
        "results": results_list,
    }
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    print(f"Saved {out_path}")

    print("\n--- EXP-0047 d_hi475 execution controls (n_windows={}) ---".format(n_w))
    print(
        "variant      | ROI     | total_profit | max_dd   | profit/1k  | bet_count | race_count | avg_b/r | prof_w | lose_w | longest_lose | worst_w"
    )
    print("-" * 130)
    for name, _, _, _, _ in CONTROL_VARIANTS:
        r = results[name]
        abr = r.get("average_bets_per_race") or 0
        print(
            f"  {name:12} | {r['ROI']:6}% | {r['total_profit']:12} | {r['max_drawdown']:8} | {r['profit_per_1000_bets']:10} | {r['bet_count']:9} | {r['race_count']:9} | {abr:6} | {r['profitable_windows']:6} | {r['losing_windows']:6} | {r['longest_losing_streak']:12} | {r.get('worst_window_profit') or 0:7}"
        )

    return 0


if __name__ == "__main__":
    sys.exit(main())
