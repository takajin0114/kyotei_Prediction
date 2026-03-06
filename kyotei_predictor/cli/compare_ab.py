"""
A/B比較 CLI: 同一条件で A案・B案の予測を検証し、結果を並べて保存する。

既存 verify 基盤を再利用し、model_name, approach, hit_rate, roi_pct 等を一覧する。
"""

import argparse
import csv
import json
import sys
from pathlib import Path

_THIS_DIR = Path(__file__).resolve().parent
_PROJECT_ROOT = _THIS_DIR.parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from kyotei_predictor.infrastructure.path_manager import PROJECT_ROOT
from kyotei_predictor.application.compare_ab_usecase import run_compare_ab


def main() -> int:
    parser = argparse.ArgumentParser(
        description="A案・B案の予測を同一条件で検証し、比較結果を出力する"
    )
    parser.add_argument("--prediction-a", type=Path, required=True, help="A案の予測 JSON パス")
    parser.add_argument("--prediction-b", type=Path, required=True, help="B案の予測 JSON パス")
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=None,
        help="race_data のディレクトリ。未指定時は kyotei_predictor/data/test_raw",
    )
    parser.add_argument(
        "--evaluation-mode",
        type=str,
        choices=("first_only", "selected_bets"),
        default="first_only",
        help="検証モード（両方同じ条件で揃える）",
    )
    parser.add_argument("--name-a", type=str, default="A", help="A案の表示名")
    parser.add_argument("--name-b", type=str, default="B", help="B案の表示名")
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="比較結果の出力先（.json または .csv）。未指定時は outputs/compare_ab.json",
    )
    parser.add_argument(
        "--format",
        type=str,
        choices=("json", "csv"),
        default="json",
        help="出力形式",
    )
    args = parser.parse_args()

    data_dir = args.data_dir or PROJECT_ROOT / "kyotei_predictor" / "data" / "test_raw"
    data_dir = Path(data_dir)
    out_path = args.output or PROJECT_ROOT / "outputs" / "compare_ab.json"
    out_path = Path(out_path)

    if not data_dir.is_dir():
        print(f"エラー: データディレクトリがありません: {data_dir}")
        return 1

    rows = run_compare_ab(
        prediction_a_path=Path(args.prediction_a),
        prediction_b_path=Path(args.prediction_b),
        data_dir=data_dir,
        evaluation_mode=args.evaluation_mode,
        model_name_a=args.name_a,
        model_name_b=args.name_b,
    )

    out_path.parent.mkdir(parents=True, exist_ok=True)
    if args.format == "csv" or str(out_path).endswith(".csv"):
        keys = ["model_name", "approach", "betting_strategy", "evaluation_mode", "hit_rate_rank1_pct", "hit_rate_top3_pct", "roi_pct", "total_bet", "total_payout", "hit_count", "races_with_result", "error"]
        with open(out_path, "w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=keys, extrasaction="ignore")
            w.writeheader()
            w.writerows(rows)
    else:
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(rows, f, ensure_ascii=False, indent=2)

    print(f"比較結果を保存しました: {out_path}")
    for r in rows:
        if "error" in r:
            print(f"  {r.get('model_name')}: エラー - {r['error']}")
        else:
            print(f"  {r.get('model_name')}: hit_rate_1={r.get('hit_rate_rank1_pct')}% roi_pct={r.get('roi_pct')}% hit_count={r.get('hit_count')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
