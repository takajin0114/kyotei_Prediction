"""
時系列分離検証の集計スクリプト。

指定期間の日別予測ファイルを verify し、合算して JSON に保存する。
B案ロールング検証（train 2024-06 / test 2024-07）の結果集計に使用。
"""

import json
import sys
from pathlib import Path

_THIS_DIR = Path(__file__).resolve().parent
_PROJECT_ROOT = _THIS_DIR.parent.parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from kyotei_predictor.application.verify_usecase import run_verify


def aggregate_period(
    dates: list,
    data_dir: Path,
    spec_name: str,
    path_fn,
    strategy: str,
    top_n: int,
    ev_threshold: float = None,
) -> dict:
    """
    日別に verify して合算し、1件の結果辞書を返す。
    """
    tb = tp = hc = rwr = 0
    for day in dates:
        path = path_fn(day)
        if not path.exists():
            continue
        try:
            summary, _ = run_verify(path, data_dir, evaluation_mode="selected_bets")
            tb += summary.get("total_bet") or 0
            tp += summary.get("total_payout") or 0
            hc += summary.get("hit_count") or 0
            rwr += summary.get("races_with_result") or 0
        except Exception:
            continue
    roi = round((tp / tb - 1) * 100, 2) if tb else 0
    hr1 = round(hc / rwr * 100, 2) if rwr else 0
    # hit_rate_top3 は summary に含まれるが selected_bets 時は total と異なるので簡易に hr1 ベースで
    return {
        "strategy": strategy,
        "strategy_name": spec_name,
        "top_n": top_n,
        "ev_threshold": ev_threshold,
        "roi_pct": roi,
        "hit_rate_rank1_pct": hr1,
        "hit_rate_top3_pct": None,  # 必要なら日別から集計
        "total_bet": tb,
        "total_payout": tp,
        "hit_count": hc,
        "races_with_result": rwr,
    }


def main() -> int:
    data_dir_july = Path("kyotei_predictor/data/raw/2024-07")
    if not data_dir_july.is_dir():
        data_dir_july = _PROJECT_ROOT / "kyotei_predictor" / "data" / "raw" / "2024-07"
    july_dates = [f"2024-07-{d:02d}" for d in range(1, 32)]
    out_dir = Path("outputs/rolling_train202406")
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)

    specs = [
        (
            "B top_n=3",
            lambda d: out_dir / f"predictions_baseline_{d}.json",
            "top_n",
            3,
            None,
        ),
        (
            "B top_n=5 EV>1.05",
            lambda d: out_dir / f"predictions_baseline_{d}_top5ev105.json",
            "top_n_ev",
            5,
            1.05,
        ),
        (
            "B top_n=10 EV>1.10",
            lambda d: out_dir / f"predictions_baseline_{d}_top10ev110.json",
            "top_n_ev",
            10,
            1.10,
        ),
    ]

    results = []
    for spec_name, path_fn, strategy, top_n, ev_th in specs:
        row = aggregate_period(
            july_dates,
            data_dir_july,
            spec_name,
            path_fn,
            strategy=strategy,
            top_n=top_n,
            ev_threshold=ev_th,
        )
        row["train_period"] = "2024-06-01 to 2024-06-30"
        row["test_period"] = "2024-07-01 to 2024-07-31"
        results.append(row)

    out = {
        "train_period": "2024-06-01 to 2024-06-30",
        "test_period": "2024-07-01 to 2024-07-31",
        "evaluation_mode": "selected_bets",
        "model_note": "B案を6月データのみで学習（baseline_b_train202406.joblib）",
        "results": results,
    }

    out_path = logs_dir / "rolling_validation_b_202406_202407.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    print(f"Saved: {out_path}")
    for r in results:
        print(r["strategy_name"], "roi_pct=", r["roi_pct"], "total_bet=", r["total_bet"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
