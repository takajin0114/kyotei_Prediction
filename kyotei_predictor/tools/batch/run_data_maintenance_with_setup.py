#!/usr/bin/env python3
"""
データ取得前準備・実行一括バッチツール
依存関係のインストールからデータ取得・品質チェックまで自動実行
"""

import subprocess
import sys
import argparse
from datetime import datetime
import os
import platform
import atexit
import shutil

LOG_FILE = f"data/logs/data_maintenance_setup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

def log(msg):
    """ログ出力関数"""
    import os
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    print(msg)
    with open(LOG_FILE, 'a', encoding='utf-8') as f:
        f.write(msg + '\n')

def run_step(cmd, step_name, check_return=True):
    """コマンド実行ステップ"""
    print(f"[CMD] {cmd}", flush=True)
    try:
        result = subprocess.run(cmd, check=check_return, stdout=sys.stdout, stderr=sys.stderr)
        if check_return and result.returncode != 0:
            print(f"[FAIL] {step_name} failed with code {result.returncode}", flush=True)
            return False
        print(f"[OK] {step_name} 完了", flush=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"[FAIL] {step_name} failed with code {e.returncode}", flush=True)
        return False
    except FileNotFoundError:
        print(f"[FAIL] {step_name} - コマンドが見つかりません: {cmd[0]}", flush=True)
        return False

