#!/usr/bin/env python3
"""
2024年3月データでの最適化テスト実行スクリプト
"""

import sys
import os

# プロジェクトルートをパスに追加
sys.path.append('.')

def main():
    print("=== 2024年3月データ最適化テスト開始 ===")
    
    try:
        from kyotei_predictor.tools.optimization.optimize_graduated_reward import optimize_graduated_reward
        
        print("最適化関数をインポートしました")
        
        # 最適化実行
        study = optimize_graduated_reward(
            n_trials=3,
            study_name="test_202403_optimization",
            data_dir="kyotei_predictor/data/raw/2024-03",
            test_mode=True
        )
        
        print("=== 最適化完了 ===")
        print(f"最良の試行: {study.best_trial.number}")
        print(f"最良のスコア: {study.best_value:.4f}")
        print(f"総試行数: {len(study.trials)}")
        
    except Exception as e:
        print(f"エラーが発生しました: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()