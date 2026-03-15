"""
EXP-0066: Prediction Diagnostics.

モデル予測の品質を分析し、ROI 改善のボトルネックを特定する。

分析項目:
1. Calibration curve
2. Brier score
3. Log loss
4. EV bucket performance（EV 1.0-1.2, 1.2-1.5, 1.5-2.0, 2.0+ の ROI）

rolling validation n_windows=36 の予測を使用（既存 calib_sigmoid を参照）。
"""

import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

_THIS_DIR = Path(__file__).resolve().parent
_REPO_ROOT = _THIS_DIR.parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

os.environ["KYOTEI_USE_MOTOR_WIN_PROXY"] = os.environ.get("KYOTEI_USE_MOTOR_WIN_PROXY", "1")
os.environ["KYOTEI_FEATURE_SET"] = os.environ.get("KYOTEI_FEATURE_SET", "extended_features")

from kyotei_predictor.tools.rolling_validation_roi import (
    build_windows,
    get_db_date_range,
)
from kyotei_predictor.tools.rolling_validation_windows import _date_range, _month_dir
from kyotei_predictor.application.verify_usecase import run_verify
from kyotei_predictor.domain.verification_models import get_actual_trifecta_from_race_data
from kyotei_predictor.infrastructure.repositories.race_data_repository_factory import (
    get_race_data_repository,
)
from kyotei_predictor.tools.run_exp0042_selection_verified import (
    _all_bets_for_race,
    _resolve_db_path,
)

# EXP-0065 と同じ戦略サフィックス（sigmoid 予測）
STRATEGY_SUFFIX = "_top3ev120_evgap0x07"
TRAIN_DAYS = 30
TEST_DAYS = 7
STEP_DAYS = 7
N_WINDOWS = 36

# EV bucket 境界（EV 別 ROI 用）
EV_BUCKETS: List[Tuple[str, float, float]] = [
    ("EV_1.0_1.2", 1.0, 1.2),
    ("EV_1.2_1.5", 1.2, 1.5),
    ("EV_1.5_2.0", 1.5, 2.0),
    ("EV_2.0_plus", 2.0, 1e9),
]


def _norm(s: str) -> str:
    return (s or "").replace(" ", "")


def _collect_calibration_data(
    out_pred_dir: Path,
    repo,
    need_days: Set[str],
) -> Tuple[List[float], List[float]]:
    """全予測から (y_prob, y_true) を収集。y_true=1 はその組み合わせが本命だった場合。"""
    y_prob: List[float] = []
    y_true: List[float] = []
    for day in sorted(need_days):
        path = out_pred_dir / f"predictions_baseline_{day}{STRATEGY_SUFFIX}.json"
        if not path.exists():
            continue
        try:
            with open(path, encoding="utf-8") as f:
                pred = json.load(f)
        except Exception:
            continue
        prediction_date = pred.get("prediction_date") or day
        predictions_list = pred.get("predictions") or []
        for race in predictions_list:
            venue = race.get("venue") or ""
            rno = int(race.get("race_number") or 0)
            if not venue or rno <= 0:
                continue
            race_data = repo.load_race(prediction_date, venue, rno)
            if race_data is None:
                continue
            actual = get_actual_trifecta_from_race_data(race_data)
            if actual is None:
                continue
            actual_norm = _norm(actual)
            all_comb = race.get("all_combinations") or []
            for c in all_comb:
                prob = c.get("probability") or c.get("score")
                if prob is None:
                    continue
                try:
                    p = float(prob)
                except (TypeError, ValueError):
                    continue
                if p <= 0 or p > 1:
                    continue
                comb_raw = (c.get("combination") or "").strip()
                if not comb_raw:
                    continue
                hit = 1.0 if _norm(comb_raw) == actual_norm else 0.0
                y_prob.append(p)
                y_true.append(hit)
    return y_prob, y_true


