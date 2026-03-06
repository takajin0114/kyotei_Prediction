"""
特徴量 1 つ追加の before/after 比較用ロールング検証。

KYOTEI_USE_MOTOR_WIN_PROXY=0（従来）と =1（モーター勝率代理あり）で、
同じ 15日学習・7日検証の 4 window を実行し、結果を比較する。
出力: logs/rolling_validation_feature_before_after.json

実行方法（プロジェクトルートで）:
  PYTHONPATH=. python3 kyotei_predictor/tools/rolling_validation_feature.py
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


def aggregate_by_strategy(windows_list: list, strategy_name: str) -> dict:
    """戦略名で window 結果を集約する。"""
    rois = []
    hr1s = []
    hr3s = []
    tb_total = 0
    tp_total = 0
    hc_total = 0
    for w in windows_list:
        for r in w["results"]:
            if r["strategy_name"] == strategy_name:
                rois.append(r["roi_pct"])
                if r.get("hit_rate_rank1_pct") is not None:
                    hr1s.append(r["hit_rate_rank1_pct"])
                if r.get("hit_rate_top3_pct") is not None:
                    hr3s.append(r["hit_rate_top3_pct"])
                tb_total += r.get("total_bet") or 0
                tp_total += r.get("total_payout") or 0
                hc_total += r.get("hit_count") or 0
                break
    return {
        "mean_roi_pct": round(statistics.mean(rois), 2) if rois else None,
        "median_roi_pct": round(statistics.median(rois), 2) if rois else None,
        "variance_roi": round(statistics.variance(rois), 2) if len(rois) > 1 else None,
        "mean_hit_rate_rank1_pct": round(statistics.mean(hr1s), 2) if hr1s else None,
        "mean_hit_rate_top3_pct": round(statistics.mean(hr3s), 2) if hr3s else None,
        "total_bet": tb_total,
        "total_payout": tp_total,
        "hit_count": hc_total,
        "positive_roi_windows": sum(1 for x in rois if x > 0),
        "total_windows": len(rois),
    }


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

    _data_source = os.environ.get("KYOTEI_DATA_SOURCE")
    _db_path = os.environ.get("KYOTEI_DB_PATH")

    # --- Before: モーター勝率代理なし (KYOTEI_USE_MOTOR_WIN_PROXY=0) ---
    os.environ["KYOTEI_USE_MOTOR_WIN_PROXY"] = "0"
    pred_dir_before = outputs_dir / "rolling_windows_15d_feature_before"
    pred_dir_before.mkdir(exist_ok=True)
    model_path_before = outputs_dir / "rolling_b_feature_before.joblib"
    before_windows = []
    for i, (ts, te, tst, tend) in enumerate(windows_15d):
        print(f"[Before] window {i+1}: train {ts}~{te} test {tst}~{tend}")
        row = run_one_window(
            train_start=ts,
            train_end=te,
            test_start=tst,
            test_end=tend,
            data_dir_raw=raw_dir,
            model_path=model_path_before,
            out_pred_dir=pred_dir_before,
            strategies=strategies,
            train_days=15,
            data_source=_data_source,
            db_path=_db_path,
        )
        row["window_id"] = i + 1
        before_windows.append(row)

    # --- After: モーター勝率代理あり (KYOTEI_USE_MOTOR_WIN_PROXY=1) ---
    os.environ["KYOTEI_USE_MOTOR_WIN_PROXY"] = "1"
    pred_dir_after = outputs_dir / "rolling_windows_15d_feature_after"
    pred_dir_after.mkdir(exist_ok=True)
    model_path_after = outputs_dir / "rolling_b_feature_after.joblib"
    after_windows = []
    for i, (ts, te, tst, tend) in enumerate(windows_15d):
        print(f"[After] window {i+1}: train {ts}~{te} test {tst}~{tend}")
        row = run_one_window(
            train_start=ts,
            train_end=te,
            test_start=tst,
            test_end=tend,
            data_dir_raw=raw_dir,
            model_path=model_path_after,
            out_pred_dir=pred_dir_after,
            strategies=strategies,
            train_days=15,
            data_source=_data_source,
            db_path=_db_path,
        )
        row["window_id"] = i + 1
        after_windows.append(row)

    # 戦略別集約
    comparison_before = {s[0]: aggregate_by_strategy(before_windows, s[0]) for s in strategies}
    comparison_after = {s[0]: aggregate_by_strategy(after_windows, s[0]) for s in strategies}

    out = {
        "description": "特徴量1つ追加の before/after（15日学習・7日検証・4 window）",
        "feature_flag": "KYOTEI_USE_MOTOR_WIN_PROXY",
        "before_label": "0 (従来・モーター勝率代理なし)",
        "after_label": "1 (モーター勝率代理あり)",
        "train_days": 15,
        "test_days": 7,
        "windows": 4,
        "before": comparison_before,
        "after": comparison_after,
        "windows_before": before_windows,
        "windows_after": after_windows,
        "strategies": [s[0] for s in strategies],
    }
    out_path = logs_dir / "rolling_validation_feature_before_after.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)

    print(f"Saved {out_path}")
    print("Before:", comparison_before)
    print("After:", comparison_after)
    return 0


if __name__ == "__main__":
    sys.exit(main())
