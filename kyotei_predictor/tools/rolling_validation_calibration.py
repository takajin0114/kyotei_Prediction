"""
確率キャリブレーションの before/after 比較用ロールング検証。

calibration=none / sigmoid / isotonic のそれぞれで、
同じ 15日学習・7日検証の 4 window を実行し、結果を比較する。
出力: logs/rolling_validation_calibration_before_after.json

実行方法（プロジェクトルートで）:
  PYTHONPATH=. python3 kyotei_predictor/tools/rolling_validation_calibration.py
"""

import json
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

    import os as _os
    _data_source = _os.environ.get("KYOTEI_DATA_SOURCE")
    _db_path = _os.environ.get("KYOTEI_DB_PATH")

    # 比較するキャリブレーション種別（none = before、sigmoid / isotonic = after）
    calibration_types = ["none", "sigmoid", "isotonic"]
    all_results = {}
    all_windows = {}

    for calib in calibration_types:
        pred_dir = outputs_dir / f"rolling_windows_15d_calib_{calib}"
        pred_dir.mkdir(exist_ok=True)
        model_path = outputs_dir / f"rolling_b_calib_{calib}.joblib"
        windows_list = []
        for i, (ts, te, tst, tend) in enumerate(windows_15d):
            print(f"[calibration={calib}] window {i+1}: train {ts}~{te} test {tst}~{tend}")
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
                data_source=_data_source,
                db_path=_db_path,
                calibration=calib,
            )
            row["window_id"] = i + 1
            windows_list.append(row)
        comparison = {s[0]: aggregate_by_strategy(windows_list, s[0]) for s in strategies}
        all_results[calib] = comparison
        all_windows[calib] = windows_list

    # 比較サマリ（EV>1.10 / 1.15 の最適設定検討用）
    comparison_summary = []
    for calib in calibration_types:
        for strategy_name in [s[0] for s in strategies]:
            r = all_results[calib].get(strategy_name, {})
            comparison_summary.append({
                "calibration": calib,
                "strategy": strategy_name,
                "mean_roi_pct": r.get("mean_roi_pct"),
                "median_roi_pct": r.get("median_roi_pct"),
                "positive_roi_windows": r.get("positive_roi_windows"),
                "total_windows": r.get("total_windows"),
                "mean_hit_rate_rank1_pct": r.get("mean_hit_rate_rank1_pct"),
                "total_bet": r.get("total_bet"),
            })

    out = {
        "description": "確率キャリブレーションの比較（15日学習・7日検証・4 window）。EV>1.10/1.15 の最適 calibration を決める用。",
        "train_days": 15,
        "test_days": 7,
        "windows": 4,
        "comparison_summary": comparison_summary,
        "calibration_none": all_results["none"],
        "calibration_sigmoid": all_results["sigmoid"],
        "calibration_isotonic": all_results["isotonic"],
        "windows_none": all_windows["none"],
        "windows_sigmoid": all_windows["sigmoid"],
        "windows_isotonic": all_windows["isotonic"],
        "strategies": [s[0] for s in strategies],
    }
    for filename in ["rolling_validation_calibration_before_after.json", "rolling_validation_calibration_compare.json"]:
        out_path = logs_dir / filename
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(out, f, ensure_ascii=False, indent=2)
        print(f"Saved {out_path}")
    print("calibration=none:", all_results["none"])
    print("calibration=sigmoid:", all_results["sigmoid"])
    print("calibration=isotonic:", all_results["isotonic"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
