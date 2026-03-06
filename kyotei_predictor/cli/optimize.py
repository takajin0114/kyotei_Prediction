"""
最適化の CLI 入口。optimization_config.ini を読み、既存の optimize_graduated_reward に渡す。
OS 非依存: どこからでも python -m kyotei_predictor.cli.optimize で実行可能。
"""
import argparse
import sys
from pathlib import Path

# プロジェクトルートをパスに追加（cli 単体実行時）
_THIS_DIR = Path(__file__).resolve().parent
_PROJECT_ROOT = _THIS_DIR.parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from kyotei_predictor.cli.config_loader import load_optimization_config


def main() -> int:
    parser = argparse.ArgumentParser(
        description="最適化を実行（optimization_config.ini または引数で指定）"
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=None,
        help="optimization_config.ini のパス（未指定時はカレントの optimization_config.ini）",
    )
    parser.add_argument("--n-trials", type=int, default=None, help="試行数（config を上書き）")
    parser.add_argument(
        "--mode",
        choices=("fast", "medium", "normal"),
        default=None,
        help="モード（config の MODE を上書き）",
    )
    parser.add_argument("--year-month", type=str, default=None, help="対象年月 YYYY-MM（config を上書き）")
    args = parser.parse_args()

    cfg = load_optimization_config(args.config)
    n_trials = args.n_trials if args.n_trials is not None else int(cfg.get("TRIALS", 20))
    mode = args.mode or cfg.get("MODE", "fast")
    year_month = args.year_month if args.year_month is not None else cfg.get("YEAR_MONTH", "")

    # 既存の最適化ツールを呼び出す
    from kyotei_predictor.tools.optimization.optimize_graduated_reward import main as opt_main

    # optimize_graduated_reward は sys.argv を参照するため、擬似的に組み立てる
    sys.argv = ["optimize_graduated_reward", "--n-trials", str(n_trials)]
    if mode == "fast":
        sys.argv.append("--fast-mode")
    elif mode == "medium":
        sys.argv.append("--medium-mode")
    if year_month:
        sys.argv.extend(["--year-month", year_month])
    opt_main()
    return 0


if __name__ == "__main__":
    sys.exit(main())