def _compute_ev_bucket_roi(
    out_pred_dir: Path,
    repo,
    need_days: Set[str],
) -> List[Dict]:
    """全 bet を EV バケット別に集計し、ROI を返す。"""
    # bucket_name -> (stake_sum, payout_sum, bet_count)
    bucket_stats: Dict[str, Tuple[float, float, int]] = {b[0]: (0.0, 0.0, 0) for b in EV_BUCKETS}
    stake = 100.0
    for day in sorted(need_days):
        path = out_pred_dir / f"predictions_baseline_{day}{STRATEGY_SUFFIX}.json"
        if not path.exists():
            continue
        try:
            with open(path, encoding="utf-8") as f:
                pred = json.load(f)
        except Exception:
            continue
        prediction_date = pred.get("prediction_date") or day
        predictions_list = pred.get("predictions") or []
        for race in predictions_list:
            bets = _all_bets_for_race(race, prediction_date, repo)
            if not bets:
                continue
            for ev, _prob, odds, hit in bets:
                for bucket_name, lo, hi in EV_BUCKETS:
                    if lo <= ev < hi:
                        bucket_stats[bucket_name] = (
                            bucket_stats[bucket_name][0] + stake,
                            bucket_stats[bucket_name][1] + (stake * odds if hit else 0.0),
                            bucket_stats[bucket_name][2] + 1,
                        )
                        break
    out: List[Dict] = []
    for bucket_name, lo, hi in EV_BUCKETS:
        s, p, n = bucket_stats[bucket_name]
        roi = round((p / s - 1) * 100, 2) if s > 0 else None
        out.append({
            "bucket": bucket_name,
            "ev_min": lo,
            "ev_max": hi if hi < 1e8 else None,
            "total_stake": round(s, 2),
            "total_payout": round(p, 2),
            "bet_count": n,
            "ROI_pct": roi,
        })
    return out


