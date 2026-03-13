"""
EXP-0031: EXP-0015 条件 + confidence_weighted_sizing を前提に、
高EV帯除外（EV percentile 上位 10% skip / 20% skip / skip なし）を比較する。

ベースライン: EXP-0015 + confidence_weighted（ev_gap_high=0.11, normal_unit=0.5）
比較: ev_skip_top_pct = 0（なし）, 0.1（10% skip）, 0.2（20% skip）
日付ごとにその日のレースを EV 順に並べ、上位 N% のレースをベット対象から除外して集計。
rolling validation n_windows=12。
"""

import argparse
import json
import os
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

# (表示名, ev_skip_top_pct): 0=なし, 0.1=上位10%skip, 0.2=上位20%skip
EV_SKIP_VARIANTS: List[Tuple[str, float]] = [
    ("no_skip", 0.0),
    ("skip_top10pct", 0.1),
    ("skip_top20pct", 0.2),
]


def _max_ev_for_race(race: dict) -> float:
    """レースの selected_bets に対応する EV の最大値を返す。EV = probability * ratio。"""
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
    parser.add_argument("--n-windows", type=int, default=12)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    raw_dir = _REPO_ROOT / "kyotei_predictor" / "data" / "raw"
    if not raw_dir.is_dir():
        raw_dir = Path("kyotei_predictor/data/raw")
    output_dir = args.output_dir or _REPO_ROOT / "outputs" / "confidence_weighted_sizing_experiments"
    output_dir.mkdir(parents=True, exist_ok=True)
    out_pred_dir = output_dir / "rolling_roi_predictions"

    # 1) EXP-0015 の rolling 予測を用意（既存があれば流用）
    if not (out_pred_dir.exists() and list(out_pred_dir.glob("predictions_baseline_*" + STRATEGY_SUFFIX + ".json"))):
        print(f"EXP-0031: Running rolling validation (n_windows={args.n_windows}) for EXP-0015...")
        run_rolling_validation_roi(
            db_path=args.db_path,
            output_dir=output_dir,
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
    else:
        print(f"Using existing predictions in {out_pred_dir}")

    min_date, max_date = get_db_date_range(args.db_path)
    window_list = build_windows(
        min_date, max_date, TRAIN_DAYS, TEST_DAYS, STEP_DAYS, args.n_windows
    )

    # 2) 日付×レースごとに confidence_weighted で verify し、max_ev と stake/payout/race_profit/bet_count を取得
    # races_per_date[date] = [(max_ev, stake, payout, race_profit, bet_count), ...]
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

            day_races: List[Tuple[float, float, float, float, int]] = []
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
                stake = payout - race_profit  # race_profit = payout - stake
                bet_count = int(d.get("purchased_bets") or 0)
                if bet_count <= 0:
                    continue
                day_races.append((max_ev, stake, payout, race_profit, bet_count))

            if day_races:
                races_per_date[day] = day_races

    # 3) 日付ごとに EV 順でソートし、ev_skip_top_pct に応じて除外して集計
    # results[variant_name] = { total_stake, total_payout, total_profit, bet_count, window_profits[] }
    results: Dict[str, Dict] = {}
    for variant_name, skip_pct in EV_SKIP_VARIANTS:
        results[variant_name] = {
            "total_bet_selected": 0.0,
            "total_payout_selected": 0.0,
            "selected_bets_total_count": 0,
            "window_profits": [0.0] * len(window_list),
        }

    for day, day_races in races_per_date.items():
        # その日のレースを max_ev 降順でソート
        day_races_sorted = sorted(day_races, key=lambda x: -x[0])
        n = len(day_races_sorted)
        for variant_name, skip_pct in EV_SKIP_VARIANTS:
            if skip_pct <= 0:
                include_from = 0
            else:
                k_skip = int(n * skip_pct)  # 除外する件数（上位）
                include_from = min(k_skip, n)
            included = day_races_sorted[include_from:]
            total_stake = sum(r[1] for r in included)
            total_payout = sum(r[2] for r in included)
            total_profit_day = total_payout - total_stake
            total_bets_day = sum(r[4] for r in included)
            results[variant_name]["total_bet_selected"] += total_stake
            results[variant_name]["total_payout_selected"] += total_payout
            results[variant_name]["selected_bets_total_count"] += total_bets_day
            # この日が属する window に profit を加算（日付から window を逆引き）
            for wi, (ts, te, tst, tend) in enumerate(window_list):
                if tst <= day <= tend:
                    results[variant_name]["window_profits"][wi] += total_profit_day
                    break

    # 4) ROI, total_profit, max_drawdown, profit_per_1000_bets, bet_count を計算
    results_list: List[Dict] = []
    for variant_name, skip_pct in EV_SKIP_VARIANTS:
        r = results[variant_name]
        tb = r["total_bet_selected"]
        tp = r["total_payout_selected"]
        cnt = r["selected_bets_total_count"]
        total_profit = round(tp - tb, 2)
        roi = round((tp / tb - 1) * 100, 2) if tb else None
        profit_per_1000 = round(1000.0 * (tp - tb) / cnt, 2) if cnt else 0.0
        cum = 0.0
        peak = 0.0
        dd = 0.0
        for wprof in r["window_profits"]:
            cum += wprof
            if cum > peak:
                peak = cum
            if peak - cum > dd:
                dd = peak - cum
        out = {
            "variant": variant_name,
            "ev_skip_top_pct": skip_pct,
            "overall_roi_selected": roi,
            "total_profit": total_profit,
            "max_drawdown": round(dd, 2),
            "profit_per_1000_bets": profit_per_1000,
            "bet_count": cnt,
            "total_bet_selected": round(tb, 2),
            "total_payout_selected": round(tp, 2),
        }
        results[variant_name].update(out)
        results_list.append(out)

    out_path = output_dir / "exp0031_ev_high_skip_results.json"
    payload = {
        "experiment_id": "EXP-0031",
        "baseline": "EXP-0015 + confidence_weighted (ev_gap_high=0.11, normal_unit=0.5)",
        "n_windows": args.n_windows,
        "seed": args.seed,
        "ev_skip_variants": [{"name": n, "ev_skip_top_pct": p} for n, p in EV_SKIP_VARIANTS],
        "results": results_list,
    }
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    print(f"Saved {out_path}")

    print("\n--- EXP-0031 Results (variant | ROI | total_profit | max_drawdown | profit_per_1000_bets | bet_count) ---")
    for variant_name in [v[0] for v in EV_SKIP_VARIANTS]:
        r = results[variant_name]
        print(
            f"  {variant_name} | ROI={r.get('overall_roi_selected')}% | total_profit={r.get('total_profit')} | "
            f"max_drawdown={r.get('max_drawdown')} | profit_per_1000_bets={r.get('profit_per_1000_bets')} | bet_count={r.get('bet_count')}"
        )

    return 0


if __name__ == "__main__":
    sys.exit(main())
