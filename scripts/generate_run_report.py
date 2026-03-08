#!/usr/bin/env python3
"""
開発結果を自動でまとめ、docs/ai_dev/run_report.md に書き込む。
Python標準ライブラリのみ使用。リポジトリルートを自動判定。
"""

import os
import subprocess
from datetime import datetime
from pathlib import Path


def find_repo_root(start: Path) -> Path:
    """.git があるディレクトリをリポジトリルートとする。"""
    current = start.resolve()
    while current != current.parent:
        if (current / ".git").exists():
            return current
        current = current.parent
    return start


def run_git(cwd: Path, *args: str) -> str:
    """git コマンドを実行し、標準出力を返す。"""
    try:
        r = subprocess.run(
            ["git"] + list(args),
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=30,
        )
        return r.stdout if r.returncode == 0 else ""
    except (subprocess.SubprocessError, FileNotFoundError):
        return ""


def main() -> None:
    # スクリプト位置からリポジトリルートを判定（scripts/ から1階層上）
    script_dir = Path(__file__).resolve().parent
    repo_root = find_repo_root(script_dir)

    diff_names = run_git(repo_root, "diff", "--name-only").strip()
    diff_stat = run_git(repo_root, "diff", "--stat").strip()
    status_short = run_git(repo_root, "status", "--short").strip()

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    report_path = repo_root / "docs" / "ai_dev" / "run_report.md"

    header = (
        "<!-- AI開発ワークフロー用ファイル: Cursorがここに実装結果をまとめる -->\n\n"
    )
    body = f"""# Run Report

## Summary

Generated at: {timestamp}

## Changed files

```
{diff_names or '(none)'}
```

## Commands run

(実行したコマンドをここに記入)

## Execution results

(実行結果をここに記入)

## Diff summary

### git diff --stat

```
{diff_stat or '(no diff)'}
```

### git status --short

```
{status_short or '(clean)'}
```

## Concerns

(懸念点をここに記入)

## Next actions

(次アクション候補をここに記入。ChatGPT でレビューする場合は bash scripts/ai_dev_cycle.sh で chat_context.md を生成し raw URL を渡す。)
"""

    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(header + body, encoding="utf-8")


if __name__ == "__main__":
    main()
