import subprocess
import sys
import argparse
from datetime import datetime
import os
import platform

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
        subprocess.run(cmd, shell=True, check=True, stdout=sys.stdout, stderr=sys.stderr)
    except subprocess.CalledProcessError as e:
        print(f"[FAIL] {step_name} failed with code {e.returncode}", flush=True)
        return False
    print(f"[OK] {step_name} 完了", flush=True)
    return True

def main():
    # 多重起動チェック（run_data_maintenance.py自身のみ対象、--is-childは除外）
    if platform.system() == "Windows":
        this_cmd = f"python -m kyotei_predictor.tools.batch.run_data_maintenance"
        result = subprocess.run('wmic process get ProcessId,CommandLine /FORMAT:LIST', shell=True, capture_output=True, text=True)
        my_pid = os.getpid()
        for block in result.stdout.split("\n\n"):
            if this_cmd in block and str(my_pid) not in block:
                # --is-childが含まれる場合は除外
                if "--is-child" in block:
                    continue
                print("[警告] すでにrun_data_maintenance.pyが起動中です。多重起動は進捗表示が見えなくなる原因となります。", flush=True)
                print("このウィンドウで進捗を見たい場合は、他のrun_data_maintenance.pyを停止してから再実行してください。", flush=True)
                sys.exit(1)

    parser = argparse.ArgumentParser(description="データ取得・欠損集計・再取得・品質チェック一括実行バッチ")
    parser.add_argument('--start-date', type=str, help='取得開始日 (YYYY-MM-DD)', default=None)
    parser.add_argument('--end-date', type=str, help='取得終了日 (YYYY-MM-DD)', default=None)
    parser.add_argument('--stadiums', type=str, help='対象会場 (ALLまたはカンマ区切り)', default='ALL')
    parser.add_argument('--schedule-workers', type=int, default=8, help='開催日取得の並列数（デフォルト: 8）')
    parser.add_argument('--race-workers', type=int, default=16, help='レース取得の並列数（デフォルト: 16）')
    args = parser.parse_args()

    # 1. データ取得
    fetch_cmd = f"python -u -m kyotei_predictor.tools.batch.batch_fetch_all_venues"
    if args.start_date:
        fetch_cmd += f" --start-date {args.start_date}"
    if args.end_date:
        fetch_cmd += f" --end-date {args.end_date}"
    if args.stadiums:
        fetch_cmd += f" --stadiums {args.stadiums}"
    if args.schedule_workers:
        fetch_cmd += f" --schedule-workers {args.schedule_workers}"
    if args.race_workers:
        fetch_cmd += f" --race-workers {args.race_workers}"
    fetch_cmd += " --is-child"
    run_step(fetch_cmd, "データ取得（batch_fetch_all_venues）")

    # 2. 取得状況サマリ
    run_step("python -m kyotei_predictor.tools.batch.list_fetched_data_summary", "取得状況サマリ（list_fetched_data_summary）")

    # 3. 欠損データ再取得
    retry_cmd = f"python -m kyotei_predictor.tools.batch.retry_missing_races"
    if args.start_date:
        retry_cmd += f" --start-date {args.start_date}"
    if args.end_date:
        retry_cmd += f" --end-date {args.end_date}"
    run_step(retry_cmd, "欠損データ再取得（retry_missing_races）")

    # 4. データ品質チェック
    run_step("python -m kyotei_predictor.tools.analysis.data_availability_checker", "データ品質チェック（data_availability_checker）")

    log("\n=== データメンテナンス一括実行 完了 ===")
    log(f"ログファイル: {LOG_FILE}")

if __name__ == "__main__":
    main() 