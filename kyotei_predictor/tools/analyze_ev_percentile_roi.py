"""
EXP-0027: EV percentile 別 ROI 分析。
selected bets を持つレースを EV（レース内の選抜ベットの最大 EV）順に並べ、
top 1% / 5% / 10% / 20% / 50% / full の帯ごとに ROI・total_profit・max_drawdown・profit_per_1000_bets・bet_count を集計する。
どの EV 帯が利益源でどの帯が損失源かを特定する。

対象戦略: EXP-0015, EXP-0013, EXP-0007
"""

import argparse
import json
import os
import re
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
    ("exp0013", "top_n_ev_gap_filter", TOP_N, 1.18, None, None, None, 0.05),
    ("exp0007", "top_n_ev", TOP_N, 1.18, None, None, None, None),
]

STRATEGY_SUFFIXES: Dict[str, str] = {
    "exp0015": "_top3ev120_evgap0x07",
    "exp0013": "_top3ev118_evgap0x05",
    "exp0007": "_top3ev118",
}

BANDS = ["top_1pct", "top_5pct", "top_10pct", "top_20pct", "top_50pct", "full"]
BAND_CUTOFFS = [0.01, 0.05, 0.10, 0.20, 0.50, 1.0]


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


def _date_from_path(path: Path) -> str:
    """predictions_baseline_YYYY-MM-DD_suffix.json から日付を抽出。"""
    stem = path.stem
    m = re.match(r"predictions_baseline_(\d{4}-\d{2}-\d{2})", stem)
    return m.group(1) if m else ""


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
    output_dir = args.output_dir or _REPO_ROOT / "outputs" / "ev_percentile_analysis"
    output_dir.mkdir(parents=True, exist_ok=True)
    out_pred_dir = output_dir / "rolling_roi_predictions"
    need_run = not (out_pred_dir.exists() and list(out_pred_dir.glob("predictions_baseline_*")))
    if need_run:
        print(f"Running rolling validation (n_windows={args.n_windows}) for {len(STRATEGIES)} strategies...")
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

    all_results: Dict[str, Dict[str, dict]] = {}

    for strat_name in ["exp0015", "exp0013", "exp0007"]:
        suffix = STRATEGY_SUFFIXES[strat_name]
        races: List[Tuple[str, str, int, float, float, float, float, int]] = []

        for wi, (ts, te, tst, tend) in enumerate(window_list):
            test_dates = _date_range(tst, tend)
            for day in test_dates:
                month = _month_dir(day)
                data_dir_month = raw_dir / month
                path = out_pred_dir / f"predictions_baseline_{day}{suffix}.json"
                if not path.exists() or not data_dir_month.exists():
                    continue
                pred_date = _date_from_path(path)
                if not pred_date:
                    pred_date = day
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
                        bet_sizing_mode="fixed",
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
                    d = detail_by_key.get((venue, rno))
                    if not d:
                        continue
                    payout = float(d.get("payout") or 0)
                    race_profit = float(d.get("race_profit") or 0)
                    stake = payout - race_profit
                    bet_count = int(d.get("purchased_bets") or 0)
                    if bet_count <= 0:
                        continue
                    races.append((pred_date, venue, rno, max_ev, stake, payout, race_profit, bet_count))

        if not races:
            all_results[strat_name] = {}
            continue

        races.sort(key=lambda x: -x[3])
        n_races = len(races)
        band_races: Dict[str, List[Tuple]] = {}
        for i, cutoff in enumerate(BAND_CUTOFFS):
            k = int(n_races * cutoff)
            k = min(k, n_races)
            band_races[BANDS[i]] = races[:k]

        all_results[strat_name] = {}
        for band_name, band_list in band_races.items():
            if not band_list:
                all_results[strat_name][band_name] = {
                    "band": band_name,
                    "roi": None,
                    "total_profit": 0.0,
                    "max_drawdown": 0.0,
                    "profit_per_1000_bets": None,
                    "bet_count": 0,
                    "race_count": 0,
                }
                continue
            total_stake = sum(r[4] for r in band_list)
            total_payout = sum(r[5] for r in band_list)
            total_profit = total_payout - total_stake
            bet_count = sum(r[7] for r in band_list)
            roi = round((total_payout / total_stake - 1) * 100, 2) if total_stake else None
            profit_per_1000 = round(1000.0 * total_profit / bet_count, 2) if bet_count else None
            band_list_by_date = sorted(band_list, key=lambda x: (x[0], x[1], x[2]))
            cum = 0.0
            peak = 0.0
            dd = 0.0
            for r in band_list_by_date:
                cum += r[6]
                if cum > peak:
                    peak = cum
                if peak - cum > dd:
                    dd = peak - cum
            all_results[strat_name][band_name] = {
                "band": band_name,
                "roi": roi,
                "total_profit": round(total_profit, 2),
                "max_drawdown": round(dd, 2),
                "profit_per_1000_bets": profit_per_1000,
                "bet_count": bet_count,
                "race_count": len(band_list),
            }

    results_list: List[dict] = []
    for strat_name in ["exp0015", "exp0013", "exp0007"]:
        for band_name in BANDS:
            r = all_results.get(strat_name, {}).get(band_name, {})
            r = dict(r)
            r["strategy_id"] = strat_name
            results_list.append(r)

    out_path = output_dir / "exp0027_ev_percentile_analysis_results.json"
    payload = {
        "experiment_id": "EXP-0027",
        "n_windows": args.n_windows,
        "strategies": [{"name": s[0], "strategy": s[1]} for s in STRATEGIES],
        "bands": BANDS,
        "band_cutoffs": BAND_CUTOFFS,
        "results": results_list,
    }
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    print(f"Saved {out_path}")

    print("\n--- Results (strategy_id | band | ROI | total_profit | max_drawdown | profit_per_1000_bets | bet_count) ---")
    for strat_name in ["exp0015", "exp0013", "exp0007"]:
        for band_name in BANDS:
            r = all_results.get(strat_name, {}).get(band_name, {})
            print(
                f"  {strat_name} | {band_name} | ROI={r.get('roi')}% | total_profit={r.get('total_profit')} | "
                f"max_drawdown={r.get('max_drawdown')} | profit_per_1000_bets={r.get('profit_per_1000_bets')} | bet_count={r.get('bet_count')}"
            )

    return 0


if __name__ == "__main__":
    sys.exit(main())
