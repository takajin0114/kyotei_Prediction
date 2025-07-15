import os
import re
from datetime import datetime, date, timedelta
from collections import defaultdict
import subprocess
from kyotei_predictor.tools.batch.batch_fetch_all_venues import get_all_stadiums

RAW_DIR = os.path.join(os.path.dirname(__file__), '../../data/raw')
race_pattern = re.compile(r'race_data_(\d{4}-\d{2}-\d{2})_([A-Z0-9]+)_R\d+\.json')

# 取得済み日付を集計
def collect_days():
    days = defaultdict(set)
    for fname in os.listdir(RAW_DIR):
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
                    # プロジェクトルートを絶対パスで取得し、venv311/Scripts/python.exeを指す
                    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../'))
                    python_exe = os.path.join(project_root, 'venv311', 'Scripts', 'python.exe')
                    print(f'[DEBUG] python_exe: {python_exe}')
                    if not os.path.exists(python_exe):
                        print(f'[ERROR] python_exe not found: {python_exe}')
                        continue
                    cmd = [
                        python_exe, '-m', 'kyotei_predictor.tools.batch.batch_fetch_all_venues',
                        '--start-date', first.strftime('%Y-%m-%d'),
                        '--end-date', last.strftime('%Y-%m-%d'),
                        '--stadiums', sname
                    ]
                    # 親の環境変数をコピーし、PYTHONPATHを明示的に渡す
                    env = os.environ.copy()
                    env["PYTHONPATH"] = os.environ.get("PYTHONPATH", "")
                    # エラーログをlogs/batch_err/に出力
                    log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'logs', 'batch_err')
                    os.makedirs(log_dir, exist_ok=True)
                    errfile_path = os.path.join(log_dir, f"fetch_err_{sname}_{first.strftime('%Y-%m')}.log")
                    errfile = open(errfile_path, "w")
                    subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=errfile, env=env)
    finally:
        if not is_child and os.path.exists(lockfile):
            os.remove(lockfile)

if __name__ == '__main__':
    main() 