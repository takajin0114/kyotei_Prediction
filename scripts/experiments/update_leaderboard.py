#!/usr/bin/env python3
"""
新しい実験結果を experiments/leaderboard.md に追加する。
追加フォーマット: | Experiment | ROI | Notes |
Python標準ライブラリのみ使用。
"""

import argparse
from pathlib import Path


def find_repo_root(script_path: Path) -> Path:
    """scripts/experiments/ からリポジトリルートを返す。"""
    return script_path.resolve().parent.parent.parent


def main() -> int:
    parser = argparse.ArgumentParser(description="Append experiment row to leaderboard")
    parser.add_argument("--experiment", type=str, required=True, help="Experiment ID (e.g. EXP-0006)")
    parser.add_argument("--roi", type=str, required=True, help="ROI value (e.g. -20.7% or -20.7)")
    parser.add_argument("--notes", type=str, default="", help="Notes for the row")
    args = parser.parse_args()

    script_path = Path(__file__).resolve()
    repo_root = find_repo_root(script_path)
    leaderboard_path = repo_root / "experiments" / "leaderboard.md"

    roi_display = args.roi if "%" in args.roi else f"{args.roi}%"
    new_line = f"| {args.experiment} | {roi_display} | {args.notes} |\n"

    leaderboard_path.parent.mkdir(parents=True, exist_ok=True)
    if not leaderboard_path.is_file():
        content = "# Experiment Leaderboard\n\n## Recent\n\n| Experiment | ROI | Notes |\n|---|---|---|\n" + new_line
        leaderboard_path.write_text(content, encoding="utf-8")
    else:
        text = leaderboard_path.read_text(encoding="utf-8")
        if "## Recent" in text:
            # 既存の Recent 表の末尾（最後の | で終わる行の次）に1行追加
            text = text.rstrip() + "\n" + new_line + "\n"
            leaderboard_path.write_text(text, encoding="utf-8")
        else:
            section = "\n\n## Recent\n\n| Experiment | ROI | Notes |\n|---|---|---|\n" + new_line
            leaderboard_path.write_text(text.rstrip() + section + "\n", encoding="utf-8")

    print(f"Updated {leaderboard_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
