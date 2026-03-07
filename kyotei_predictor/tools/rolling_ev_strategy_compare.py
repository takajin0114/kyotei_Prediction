"""
EV 戦略の rolling validation 比較（ROI / max drawdown / Sharpe / profit factor）。

calibration=sigmoid、15日学習・7日検証・4 window。
比較: EV threshold (1.10, 1.15)、bet sizing (fixed, kelly_half)。
結果: logs/rolling_ev_strategy_compare.json

実行（プロジェクトルート）:
  PYTHONPATH=. python3 kyotei_predictor/tools/rolling_ev_strategy_compare.py
"""

import json
import os
import statistics
import sys
from pathlib import Path

_THIS_DIR = Path(__file__).resolve().parent
_PROJECT_ROOT = _THIS_DIR.parent.parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from kyotei_predictor.tools.rolling_validation_windows import run_one_window
from kyotei_predictor.application.verify_usecase import run_verify
from kyotei_predictor.betting.bankroll_simulation import build_bet_list_from_verify, simulate_bankroll
from kyotei_predictor.infrastructure.file_loader import load_json


def _date_range(start: str, end: str):
    from datetime import datetime, timedelta
    s = datetime.strptime(start, "%Y-%m-%d")
    e = datetime.strptime(end, "%Y-%m-%d")
    out = []
    while s <= e:
        out.append(s.strftime("%Y-%m-%d"))
        s += timedelta(days=1)
    return out


def _month_dir(date_str: str) -> str:
    return date_str[:7]