def main() -> int:
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--db-path", type=str, default=None)
    parser.add_argument("--output-dir", type=Path, default=None)
    parser.add_argument("--predictions-dir", type=Path, default=None)
    parser.add_argument("--n-windows", type=int, default=N_WINDOWS)
    parser.add_argument("--no-plot", action="store_true", help="Skip calibration plot")
    args = parser.parse_args()

    n_w = args.n_windows
    if n_w <= 0:
        n_w = N_WINDOWS

    db_path_resolved = _resolve_db_path(args.db_path)
    if not db_path_resolved.exists():
        print("[EXP-0066] ERROR: DB not found: {}".format(db_path_resolved), file=sys.stderr)
        return 1
    db_path_str = str(db_path_resolved)
    print("[EXP-0066] DB found: {}".format(db_path_str))

    raw_dir = _REPO_ROOT / "kyotei_predictor" / "data" / "raw"
    if not raw_dir.is_dir():
        raw_dir = Path("kyotei_predictor/data/raw")

    output_dir = args.output_dir or _REPO_ROOT / "outputs" / "prediction_diagnostics"
    output_dir.mkdir(parents=True, exist_ok=True)

    pred_parent = args.predictions_dir or _REPO_ROOT / "outputs" / "calibration_comparison" / "calib_sigmoid"
    out_pred_dir = pred_parent / "rolling_roi_predictions"

    min_date, max_date = get_db_date_range(db_path_str)
    window_list_full = build_windows(
        min_date, max_date, TRAIN_DAYS, TEST_DAYS, STEP_DAYS, n_w
    )
    if len(window_list_full) < n_w:
        n_w = len(window_list_full)
    window_list = list(window_list_full[:n_w])

    need_days: Set[str] = set()
    for _ts, _te, tst, tend in window_list:
        for d in _date_range(tst, tend):
            need_days.add(d)

    if not out_pred_dir.exists():
        print("[EXP-0066] ERROR: Predictions dir not found: {}".format(out_pred_dir), file=sys.stderr)
        print("  Run EXP-0065 first: python3 -m kyotei_predictor.tools.run_exp0065_calibration_comparison --n-windows {}".format(n_w), file=sys.stderr)
        return 1

    repo = get_race_data_repository("db", data_dir=raw_dir, db_path=db_path_str)

    # 1) Brier score & Log loss（日別 run_verify の平均）
    log_loss_list: List[float] = []
    brier_list: List[float] = []
    for day in sorted(need_days):
        path = out_pred_dir / f"predictions_baseline_{day}{STRATEGY_SUFFIX}.json"
        if not path.exists():
            continue
        month = _month_dir(day)
        data_dir_month = raw_dir / month
        try:
            summary, _ = run_verify(
                path,
                data_dir_month,
                evaluation_mode="selected_bets",
                data_source="db",
                db_path=db_path_str,
            )
            if summary.get("log_loss") is not None:
                log_loss_list.append(summary["log_loss"])
            if summary.get("brier_score") is not None:
                brier_list.append(summary["brier_score"])
        except Exception:
            continue

    mean_log_loss = round(sum(log_loss_list) / len(log_loss_list), 6) if log_loss_list else None
    mean_brier_score = round(sum(brier_list) / len(brier_list), 6) if brier_list else None

    # 2) Calibration curve 用データ収集 & プロット
    y_prob, y_true = _collect_calibration_data(out_pred_dir, repo, need_days)
    calibration_plot_path: Optional[str] = None
    if y_prob and not args.no_plot:
        try:
            import numpy as np
            from sklearn.calibration import calibration_curve
            import matplotlib
            matplotlib.use("Agg")
            import matplotlib.pyplot as plt

            prob_true, prob_pred = calibration_curve(y_true, y_prob, n_bins=10)
            fig, ax = plt.subplots(figsize=(6, 5))
            ax.plot([0, 1], [0, 1], "k--", label="Perfect")
            ax.plot(prob_pred, prob_true, "s-", label="Model (n_w={})".format(n_w))
            ax.set_xlabel("Mean predicted probability")
            ax.set_ylabel("Fraction of positives")
            ax.set_title("Calibration curve (EXP-0066)")
            ax.legend()
            ax.grid(True, alpha=0.3)
            plot_path = output_dir / "exp0066_calibration_curve.png"
            fig.savefig(plot_path, dpi=120, bbox_inches="tight")
            plt.close()
            calibration_plot_path = str(plot_path)
            print("[EXP-0066] Saved calibration plot: {}".format(calibration_plot_path))
        except Exception as e:
            print("[EXP-0066] WARNING: Calibration plot failed: {}".format(e), file=sys.stderr)

    # 3) EV bucket ROI
    ev_bucket_results = _compute_ev_bucket_roi(out_pred_dir, repo, need_days)

    payload = {
        "experiment_id": "EXP-0066",
        "purpose": "Prediction diagnostics: calibration, Brier, log loss, EV bucket ROI. n_w=36.",
        "db_path_used": db_path_str,
        "n_windows": n_w,
        "predictions_source": str(out_pred_dir),
        "brier_score": mean_brier_score,
        "log_loss": mean_log_loss,
        "calibration_plot_path": calibration_plot_path,
        "ev_bucket_roi": ev_bucket_results,
    }

    out_path = output_dir / "exp0066_prediction_diagnostics.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    print("Saved {}".format(out_path))

    print("\n--- EXP-0066 Prediction Diagnostics (n_windows={}) ---".format(n_w))
    print("Brier score:  {}".format(mean_brier_score))
    print("Log loss:     {}".format(mean_log_loss))
    print("Calibration:  {}".format(calibration_plot_path or "(no plot)"))
    print("\nEV bucket ROI:")
    for r in ev_bucket_results:
        print("  {}  ROI={}%  bet_count={}  stake={}".format(
            r["bucket"],
            r["ROI_pct"] if r["ROI_pct"] is not None else "—",
            r["bet_count"],
            r["total_stake"],
        ))

    return 0


if __name__ == "__main__":
    sys.exit(main())
