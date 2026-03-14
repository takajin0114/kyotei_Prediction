"""
EXP-0048: 通常版/保守版のモード切替ルール検証。

EXP-0047 で採用した通常版（d_hi475 + stake=100）と保守版（d_hi475 + stake=80）について、
window 単位の単純な切替ルールを検証する。選抜は d_hi475 固定。

比較対象:
- normal_only: 常に stake=100
- conservative_only: 常に stake=80
- switch_after_2_loss: 直近2 window 連続赤字なら次 window は stake=80（参照は normal_only の window 利益）
- switch_after_3_loss: 直近3 window 連続赤字なら次 window は stake=80
- switch_dd5000: 累積DD（normal 基準）が 5000 以上ならその window は stake=80
- recover_after_1win: 2連続赤字で保守化、1 window 黒字で通常に復帰

評価: verified ロジック、n_windows=24。必須指標を出力。
"""

import argparse
import json
import os
import statistics
import sys
from pathlib import Path
from typing import Dict, List, Tuple

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
DD_THRESHOLD = 5000

# (名前, ルール種別). ルール種別: "normal_only" | "conservative_only" | "switch_2loss" | "switch_3loss" | "switch_dd" | "recover_1win"
MODE_VARIANTS: List[Tuple[str, str]] = [
    ("normal_only", "normal_only"),
    ("conservative_only", "conservative_only"),
    ("switch_after_2_loss", "switch_2loss"),
    ("switch_after_3_loss", "switch_3loss"),
    ("switch_dd5000", "switch_dd"),
    ("recover_after_1win", "recover_1win"),
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


def _stake_schedule(
    rule: str,
    n_w: int,
    ref_profit: List[float],
) -> List[int]:
    """各 window の stake (100 or 80) を返す。ref_profit は normal_only の window 別利益。"""
    schedule = [100] * n_w
    if rule == "normal_only":
        return schedule
    if rule == "conservative_only":
        return [80] * n_w

    if rule == "switch_2loss":
        for wi in range(2, n_w):
            if ref_profit[wi - 1] < 0 and ref_profit[wi - 2] < 0:
                schedule[wi] = 80
        return schedule

    if rule == "switch_3loss":
        for wi in range(3, n_w):
            if ref_profit[wi - 1] < 0 and ref_profit[wi - 2] < 0 and ref_profit[wi - 3] < 0:
                schedule[wi] = 80
        return schedule

    if rule == "switch_dd":
        cum = 0.0
        peak = 0.0
        for wi in range(n_w):
            cum += ref_profit[wi]
            if cum > peak:
                peak = cum
            dd = peak - cum
            if dd >= DD_THRESHOLD:
                schedule[wi] = 80
        return schedule

    if rule == "recover_1win":
        state = 100  # 100=normal, 80=conservative
        for wi in range(n_w):
            schedule[wi] = state
            if wi >= 2:
                if state == 100 and ref_profit[wi - 1] < 0 and ref_profit[wi - 2] < 0:
                    state = 80
                elif state == 80 and ref_profit[wi - 1] > 0:
                    state = 100
        return schedule

    return schedule


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
    print(f"[EXP-0048] DB found: {db_path_str}")

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
        print(f"[WARN] Requested n_windows={args.n_windows}, got {len(window_list)}.", file=sys.stderr)

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
        print(f"EXP-0048: Using existing predictions in {out_pred_dir} ({len(existing)} files).")
    else:
        print(f"EXP-0048: Running rolling validation (n_windows={args.n_windows})...")
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

    n_w = len(window_list)
    half = n_w // 2

    # 日別: (wi, stake_100, payout_100, stake_80, payout_80, bet_count, hit_count, sum_odds, sum_ev, sum_prob)
    day_data: Dict[str, Tuple[int, float, float, float, float, int, int, float, float, float]] = {}
    for day, day_races in races_per_date.items():
        wi = day_to_wi.get(day, 0)
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

    # 参照: normal_only の window 別利益
    ref_profit: List[float] = [0.0] * n_w
    for day, (wi, s100, p100, _s80, _p80, _bc, _hc, _so, _se, _sp) in day_data.items():
        ref_profit[wi] += p100 - s100

    # 各 variant の stake_schedule と集計
    results: Dict[str, Dict] = {}
    for name, rule in MODE_VARIANTS:
        schedule = _stake_schedule(rule, n_w, ref_profit)
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
        for day, (wi, s100, p100, s80, p80, bet_count, hit_count, sum_odds, sum_ev, sum_prob) in day_data.items():
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
            results[name]["sum_odds"] += sum_odds
            results[name]["sum_ev"] += sum_ev
            results[name]["sum_prob"] += sum_prob

    results_list: List[Dict] = []
    for name, _rule in MODE_VARIANTS:
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
            "average_stake_per_race": round(ts / rc, 2) if rc else 0.0,
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

    out_path = output_dir / "exp0048_mode_switch_rules_verified_results.json"
    payload = {
        "experiment_id": "EXP-0048",
        "n_windows": n_w,
        "db_path_used": db_path_str,
        "selection": "d_hi475: skip_top20pct, 4.30<=EV<4.75, prob>=0.05",
        "evaluation_logic": "stake 100 or 80 per window by rule; payout=stake*odds if hit",
        "mode_variants": [{"name": n, "rule": r} for n, r in MODE_VARIANTS],
        "ref_for_switch": "normal_only window profits",
        "results": results_list,
    }
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    print(f"Saved {out_path}")

    print("\n--- EXP-0048 mode switch rules (n_windows={}) ---".format(n_w))
    print(
        "variant             | ROI     | total_profit | max_dd   | profit/1k  | bet_count | total_stake | prof_w | lose_w | longest_lose | worst_w"
    )
    print("-" * 140)
    for name, _ in MODE_VARIANTS:
        r = results[name]
        print(
            f"  {name:18} | {r['ROI']:6}% | {r['total_profit']:12} | {r['max_drawdown']:8} | {r['profit_per_1000_bets']:10} | {r['bet_count']:9} | {r['total_stake']:11} | {r['profitable_windows']:6} | {r['losing_windows']:6} | {r['longest_losing_streak']:12} | {r.get('worst_window_profit') or 0:7}"
        )

    return 0


if __name__ == "__main__":
    sys.exit(main())
