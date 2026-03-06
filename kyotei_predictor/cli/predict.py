"""
予測の CLI 入口。既存の prediction_tool に引数をそのまま渡す。
--config で optimization_config.ini を指定可能（将来 DATA_DIR 等の読込に利用）。
OS 非依存。
"""
import argparse
import sys
from pathlib import Path

_THIS_DIR = Path(__file__).resolve().parent
_PROJECT_ROOT = _THIS_DIR.parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))


def main() -> int:
    parser = argparse.ArgumentParser(description="予測を実行（prediction_tool に引数を転送）")
    parser.add_argument("--config", type=Path, default=None, help="optimization_config.ini（将来の拡張用）")
    args, rest = parser.parse_known_args()
    if args.config:
        from kyotei_predictor.cli.config_loader import load_optimization_config
        load_optimization_config(args.config)  # 将来: ここで DATA_DIR 等を env に設定
    sys.argv = ["prediction_tool"] + rest
    from kyotei_predictor.tools.prediction_tool import main as pt_main
    pt_main()
    return 0


if __name__ == "__main__":
    sys.exit(main())
