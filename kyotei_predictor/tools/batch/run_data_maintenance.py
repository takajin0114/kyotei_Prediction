import subprocess
import sys
import argparse
from datetime import datetime
import os
import platform
import atexit

LOG_FILE = f"data/logs/data_maintenance_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

def log(msg):
    import os
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    print(msg)
    with open(LOG_FILE, 'a', encoding='utf-8') as f:
        f.write(msg + '\n')

def run_step(cmd, step_name):
    print(f"[CMD] {cmd}", flush=True)
    try:
        subprocess.run(cmd, check=True, stdout=sys.stdout, stderr=sys.stderr)
    except subprocess.CalledProcessError as e:
        print(f"[FAIL] {step_name} failed with code {e.returncode}", flush=True)
        return False
    print(f"[OK] {step_name} 完了", flush=True)
    return True

def main():
    import os
    import sys
    import atexit
    from datetime import datetime
    lockfile = 'run_data_maintenance.lock'
    is_child = '--is-child' in sys.argv
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

    parser = argparse.ArgumentParser(description="データ取得・欠損集計・再取得・品質チェック一括実行バッチ")
    parser.add_argument('--start-date', type=str, help='取得開始日 (YYYY-MM-DD)', default=None)
    parser.add_argument('--end-date', type=str, help='取得終了日 (YYYY-MM-DD)', default=None)
    parser.add_argument('--stadiums', type=str, help='対象会場 (ALLまたはカンマ区切り)', default='ALL')
    parser.add_argument('--schedule-workers', type=int, default=8, help='開催日取得の並列数（デフォルト: 8）')
    parser.add_argument('--race-workers', type=int, default=16, help='レース取得の並列数（デフォルト: 16）')
    args = parser.parse_args()

    # 1. データ取得
    fetch_cmd = ["python", "-u", "-m", "kyotei_predictor.tools.batch.batch_fetch_all_venues"]
    if args.start_date:
        fetch_cmd += ["--start-date", args.start_date]
    if args.end_date:
        fetch_cmd += ["--end-date", args.end_date]
    if args.stadiums:
        fetch_cmd += ["--stadiums", args.stadiums]
    if args.schedule_workers:
        fetch_cmd += ["--schedule-workers", str(args.schedule_workers)]
    if args.race_workers:
        fetch_cmd += ["--race-workers", str(args.race_workers)]
    fetch_cmd += ["--is-child"]
    run_step(fetch_cmd, "データ取得（batch_fetch_all_venues）")

    # 2. 取得状況サマリ
    run_step(["python", "-m", "kyotei_predictor.tools.batch.list_fetched_data_summary"], "取得状況サマリ（list_fetched_data_summary）")

    # 3. 欠損データ再取得
    retry_cmd = ["python", "-m", "kyotei_predictor.tools.batch.retry_missing_races"]
    if args.start_date:
        retry_cmd += ["--start-date", args.start_date]
    if args.end_date:
        retry_cmd += ["--end-date", args.end_date]
    run_step(retry_cmd, "欠損データ再取得（retry_missing_races）")

    # 4. データ品質チェック
    run_step(["python", "-m", "kyotei_predictor.tools.analysis.data_availability_checker"], "データ品質チェック（data_availability_checker）")

    log("\n=== データメンテナンス一括実行 完了 ===")
    log(f"ログファイル: {LOG_FILE}")

if __name__ == "__main__":
    main() 