#!/usr/bin/env python3
"""
最適化結果分析スクリプト
"""

import sys
import os
import json
import numpy as np
from datetime import datetime

# プロジェクトルートをパスに追加
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def analyze_optimization_results():
    """最適化結果の詳細分析"""
    
    print("=== 最適化結果分析 ===")
    print(f"分析時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 1. 最新のスタディファイルを確認
    study_files = [f for f in os.listdir('optuna_studies') if f.endswith('.db')]
    study_files.sort(key=lambda x: os.path.getmtime(os.path.join('optuna_studies', x)), reverse=True)
    
    if not study_files:
        print("❌ スタディファイルが見つかりません")
        return
    
    latest_study = study_files[0]
    print(f"最新スタディ: {latest_study}")
    
    # 2. ログディレクトリの確認
    log_dirs = [d for d in os.listdir('optuna_logs') if d.startswith('trial_')]
    print(f"完了試行数: {len(log_dirs)}")
    
    # 3. 結果ファイルの確認
    result_files = [f for f in os.listdir('optuna_results') if f.endswith('.json')]
    if result_files:
        result_files.sort(key=lambda x: os.path.getmtime(os.path.join('optuna_results', x)), reverse=True)
        latest_result = result_files[0]
        print(f"最新結果ファイル: {latest_result}")
        
        # 結果ファイルの読み込み
        try:
            with open(f'optuna_results/{latest_result}', 'r', encoding='utf-8') as f:
                results = json.load(f)
            
            print(f"\n=== 最適化結果サマリー ===")
            print(f"最良スコア: {results['best_trial']['value']:.4f}")
            print(f"最良試行: {results['best_trial']['number']}")
            print(f"総試行数: {len(results['trials'])}")
            
            print(f"\n=== 最良パラメータ ===")
            for key, value in results['best_trial']['params'].items():
                print(f"  {key}: {value}")
                
        except Exception as e:
            print(f"結果ファイルの読み込みエラー: {e}")
    
    # 4. 評価結果の分析
    print(f"\n=== 評価結果分析 ===")
    for i in range(min(5, len(log_dirs))):  # 最初の5試行を分析
        trial_dir = f"trial_{i}"
        eval_file = os.path.join('optuna_logs', trial_dir, 'evaluations.npz')
        
        if os.path.exists(eval_file):
            try:
                eval_data = np.load(eval_file)
                rewards = eval_data['rewards']
                hit_rates = eval_data['hit_rates']
                
                print(f"試行 {i}:")
                print(f"  平均報酬: {np.mean(rewards):.4f}")
                print(f"  的中率: {np.mean(hit_rates)*100:.2f}%")
                print(f"  スコア: {np.mean(hit_rates)*100 + np.mean(rewards)/1000:.4f}")
                
            except Exception as e:
                print(f"  試行 {i} の評価結果読み込みエラー: {e}")
    
    # 5. 最良試行の詳細分析
    if 'results' in locals():
        best_trial_num = results['best_trial']['number']
        best_trial_dir = f"trial_{best_trial_num}"
        best_eval_file = os.path.join('optuna_logs', best_trial_dir, 'evaluations.npz')
        
        if os.path.exists(best_eval_file):
            try:
                eval_data = np.load(best_eval_file)
                rewards = eval_data['rewards']
                hit_rates = eval_data['hit_rates']
                
                print(f"\n=== 最良試行 {best_trial_num} の詳細 ===")
                print(f"平均報酬: {np.mean(rewards):.4f}")
                print(f"的中率: {np.mean(hit_rates)*100:.2f}%")
                print(f"報酬の標準偏差: {np.std(rewards):.4f}")
                print(f"的中率の標準偏差: {np.std(hit_rates)*100:.2f}%")
                
            except Exception as e:
                print(f"最良試行の詳細分析エラー: {e}")
    
    print(f"\n=== 分析完了 ===")

if __name__ == "__main__":
    analyze_optimization_results() 