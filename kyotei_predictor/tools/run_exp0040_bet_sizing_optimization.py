"""
EXP-0040: ベットサイジング最適化。

採用条件（skip_top20pct + 3≤EV<5 + prob≥0.05）を固定し、
「いくら買うか」だけを変えて ROI・total_profit・max_drawdown・profit_per_1000_bets を比較する。

既存 rolling predictions と verify 結果（race 単位の payout）を利用。
選ばれる bet 集合は全 variant で同一。各 variant で bet ごとの stake を算出し、
race 単位で stake 合計と payout を集計して指標を算出する。

bet sizing 定義:
- baseline の unit: 100（全 bet 同額）。
- 比例係数: 下記各 variant の式で EV/prob のスケールに合わせて設定。
- 最小 unit: 50、最大 unit: 200（capped 系は max 150）。
- 丸め: round() で整数。レース単位の総額制約は設けず、bet ごとに clip のみ。
- 既存 verify_usecase は 1 回だけ実行し payout を取得。stake は本ツールで後段計算。
"""

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Callable, Dict, List, Tuple

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
from kyotei_predictor.tools.rolling_validation_windows import _date_range, _month_dir
from kyotei_predictor.application.verify_usecase import run_verify

TRAIN_DAYS = 30
TEST_DAYS = 7
STEP_DAYS = 7
TOP_N = 3

STRATEGIES: List[Tuple] = [
    ("exp0015", "top_n_ev_gap_filter", TOP_N, 1.20, None, None, None, 0.07),
]
STRATEGY_SUFFIX = "_top3ev120_evgap0x07"

CONFIDENCE_WEIGHTED_CONFIG = {"ev_gap_high": 0.11, "normal_unit": 0.5}

SKIP_TOP_PCT = 0.2
EV_LO, EV_HI = 3.0, 5.0
PROB_MIN = 0.05

# bet sizing 制約（全 variant 共通の最小・最大。capped 系は別で max を下げる）
MIN_UNIT = 50
MAX_UNIT = 200
MAX_UNIT_CAPPED = 150
BASELINE_UNIT = 100


def _ev_prob_list_for_race(race: dict) -> List[Tuple[float, float]]:
    """レースの selected_bets のうち 3≤EV<5 かつ prob≥0.05 を満たす (ev, prob) を EV 降順で返す。"""
    selected = race.get("selected_bets") or []
    all_comb = race.get("all_combinations") or []
    comb_to_ev: Dict[str, float] = {}
    comb_to_prob: Dict[str, float] = {}
    for c in all_comb:
        comb_raw = (c.get("combination") or "").strip()
        if not comb_raw:
            continue
        prob = float(c.get("probability", c.get("score", 0.0)))
        r = c.get("ratio") or c.get("odds")
        if r is None:
            continue
        try:
            ratio = float(r)
        except (TypeError, ValueError):
            continue
        if ratio <= 0:
            continue
        ev = prob * ratio
        comb_to_ev[comb_raw] = ev
        comb_to_prob[comb_raw] = prob
    out: List[Tuple[float, float]] = []
    for c in selected:
        comb_raw = (c if isinstance(c, str) else "").strip()
        ev = comb_to_ev.get(comb_raw, 0.0)
        prob = comb_to_prob.get(comb_raw, 0.0)
        if EV_LO <= ev < EV_HI and prob >= PROB_MIN:
            out.append((ev, prob))
    out.sort(key=lambda x: -x[0])
    return out


def _max_ev_for_race(race: dict) -> float:
    """レースの selected_bets の EV 最大値（skip_top20pct 用）。"""
    selected = race.get("selected_bets") or []
    all_comb = race.get("all_combinations") or []
    comb_to_ev: Dict[str, float] = {}
    for c in all_comb:
        comb_raw = (c.get("combination") or "").strip()
        if not comb_raw:
            continue
        prob = float(c.get("probability", c.get("score", 0.0)))
        r = c.get("ratio") or c.get("odds")
        if r is None:
            continue
        try:
            ratio = float(r)
        except (TypeError, ValueError):
            continue
        if ratio <= 0:
            continue
        comb_to_ev[comb_raw] = prob * ratio
    if not selected:
        return 0.0
    evs = [comb_to_ev.get((c if isinstance(c, str) else "").strip(), 0.0) for c in selected]
    return max(evs) if evs else 0.0


def _clip_round(x: float, lo: int, hi: int) -> int:
    return max(lo, min(hi, round(x)))


# Sizing: list of (ev, prob) -> list of int (stake per bet)
def _fixed(bets: List[Tuple[float, float]]) -> List[int]:
    return [BASELINE_UNIT] * len(bets)


