#!/usr/bin/env python3
"""
簡単な最適化監視スクリプト
"""

import os
import glob
import time
from datetime import datetime

def simple_monitor():
    """最適化の進捗を簡単に監視"""
    print("=== 最適化進捗監視 ===")
    
    # 初期状態を記録
    initial_results = len(glob.glob("optuna_results/*.json"))
    initial_models = len(glob.glob("optuna_models/trial_*"))
    initial_logs = len(glob.glob("optuna_logs/trial_*"))
    
    print(f"初期状態 (開始時刻: {datetime.now()})")
    print(f"  結果ファイル: {initial_results}")
    print(f"  モデルディレクトリ: {initial_models}")
    print(f"  ログディレクトリ: {initial_logs}")
    
    # 監視ループ
    for i in range(12):  # 12回チェック（1時間分）
        time.sleep(300)  # 5分待機
        
        current_results = len(glob.glob("optuna_results/*.json"))
        current_models = len(glob.glob("optuna_models/trial_*"))
        current_logs = len(glob.glob("optuna_logs/trial_*"))
        
        print(f"\n=== チェック {i+1}/12 ({datetime.now()}) ===")
        print(f"  結果ファイル: {current_results} (変化: {current_results - initial_results})")
        print(f"  モデルディレクトリ: {current_models} (変化: {current_models - initial_models})")
        print(f"  ログディレクトリ: {current_logs} (変化: {current_logs - initial_logs})")
        
        if current_results > initial_results:
            print("✅ 最適化が進行中です")
        else:
            print("⏳ 最適化の開始を待機中です")
    
    print("\n=== 監視終了 ===")

if __name__ == "__main__":
    simple_monitor()