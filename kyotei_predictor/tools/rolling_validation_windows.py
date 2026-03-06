"""
ロールング検証（複数 window）の実行と集計。

train/test を固定長でスライドさせ、各 window で B案を学習・予測・検証する。
改善前（15日学習）と改善後（30日学習）の両方を実行し、before/after 比較結果を保存する。
"""

import json
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

_THIS_DIR = Path(__file__).resolve().parent
_PROJECT_ROOT = _THIS_DIR.parent.parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))


def _date_range(start: str, end: str) -> list:
    """start から end まで（含む）の日付リストを YYYY-MM-DD で返す。"""
    s = datetime.strptime(start, "%Y-%m-%d")
    e = datetime.strptime(end, "%Y-%m-%d")
    out = []
    while s <= e:
        out.append(s.strftime("%Y-%m-%d"))
        s += timedelta(days=1)
    return out


def _month_dir(date_str: str) -> str:
    """日付から月ディレクトリ名を返す（例: 2024-06-15 -> 2024-06）。"""
    return date_str[:7]


def run_one_window(
    train_start: str,
    train_end: str,
    test_start: str,
    test_end: str,
    data_dir_raw: Path,
    model_path: Path,
    out_pred_dir: Path,
    strategies: list,
    train_days: int,
    data_source: Optional[str] = None,
    db_path: Optional[str] = None,
) -> dict:
    """
    1 window 分の学習・予測・検証を行い、戦略別の結果を返す。
    strategies: [(name, strategy, top_n, ev_threshold), ...]
    data_source: "json" | "db" | None。None のときは従来通り JSON 直読。
    """
    import os
    from kyotei_predictor.application.baseline_train_usecase import run_baseline_train
    from kyotei_predictor.application.verify_usecase import run_verify
    from kyotei_predictor.application.baseline_predict_usecase import run_baseline_predict

    ds = data_source or os.environ.get("KYOTEI_DATA_SOURCE") or None
    dbp = db_path

    # 学習（日付フィルタ付き）
    run_baseline_train(
        data_dir=data_dir_raw,
        model_save_path=model_path,
        max_samples=50000,
        train_start=train_start,
        train_end=train_end,
        data_source=ds,
        db_path=dbp,
    )

    test_dates = _date_range(test_start, test_end)
    # 日別に予測: 日付ごとに data_dir は月ディレクトリ
    for day in test_dates:
        month = _month_dir(day)
        data_dir_month = data_dir_raw / month
        if not data_dir_month.exists():
            continue
        for spec_name, strategy, top_n, ev_th in strategies:
            suffix = ""
            if strategy == "top_n_ev":
                suffix = f"_top5ev{int(ev_th * 100)}" if ev_th else ""
            out_path = out_pred_dir / f"predictions_baseline_{day}{suffix}.json"
            if out_path.exists():
                continue
            try:
                result = run_baseline_predict(
                    model_path=model_path,
                    data_dir=data_dir_month,
                    prediction_date=day,
                    include_selected_bets=True,
                    betting_strategy=strategy,
                    betting_top_n=top_n,
                    betting_score_threshold=None,
                    betting_ev_threshold=ev_th,
                    data_source=ds,
                    db_path=dbp,
                )
                with open(out_path, "w", encoding="utf-8") as f:
                    json.dump(result, f, ensure_ascii=False, indent=2)
            except Exception:
                pass

    # 検証集計（戦略別）
    results = []
    for spec_name, strategy, top_n, ev_th in strategies:
        suffix = ""
        if strategy == "top_n_ev":
            suffix = f"_top5ev{int(ev_th * 100)}" if ev_th else ""
        tb = tp = hc = rwr = 0
        for day in test_dates:
            month = _month_dir(day)
            data_dir_month = data_dir_raw / month
            path = out_pred_dir / f"predictions_baseline_{day}{suffix}.json"
            if not path.exists() or not data_dir_month.exists():
                continue
            try:
                summary, _ = run_verify(
                    path,
                    data_dir_month,
                    evaluation_mode="selected_bets",
                    data_source=ds,
                    db_path=dbp,
                )
                tb += summary.get("total_bet") or 0
                tp += summary.get("total_payout") or 0
                hc += summary.get("hit_count") or 0
                rwr += summary.get("races_with_result") or 0
            except Exception:
                continue
        roi = round((tp / tb - 1) * 100, 2) if tb else 0
        hr1 = round(hc / rwr * 100, 2) if rwr else 0
        hr3 = None  # selected_bets 時は別集計が必要なら追加
        results.append({
            "strategy": strategy,
            "strategy_name": spec_name,
            "top_n": top_n,
            "ev_threshold": ev_th,
            "roi_pct": roi,
            "hit_rate_rank1_pct": hr1,
            "hit_rate_top3_pct": hr3,
            "total_bet": tb,
            "total_payout": tp,
            "hit_count": hc,
            "races_with_result": rwr,
        })
    return {
        "train_start": train_start,
        "train_end": train_end,
        "test_start": test_start,
        "test_end": test_end,
        "train_days": train_days,
        "results": results,
    }


