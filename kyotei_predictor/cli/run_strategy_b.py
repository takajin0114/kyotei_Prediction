"""
主戦略（baseline B + sigmoid + top_n=5 + EV>=1.15 + fixed）の 1 本実行 CLI。

学習 → 予測 → 検証 → サマリ保存 を一括実行する。
未指定の引数は config の主戦略に合わせる（本 CLI は主戦略固定のため上書きオプションは持たない）。
"""

import argparse
import json
import sys
from pathlib import Path

_THIS_DIR = Path(__file__).resolve().parent
_PROJECT_ROOT = _THIS_DIR.parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from kyotei_predictor.infrastructure.path_manager import PROJECT_ROOT
from kyotei_predictor.application.run_strategy_b_usecase import run_strategy_b


def main() -> int:
    parser = argparse.ArgumentParser(
        description="主戦略で 学習→予測→検証 を一括実行し、サマリを保存する（baseline B + sigmoid + EV>=1.15 + fixed）"
    )
    parser.add_argument("--train-start", type=str, required=True, help="学習開始日 YYYY-MM-DD")
    parser.add_argument("--train-end", type=str, required=True, help="学習終了日 YYYY-MM-DD")
    parser.add_argument("--predict-date", type=str, required=True, help="予測対象日 YYYY-MM-DD")
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=None,
        help="生データルート（月別 YYYY-MM サブディレクトリ想定）。未指定時は kyotei_predictor/data/raw",
    )
    parser.add_argument(
        "--model-path",
        type=Path,
        default=None,
        help="モデル保存先。未指定時は --output 配下の strategy_b_model.joblib",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="予測・サマリの出力先ディレクトリ。未指定時は data-dir の親の outputs/strategy_b",
    )
    parser.add_argument(
        "--data-source",
        type=str,
        choices=("json", "db"),
        default=None,
        help="レースデータ読込元。未指定時は JSON 直読",
    )
    parser.add_argument("--db-path", type=Path, default=None, help="data-source=db 時の SQLite パス")
    parser.add_argument("--seed", type=int, default=42, help="乱数シード。再現性用。未指定時は 42。")
    parser.add_argument("--max-samples", type=int, default=50000, help="最大学習サンプル数。sample-mode=all のときは無視。")
    parser.add_argument(
        "--sample-mode",
        type=str,
        choices=("head", "random", "all"),
        default="head",
        help="学習サンプル抽出: head=先頭から, random=seed固定ランダム, all=期間内全件",
    )
    parser.add_argument(
        "--save-summary-to",
        type=Path,
        default=None,
        help="サマリ JSON の保存先（ファイルパス）。未指定時は output/strategy_b_summary_<predict_date>.json",
    )
    args = parser.parse_args()

    data_dir = args.data_dir or PROJECT_ROOT / "kyotei_predictor" / "data" / "raw"
    data_dir = Path(data_dir)
    if not data_dir.is_dir():
        print(f"エラー: データディレクトリがありません: {data_dir}")
        return 1

    try:
        result = run_strategy_b(
            train_start=args.train_start,
            train_end=args.train_end,
            predict_date=args.predict_date,
            data_dir_raw=data_dir,
            model_save_path=args.model_path,
            output_dir=args.output,
            data_source=args.data_source,
            db_path=args.db_path,
            seed=args.seed,
            max_samples=args.max_samples,
            sample_mode=args.sample_mode,
        )
    except Exception as e:
        print(f"エラー: {e}")
        return 1

    summary = result["summary"]
    conditions = result["conditions"]
    print("条件:", conditions)
    print("ROI(%):", summary.get("roi_pct"))
    print("total_bet:", summary.get("total_bet"))
    print("total_payout:", summary.get("total_payout"))
    print("hit_count:", summary.get("hit_count"))
    print("サマリ保存:", result.get("summary_path", ""))
    if args.save_summary_to:
        out_path = Path(args.save_summary_to)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump({"conditions": conditions, "summary": summary, "prediction_path": result["prediction_path"], "model_path": result["model_path"]}, f, ensure_ascii=False, indent=2)
        print("指定先へ保存:", out_path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
