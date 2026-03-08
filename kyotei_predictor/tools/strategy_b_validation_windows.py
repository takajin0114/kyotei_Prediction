"""
主戦略（EV>=1.15 + fixed）の複数 window 再検証。

固定条件: calibration=sigmoid, top_n=5, EV threshold=1.15, bet_sizing=fixed。
各 window で 学習 → 予測 → 検証 を実行し、roi_pct, hit_rate, total_bet, profit, mean_odds_placed 等を記録する。
結果: logs/strategy_b_validation_windows.json

実行（プロジェクトルート）:
  PYTHONPATH=. python3 kyotei_predictor/tools/strategy_b_validation_windows.py
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

from kyotei_predictor.tools.rolling_validation_windows import (
    _date_range,
    _month_dir,
    run_one_window,
)


def _mean_odds_from_prediction(pred_path: Path) -> tuple:
    """予測ファイルから selected_bets の平均オッズを計算。(合計オッズ, 賭け数) を返す。"""
    try:
        data = json.loads(pred_path.read_text(encoding="utf-8"))
    except Exception:
        return 0.0, 0
    predictions = data.get("predictions") or []
    total_odds = 0.0
    count = 0
    for race in predictions:
        selected = race.get("selected_bets") or []
        combs = {str((c.get("combination") or "").strip().replace(" ", "")): c for c in (race.get("all_combinations") or [])}
        for comb in selected:
            c = (comb if isinstance(comb, str) else "").strip().replace(" ", "")
            if not c:
                continue
            cand = combs.get(c)
            if cand is None:
                continue
            odds = cand.get("ratio") or cand.get("odds")
            if odds is not None:
                total_odds += float(odds)
                count += 1
    return total_odds, count


def main() -> int:
    raw_dir = Path("kyotei_predictor/data/raw")
    if not raw_dir.is_dir():
        raw_dir = _PROJECT_ROOT / "kyotei_predictor" / "data" / "raw"
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)
    outputs_dir = Path("outputs")
    outputs_dir.mkdir(exist_ok=True)

    # 4 window（従来と同じ）+ 主戦略のみ + 比較用 EV 1.10
    windows = [
        ("2024-06-01", "2024-06-15", "2024-06-16", "2024-06-22"),
        ("2024-06-08", "2024-06-22", "2024-06-23", "2024-06-29"),
        ("2024-06-15", "2024-06-29", "2024-06-30", "2024-07-06"),
        ("2024-06-22", "2024-07-06", "2024-07-07", "2024-07-13"),
    ]
    strategies = [
        ("B top_n=5 EV>1.15", "top_n_ev", 5, 1.15),
        ("B top_n=5 EV>1.10", "top_n_ev", 5, 1.10),
        ("B ev_threshold_only EV>1.15", "ev_threshold_only", 0, 1.15),
        ("B ev_threshold_only EV>1.20", "ev_threshold_only", 0, 1.20),
    ]

    data_source = os.environ.get("KYOTEI_DATA_SOURCE")
    db_path = os.environ.get("KYOTEI_DB_PATH")
    calibration = "sigmoid"
    seed = 42  # 再現性固定

    pred_dir = outputs_dir / "strategy_b_validation"
    pred_dir.mkdir(exist_ok=True)
    model_path = outputs_dir / "strategy_b_validation_model.joblib"

    all_windows = []
    for i, (ts, te, tst, tend) in enumerate(windows):
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
            seed=seed,
        )
        row["window_id"] = i + 1
        test_dates = _date_range(tst, tend)
        # 各戦略ごとに mean_odds_placed, selected_bets_count を追加
        for r in row["results"]:
            ev_th = r.get("ev_threshold")
            suffix = f"_top5ev{int(ev_th * 100)}" if ev_th else ""
            odds_sum = 0.0
            odds_count = 0
            sb_count = 0
            for day in test_dates:
                month = _month_dir(day)
                path = pred_dir / f"predictions_baseline_{day}{suffix}.json"
                if path.exists():
                    so, sc = _mean_odds_from_prediction(path)
                    odds_sum += so
                    odds_count += sc
                    sb_count += sc
            r["selected_bets_count"] = sb_count
            r["mean_odds_placed"] = round(odds_sum / odds_count, 2) if odds_count else None
            r["profit"] = round((r.get("total_payout") or 0) - (r.get("total_bet") or 0), 2)
        all_windows.append(row)

    # 集約（戦略別）
    strategy_names = [s[0] for s in strategies]
    aggregate = {}
    for sn in strategy_names:
        rois = []
        hr1 = []
        hr3 = []
        tb_total = 0
        tp_total = 0
        hc_total = 0
        profit_total = 0.0
        for w in all_windows:
            for r in w["results"]:
                if r["strategy_name"] == sn:
                    rois.append(r["roi_pct"])
                    if r.get("hit_rate_rank1_pct") is not None:
                        hr1.append(r["hit_rate_rank1_pct"])
                    if r.get("hit_rate_top3_pct") is not None:
                        hr3.append(r["hit_rate_top3_pct"])
                    tb_total += r.get("total_bet") or 0
                    tp_total += r.get("total_payout") or 0
                    hc_total += r.get("hit_count") or 0
                    profit_total += r.get("profit") or 0
                    break
        aggregate[sn] = {
            "mean_roi_pct": round(statistics.mean(rois), 2) if rois else None,
            "median_roi_pct": round(statistics.median(rois), 2) if rois else None,
            "positive_roi_windows": sum(1 for x in rois if x > 0),
            "total_windows": len(rois),
            "mean_hit_rate_rank1_pct": round(statistics.mean(hr1), 2) if hr1 else None,
            "mean_hit_rate_top3_pct": round(statistics.mean(hr3), 2) if hr3 else None,
            "total_bet": tb_total,
            "total_payout": tp_total,
            "hit_count": hc_total,
            "total_profit": round(profit_total, 2),
        }

    out = {
        "description": "主戦略（EV>=1.15 + fixed）の複数 window 再検証。calibration=sigmoid, top_n=5。seed 固定で再現性確保。",
        "calibration": calibration,
        "seed": seed,
        "train_days": 15,
        "test_days": 7,
        "windows": 4,
        "strategies": strategy_names,
        "windows_detail": all_windows,
        "aggregate_by_strategy": aggregate,
    }
    out_path = logs_dir / "strategy_b_validation_windows.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    print(f"Saved {out_path}")
    print("Aggregate:", json.dumps(aggregate, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
