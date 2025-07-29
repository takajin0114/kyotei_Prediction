#!/usr/bin/env python3
"""
最適化プロセスの状況確認スクリプト
"""

import os
import glob
import time
from datetime import datetime

def check_optimization_status():
    """最適化プロセスの状況を確認"""
    print("=== 最適化プロセス状況確認 ===")
    print(f"確認時刻: {datetime.now()}")
    
    # 結果ファイルの確認
    result_files = glob.glob("optuna_results/*.json")
    print(f"結果ファイル数: {len(result_files)}")
    
    # 最新の結果ファイルを確認
    if result_files:
        latest_result = max(result_files, key=os.path.getctime)
        print(f"最新結果ファイル: {latest_result}")
        
        # ファイルサイズを確認
        file_size = os.path.getsize(latest_result)
        print(f"ファイルサイズ: {file_size} bytes")
        
        # ファイルの更新時刻を確認
        mtime = os.path.getmtime(latest_result)
        mtime_str = datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M:%S")
        print(f"最終更新時刻: {mtime_str}")
    
    # モデルディレクトリの確認
    model_dirs = glob.glob("optuna_models/trial_*")
    print(f"モデルディレクトリ数: {len(model_dirs)}")
    
    # ログディレクトリの確認
    log_dirs = glob.glob("optuna_logs/trial_*")
    print(f"ログディレクトリ数: {len(log_dirs)}")
    
    # 最新のログディレクトリを確認
    if log_dirs:
        latest_log_dir = max(log_dirs, key=os.path.getctime)
        print(f"最新ログディレクトリ: {latest_log_dir}")
        
        # ログファイルの内容を確認
        log_files = glob.glob(f"{latest_log_dir}/*")
        print(f"ログファイル数: {len(log_files)}")
    
    print("\n=== 状況サマリー ===")
    if len(result_files) > 8:  # 既存のファイル数より多い場合
        print("✅ 最適化プロセスが実行中です")
    else:
        print("⏳ 最適化プロセスの開始を待機中です")
    
    print(f"総結果ファイル数: {len(result_files)}")
    print(f"総モデルディレクトリ数: {len(model_dirs)}")
    print(f"総ログディレクトリ数: {len(log_dirs)}")

if __name__ == "__main__":
    check_optimization_status()