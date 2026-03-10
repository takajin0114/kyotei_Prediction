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
    calibration: Optional[str] = None,
    model_type: Optional[str] = None,
    feature_set: Optional[str] = None,
    seed: Optional[int] = 42,
) -> dict:
    """
    1 window 分の学習・予測・検証を行い、戦略別の結果を返す。
    strategies: [(name, strategy, top_n, ev_threshold), ...]
    data_source: "json" | "db" | None。None のときは従来通り JSON 直読。
    calibration: "none" | "sigmoid" | "isotonic"。None のときは "none"。
    model_type: "sklearn" | "lightgbm" | "xgboost"。None のときは "sklearn"。
    feature_set: 特徴量セット。None のときは環境変数に従う。
    seed: 乱数シード。再現性用。None のときは 42。
    """
    import os
    from kyotei_predictor.application.baseline_train_usecase import run_baseline_train
    from kyotei_predictor.application.verify_usecase import run_verify
    from kyotei_predictor.application.baseline_predict_usecase import run_baseline_predict

    ds = data_source or os.environ.get("KYOTEI_DATA_SOURCE") or None
    dbp = db_path
    calib = calibration or "none"
    mtype = model_type or "sklearn"
    if seed is None:
        seed = 42

    # 学習（日付フィルタ付き・キャリブレーション・model_type・feature_set・seed 指定可）
    run_baseline_train(
        data_dir=data_dir_raw,
        model_save_path=model_path,
        max_samples=50000,
        train_start=train_start,
        train_end=train_end,
        data_source=ds,
        db_path=dbp,
        calibration=calib,
        model_type=mtype,
        feature_set=feature_set,
        seed=seed,
    )

    def _normalize_spec(s):
        # (name, strategy, top_n, ev_threshold[, ... [, odds_low, odds_high[, max_bets_per_race]]])
        if len(s) >= 11:
            return s[0], s[1], s[2], s[3], s[4], s[5], s[6], s[7], s[8], s[9], s[10]
        if len(s) >= 10:
            return s[0], s[1], s[2], s[3], s[4], s[5], s[6], s[7], s[8], s[9], None
        if len(s) >= 8:
            return s[0], s[1], s[2], s[3], s[4], s[5], s[6], s[7], None, None, None
        if len(s) >= 7:
            return s[0], s[1], s[2], s[3], s[4], s[5], s[6], None, None, None, None
        if len(s) >= 5:
            return s[0], s[1], s[2], s[3], s[4], None, None, None, None, None, None
        return s[0], s[1], s[2], s[3], None, None, None, None, None, None, None

    def _suffix_for_strategy(strategy, top_n, ev_th, confidence_type, prob_gap_min=None, entropy_max=None, ev_gap_threshold=None, odds_low=None, odds_high=None, max_bets_per_race=None):
        if strategy == "top_n_ev":
            return f"_top{top_n}ev{int(ev_th * 100)}" if ev_th else ""
        if strategy == "top_n_ev_gap_filter":
            g = ev_gap_threshold if ev_gap_threshold is not None else 0.05
            gstr = str(g).replace(".", "x")
            return f"_top{top_n}ev{int(ev_th * 100)}_evgap{gstr}" if ev_th else f"_top{top_n}_evgap{gstr}"
        if strategy == "top_n_ev_gap_filter_entropy":
            g = ev_gap_threshold if ev_gap_threshold is not None else 0.07
            gstr = str(g).replace(".", "x")
            ent = entropy_max if entropy_max is not None else 1.5
            estr = str(ent).replace(".", "x")
            return f"_top{top_n}ev{int(ev_th * 100)}_evgap{gstr}_ent{estr}" if ev_th else f"_top{top_n}_evgap{gstr}_ent{estr}"
        if strategy == "top_n_ev_gap_filter_odds_band":
            g = ev_gap_threshold if ev_gap_threshold is not None else 0.07
            gstr = str(g).replace(".", "x")
            lo = odds_low if odds_low is not None else 1.2
            hi = odds_high if odds_high is not None else 25
            return f"_top{top_n}ev{int(ev_th * 100)}_evgap{gstr}_odds{str(lo).replace('.', 'x')}_{int(hi)}"
        if strategy == "top_n_ev_gap_filter_odds_band_bet_limit":
            g = ev_gap_threshold if ev_gap_threshold is not None else 0.07
            gstr = str(g).replace(".", "x")
            lo = odds_low if odds_low is not None else 1.3
            hi = odds_high if odds_high is not None else 25
            mx = max_bets_per_race if max_bets_per_race is not None else 1
            return f"_top{top_n}ev{int(ev_th * 100)}_evgap{gstr}_odds{str(lo).replace('.', 'x')}_{int(hi)}_max{mx}"
        if strategy == "top_n_ev_conditional_prob_gap":
            if isinstance(prob_gap_min, (list, tuple)) and prob_gap_min:
                parts = [str(round(e, 2)).replace(".", "x") for e in prob_gap_min]
                return "_condpg_" + "_".join(parts)
            return "_condpg"
        if strategy == "top_n_ev_confidence":
            base = f"_top{top_n}ev{int(ev_th * 100)}" if ev_th else ""
            conf = (confidence_type or "pred_prob").replace(" ", "_")
            return f"{base}_conf_{conf}"
        if strategy == "race_filtered_top_n_ev":
            base = f"_racefilter_top{top_n}ev{int(ev_th * 100)}" if ev_th else ""
            pg = int((prob_gap_min or 0.05) * 100)
            ent = int((entropy_max or 1.7) * 10)
            return f"{base}_pg{pg}_ent{ent}"
        if strategy == "top_n_ev_prob_pool":
            pk = int(prob_gap_min or 5) if prob_gap_min is not None else 5  # 5th element is pool_k for this strategy
            base = f"_probpool_k{pk}_top{top_n}ev{int(ev_th * 100)}" if ev_th else f"_probpool_k{pk}_top{top_n}"
            if confidence_type:
                conf = (confidence_type or "").replace(" ", "_")
                return f"{base}_conf_{conf}"
            return base
        if strategy == "top_n_ev_power_prob":
            al = prob_gap_min if prob_gap_min is not None else 1.0  # 6th element is alpha for this strategy
            astr = str(al).replace(".", "x")
            return f"_powerprob_a{astr}_top{top_n}ev{int(ev_th * 100)}" if ev_th else f"_powerprob_a{astr}_top{top_n}"
        if strategy == "ev_threshold_only":
            return f"_evonly{int(ev_th * 100)}" if ev_th else ""
        return ""

    test_dates = _date_range(test_start, test_end)
    # 日別に予測: 日付ごとに data_dir は月ディレクトリ
    for day in test_dates:
        month = _month_dir(day)
        data_dir_month = data_dir_raw / month
        if not data_dir_month.exists():
            continue
        for spec in strategies:
            norm = _normalize_spec(spec)
            spec_name, strategy, top_n, ev_th, confidence_type, prob_gap_min, entropy_max = norm[0], norm[1], norm[2], norm[3], norm[4], norm[5], norm[6]
            ev_gap_th = norm[7] if len(norm) >= 8 else None
            odds_lo, odds_hi = (norm[8], norm[9]) if len(norm) >= 10 else (None, None)
            max_bpr = norm[10] if len(norm) >= 11 else None
            suffix = _suffix_for_strategy(strategy, top_n, ev_th, confidence_type, prob_gap_min, entropy_max, ev_gap_th, odds_lo, odds_hi, max_bpr)
            out_path = out_pred_dir / f"predictions_baseline_{day}{suffix}.json"
            if out_path.exists():
                continue
            try:
                run_kw: dict = {
                    "model_path": model_path,
                    "data_dir": data_dir_month,
                    "prediction_date": day,
                    "include_selected_bets": True,
                    "betting_strategy": strategy,
                    "betting_top_n": top_n,
                    "betting_score_threshold": None,
                    "betting_ev_threshold": ev_th,
                    "betting_confidence_type": confidence_type,
                    "data_source": ds,
                    "db_path": dbp,
                    "feature_set": feature_set,
                }
                if strategy == "top_n_ev_prob_pool":
                    run_kw["betting_pool_k"] = int(prob_gap_min) if prob_gap_min is not None else 5
                elif strategy == "top_n_ev_power_prob":
                    run_kw["betting_alpha"] = float(prob_gap_min) if prob_gap_min is not None else 1.0
                elif strategy == "top_n_ev_gap_filter":
                    run_kw["betting_ev_gap_threshold"] = float(ev_gap_th) if ev_gap_th is not None else 0.05
                elif strategy == "top_n_ev_gap_filter_entropy":
                    run_kw["betting_ev_gap_threshold"] = float(ev_gap_th) if ev_gap_th is not None else 0.07
                    run_kw["betting_entropy_threshold"] = float(entropy_max) if entropy_max is not None else 1.5
                elif strategy == "top_n_ev_gap_filter_odds_band":
                    run_kw["betting_ev_gap_threshold"] = float(ev_gap_th) if ev_gap_th is not None else 0.07
                    if odds_lo is not None:
                        run_kw["betting_odds_low"] = float(odds_lo)
                    if odds_hi is not None:
                        run_kw["betting_odds_high"] = float(odds_hi)
                elif strategy == "top_n_ev_gap_filter_odds_band_bet_limit":
                    run_kw["betting_ev_gap_threshold"] = float(ev_gap_th) if ev_gap_th is not None else 0.07
                    if odds_lo is not None:
                        run_kw["betting_odds_low"] = float(odds_lo)
                    if odds_hi is not None:
                        run_kw["betting_odds_high"] = float(odds_hi)
                    if max_bpr is not None:
                        run_kw["betting_max_bets_per_race"] = int(max_bpr)
                elif strategy == "top_n_ev_conditional_prob_gap" and isinstance(prob_gap_min, (list, tuple)) and isinstance(entropy_max, (list, tuple)):
                    run_kw["betting_band_edges"] = list(prob_gap_min)
                    run_kw["betting_band_params"] = list(entropy_max)
                else:
                    run_kw["betting_prob_gap_min"] = prob_gap_min
                    run_kw["betting_entropy_max"] = entropy_max
                result = run_baseline_predict(**run_kw)
                with open(out_path, "w", encoding="utf-8") as f:
                    json.dump(result, f, ensure_ascii=False, indent=2)
            except Exception:
                pass

    # 検証集計（戦略別）: selected_bets 用メトリクスを優先
    results = []
    for spec in strategies:
        norm = _normalize_spec(spec)
        spec_name, strategy, top_n, ev_th, confidence_type, prob_gap_min, entropy_max = norm[0], norm[1], norm[2], norm[3], norm[4], norm[5], norm[6]
        ev_gap_th = norm[7] if len(norm) >= 8 else None
        odds_lo, odds_hi = (norm[8], norm[9]) if len(norm) >= 10 else (None, None)
        max_bpr = norm[10] if len(norm) >= 11 else None
        suffix = _suffix_for_strategy(strategy, top_n, ev_th, confidence_type, prob_gap_min, entropy_max, ev_gap_th, odds_lo, odds_hi, max_bpr)
        tb_sel = tp_sel = sc = rwr = hc = om = rwsb = 0
        log_loss_list = []
        brier_list = []
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
                tb_sel += summary.get("total_bet_selected") or 0
                tp_sel += summary.get("total_payout_selected") or 0
                sc += summary.get("selected_bets_total_count") or 0
                rwr += summary.get("races_with_result") or 0
                hc += summary.get("hit_count") or 0
                om += summary.get("odds_missing_count") or 0
                rwsb += summary.get("races_with_selected_bets") or 0
                if summary.get("log_loss") is not None:
                    log_loss_list.append(summary["log_loss"])
                if summary.get("brier_score") is not None:
                    brier_list.append(summary["brier_score"])
            except Exception:
                continue
        roi_sel = round((tp_sel / tb_sel - 1) * 100, 2) if tb_sel else 0.0
        hr1 = round(hc / rwr * 100, 2) if rwr else 0.0
        profit = round(tp_sel - tb_sel, 2) if tb_sel else 0.0
        mean_log_loss = round(sum(log_loss_list) / len(log_loss_list), 6) if log_loss_list else None
        mean_brier = round(sum(brier_list) / len(brier_list), 6) if brier_list else None
        results.append({
            "strategy": strategy,
            "strategy_name": spec_name,
            "top_n": top_n,
            "ev_threshold": ev_th,
            "roi_pct": roi_sel,
            "roi_selected": roi_sel,
            "hit_rate": hr1,
            "hit_rate_rank1_pct": hr1,
            "hit_rate_top3_pct": None,
            "total_bet": tb_sel,
            "total_payout": tp_sel,
            "total_bet_selected": tb_sel,
            "total_payout_selected": tp_sel,
            "selected_bets_count": sc,
            "selected_bets_total_count": sc,
            "odds_missing_count": om,
            "profit": profit,
            "hit_count": hc,
            "races_with_result": rwr,
            "races_with_selected_bets": rwsb,
            "log_loss": mean_log_loss,
            "brier_score": mean_brier,
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
