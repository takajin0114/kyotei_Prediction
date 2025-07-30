#!/usr/bin/env python3
"""
不足月データ取得スクリプト
"""

import os
import re
import sys
import atexit
from collections import defaultdict
from datetime import date, timedelta
import subprocess
from pathlib import Path

# プロジェクトルートを動的に取得
def get_project_root() -> Path:
    """プロジェクトルートを動的に検出"""
    current_file = Path(__file__)
    project_root = current_file.parent.parent.parent.parent
    
    # Google Colab環境の検出
    if str(project_root).startswith('/content/'):
        return Path('/content/kyotei_Prediction')
    
    return project_root

PROJECT_ROOT = get_project_root()
RAW_DIR = PROJECT_ROOT / "kyotei_predictor" / "data" / "raw"

from kyotei_predictor.tools.batch.batch_fetch_all_venues import get_all_stadiums

race_pattern = re.compile(r'race_data_(\d{4}-\d{2}-\d{2})_([A-Z0-9]+)_R\d+\.json')

# 取得済み日付を集計
def collect_days():
    days = defaultdict(set)
    for root, dirs, files in os.walk(RAW_DIR):
        for fname in files:
            m = race_pattern.match(fname)
            if m:
                day, stadium = m.groups()
                days[stadium].add(day)
    return days

def month_range(start, end):
    months = []
    d = date(start.year, start.month, 1)
    while d <= end:
        months.append(d)
        if d.month == 12:
            d = date(d.year+1, 1, 1)
        else:
            d = date(d.year, d.month+1, 1)
    return months

def get_last_day(year, month):
    if month == 12:
        return date(year+1, 1, 1) - timedelta(days=1)
    else:
        return date(year, month+1, 1) - timedelta(days=1)

def main():
    lockfile = 'fetch_missing_months.lock'
    import os
    import sys
    import atexit
    from datetime import datetime
    is_child = '--is-child' in sys.argv if '--is-child' in sys.argv else False
    if not is_child:
        if os.path.exists(lockfile):
            print(f"[警告] すでにロックファイル {lockfile} が存在します。多重起動はできません。", flush=True)
            print("このウィンドウで進捗を見たい場合は、他のバッチを停止してロックファイルを削除してから再実行してください。", flush=True)
            sys.exit(1)
        with open(lockfile, 'w') as f:
            f.write(f"pid={os.getpid()}\n")
            f.write(f"start={datetime.now().isoformat()}\n")
            f.write(f"cmd={' '.join(sys.argv)}\n")
        def remove_lockfile():
            if os.path.exists(lockfile):
                os.remove(lockfile)
        atexit.register(remove_lockfile)
    try:
        # 取得済み日付
        days = collect_days()
        all_stadiums = get_all_stadiums()
        today = date.today()
        earliest = date(2024, 6, 1)  # 取得開始基準
        months = month_range(earliest, today)
        for stadium in all_stadiums:
            sname = stadium.name
            got = set(days.get(sname, []))
            for m in months:
                first = m
                last = get_last_day(m.year, m.month)
                # その月の全日付
                alldays = {(first + timedelta(days=i)).strftime('%Y-%m-%d') for i in range((last-first).days+1)}
                if not alldays.issubset(got):
                    # 未取得日がある月はバッチ取得
                    print(f'未取得: {sname} {first.strftime("%Y-%m")}, バッチ取得開始')
                    
                    # 動的にPython実行ファイルを決定
                    python_cmd = [sys.executable, '-m', 'kyotei_predictor.tools.batch.batch_fetch_all_venues',
                        '--start-date', first.strftime('%Y-%m-%d'),
                        '--end-date', last.strftime('%Y-%m-%d'),
                        '--stadiums', sname
                    ]
                    
                    # 親の環境変数をコピーし、PYTHONPATHを明示的に渡す
                    env = os.environ.copy()
                    env["PYTHONPATH"] = os.environ.get("PYTHONPATH", "")
                    
                    # エラーログをlogs/batch_err/に出力
                    log_dir = PROJECT_ROOT / "kyotei_predictor" / "logs" / "batch_err"
                    log_dir.mkdir(parents=True, exist_ok=True)
                    errfile_path = log_dir / f"fetch_err_{sname}_{first.strftime('%Y-%m')}.log"
                    errfile = open(errfile_path, "w")
                    subprocess.Popen(python_cmd, stdout=subprocess.DEVNULL, stderr=errfile, env=env)
    finally:
        if not is_child and os.path.exists(lockfile):
            os.remove(lockfile)

if __name__ == '__main__':
    main() 