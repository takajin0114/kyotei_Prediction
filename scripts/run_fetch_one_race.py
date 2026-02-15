#!/usr/bin/env python3
"""
1R のみ取得する実行用ランチャー。
プロジェクトルートを __file__ から算出するため、どこから実行しても動く。

使い方:
  python scripts/run_fetch_one_race.py
"""
import os
import subprocess
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
os.chdir(PROJECT_ROOT)

out_dir = PROJECT_ROOT / "kyotei_predictor" / "data" / "raw"
cmd = [
    sys.executable,
    "-m", "kyotei_predictor.tools.batch.batch_fetch_all_venues",
    "--start-date", "2026-02-14",
    "--end-date", "2026-02-14",
    "--stadiums", "KIRYU",
    "--races", "1",
    "--output-data-dir", str(out_dir),
]
print("Run:", " ".join(cmd))
sys.exit(subprocess.run(cmd).returncode)