def main() -> int:
    raw_dir = Path("kyotei_predictor/data/raw")
    if not raw_dir.is_dir():
        raw_dir = _PROJECT_ROOT / "kyotei_predictor" / "data" / "raw"
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)
    outputs_dir = Path("outputs")
    outputs_dir.mkdir(exist_ok=True)

    windows_15d = [
        ("2024-06-01", "2024-06-15", "2024-06-16", "2024-06-22"),
        ("2024-06-08", "2024-06-22", "2024-06-23", "2024-06-29"),
        ("2024-06-15", "2024-06-29", "2024-06-30", "2024-07-06"),
        ("2024-06-22", "2024-07-06", "2024-07-07", "2024-07-13"),
    ]
    strategies = [
        ("B top_n=3", "top_n", 3, None),
        ("B top_n=5 EV>1.10", "top_n_ev", 5, 1.10),
        ("B top_n=5 EV>1.15", "top_n_ev", 5, 1.15),
    ]

    data_source = os.environ.get("KYOTEI_DATA_SOURCE")
    db_path = os.environ.get("KYOTEI_DB_PATH")
    calibration = "sigmoid"

    pred_dir = outputs_dir / "rolling_windows_15d_ev_compare"
    pred_dir.mkdir(exist_ok=True)
    model_path = outputs_dir / "rolling_b_ev_compare.joblib"

    # 1. 各 window で学習・予測・検証（run_one_window）
    all_windows = []
    for i, (ts, te, tst, tend) in enumerate(windows_15d):
        print(f"Window {i+1}: train {ts}~{te} test {tst}~{tend}")
        row = run_one_window(
            train_start=ts,
            train_end=te,
            test_start=tst,
            test_end=tend,
            data_dir_raw=raw_dir,
            model_path=model_path,
            out_pred_dir=pred_dir,
            strategies=strategies,
            train_days=15,
            data_source=data_source,
            db_path=db_path,
            calibration=calibration,
        )
        row["window_id"] = i + 1
        all_windows.append(row)

    # 2. 各 (window, strategy) で verify の details を取得し、bet list を組み立てて bankroll シミュレーション
    test_dates_per_window = [_date_range(w["test_start"], w["test_end"]) for w in all_windows]
    results_by_window_strategy: list = []
    initial_bankroll = 100_000.0

    for wi, w in enumerate(all_windows):
        test_dates = test_dates_per_window[wi]
        for spec_name, strategy, top_n, ev_th in strategies:
            all_bets: list = []
            total_bet_fixed = 0.0
            total_payout_fixed = 0.0

            for day in test_dates:
                month = _month_dir(day)
                data_dir_month = raw_dir / month
                if strategy == "top_n_ev" and ev_th:
                    path = pred_dir / f"predictions_baseline_{day}_top5ev{int(ev_th * 100)}.json"
                else:
                    path = pred_dir / f"predictions_baseline_{day}.json"
                if not path.exists() or not data_dir_month.exists():
                    continue
                try:
                    summary, details = run_verify(
                        path,
                        data_dir_month,
                        evaluation_mode="selected_bets",
                        data_source=data_source,
                        db_path=db_path,
                    )
                    pred = load_json(path)
                    preds = pred.get("predictions") or []
                    bets = build_bet_list_from_verify(preds, details, fixed_stake=100.0)
                    all_bets.extend(bets)
                    total_bet_fixed += summary.get("total_bet") or 0
                    total_payout_fixed += summary.get("total_payout") or 0
                except Exception as e:
                    print(f"Verify/build_bets failed {path}: {e}")

            roi_pct = round((total_payout_fixed / total_bet_fixed - 1) * 100, 2) if total_bet_fixed else 0.0
            sim_fixed = simulate_bankroll(all_bets, initial_bankroll=initial_bankroll, bet_sizing="fixed", unit_stake=100.0)
            sim_kelly = simulate_bankroll(all_bets, initial_bankroll=initial_bankroll, bet_sizing="kelly_half", unit_stake=100.0)

            results_by_window_strategy.append({
                "window_id": wi + 1,
                "strategy_name": spec_name,
                "roi_pct": roi_pct,
                "total_bet": total_bet_fixed,
                "total_payout": total_payout_fixed,
                "fixed": {
                    "max_drawdown": sim_fixed["max_drawdown"],
                    "sharpe_ratio": sim_fixed["sharpe_ratio"],
                    "profit_factor": sim_fixed["profit_factor"],
                    "final_bankroll": sim_fixed["final_bankroll"],
                },
                "kelly_half": {
                    "max_drawdown": sim_kelly["max_drawdown"],
                    "sharpe_ratio": sim_kelly["sharpe_ratio"],
                    "profit_factor": sim_kelly["profit_factor"],
                    "final_bankroll": sim_kelly["final_bankroll"],
                },
            })

    # 3. 戦略別・bet_sizing 別に集約（平均 ROI、平均 max_drawdown、平均 Sharpe 等）
    strategy_names = [s[0] for s in strategies]
    aggregate = {}
    for sn in strategy_names:
        rows = [r for r in results_by_window_strategy if r["strategy_name"] == sn]
        rois = [r["roi_pct"] for r in rows]
        fixed_dd = [r["fixed"]["max_drawdown"] for r in rows]
        fixed_sharpe = [r["fixed"]["sharpe_ratio"] for r in rows]
        kelly_dd = [r["kelly_half"]["max_drawdown"] for r in rows]
        kelly_sharpe = [r["kelly_half"]["sharpe_ratio"] for r in rows]
        aggregate[sn] = {
            "mean_roi_pct": round(statistics.mean(rois), 2) if rois else None,
            "median_roi_pct": round(statistics.median(rois), 2) if rois else None,
            "positive_roi_windows": sum(1 for x in rois if x > 0),
            "total_windows": len(rois),
            "fixed": {
                "mean_max_drawdown": round(statistics.mean(fixed_dd), 2) if fixed_dd else None,
                "mean_sharpe_ratio": round(statistics.mean(fixed_sharpe), 4) if fixed_sharpe else None,
            },
            "kelly_half": {
                "mean_max_drawdown": round(statistics.mean(kelly_dd), 2) if kelly_dd else None,
                "mean_sharpe_ratio": round(statistics.mean(kelly_sharpe), 4) if kelly_sharpe else None,
            },
        }

    out = {
        "description": "EV strategy rolling comparison (calibration=sigmoid, 15d train / 7d test, 4 windows). ROI, max_drawdown, Sharpe, profit_factor.",
        "calibration": calibration,
        "train_days": 15,
        "test_days": 7,
        "windows": 4,
        "strategies": strategy_names,
        "windows_detail": all_windows,
        "results_by_window_strategy": results_by_window_strategy,
        "aggregate_by_strategy": aggregate,
    }
    out_path = logs_dir / "rolling_ev_strategy_compare.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    print(f"Saved {out_path}")
    print("Aggregate:", aggregate)
    return 0


if __name__ == "__main__":
    sys.exit(main())
