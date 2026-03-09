#!/usr/bin/env python3
"""
EXP-0008: Fractional Kelly optimization, calibration comparison, ensemble.

Reference: xgboost, sigmoid, extended_features, top_n_ev, top_n=3, ev_threshold=1.20.

Task1: Fractional Kelly sweep (selection fixed). Kelly cap: 0.002, 0.005, 0.01, 0.02.
Task2: Calibration comparison (none vs sigmoid). Same conditions, ROI.
Task3: Model comparison xgboost / lightgbm / ensemble (average probability). EV 計算で比較.

n_windows=12, seed=42. リポジトリルートで実行。
"""

import argparse
import copy
import json
import os
import sys
from pathlib import Path

_SCRIPT_DIR = Path(__file__).resolve().parent
_PROJECT_ROOT = _SCRIPT_DIR.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

os.environ["KYOTEI_USE_MOTOR_WIN_PROXY"] = os.environ.get("KYOTEI_USE_MOTOR_WIN_PROXY", "1")
os.environ["KYOTEI_FEATURE_SET"] = os.environ.get("KYOTEI_FEATURE_SET", "extended_features")

from kyotei_predictor.tools.rolling_validation_roi import (
    run_rolling_validation_roi,
    get_db_date_range,
    build_windows,
)
from kyotei_predictor.tools.rolling_validation_windows import _date_range
from kyotei_predictor.application.verify_usecase import run_verify
from kyotei_predictor.betting.bankroll_simulation import (
    simulate_bankroll,
    build_bet_list_from_verify,
)
from kyotei_predictor.infrastructure.file_loader import load_json

TRAIN_DAYS = 30
TEST_DAYS = 7
STEP_DAYS = 7
REF_TOP_N = 3
REF_EV = 1.20
KELLY_CAPS = [0.002, 0.005, 0.01, 0.02]
STRATEGY_SUFFIX = f"_top{REF_TOP_N}ev{int(REF_EV * 100)}"


def _collect_bets_from_predictions(db_path, raw_dir, pred_dir, windows_list, suffix):
    all_bets = []
    for ts, te, tst, tend in windows_list:
        for day in _date_range(tst, tend):
            month = day[:7]
            data_dir_month = raw_dir / month
            path = pred_dir / f"predictions_baseline_{day}{suffix}.json"
            if not path.exists() or not data_dir_month.exists():
                continue
            try:
                pred = load_json(path)
                predictions = pred.get("predictions") or []
                _, details = run_verify(
                    path, data_dir_month,
                    evaluation_mode="selected_bets",
                    data_source="db",
                    db_path=db_path,
                )
                bets = build_bet_list_from_verify(predictions, details, fixed_stake=100.0)
                all_bets.extend(bets)
            except Exception:
                pass
    return all_bets


