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
    parser.add_argument("--n-estimators", type=int, default=50, help="RandomForest の本数")
    parser.add_argument("--max-depth", type=int, default=10, help="最大深さ")
    args = parser.parse_args()

    data_dir = args.data_dir or PROJECT_ROOT / "kyotei_predictor" / "data" / "test_raw"
    model_path = args.model_path or PROJECT_ROOT / "outputs" / "baseline_b_model.joblib"
    data_dir = Path(data_dir)
    model_path = Path(model_path)

    if not data_dir.is_dir():
        print(f"エラー: データディレクトリがありません: {data_dir}")
        return 1
    try:
        summary = run_baseline_train(
            data_dir=data_dir,
            model_save_path=model_path,
            max_samples=args.max_samples,
            n_estimators=args.n_estimators,
            max_depth=args.max_depth,
        )
        print("学習完了:", summary)
        return 0
    except Exception as e:
        print(f"エラー: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
