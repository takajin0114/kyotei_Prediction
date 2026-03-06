"""
60日（2024-06-01〜07-31）の B案 top_n=5 EV閾値比較を集計する。

既存の日別予測（outputs/predictions_baseline_*_top5ev*.json）を verify して合算し、
logs/ev_threshold_comparison_60day.json に保存する。
"""

import json
import sys
from pathlib import Path

_THIS_DIR = Path(__file__).resolve().parent
_PROJECT_ROOT = _THIS_DIR.parent.parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from kyotei_predictor.application.verify_usecase import run_verify


def main() -> int:
    june_dir = Path("kyotei_predictor/data/raw/2024-06")
    july_dir = Path("kyotei_predictor/data/raw/2024-07")
    if not june_dir.is_dir():
        june_dir = _PROJECT_ROOT / "kyotei_predictor" / "data" / "raw" / "2024-06"
    if not july_dir.is_dir():
        july_dir = _PROJECT_ROOT / "kyotei_predictor" / "data" / "raw" / "2024-07"
    out_dir = Path("outputs")
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)

    # B top_n=5 EV 1.02, 1.05, 1.10, 1.15
    specs = [
        ("B top_n=5 EV>1.02", 1.02, lambda d, m: out_dir / f"predictions_baseline_{d}_top5ev102.json"),
        ("B top_n=5 EV>1.05", 1.05, lambda d, m: out_dir / f"predictions_baseline_{d}_top5ev105.json"),
        ("B top_n=5 EV>1.10", 1.10, lambda d, m: out_dir / f"predictions_baseline_{d}_top5ev110.json"),
        ("B top_n=5 EV>1.15", 1.15, lambda d, m: out_dir / f"predictions_baseline_{d}_top5ev115.json"),
    ]

    june_dates = [f"2024-06-{d:02d}" for d in range(1, 31)]
    july_dates = [f"2024-07-{d:02d}" for d in range(1, 32)]

    results = []
    for spec_name, ev_th, path_fn in specs:
        tb = tp = hc = rwr = 0
        for day in june_dates:
            path = path_fn(day, "06")
            if not path.exists():
                continue
            try:
                summary, _ = run_verify(path, june_dir, evaluation_mode="selected_bets")
                tb += summary.get("total_bet") or 0
                tp += summary.get("total_payout") or 0
                hc += summary.get("hit_count") or 0
                rwr += summary.get("races_with_result") or 0
            except Exception:
                continue
        for day in july_dates:
            path = path_fn(day, "07")
            if not path.exists():
                continue
            try:
                summary, _ = run_verify(path, july_dir, evaluation_mode="selected_bets")
                tb += summary.get("total_bet") or 0
                tp += summary.get("total_payout") or 0
                hc += summary.get("hit_count") or 0
                rwr += summary.get("races_with_result") or 0
            except Exception:
                continue
        roi = round((tp / tb - 1) * 100, 2) if tb else 0
        hr1 = round(hc / rwr * 100, 2) if rwr else 0
        results.append({
            "strategy_name": spec_name,
            "ev_threshold": ev_th,
            "roi_pct": roi,
            "hit_rate_rank1_pct": hr1,
            "hit_rate_top3_pct": None,
            "total_bet": tb,
            "total_payout": tp,
            "hit_count": hc,
            "races_with_result": rwr,
            "number_of_selected_bets": int(tb / 100) if tb else 0,
        })

    out = {
        "period": "2024-06-01 to 2024-07-31",
        "evaluation_mode": "selected_bets",
        "model_note": "B案 baseline_b_abtest.joblib（7月中心学習想定）",
        "ev_threshold_comparison": results,
    }
    out_path = logs_dir / "ev_threshold_comparison_60day.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    print(f"Saved: {out_path}")
    for r in results:
        print(r["strategy_name"], "roi_pct=", r["roi_pct"], "total_bet=", r["total_bet"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