def _merge_predictions_average_prob(pred_a: dict, pred_b: dict) -> dict:
    """2つの予測を確率平均でマージ。all_combinations の probability を平均し、selected_bets は top_n_ev で再計算。"""
    out = copy.deepcopy(pred_a)
    preds_a = {}
    for r in pred_a.get("predictions") or []:
        v, rno = r.get("venue", ""), r.get("race_number")
        preds_a.setdefault(v, {})[rno] = r
    preds_b = {}
    for r in pred_b.get("predictions") or []:
        v, rno = r.get("venue", ""), r.get("race_number")
        preds_b.setdefault(v, {})[rno] = r
    merged_list = []
    for venue, by_rno in preds_a.items():
        for rno, race_a in by_rno.items():
            race_b = (preds_b.get(venue) or {}).get(rno)
            if not race_b:
                merged_list.append(race_a)
                continue
            combs_a = {str((c.get("combination") or "").strip()): c for c in (race_a.get("all_combinations") or [])}
            combs_b = {str((c.get("combination") or "").strip()): c for c in (race_b.get("all_combinations") or [])}
            merged_combs = []
            for comb_key in set(combs_a) | set(combs_b):
                ca = combs_a.get(comb_key) or {}
                cb = combs_b.get(comb_key) or {}
                prob_a = float(ca.get("probability") or ca.get("score") or 0)
                prob_b = float(cb.get("probability") or cb.get("score") or 0)
                # 片方だけある場合はそのまま
                if comb_key not in combs_b:
                    merged_combs.append(copy.deepcopy(ca))
                    continue
                if comb_key not in combs_a:
                    merged_combs.append(copy.deepcopy(cb))
                    continue
                m = copy.deepcopy(ca)
                m["probability"] = (prob_a + prob_b) / 2.0
                if "score" in m:
                    m["score"] = m["probability"]
                merged_combs.append(m)
            merged_race = copy.deepcopy(race_a)
            merged_race["all_combinations"] = merged_combs
            # top_n_ev で selected_bets を再計算
            from kyotei_predictor.utils.betting_selector import select_top_n_ev
            selected = select_top_n_ev(merged_combs, REF_TOP_N, REF_EV)
            merged_race["selected_bets"] = selected
            merged_list.append(merged_race)
    out["predictions"] = merged_list
    return out


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db-path", required=True, help="SQLite DB path")
    parser.add_argument("--output-dir", type=Path, default=None)
    parser.add_argument("--n-windows", type=int, default=12)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    raw_dir = _PROJECT_ROOT / "kyotei_predictor" / "data" / "raw"
    if not raw_dir.is_dir():
        raw_dir = Path("kyotei_predictor/data/raw")
    output_dir = args.output_dir or _PROJECT_ROOT / "outputs"
    output_dir.mkdir(parents=True, exist_ok=True)
    base_pred_dir = output_dir / "rolling_roi_predictions"

    strategies_ref = [(f"top{REF_TOP_N}_ev{int(REF_EV*100)}", "top_n_ev", REF_TOP_N, REF_EV)]

    # Task1: Reference 条件で予測を1回生成し、fractional Kelly sweep
    print("Task1: Generating predictions (top_n=3, ev=1.20, xgboost, sigmoid)...")
    run_rolling_validation_roi(
        db_path=args.db_path,
        output_dir=output_dir,
        data_dir_raw=raw_dir,
        train_days=TRAIN_DAYS,
        test_days=TEST_DAYS,
        step_days=STEP_DAYS,
        n_windows=args.n_windows,
        strategies=strategies_ref,
        model_type="xgboost",
        calibration="sigmoid",
        feature_set="extended_features",
        seed=args.seed,
    )
    min_date, max_date = get_db_date_range(args.db_path)
    windows_list = build_windows(
        min_date, max_date, TRAIN_DAYS, TEST_DAYS, STEP_DAYS, args.n_windows
    )
    all_bets = _collect_bets_from_predictions(
        args.db_path, raw_dir, base_pred_dir, windows_list, STRATEGY_SUFFIX
    )
    print(f"  Collected {len(all_bets)} bets for Task1.")

    task1_results = []
    for cap in KELLY_CAPS:
        sizing = f"capped_kelly_{cap}"
        sim = simulate_bankroll(
            all_bets, initial_bankroll=100_000.0,
            bet_sizing=sizing, unit_stake=100.0,
        )
        task1_results.append({
            "kelly_cap": cap,
            "bet_sizing": sizing,
            "overall_roi_selected": sim["roi_pct"],
            "profit": round(sim["total_payout"] - sim["total_stake"], 2),
            "max_drawdown": sim["max_drawdown"],
            "bet_count": sim["bet_count"],
        })
    print("Task1: fractional Kelly sweep done.")
    for r in task1_results:
        print(f"  cap={r['kelly_cap']} -> roi={r['overall_roi_selected']}% profit={r['profit']} max_dd={r['max_drawdown']} bet_count={r['bet_count']}")

    # Task2: Calibration comparison (none vs sigmoid)
    print("Task2: Calibration comparison (none vs sigmoid)...")
    task2_results = []
    for cal in ["none", "sigmoid"]:
        out_sub = output_dir / f"cal_{cal}"
        out_sub.mkdir(parents=True, exist_ok=True)
        summary, windows = run_rolling_validation_roi(
            db_path=args.db_path,
            output_dir=out_sub,
            data_dir_raw=raw_dir,
            train_days=TRAIN_DAYS,
            test_days=TEST_DAYS,
            step_days=STEP_DAYS,
            n_windows=args.n_windows,
            strategies=strategies_ref,
            model_type="xgboost",
            calibration=cal,
            feature_set="extended_features",
            seed=args.seed,
        )
        if isinstance(summary, dict):
            summary = [summary]
            windows = [windows]
        s = summary[0]
        w = windows[0]
        tb = s.get("total_bet_selected") or 0
        tp = s.get("total_payout_selected") or 0
        profit = round(tp - tb, 2) if tb else 0.0
        cum, peak, max_dd = 0.0, 0.0, 0.0
        for ww in w:
            tbw = ww.get("total_bet_selected") or 0
            tpw = ww.get("total_payout_selected") or 0
            cum += (tpw - tbw) if tbw else 0
            if cum > peak:
                peak = cum
            if peak - cum > max_dd:
                max_dd = peak - cum
        task2_results.append({
            "calibration": cal,
            "overall_roi_selected": s["overall_roi_selected"],
            "profit": profit,
            "max_drawdown": round(max_dd, 2),
            "bet_count": s.get("total_selected_bets") or 0,
        })
    print("Task2 done.")
    for r in task2_results:
        print(f"  calibration={r['calibration']} -> roi={r['overall_roi_selected']}% profit={r['profit']}")

    # Task3: xgboost, lightgbm, ensemble
    print("Task3: Model comparison (xgboost, lightgbm, ensemble)...")
    task3_results = []
    for model_type in ["xgboost", "lightgbm"]:
        out_sub = output_dir / model_type
        out_sub.mkdir(parents=True, exist_ok=True)
        summary, windows = run_rolling_validation_roi(
            db_path=args.db_path,
            output_dir=out_sub,
            data_dir_raw=raw_dir,
            train_days=TRAIN_DAYS,
            test_days=TEST_DAYS,
            step_days=STEP_DAYS,
            n_windows=args.n_windows,
            strategies=strategies_ref,
            model_type=model_type,
            calibration="sigmoid",
            feature_set="extended_features",
            seed=args.seed,
        )
        if isinstance(summary, dict):
            summary = [summary]
            windows = [windows]
        s = summary[0]
        w = windows[0]
        tb = s.get("total_bet_selected") or 0
        tp = s.get("total_payout_selected") or 0
        profit = round(tp - tb, 2) if tb else 0.0
        cum, peak, max_dd = 0.0, 0.0, 0.0
        for ww in w:
            tbw = ww.get("total_bet_selected") or 0
            tpw = ww.get("total_payout_selected") or 0
            cum += (tpw - tbw) if tbw else 0
            if cum > peak:
                peak = cum
            if peak - cum > max_dd:
                max_dd = peak - cum
        task3_results.append({
            "model": model_type,
            "overall_roi_selected": s["overall_roi_selected"],
            "profit": profit,
            "max_drawdown": round(max_dd, 2),
            "bet_count": s.get("total_selected_bets") or 0,
        })

    # Ensemble: average probability from xgboost and lightgbm predictions
    pred_dir_xgb = output_dir / "xgboost" / "rolling_roi_predictions"
    pred_dir_lgb = output_dir / "lightgbm" / "rolling_roi_predictions"
    ensemble_dir = output_dir / "ensemble"
    ensemble_dir.mkdir(parents=True, exist_ok=True)
    ensemble_pred_dir = ensemble_dir / "rolling_roi_predictions"
    ensemble_pred_dir.mkdir(parents=True, exist_ok=True)

    total_bet_ens = 0.0
    total_payout_ens = 0.0
    total_bet_count_ens = 0
    cum, peak, max_dd_ens = 0.0, 0.0, 0.0

    for i, (ts, te, tst, tend) in enumerate(windows_list):
        tb_w, tp_w = 0.0, 0.0
        count_w = 0
        for day in _date_range(tst, tend):
            month = day[:7]
            data_dir_month = raw_dir / month
            path_x = pred_dir_xgb / f"predictions_baseline_{day}{STRATEGY_SUFFIX}.json"
            path_l = pred_dir_lgb / f"predictions_baseline_{day}{STRATEGY_SUFFIX}.json"
            if not path_x.exists() or not path_l.exists() or not data_dir_month.exists():
                continue
            try:
                pred_x = load_json(path_x)
                pred_l = load_json(path_l)
                merged = _merge_predictions_average_prob(pred_x, pred_l)
                out_path = ensemble_pred_dir / f"predictions_baseline_{day}{STRATEGY_SUFFIX}.json"
                with open(out_path, "w", encoding="utf-8") as f:
                    json.dump(merged, f, ensure_ascii=False, indent=2)
                summary_v, _ = run_verify(
                    out_path, data_dir_month,
                    evaluation_mode="selected_bets",
                    data_source="db",
                    db_path=args.db_path,
                )
                tb_w += summary_v.get("total_bet_selected") or 0
                tp_w += summary_v.get("total_payout_selected") or 0
                count_w += summary_v.get("selected_bets_total_count") or 0
            except Exception:
                pass
        total_bet_ens += tb_w
        total_payout_ens += tp_w
        total_bet_count_ens += count_w
        cum += (tp_w - tb_w) if tb_w else 0
        if cum > peak:
            peak = cum
        if peak - cum > max_dd_ens:
            max_dd_ens = peak - cum

    roi_ens = round((total_payout_ens / total_bet_ens - 1) * 100, 2) if total_bet_ens else 0.0
    profit_ens = round(total_payout_ens - total_bet_ens, 2)
    task3_results.append({
        "model": "ensemble",
        "overall_roi_selected": roi_ens,
        "profit": profit_ens,
        "max_drawdown": round(max_dd_ens, 2),
        "bet_count": total_bet_count_ens,
    })
    print("Task3 done.")
    for r in task3_results:
        print(f"  model={r['model']} -> roi={r['overall_roi_selected']}% profit={r['profit']} max_dd={r['max_drawdown']} bet_count={r['bet_count']}")

    out = {
        "experiment_id": "EXP-0008",
        "model": "xgboost",
        "calibration": "sigmoid",
        "features": "extended_features",
        "strategy": "top_n_ev",
        "top_n": REF_TOP_N,
        "ev_threshold": REF_EV,
        "n_windows": args.n_windows,
        "seed": args.seed,
        "task1_fractional_kelly": task1_results,
        "task2_calibration": task2_results,
        "task3_model_ensemble": task3_results,
    }
    out_path = output_dir / "exp0008_fractional_kelly.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    print(f"Saved {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
