#!/usr/bin/env python3
"""
2024年3月データを使用した最適化実行スクリプト
"""

import sys
import os

# プロジェクトルートをパスに追加
sys.path.append('.')

# 最適化スクリプトをインポート
from kyotei_predictor.tools.optimization.optimize_graduated_reward_202403 import optimize_graduated_reward_202403

def main():
    print("=== 2024年3月データを使用した最適化開始 ===")
    
    # 最適化実行
    study = optimize_graduated_reward_202403(
        n_trials=3,
        study_name="opt_202403",
        data_dir="kyotei_predictor/data/raw/2024-03",
        test_mode=True,
        resume_existing=False
    )
    
    if study:
        print(f"\n=== 最適化完了 ===")
        print(f"最良の試行: {study.best_trial.number}")
        print(f"最良のスコア: {study.best_value:.4f}")
        print(f"総試行数: {len(study.trials)}")
    else:
        print("最適化に失敗しました")
    
    return study

if __name__ == "__main__":
    main()