def main() -> int:
    raw_dir = Path("kyotei_predictor/data/raw")
    if not raw_dir.is_dir():
        raw_dir = _PROJECT_ROOT / "kyotei_predictor" / "data" / "raw"
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)
    outputs_dir = Path("outputs")
    outputs_dir.mkdir(exist_ok=True)

    # window 定義: train 15日 or 30日、test 7日
    # 各要素: (train_start, train_end, test_start, test_end)
    windows_15d = [
        ("2024-06-01", "2024-06-15", "2024-06-16", "2024-06-22"),
        ("2024-06-08", "2024-06-22", "2024-06-23", "2024-06-29"),
        ("2024-06-15", "2024-06-29", "2024-06-30", "2024-07-06"),
        ("2024-06-22", "2024-07-06", "2024-07-07", "2024-07-13"),
    ]
    # 30日学習: 同じ test に対して train をできるだけ長く（test_start の 30 日前から）
    def extend_train(test_start: str, test_end: str, n_days: int) -> tuple:
        t = datetime.strptime(test_start, "%Y-%m-%d")
        start = (t - timedelta(days=n_days - 1)).strftime("%Y-%m-%d")
        # データがある範囲にクリップ（2024-06-01 以降）
        if start < "2024-06-01":
            start = "2024-06-01"
        end = (datetime.strptime(test_start, "%Y-%m-%d") - timedelta(days=1)).strftime("%Y-%m-%d")
        return (start, end, test_start, test_end)

    windows_30d = [
        extend_train("2024-06-16", "2024-06-22", 30),  # train 06-01~06-15 (15d のみ)
        extend_train("2024-06-23", "2024-06-29", 30),  # train 06-01~06-22 (22d)
        extend_train("2024-06-30", "2024-07-06", 30),  # train 06-01~06-29 (29d)
        extend_train("2024-07-07", "2024-07-13", 30),  # train 06-08~07-06 (29d)
    ]

    strategies = [
        ("B top_n=3", "top_n", 3, None),
        ("B top_n=5 EV>1.10", "top_n_ev", 5, 1.10),
        ("B top_n=5 EV>1.15", "top_n_ev", 5, 1.15),
    ]

    import os as _os
    _data_source = _os.environ.get("KYOTEI_DATA_SOURCE")
    _db_path = _os.environ.get("KYOTEI_DB_PATH")

    # 改善前: 15日学習
    pred_dir_before = outputs_dir / "rolling_windows_15d"
    pred_dir_before.mkdir(exist_ok=True)
    model_path = outputs_dir / "rolling_b_window_model.joblib"
    before_windows = []
    for i, (ts, te, tst, tend) in enumerate(windows_15d):
        print(f"Before window {i+1}: train {ts}~{te} test {tst}~{tend}")
        row = run_one_window(
            train_start=ts,
            train_end=te,
            test_start=tst,
            test_end=tend,
            data_dir_raw=raw_dir,
            model_path=model_path,
            out_pred_dir=pred_dir_before,
            strategies=strategies,
            train_days=15,
            data_source=_data_source,
            db_path=_db_path,
        )
        row["window_id"] = i + 1
        before_windows.append(row)

    # 改善後: 30日学習（同じ test 期間）
    pred_dir_after = outputs_dir / "rolling_windows_30d"
    pred_dir_after.mkdir(exist_ok=True)
    after_windows = []
    for i, (ts, te, tst, tend) in enumerate(windows_30d):
        print(f"After window {i+1}: train {ts}~{te} test {tst}~{tend}")
        row = run_one_window(
            train_start=ts,
            train_end=te,
            test_start=tst,
            test_end=tend,
            data_dir_raw=raw_dir,
            model_path=model_path,
            out_pred_dir=pred_dir_after,
            strategies=strategies,
            train_days=30,
            data_source=_data_source,
            db_path=_db_path,
        )
        row["window_id"] = i + 1
        after_windows.append(row)

    # 戦略別に before/after を集約
    def aggregate_by_strategy(windows_list: list, strategy_name: str) -> dict:
        rois = []
        hr1s = []
        tb_total = 0
        for w in windows_list:
            for r in w["results"]:
                if r["strategy_name"] == strategy_name:
                    rois.append(r["roi_pct"])
                    hr1s.append(r["hit_rate_rank1_pct"])
                    tb_total += r["total_bet"]
                    break
        import statistics
        return {
            "mean_roi_pct": round(statistics.mean(rois), 2) if rois else None,
            "median_roi_pct": round(statistics.median(rois), 2) if rois else None,
            "variance_roi": round(statistics.variance(rois), 2) if len(rois) > 1 else None,
            "mean_hit_rate_rank1_pct": round(statistics.mean(hr1s), 2) if hr1s else None,
            "total_bet": tb_total,
            "positive_roi_windows": sum(1 for x in rois if x > 0),
            "total_windows": len(rois),
        }

    comparison = {
        "before_15d": {s[0]: aggregate_by_strategy(before_windows, s[0]) for s in strategies},
        "after_30d": {s[0]: aggregate_by_strategy(after_windows, s[0]) for s in strategies},
    }

    # 保存
    out_windows = {
        "evaluation_mode": "selected_bets",
        "windows_before_15d": before_windows,
        "windows_after_30d": after_windows,
        "strategies": [s[0] for s in strategies],
    }
    with open(logs_dir / "rolling_validation_b_windows.json", "w", encoding="utf-8") as f:
        json.dump(out_windows, f, ensure_ascii=False, indent=2)

    out_compare = {
        "description": "改善前(15日学習) vs 改善後(30日学習)",
        "before": comparison["before_15d"],
        "after": comparison["after_30d"],
    }
    with open(logs_dir / "rolling_validation_b_before_after.json", "w", encoding="utf-8") as f:
        json.dump(out_compare, f, ensure_ascii=False, indent=2)

    print("Saved logs/rolling_validation_b_windows.json and rolling_validation_b_before_after.json")
    print("Before (15d):", comparison["before_15d"])
    print("After (30d):", comparison["after_30d"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