def _by_ev_linear(bets: List[Tuple[float, float]]) -> List[int]:
    # unit = clip(round(25 * EV), 50, 200). EV in [3,5) -> about [75,125]
    return [_clip_round(25.0 * ev, MIN_UNIT, MAX_UNIT) for ev, _ in bets]


def _by_prob_linear(bets: List[Tuple[float, float]]) -> List[int]:
    # unit = clip(round(200 * prob), 50, 200)
    return [_clip_round(200.0 * prob, MIN_UNIT, MAX_UNIT) for _, prob in bets]


def _by_ev_prob(bets: List[Tuple[float, float]]) -> List[int]:
    # unit = clip(round(40 * EV * prob), 50, 200)
    return [_clip_round(40.0 * ev * prob, MIN_UNIT, MAX_UNIT) for ev, prob in bets]


def _by_ev_capped(bets: List[Tuple[float, float]]) -> List[int]:
    return [_clip_round(25.0 * ev, MIN_UNIT, MAX_UNIT_CAPPED) for ev, _ in bets]


def _by_ev_prob_capped(bets: List[Tuple[float, float]]) -> List[int]:
    return [_clip_round(40.0 * ev * prob, MIN_UNIT, MAX_UNIT_CAPPED) for ev, prob in bets]


VARIANTS: List[Tuple[str, Callable[[List[Tuple[float, float]]], List[int]]]] = [
    ("baseline_fixed", _fixed),
    ("size_by_ev_linear", _by_ev_linear),
    ("size_by_prob_linear", _by_prob_linear),
    ("size_by_ev_prob", _by_ev_prob),
    ("size_by_ev_capped", _by_ev_capped),
    ("size_by_ev_prob_capped", _by_ev_prob_capped),
]

