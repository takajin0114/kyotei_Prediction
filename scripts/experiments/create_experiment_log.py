#!/usr/bin/env python3
"""
実験結果から experiments/logs/ に EXP-xxxx.md 形式のログを生成する。
既存ログの次番号を採番。Python標準ライブラリのみ使用。
"""

import argparse
import json
import re
from datetime import datetime
from pathlib import Path


def find_repo_root(script_path: Path) -> Path:
    """scripts/experiments/ からリポジトリルート（2階層上）を返す。"""
    return script_path.resolve().parent.parent.parent


def next_experiment_id(logs_dir: Path) -> str:
    """experiments/logs/ 内の EXP-xxxx.md を走査し、次番号を返す（例: EXP-0006）。"""
    pattern = re.compile(r"^EXP-(\d{4})")
    max_n = 0
    if not logs_dir.is_dir():
        return "EXP-0001"
    for f in logs_dir.iterdir():
        if f.suffix.lower() != ".md":
            continue
        m = pattern.match(f.stem.split("_")[0] if "_" in f.stem else f.stem)
        if m:
            max_n = max(max_n, int(m.group(1)))
    return f"EXP-{max_n + 1:04d}"


def load_roi_from_summary(summary_path: Path) -> str:
    """rolling_validation_summary.json から ROI 表記を取得。"""
    if not summary_path.is_file():
        return "(未取得)"
    try:
        with open(summary_path, encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError):
        return "(読込失敗)"
    # 単一 summary またはリストの先頭
    if isinstance(data, list):
        data = data[0] if data else {}
    roi = data.get("overall_roi_selected")
    if roi is None:
        return "(なし)"
    return f"{roi}%"


def main() -> int:
    parser = argparse.ArgumentParser(description="Create experiment log EXP-xxxx.md in experiments/logs/")
    parser.add_argument(
        "--summary-json",
        type=Path,
        default=None,
        help="Path to rolling_validation_summary.json (e.g. outputs/rolling_validation_summary.json)",
    )
    parser.add_argument("--notes", type=str, default="", help="Notes for the experiment")
    parser.add_argument("--conditions", type=str, default="", help="Conditions description")
    args = parser.parse_args()

    script_path = Path(__file__).resolve()
    repo_root = find_repo_root(script_path)
    logs_dir = repo_root / "experiments" / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)

    exp_id = next_experiment_id(logs_dir)
    date_str = datetime.now().strftime("%Y-%m-%d")

    roi_str = "(手動記入)"
    if args.summary_json:
        summary_path = args.summary_json if args.summary_json.is_absolute() else repo_root / args.summary_json
        roi_str = load_roi_from_summary(summary_path)

    content = f"""# Experiment

## Date

{date_str}

## Summary

(実験の要約を記入)

## Conditions

{args.conditions or '(条件を記入)'}

## Results

ROI: {roi_str}

## Notes

{args.notes or '(メモを記入)'}
"""

    out_path = logs_dir / f"{exp_id}.md"
    out_path.write_text(content, encoding="utf-8")
    print(f"Created {out_path}")
    print(f"EXP_ID={exp_id}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
