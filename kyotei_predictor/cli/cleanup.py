"""
リポジトリ内の古い生成物を削除する CLI（OS 非依存）。

logs/ の古い .log、optuna_* 配下の古いファイル等を、日数指定で削除する。
詳細な運用方針は docs/REPOSITORY_HYGIENE_AND_CLEANUP.md を参照。
"""

import argparse
import sys
import time
from pathlib import Path

_THIS_DIR = Path(__file__).resolve().parent
_PROJECT_ROOT = _THIS_DIR.parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from kyotei_predictor.infrastructure.path_manager import PROJECT_ROOT


# デフォルトで cleanup 対象とするディレクトリ（プロジェクトルート基準）
DEFAULT_TARGET_DIRS = [
    "logs",
    "optuna_logs",
    "optuna_models",
    "optuna_results",
    "optuna_tensorboard",
    "optuna_studies",
]
# ログファイルとして扱い、--days で削除する拡張子
LOG_EXTENSIONS = (".log",)


# 削除してはいけないファイル名（Git で追跡している等）
SKIP_NAMES = {".gitkeep", "README.md"}


def _iter_old_files(root: Path, days: int, extensions: tuple = (".log",)) -> list:
    """root 配下で、指定日数より古いファイルのパスを返す。.gitkeep 等は除外。"""
    if not root.exists() or not root.is_dir():
        return []
    cutoff = time.time() - days * 86400
    out = []
    for p in root.rglob("*"):
        if not p.is_file() or p.name in SKIP_NAMES:
            continue
        if extensions and p.suffix.lower() not in extensions:
            continue
        try:
            if p.stat().st_mtime < cutoff:
                out.append(p)
        except OSError:
            continue
    return out


def _iter_old_files_any(root: Path, days: int) -> list:
    """root 配下で、指定日数より古いファイルをすべて返す（拡張子制限なし）。.gitkeep 等は除外。"""
    if not root.exists() or not root.is_dir():
        return []
    cutoff = time.time() - days * 86400
    out = []
    for p in root.rglob("*"):
        if not p.is_file() or p.name in SKIP_NAMES:
            continue
        try:
            if p.stat().st_mtime < cutoff:
                out.append(p)
        except OSError:
            continue
    return out


def main() -> int:
    parser = argparse.ArgumentParser(
        description="古いログ・Optuna 成果物を削除する（OS 非依存）。docs/REPOSITORY_HYGIENE_AND_CLEANUP.md 参照。"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="削除せず、削除対象の一覧だけ表示する",
    )
    parser.add_argument(
        "--days",
        type=int,
        default=7,
        help="この日数より古いファイルを対象にする（デフォルト: 7）",
    )
    parser.add_argument(
        "--targets",
        type=str,
        default="all",
        help="対象ディレクトリ。カンマ区切り（例: logs,optuna_logs）または all（デフォルト: all）",
    )
    parser.add_argument(
        "--logs-only",
        action="store_true",
        help="logs/ のみ対象とし、.log だけ削除する（30日以上で使う想定）",
    )
    args = parser.parse_args()

    root = Path(PROJECT_ROOT)
    if args.logs_only:
        targets = ["logs"]
        extensions = LOG_EXTENSIONS
        dirs_to_scan = [root / "logs"]
        if (root / "kyotei_predictor" / "logs").exists():
            dirs_to_scan.append(root / "kyotei_predictor" / "logs")
    else:
        if args.targets.strip().lower() == "all":
            targets = DEFAULT_TARGET_DIRS
        else:
            targets = [t.strip() for t in args.targets.split(",") if t.strip()]
        extensions = ()  # 全ファイル
        dirs_to_scan = [root / d for d in targets if (root / d).exists()]

    to_delete = []
    for d in dirs_to_scan:
        if args.logs_only and extensions:
            to_delete.extend(_iter_old_files(d, args.days, extensions))
        else:
            to_delete.extend(_iter_old_files_any(d, args.days))

    to_delete = sorted(set(to_delete))
    if not to_delete:
        print("削除対象のファイルはありません。")
        return 0

    print(f"対象: {len(to_delete)} 件（{args.days} 日より古い）")
    for p in to_delete[:50]:
        print(f"  {p.relative_to(root)}")
    if len(to_delete) > 50:
        print(f"  ... 他 {len(to_delete) - 50} 件")

    if args.dry_run:
        print("（--dry-run のため削除しません）")
        return 0

    for p in to_delete:
        try:
            p.unlink()
        except OSError as e:
            print(f"削除失敗: {p}: {e}", file=sys.stderr)
    print("削除しました。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
