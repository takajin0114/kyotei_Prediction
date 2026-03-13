"""
EXP-0036: EV帯ごとの成績分析。

EXP-0015 + confidence_weighted、n_windows=18 で rolling 予測を取得し、
レースの max_ev（selected_bets の EV = probability×odds の最大）で EV 帯に分類し、
各帯の bet_count / hit_rate / ROI / total_profit を集計する。

EV 帯: EV<1, 1<=EV<2, 2<=EV<3, 3<=EV<4, 4<=EV<5, 5<=EV<6, 6<=EV<8, 8<=EV<10, EV>=10
hit_rate: その帯で払戻>0 のレース数 / レース数（レース当選率）
"""

import argparse
import csv
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

# EV 帯: (表示名, (low, high))  high=None は以上
EV_BANDS: List[Tuple[str, Tuple[float, float]]] = [
    ("EV_lt_1", (0.0, 1.0)),
    ("EV_1_2", (1.0, 2.0)),
    ("EV_2_3", (2.0, 3.0)),
    ("EV_3_4", (3.0, 4.0)),
    ("EV_4_5", (4.0, 5.0)),
    ("EV_5_6", (5.0, 6.0)),
    ("EV_6_8", (6.0, 8.0)),
    ("EV_8_10", (8.0, 10.0)),
    ("EV_ge_10", (10.0, None)),
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


def _ev_band_for_max_ev(max_ev: float) -> str:
    """max_ev が属する EV 帯の表示名を返す。"""
    for name, (low, high) in EV_BANDS:
        if high is None:
            if max_ev >= low:
                return name
        else:
            if low <= max_ev < high:
                return name
    return "EV_other"


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

    output_dir = args.output_dir or _REPO_ROOT / "outputs" / "ev_distribution_analysis"
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
        print(f"EXP-0036: Using existing predictions in {out_pred_dir} ({len(existing)} files).")
    else:
        print(f"EXP-0036: Running rolling validation (n_windows={args.n_windows})...")
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

    # 帯ごと: total_stake, total_payout, bet_count, race_count, races_with_payout
    band_stats: Dict[str, Dict] = {}
    for name, _ in EV_BANDS:
        band_stats[name] = {
            "total_stake": 0.0,
            "total_payout": 0.0,
            "bet_count": 0,
            "race_count": 0,
            "races_with_payout": 0,
        }

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

            for race in predictions_list:
                venue = race.get("venue") or ""
                rno = int(race.get("race_number") or 0)
                selected = race.get("selected_bets") or []
                if not selected:
                    continue
                max_ev = _max_ev_for_race(race)
                band = _ev_band_for_max_ev(max_ev)
                d = detail_by_key.get((venue, rno))
                if not d:
                    continue
                payout = float(d.get("payout") or 0)
                race_profit = float(d.get("race_profit") or 0)
                stake = payout - race_profit
                bet_count = int(d.get("purchased_bets") or 0)
                if bet_count <= 0:
                    continue
                st = band_stats[band]
                st["total_stake"] += stake
                st["total_payout"] += payout
                st["bet_count"] += bet_count
                st["race_count"] += 1
                if payout > 0:
                    st["races_with_payout"] += 1

    results_list: List[Dict] = []
    for name, (low, high) in EV_BANDS:
        st = band_stats[name]
        tb = st["total_stake"]
        tp = st["total_payout"]
        cnt = st["bet_count"]
        rc = st["race_count"]
        rwp = st["races_with_payout"]
        total_profit = round(tp - tb, 2)
        roi = round((tp / tb - 1) * 100, 2) if tb else None
        hit_rate = round(100.0 * rwp / rc, 2) if rc else None
        row = {
            "ev_band": name,
            "ev_range": f"{low}<=EV<{high}" if high is not None else f"EV>={low}",
            "bet_count": cnt,
            "race_count": rc,
            "races_with_payout": rwp,
            "hit_rate_pct": hit_rate,
            "roi_pct": roi,
            "total_profit": total_profit,
            "total_stake": round(tb, 2),
            "total_payout": round(tp, 2),
        }
        results_list.append(row)

    out_json = output_dir / "exp0036_ev_band_analysis_results.json"
    payload = {
        "experiment_id": "EXP-0036",
        "n_windows": args.n_windows,
        "strategy": "EXP-0015 + confidence_weighted_ev_gap_v1",
        "ev_definition": "race-level max EV = max(probability*odds) over selected_bets",
        "hit_rate_definition": "races_with_payout / race_count (レース当選率)",
        "results": results_list,
    }
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    print(f"Saved {out_json}")

    out_csv = output_dir / "exp0036_ev_band_analysis_results.csv"
    with open(out_csv, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=[
            "ev_band", "ev_range", "bet_count", "race_count", "races_with_payout",
            "hit_rate_pct", "roi_pct", "total_profit", "total_stake", "total_payout",
        ])
        w.writeheader()
        w.writerows(results_list)
    print(f"Saved {out_csv}")

    print("\n--- EXP-0036 EV band vs ROI (n_windows={}) ---".format(args.n_windows))
    print("ev_band     | ev_range      | bet_count | race_count | hit_rate_pct | roi_pct   | total_profit")
    print("-" * 95)
    for r in results_list:
        ev_range = r.get("ev_range", "")
        if len(ev_range) > 12:
            ev_range = ev_range[:12]
        roi_s = str(r.get("roi_pct")) if r.get("roi_pct") is not None else "N/A"
        hit_s = str(r.get("hit_rate_pct")) if r.get("hit_rate_pct") is not None else "N/A"
        print(
            f"  {r['ev_band']:10} | {ev_range:12} | {r['bet_count']:9} | {r['race_count']:10} | "
            f"{hit_s:12} | {roi_s:8}% | {r['total_profit']}"
        )

    return 0


if __name__ == "__main__":
    sys.exit(main())
