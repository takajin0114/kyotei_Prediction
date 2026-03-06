"""
検証の CLI 入口。optimization_config.ini の EVALUATION_MODE を --evaluation-mode に渡し、
既存の verify_predictions を実行する。OS 非依存。
"""
import argparse
import sys
from pathlib import Path

_THIS_DIR = Path(__file__).resolve().parent
_PROJECT_ROOT = _THIS_DIR.parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from kyotei_predictor.cli.config_loader import load_optimization_config


def main() -> int:
    parser = argparse.ArgumentParser(description="検証を実行（config の EVALUATION_MODE を --evaluation-mode に反映）")
    parser.add_argument("--config", type=Path, default=None, help="optimization_config.ini のパス")
    parser.add_argument("--prediction", "-p", type=str, default="outputs/predictions_latest.json")
    parser.add_argument("--data-dir", "-d", type=str, default="kyotei_predictor/data/test_raw")
    parser.add_argument("--evaluation-mode", type=str, choices=("first_only", "selected_bets"), default=None)
    parser.add_argument("--output", "-o", type=str, default=None)
    parser.add_argument("--save", action="store_true")
    parser.add_argument("--verbose", "-v", action="store_true")
    args, rest = parser.parse_known_args()

    cfg = load_optimization_config(args.config)
    eval_mode = args.evaluation_mode or cfg.get("EVALUATION_MODE", "first_only")
    if eval_mode not in ("first_only", "selected_bets"):
        eval_mode = "first_only"

    # 既存の verify_predictions.main を呼ぶ（sys.argv を組み立てる）
    sys.argv = [
        "verify_predictions",
        "--prediction", args.prediction,
        "--data-dir", args.data_dir,
        "--evaluation-mode", eval_mode,
    ]
    if args.output:
        sys.argv.extend(["--output", args.output])
    if args.save:
        sys.argv.append("--save")
    if args.verbose:
        sys.argv.append("--verbose")
    sys.argv.extend(rest)

    from kyotei_predictor.tools.verify_predictions import main as vp_main
    return vp_main()


if __name__ == "__main__":
    sys.exit(main())
