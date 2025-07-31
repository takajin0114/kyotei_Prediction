#!/usr/bin/env python3
"""
2024年3月データでの段階的報酬最適化テスト（シンプル版）
"""

import sys
import os
from pathlib import Path

# プロジェクトルートを追加
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_import():
    """モジュールのインポートテスト"""
    try:
        print("=== モジュールインポートテスト ===")
        
        # 必要なモジュールのインポート
        import numpy as np
        print("✅ numpy インポート成功")
        
        import optuna
        print("✅ optuna インポート成功")
        
        from stable_baselines3 import PPO
        print("✅ stable_baselines3 インポート成功")
        
        from kyotei_predictor.pipelines.kyotei_env import KyoteiEnv
        print("✅ KyoteiEnv インポート成功")
        
        from kyotei_predictor.tools.optimization.optimize_graduated_reward import optimize_graduated_reward
        print("✅ optimize_graduated_reward インポート成功")
        
        print("\n✅ すべてのモジュールインポート成功")
        return True
        
    except Exception as e:
        print(f"❌ インポートエラー: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_data_access():
    """データアクセステスト"""
    try:
        print("\n=== データアクセステスト ===")
        
        data_dir = "kyotei_predictor/data/raw/2024-03"
        
        # データディレクトリの存在確認
        if os.path.exists(data_dir):
            print(f"✅ データディレクトリ存在: {data_dir}")
        else:
            print(f"❌ データディレクトリ不存在: {data_dir}")
            return False
        
        # ファイル数の確認
        import glob
        race_files = glob.glob(os.path.join(data_dir, "race_data_*.json"))
        odds_files = glob.glob(os.path.join(data_dir, "odds_data_*.json"))
        
        print(f"✅ レースデータファイル数: {len(race_files)}")
        print(f"✅ オッズデータファイル数: {len(odds_files)}")
        
        if len(race_files) > 0 and len(odds_files) > 0:
            print("✅ データアクセステスト成功")
            return True
        else:
            print("❌ データファイルが見つかりません")
            return False
            
    except Exception as e:
        print(f"❌ データアクセスエラー: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_optimization():
    """最適化テスト"""
    try:
        print("\n=== 最適化テスト ===")
        
        from kyotei_predictor.tools.optimization.optimize_graduated_reward import optimize_graduated_reward
        
        print("最適化を開始します...")
        
        # 最小限の設定でテスト
        result = optimize_graduated_reward(
            n_trials=1,  # 1試行のみ
            study_name="test_202403_simple",
            data_dir="kyotei_predictor/data/raw/2024-03",
            test_mode=True
        )
        
        print(f"✅ 最適化完了")
        print(f"最良の試行: {result.best_trial.number}")
        print(f"最良のスコア: {result.best_value:.4f}")
        
        return True
        
    except Exception as e:
        print(f"❌ 最適化エラー: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """メイン実行関数"""
    print("=== 2024年3月データでの段階的報酬最適化テスト ===")
    
    # ステップ1: インポートテスト
    if not test_import():
        print("❌ インポートテスト失敗")
        return
    
    # ステップ2: データアクセステスト
    if not test_data_access():
        print("❌ データアクセステスト失敗")
        return
    
    # ステップ3: 最適化テスト
    if not test_optimization():
        print("❌ 最適化テスト失敗")
        return
    
    print("\n✅ すべてのテストが成功しました！")

if __name__ == "__main__":
    main() 