# (max_ev, ev_prob_list, payout)
RaceRow = Tuple[float, List[Tuple[float, float]], float]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db-path", required=True, help="SQLite DB path")
    parser.add_argument("--output-dir", type=Path, default=None)
    parser.add_argument("--predictions-dir", type=Path, default=None)
    parser.add_argument("--n-windows", type=int, default=18)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    raw_dir = _REPO_ROOT / "kyotei_predictor" / "data" / "raw"
    if not raw_dir.is_dir():
        raw_dir = Path("kyotei_predictor/data/raw")

    output_dir = args.output_dir or _REPO_ROOT / "outputs" / "bet_sizing_optimization"
    output_dir.mkdir(parents=True, exist_ok=True)

    pred_parent = args.predictions_dir or _REPO_ROOT / "outputs" / "ev_cap_experiments"
    out_pred_dir = pred_parent / "rolling_roi_predictions"

    min_date, max_date = get_db_date_range(args.db_path)
    window_list = build_windows(
        min_date, max_date, TRAIN_DAYS, TEST_DAYS, STEP_DAYS, args.n_windows
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
        print(f"EXP-0040: Using existing predictions in {out_pred_dir} ({len(existing)} files).")
    else:
        print(f"EXP-0040: Running rolling validation (n_windows={args.n_windows})...")
        run_rolling_validation_roi(
            db_path=args.db_path,
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

    races_per_date: Dict[str, List[RaceRow]] = {}

    for wi, (ts, te, tst, tend) in enumerate(window_list):
        test_dates = _date_range(tst, tend)
        for day in test_dates:
            month = _month_dir(day)
            data_dir_month = raw_dir / month
            path = out_pred_dir / f"predictions_baseline_{day}{STRATEGY_SUFFIX}.json"
            if not path.exists() or not data_dir_month.exists():
                continue
            try:
                with open(path, encoding="utf-8") as f:
                    pred = json.load(f)
            except Exception:
                continue
            try:
                summary, details = run_verify(
                    path,
                    data_dir_month,
                    evaluation_mode="selected_bets",
                    data_source="db",
                    db_path=args.db_path,
                    bet_sizing_mode="confidence_weighted_ev_gap_v1",
                    bet_sizing_config=CONFIDENCE_WEIGHTED_CONFIG,
                )
            except Exception:
                continue
            predictions_list = pred.get("predictions") or []
            detail_by_key: Dict[Tuple[str, int], dict] = {}
            for d in details:
                v = d.get("venue") or ""
                rno = int(d.get("race_number") or 0)
                detail_by_key[(v, rno)] = d

            day_races: List[RaceRow] = []
            for race in predictions_list:
                venue = race.get("venue") or ""
                rno = int(race.get("race_number") or 0)
                selected = race.get("selected_bets") or []
                if not selected:
                    continue
                ev_prob_list = _ev_prob_list_for_race(race)
                if not ev_prob_list:
                    continue
                max_ev = _max_ev_for_race(race)
                d = detail_by_key.get((venue, rno))
                if not d:
                    continue
                payout = float(d.get("payout") or 0)
                day_races.append((max_ev, ev_prob_list, payout))

            if day_races:
                races_per_date[day] = day_races

    results: Dict[str, Dict] = {}
    for name, _ in VARIANTS:
        results[name] = {
            "total_stake": 0.0,
            "total_payout": 0.0,
            "bet_count": 0,
            "race_count": 0,
            "window_profits": [0.0] * len(window_list),
        }

    for day, day_races in races_per_date.items():
        day_races_sorted = sorted(day_races, key=lambda x: -x[0])
        n = len(day_races_sorted)
        k_skip = int(n * SKIP_TOP_PCT)
        idx_start = min(k_skip, n)
        races_after_skip = day_races_sorted[idx_start:]

        wi = next(i for i, (_, _, tst, tend) in enumerate(window_list) if tst <= day <= tend)
        for max_ev, ev_prob_list, payout in races_after_skip:
            for name, sizing_fn in VARIANTS:
                stakes = sizing_fn(ev_prob_list)
                race_stake = sum(stakes)
                race_profit = payout - race_stake
                rstats = results[name]
                rstats["total_stake"] += race_stake
                rstats["total_payout"] += payout
                rstats["bet_count"] += len(stakes)
                rstats["race_count"] += 1
                rstats["window_profits"][wi] += race_profit

    results_list: List[Dict] = []
    for name, _ in VARIANTS:
        r = results[name]
        ts = r["total_stake"]
        tp = r["total_payout"]
        cnt = r["bet_count"]
        rc = r["race_count"]
        total_profit = round(tp - ts, 2)
        roi = round((tp / ts - 1) * 100, 2) if ts else None
        profit_per_1000 = round(1000.0 * (tp - ts) / cnt, 2) if cnt else 0.0
        cum = 0.0
        peak = 0.0
        dd = 0.0
        for wprof in r["window_profits"]:
            cum += wprof
            if cum > peak:
                peak = cum
            if peak - cum > dd:
                dd = peak - cum
        avg_bet = round(ts / cnt, 2) if cnt else 0.0
        avg_stake_per_race = round(ts / rc, 2) if rc else 0.0
        out = {
            "variant": name,
            "ROI": roi,
            "total_profit": total_profit,
            "max_drawdown": round(dd, 2),
            "profit_per_1000_bets": profit_per_1000,
            "bet_count": cnt,
            "total_stake": round(ts, 2),
            "total_payout": round(tp, 2),
            "average_bet_size": avg_bet,
            "average_stake_per_race": avg_stake_per_race,
            "race_count": rc,
        }
        r.update(out)
        results_list.append(out)

    out_path = output_dir / "exp0040_bet_sizing_optimization_results.json"
    payload = {
        "experiment_id": "EXP-0040",
        "base_conditions": "skip_top20pct, 3<=EV<5, prob>=0.05",
        "n_windows": args.n_windows,
        "seed": args.seed,
        "min_unit": MIN_UNIT,
        "max_unit": MAX_UNIT,
        "max_unit_capped": MAX_UNIT_CAPPED,
        "baseline_unit": BASELINE_UNIT,
        "sizing_formulas": {
            "baseline_fixed": "unit = 100 (all bets)",
            "size_by_ev_linear": "unit = clip(round(25*EV), 50, 200)",
            "size_by_prob_linear": "unit = clip(round(200*prob), 50, 200)",
            "size_by_ev_prob": "unit = clip(round(40*EV*prob), 50, 200)",
            "size_by_ev_capped": "unit = clip(round(25*EV), 50, 150)",
            "size_by_ev_prob_capped": "unit = clip(round(40*EV*prob), 50, 150)",
        },
        "results": results_list,
    }
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    print(f"Saved {out_path}")

    print("\n--- EXP-0040 Bet sizing (skip_top20pct, 3<=EV<5, prob>=0.05, n_windows={}) ---".format(args.n_windows))
    print("variant                  | ROI     | total_profit | max_drawdown | profit/1k  | bet_count | total_stake | avg_bet | avg_stake/race")
    print("-" * 140)
    for name, _ in VARIANTS:
        r = results[name]
        print(
            f"  {name:22} | {r['ROI']:6}% | {r['total_profit']:12} | {r['max_drawdown']:12} | {r['profit_per_1000_bets']:9} | {r['bet_count']:9} | {r['total_stake']:11} | {r['average_bet_size']:7} | {r['average_stake_per_race']}"
        )

    return 0


if __name__ == "__main__":
    sys.exit(main())
