#!/usr/bin/env python3
"""
最適化プロセスの監視スクリプト
"""

import os
import time
import psutil
import glob
from datetime import datetime

def monitor_optimization():
    """最適化プロセスの監視"""
    print("=== 最適化プロセス監視開始 ===")
    print(f"開始時刻: {datetime.now()}")
    
    while True:
        try:
            # Pythonプロセスの確認
            python_processes = []
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    if 'python' in proc.info['name'].lower():
                        cmdline = ' '.join(proc.info['cmdline']) if proc.info['cmdline'] else ''
                        if 'optimize_graduated_reward' in cmdline:
                            python_processes.append({
                                'pid': proc.info['pid'],
                                'cmdline': cmdline
                            })
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            # 最適化プロセスの状況
            if python_processes:
                print(f"\n[{datetime.now()}] 最適化プロセス実行中:")
                for proc in python_processes:
                    print(f"  PID: {proc['pid']}, コマンド: {proc['cmdline']}")
            else:
                print(f"\n[{datetime.now()}] 最適化プロセスなし")
            
            # 結果ファイルの確認
            result_files = glob.glob("optuna_results/*.json")
            print(f"結果ファイル数: {len(result_files)}")
            
            # モデルファイルの確認
            model_files = glob.glob("optuna_models/trial_*")
            print(f"モデルディレクトリ数: {len(model_files)}")
            
            # ログファイルの確認
            log_files = glob.glob("optuna_logs/trial_*")
            print(f"ログディレクトリ数: {len(log_files)}")
            
            # 最新の結果ファイルを確認
            if result_files:
                latest_result = max(result_files, key=os.path.getctime)
                print(f"最新結果ファイル: {latest_result}")
            
            time.sleep(30)  # 30秒間隔で監視
            
        except KeyboardInterrupt:
            print("\n監視を停止します")
            break
        except Exception as e:
            print(f"監視エラー: {e}")
            time.sleep(30)

if __name__ == "__main__":
    monitor_optimization()