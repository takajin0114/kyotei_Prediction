"""
レポート（検証・予測サマリ）の CLI 入口。scripts/summarize_verification_results を呼ぶ。
OS 非依存。TODO: 将来 --config で project-root 等を渡せるようにする。
"""
import argparse
import sys
from pathlib import Path

_THIS_DIR = Path(__file__).resolve().parent
_PROJECT_ROOT = _THIS_DIR.parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))


def main() -> int:
    parser = argparse.ArgumentParser(description="検証・予測の簡易サマリを表示")
    parser.add_argument("--project-root", type=Path, default=None)
    parser.add_argument("--format", choices=("markdown", "json"), default="markdown")
    args = parser.parse_args()
    project_root = Path(args.project_root) if args.project_root else _PROJECT_ROOT
    # scripts/summarize_verification_results の run() を利用
    scripts_dir = project_root / "scripts"
    if str(scripts_dir) not in sys.path:
        sys.path.insert(0, str(scripts_dir))
    from summarize_verification_results import run
    run(project_root, args.format)
    return 0


if __name__ == "__main__":
    sys.exit(main())
