"""
EXP-0037: EV帯フィルタ戦略の検証。

EXP-0036 で黒字帯（3-4, 4-5, 6-8）を特定。利益を出している帯だけを購入した場合に ROI が改善するか検証する。

比較条件:
- baseline: EV <= 5（EXP-0033 = skip_top20pct + ev_cap_5.0）
- 3<=EV<5, 3<=EV<6, 3<=EV<8, 4<=EV<5, 4<=EV<6

いずれも skip_top20pct を適用したうえで、該当 EV 帯のレースのみ購入。
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

# (表示名, フィルタ関数: max_ev -> bool)
def _band_ev_lte_5(max_ev: float) -> bool:
    return max_ev <= 5.0

def _band_3_5(max_ev: float) -> bool:
    return 3.0 <= max_ev < 5.0

def _band_3_6(max_ev: float) -> bool:
    return 3.0 <= max_ev < 6.0

def _band_3_8(max_ev: float) -> bool:
    return 3.0 <= max_ev < 8.0

def _band_4_5(max_ev: float) -> bool:
    return 4.0 <= max_ev < 5.0

def _band_4_6(max_ev: float) -> bool:
    return 4.0 <= max_ev < 6.0

EV_BAND_VARIANTS: List[Tuple[str, Callable[[float], bool]]] = [
    ("baseline_ev_lte_5", _band_ev_lte_5),
    ("ev_band_3_5", _band_3_5),
    ("ev_band_3_6", _band_3_6),
    ("ev_band_3_8", _band_3_8),
    ("ev_band_4_5", _band_4_5),
    ("ev_band_4_6", _band_4_6),
]


def _max_ev_for_race(race: dict) -> float:
    """レースの selected_bets に対応する EV の最大値を返す。EV = probability * odds."""
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

    output_dir = args.output_dir or _REPO_ROOT / "outputs" / "ev_band_strategy"
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
        print(f"EXP-0037: Using existing predictions in {out_pred_dir} ({len(existing)} files).")
    else:
        print(f"EXP-0037: Running rolling validation (n_windows={args.n_windows})...")
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

    races_per_date: Dict[str, List[Tuple[float, float, float, float, int]]] = {}

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

            day_races = []
            for race in predictions_list:
                venue = race.get("venue") or ""
                rno = int(race.get("race_number") or 0)
                selected = race.get("selected_bets") or []
                if not selected:
                    continue
                max_ev = _max_ev_for_race(race)
                d = detail_by_key.get((venue, rno))
                if not d:
                    continue
                payout = float(d.get("payout") or 0)
                race_profit = float(d.get("race_profit") or 0)
                stake = payout - race_profit
                bet_count = int(d.get("purchased_bets") or 0)
                if bet_count <= 0:
                    continue
                day_races.append((max_ev, stake, payout, race_profit, bet_count))

            if day_races:
                races_per_date[day] = day_races

    results: Dict[str, Dict] = {}
    for name, _ in EV_BAND_VARIANTS:
        results[name] = {
            "total_bet_selected": 0.0,
            "total_payout_selected": 0.0,
            "selected_bets_total_count": 0,
            "window_profits": [0.0] * len(window_list),
        }

    for day, day_races in races_per_date.items():
        day_races_sorted = sorted(day_races, key=lambda x: -x[0])
        n = len(day_races_sorted)
        k_skip = int(n * SKIP_TOP_PCT)
        idx_start = min(k_skip, n)
        races_after_skip = day_races_sorted[idx_start:]

        for name, pred_fn in EV_BAND_VARIANTS:
            included = [r for r in races_after_skip if pred_fn(r[0])]
            total_stake = sum(r[1] for r in included)
            total_payout = sum(r[2] for r in included)
            total_profit_day = total_payout - total_stake
            total_bets_day = sum(r[4] for r in included)
            rstats = results[name]
            rstats["total_bet_selected"] += total_stake
            rstats["total_payout_selected"] += total_payout
            rstats["selected_bets_total_count"] += total_bets_day
            for wi, (ts, te, tst, tend) in enumerate(window_list):
                if tst <= day <= tend:
                    rstats["window_profits"][wi] += total_profit_day
                    break

    results_list: List[Dict] = []
    for name, _ in EV_BAND_VARIANTS:
        rstats = results[name]
        tb = rstats["total_bet_selected"]
        tp = rstats["total_payout_selected"]
        cnt = rstats["selected_bets_total_count"]
        total_profit = round(tp - tb, 2)
        roi = round((tp / tb - 1) * 100, 2) if tb else None
        profit_per_1000 = round(1000.0 * (tp - tb) / cnt, 2) if cnt else 0.0
        cum = 0.0
        peak = 0.0
        dd = 0.0
        for wprof in rstats["window_profits"]:
            cum += wprof
            if cum > peak:
                peak = cum
            if peak - cum > dd:
                dd = peak - cum
        out = {
            "variant": name,
            "overall_roi_selected": roi,
            "total_profit": total_profit,
            "max_drawdown": round(dd, 2),
            "profit_per_1000_bets": profit_per_1000,
            "bet_count": cnt,
            "total_bet_selected": round(tb, 2),
            "total_payout_selected": round(tp, 2),
        }
        rstats.update(out)
        results_list.append(out)

    out_path = output_dir / "exp0037_ev_band_strategy_results.json"
    payload = {
        "experiment_id": "EXP-0037",
        "baseline": "EV<=5 (EXP-0033: skip_top20pct + ev_cap_5.0)",
        "n_windows": args.n_windows,
        "seed": args.seed,
        "skip_top_pct": SKIP_TOP_PCT,
        "variants": [
            "baseline_ev_lte_5 (EV<=5)",
            "ev_band_3_5 (3<=EV<5)",
            "ev_band_3_6 (3<=EV<6)",
            "ev_band_3_8 (3<=EV<8)",
            "ev_band_4_5 (4<=EV<5)",
            "ev_band_4_6 (4<=EV<6)",
        ],
        "results": results_list,
    }
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    print(f"Saved {out_path}")

    print("\n--- EXP-0037 EV band strategy (skip_top20pct, n_windows={}) ---".format(args.n_windows))
    print("variant             | ROI     | total_profit | max_drawdown | profit_per_1000_bets | bet_count")
    print("-" * 105)
    for name, _ in EV_BAND_VARIANTS:
        r = results[name]
        print(
            f"  {name:18} | {r.get('overall_roi_selected'):6}% | {r.get('total_profit'):12} | {r.get('max_drawdown'):12} | "
            f"{r.get('profit_per_1000_bets'):20} | {r.get('bet_count')}"
        )

    return 0


if __name__ == "__main__":
    sys.exit(main())
