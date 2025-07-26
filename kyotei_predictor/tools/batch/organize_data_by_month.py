import os
import re
import shutil
from pathlib import Path

RAW_DIR = Path(__file__).parent.parent.parent / 'data' / 'raw'

# 対象ファイルパターン
PATTERNS = [
    re.compile(r'^(race|odds)_data_(\d{4}-\d{2}-\d{2})_.*\.json$'),
]

def organize_by_month(raw_dir=RAW_DIR):
    files = [f for f in os.listdir(raw_dir) if os.path.isfile(raw_dir / f)]
    for fname in files:
        for pat in PATTERNS:
            m = pat.match(fname)
            if m:
                date_str = m.group(2)  # YYYY-MM-DD
                month_str = date_str[:7]  # YYYY-MM
                month_dir = raw_dir / month_str
                month_dir.mkdir(exist_ok=True)
                src = raw_dir / fname
                dst = month_dir / fname
                print(f"Move: {src} -> {dst}")
                shutil.move(str(src), str(dst))
                break

def main():
    print(f"Organizing files in: {RAW_DIR}")
    organize_by_month(RAW_DIR)
    print("Done.")

if __name__ == "__main__":
    main() 