def check_python_version():
    """Pythonバージョンチェック"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print(f"[警告] Python 3.8以上が必要です。現在のバージョン: {version.major}.{version.minor}")
        return False
    print(f"[OK] Python バージョン: {version.major}.{version.minor}.{version.micro}")
    return True

def check_virtual_env():
    """仮想環境チェック"""
    if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        print(f"[OK] 仮想環境が有効です: {sys.prefix}")
        return True
    else:
        print("[警告] 仮想環境が有効になっていません")
        return False

def install_requirements():
    """依存関係のインストール"""
    print("\n=== 依存関係のインストール開始 ===")
    
    # プロジェクトルートのrequirements.txtを確認
    root_req = "requirements.txt"
    kyotei_req = "kyotei_predictor/requirements.txt"
    
    if os.path.exists(root_req):
        print(f"[INFO] ルートのrequirements.txtをインストール: {root_req}")
        if not run_step(["pip", "install", "-r", root_req], "ルート依存関係インストール"):
            return False
    
    if os.path.exists(kyotei_req):
        print(f"[INFO] kyotei_predictorのrequirements.txtをインストール: {kyotei_req}")
        if not run_step(["pip", "install", "-r", kyotei_req], "kyotei_predictor依存関係インストール"):
            return False
    
    # 個別に重要なモジュールをインストール
    critical_modules = ["requests", "metaboatrace", "pandas", "numpy"]
    for module in critical_modules:
        try:
            __import__(module)
            print(f"[OK] {module} は既にインストール済み")
        except ImportError:
            print(f"[INFO] {module} をインストール中...")
            if not run_step(["pip", "install", module], f"{module}インストール"):
                print(f"[警告] {module}のインストールに失敗しましたが、続行します")
    
    print("=== 依存関係のインストール完了 ===\n")
    return True

def verify_installation():
    """インストールの検証"""
    print("\n=== インストール検証開始 ===")
    
    required_modules = ["requests", "metaboatrace", "pandas", "numpy"]
    missing_modules = []
    
    for module in required_modules:
        try:
            __import__(module)
            print(f"[OK] {module} 利用可能")
        except ImportError:
            print(f"[FAIL] {module} 利用不可")
            missing_modules.append(module)
    
    if missing_modules:
        print(f"[警告] 以下のモジュールが利用できません: {missing_modules}")
        return False
    
    print("=== インストール検証完了 ===\n")
    return True

def run_data_maintenance(start_date, end_date, stadiums, schedule_workers, race_workers):
    """データメンテナンスの実行"""
    print(f"\n=== データメンテナンス実行開始 ===")
    print(f"期間: {start_date} 〜 {end_date}")
    print(f"会場: {stadiums}")
    
    # 1. データ取得
    fetch_cmd = ["python", "-u", "-m", "kyotei_predictor.tools.batch.batch_fetch_all_venues"]
    if start_date:
        fetch_cmd += ["--start-date", start_date]
    if end_date:
        fetch_cmd += ["--end-date", end_date]
    if stadiums:
        fetch_cmd += ["--stadiums", stadiums]
    if schedule_workers:
        fetch_cmd += ["--schedule-workers", str(schedule_workers)]
    if race_workers:
        fetch_cmd += ["--race-workers", str(race_workers)]
    fetch_cmd += ["--is-child"]
    
    if not run_step(fetch_cmd, "データ取得（batch_fetch_all_venues）"):
        return False

    # 2. 取得状況サマリ
    if not run_step(["python", "-m", "kyotei_predictor.tools.batch.list_fetched_data_summary"], "取得状況サマリ（list_fetched_data_summary）"):
        return False

    # 3. 欠損データ再取得
    retry_cmd = ["python", "-m", "kyotei_predictor.tools.batch.retry_missing_races"]
    if start_date:
        retry_cmd += ["--start-date", start_date]
    if end_date:
        retry_cmd += ["--end-date", end_date]
    
    if not run_step(retry_cmd, "欠損データ再取得（retry_missing_races）"):
        return False

    # 4. データ品質チェック
    if not run_step(["python", "-m", "kyotei_predictor.tools.analysis.data_availability_checker"], "データ品質チェック（data_availability_checker）"):
        return False

    print("=== データメンテナンス実行完了 ===\n")
    return True

def main():
    """メイン関数"""
    import os
    import sys
    import atexit
    from datetime import datetime
    
    lockfile = 'run_data_maintenance_setup.lock'
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

    parser = argparse.ArgumentParser(description="データ取得前準備・実行一括バッチツール")
    parser.add_argument('--start-date', type=str, help='取得開始日 (YYYY-MM-DD)', default=None)
    parser.add_argument('--end-date', type=str, help='取得終了日 (YYYY-MM-DD)', default=None)
    parser.add_argument('--stadiums', type=str, help='対象会場 (ALLまたはカンマ区切り)', default='ALL')
    parser.add_argument('--schedule-workers', type=int, default=8, help='開催日取得の並列数（デフォルト: 8）')
    parser.add_argument('--race-workers', type=int, default=16, help='レース取得の並列数（デフォルト: 16）')
    parser.add_argument('--skip-setup', action='store_true', help='前準備（依存関係インストール）をスキップ')
    parser.add_argument('--is-child', action='store_true', help='サブプロセス起動時の多重起動判定除外用フラグ')
    
    args = parser.parse_args()

    start_time = datetime.now()
    log(f"\n=== データ取得前準備・実行一括バッチ開始: {start_time} ===")

    try:
        # 1. 環境チェック
        print("\n=== 環境チェック開始 ===")
        if not check_python_version():
            print("[警告] Pythonバージョンが要件を満たしていませんが、続行します")
        
        if not check_virtual_env():
            print("[警告] 仮想環境が有効になっていませんが、続行します")
        
        print("=== 環境チェック完了 ===\n")

        # 2. 前準備（依存関係インストール）
        if not args.skip_setup:
            if not install_requirements():
                print("[警告] 依存関係のインストールに問題がありましたが、続行します")
            
            if not verify_installation():
                print("[警告] インストール検証に失敗しましたが、続行します")
        else:
            print("[INFO] 前準備をスキップしました")

        # 3. データメンテナンス実行
        if not run_data_maintenance(
            args.start_date, args.end_date, args.stadiums, 
            args.schedule_workers, args.race_workers
        ):
            print("[警告] データメンテナンスの一部が失敗しました")

        end_time = datetime.now()
        log(f"\n=== データ取得前準備・実行一括バッチ完了: {end_time} ===")
        log(f"所要時間: {end_time - start_time}")
        log(f"ログファイル: {LOG_FILE}")

    except Exception as e:
        log(f"[ERROR] 予期しないエラーが発生しました: {e}")
        print(f"[ERROR] 予期しないエラーが発生しました: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
