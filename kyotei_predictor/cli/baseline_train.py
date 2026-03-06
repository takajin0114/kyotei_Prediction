"""
B案ベースラインの学習 CLI。

学習用 race_data_*.json が入ったディレクトリを指定し、
軽量分類器を学習してモデルを保存する。
"""

import argparse
import sys
from pathlib import Path

_THIS_DIR = Path(__file__).resolve().parent
_PROJECT_ROOT = _THIS_DIR.parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from kyotei_predictor.infrastructure.path_manager import PROJECT_ROOT
from kyotei_predictor.application.baseline_train_usecase import run_baseline_train


def main() -> int:
    parser = argparse.ArgumentParser(description="B案ベースラインを学習し、モデルを保存する")
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=None,
        help="学習用 race_data_*.json のディレクトリ（着順入り）。未指定時は kyotei_predictor/data/test_raw",
    )
    parser.add_argument(
        "--model-path",
        type=Path,
        default=None,
        help="モデル保存先。未指定時は outputs/baseline_b_model.joblib",
    )
    parser.add_argument("--max-samples", type=int, default=5000, help="最大学習サンプル数")
    parser.add_argument("--n-estimators", type=int, default=50, help="本数（sklearn / lightgbm / xgboost 共通）")
    parser.add_argument("--max-depth", type=int, default=10, help="最大深さ")
    parser.add_argument(
        "--model-type",
        type=str,
        choices=("sklearn", "lightgbm", "xgboost"),
        default="sklearn",
        help="モデル種別。lightgbm/xgboost 未導入時は sklearn にフォールバック",
    )
    parser.add_argument("--train-start", type=str, default=None, help="学習に含める開始日（YYYY-MM-DD）。ロールング検証用。")
    parser.add_argument("--train-end", type=str, default=None, help="学習に含める終了日（YYYY-MM-DD）。ロールング検証用。")
    parser.add_argument(
        "--data-source",
        type=str,
        choices=("json", "db"),
        default=None,
        help="レースデータ読込元。未指定時は従来通り JSON 直読。json=race_data_*.json, db=SQLite",
    )
    parser.add_argument("--db-path", type=Path, default=None, help="data-source=db 時の SQLite ファイルパス。未指定時は設定の DB_PATH")
    args = parser.parse_args()

    data_dir = args.data_dir or PROJECT_ROOT / "kyotei_predictor" / "data" / "test_raw"
    model_path = args.model_path or PROJECT_ROOT / "outputs" / "baseline_b_model.joblib"
    data_dir = Path(data_dir)
    model_path = Path(model_path)

    if args.data_source != "db" and not data_dir.is_dir():
        print(f"エラー: データディレクトリがありません: {data_dir}")
        return 1
    try:
        summary = run_baseline_train(
            data_dir=data_dir,
            model_save_path=model_path,
            max_samples=args.max_samples,
            n_estimators=args.n_estimators,
            max_depth=args.max_depth,
            model_type=args.model_type,
            train_start=args.train_start,
            train_end=args.train_end,
            data_source=args.data_source,
            db_path=args.db_path,
        )
        print("学習完了:", summary)
        return 0
    except Exception as e:
        print(f"エラー: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
