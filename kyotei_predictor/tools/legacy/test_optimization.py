#!/usr/bin/env python3
"""
テストモードでの最適化実行スクリプト
"""

import sys
import os
from datetime import datetime

# プロジェクトルートをパスに追加
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from kyotei_predictor.tools.optimization.optimize_graduated_reward import optimize_graduated_reward

def main():
    """テストモードでの最適化実行"""
    
    print("=== テストモードでの最適化開始 ===")
    print(f"実行開始時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # テスト用のパラメータ
    n_trials = 3  # 3試行のみ
    data_dir = "kyotei_predictor/data/raw/2024-03"
    study_name = "graduated_reward_optimization_test"
    test_mode = True  # テストモード
    resume_existing = False  # 新規スタディ
    
    print(f"試行回数: {n_trials}")
    print(f"データディレクトリ: {data_dir}")
    print(f"スタディ名: {study_name}")
    print(f"テストモード: {test_mode}")
    print(f"既存スタディ継続: {resume_existing}")
    
    try:
        # 最適化実行
        study = optimize_graduated_reward(
            n_trials=n_trials,
            study_name=study_name,
            data_dir=data_dir,
            test_mode=test_mode,
            resume_existing=resume_existing
        )
        
        print(f"\n=== テスト最適化完了 ===")
        print(f"最良の試行: {study.best_trial.number}")
        print(f"最良のスコア: {study.best_value:.4f}")
        print(f"総試行数: {len(study.trials)}")
        
        return study
        
    except Exception as e:
        print(f"テスト最適化実行中にエラーが発生しました: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    main()