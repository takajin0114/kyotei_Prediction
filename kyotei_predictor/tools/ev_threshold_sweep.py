"""
EV 閾値スイープ。

閾値 1.02, 1.05, 1.08, 1.10, 1.12, 1.15, 1.20 で B案 top_n=5 を比較し、
ROI, hit_rate, bet_count, profit, 平均オッズ を記録して logs/ev_threshold_sweep.json に保存する。
calibration=sigmoid、1 window（train 15日 / test 7日）固定。

実行（プロジェクトルート）:
  PYTHONPATH=. python3 kyotei_predictor/tools/ev_threshold_sweep.py
"""

import json
import os
import sys
from pathlib import Path

_THIS_DIR = Path(__file__).resolve().parent
_PROJECT_ROOT = _THIS_DIR.parent.parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))


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

    train_start, train_end = "2024-06-01", "2024-06-15"
    test_start, test_end = "2024-06-16", "2024-06-22"
    test_dates = _date_range(test_start, test_end)

    thresholds = [1.02, 1.05, 1.08, 1.10, 1.12, 1.15, 1.20]
    top_n = 5

    from kyotei_predictor.application.baseline_train_usecase import run_baseline_train
    from kyotei_predictor.application.baseline_predict_usecase import run_baseline_predict
    from kyotei_predictor.application.verify_usecase import run_verify

    data_source = os.environ.get("KYOTEI_DATA_SOURCE")
    db_path = os.environ.get("KYOTEI_DB_PATH")

    # 1. 学習（sigmoid）
    sweep_pred_dir = outputs_dir / "ev_threshold_sweep"
    sweep_pred_dir.mkdir(exist_ok=True)
    model_path = outputs_dir / "rolling_b_ev_sweep_model.joblib"
    print(f"Training: {train_start} ~ {train_end}, calibration=sigmoid")
    run_baseline_train(
        data_dir=raw_dir,
        model_save_path=model_path,
        max_samples=50000,
        train_start=train_start,
        train_end=train_end,
        data_source=data_source,
        db_path=db_path,
        calibration="sigmoid",
    )

    # 2. 閾値ごとに予測
    for th in thresholds:
        suffix = f"_ev{int(th * 100)}"
        for day in test_dates:
            month = _month_dir(day)
            data_dir_month = raw_dir / month
            if not data_dir_month.exists():
                continue
            out_path = sweep_pred_dir / f"predictions_baseline_{day}{suffix}.json"
            if out_path.exists():
                continue
            try:
                result = run_baseline_predict(
                    model_path=model_path,
                    data_dir=data_dir_month,
                    prediction_date=day,
                    include_selected_bets=True,
                    betting_strategy="top_n_ev",
                    betting_top_n=top_n,
                    betting_score_threshold=None,
                    betting_ev_threshold=th,
                    data_source=data_source,
                    db_path=db_path,
                )
                out_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
            except Exception as e:
                print(f"Predict failed {day} ev{th}: {e}")

    # 3. 閾値ごとに検証集計
    results = []
    for th in thresholds:
        suffix = f"_ev{int(th * 100)}"
        total_bet = 0.0
        total_payout = 0.0
        hit_count = 0
        races_with_result = 0
        odds_sum = 0.0
        odds_count = 0
        for day in test_dates:
            month = _month_dir(day)
            data_dir_month = raw_dir / month
            path = sweep_pred_dir / f"predictions_baseline_{day}{suffix}.json"
            if not path.exists() or not data_dir_month.exists():
                continue
            try:
                summary, _ = run_verify(
                    path,
                    data_dir_month,
                    evaluation_mode="selected_bets",
                    data_source=data_source,
                    db_path=db_path,
                )
                total_bet += summary.get("total_bet") or 0
                total_payout += summary.get("total_payout") or 0
                hit_count += summary.get("hit_count") or 0
                races_with_result += summary.get("races_with_result") or 0
                so, sc = _mean_odds_from_prediction(path)
                odds_sum += so
                odds_count += sc
            except Exception as e:
                print(f"Verify failed {day} ev{th}: {e}")
        roi = round((total_payout / total_bet - 1) * 100, 2) if total_bet else 0.0
        hit_rate = round(hit_count / races_with_result * 100, 2) if races_with_result else 0.0
        bet_count = int(total_bet / 100) if total_bet else 0
        profit = round(total_payout - total_bet, 2)
        mean_odds = round(odds_sum / odds_count, 2) if odds_count else None
        results.append({
            "ev_threshold": th,
            "roi_pct": roi,
            "hit_rate_pct": hit_rate,
            "bet_count": bet_count,
            "profit": profit,
            "total_bet": total_bet,
            "total_payout": total_payout,
            "hit_count": hit_count,
            "races_with_result": races_with_result,
            "mean_odds_placed": mean_odds,
        })
        print(f"EV>{th}: ROI={roi}% hit_rate={hit_rate}% bet_count={bet_count} profit={profit} mean_odds={mean_odds}")

    out = {
        "description": "EV threshold sweep (B top_n=5, calibration=sigmoid, 1 window train 15d / test 7d)",
        "train_start": train_start,
        "train_end": train_end,
        "test_start": test_start,
        "test_end": test_end,
        "calibration": "sigmoid",
        "top_n": top_n,
        "thresholds": thresholds,
        "results": results,
    }
    out_path = logs_dir / "ev_threshold_sweep.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    print(f"Saved {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
