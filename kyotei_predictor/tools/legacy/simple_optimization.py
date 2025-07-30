#!/usr/bin/env python3
"""
シンプルな最適化実行スクリプト
"""

import sys
import os
import time
from datetime import datetime

# プロジェクトルートをパスに追加
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def main():
    """シンプルな最適化実行"""
    
    print("=== シンプルな最適化開始 ===")
    print(f"実行開始時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        # モジュールのインポートテスト
        print("1. モジュールインポートテスト...")
        from kyotei_predictor.tools.optimization.optimize_graduated_reward import optimize_graduated_reward
        print("   ✓ 最適化モジュールインポート成功")
        
        # 環境のテスト
        print("2. 環境テスト...")
        from kyotei_predictor.pipelines.kyotei_env import KyoteiEnvManager
        env = KyoteiEnvManager(data_dir="kyotei_predictor/data/raw/2024-03")
        print(f"   ✓ データペア数: {len(env.pairs)}")
        
        # 最適化実行
        print("3. 最適化実行...")
        study = optimize_graduated_reward(
            n_trials=3,  # 少ない試行数でテスト
            study_name="simple_test_202403",
            data_dir="kyotei_predictor/data/raw/2024-03",
            test_mode=True,  # テストモード
            resume_existing=False
        )
        
        print(f"\n=== 最適化完了 ===")
        print(f"最良の試行: {study.best_trial.number}")
        print(f"最良のスコア: {study.best_value:.4f}")
        print(f"総試行数: {len(study.trials)}")
        
        return study
        
    except Exception as e:
        print(f"エラーが発生しました: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    main()