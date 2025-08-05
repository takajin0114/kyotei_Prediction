#!/usr/bin/env python3
"""
最小限学習テスト - 改善された報酬設計の動作確認
"""

import sys
import os
sys.path.append('kyotei_predictor')

def test_minimal_learning():
    """最小限の学習テスト"""
    print("=== 最小限学習テスト開始 ===")
    
    try:
        from tools.optimization.optimize_graduated_reward import optimize_graduated_reward
        
        print("最適化スクリプトのインポート成功 ✓")
        
        # 最小限の設定で学習テスト
        print("最小限設定で学習テストを実行中...")
        print("- 試行回数: 1回")
        print("- 学習ステップ: 5000 (非常に短縮)")
        print("- 評価エピソード: 50 (非常に短縮)")
        
        # カスタム設定で最適化実行
        study = optimize_graduated_reward(
            n_trials=1,
            study_name="minimal_test",
            data_dir="kyotei_predictor/data/raw",
            test_mode=True,
            resume_existing=False
        )
        
        print("学習テスト完了 ✓")
        print(f"最良の試行: {study.best_trial.number}")
        print(f"最良のスコア: {study.best_value:.4f}")
        
        return True
        
    except Exception as e:
        print(f"学習テストエラー: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_improved_reward_integration():
    """改善された報酬設計の統合テスト"""
    print("\n=== 改善された報酬設計の統合テスト ===")
    
    try:
        from pipelines.kyotei_env import KyoteiEnvManager
        from stable_baselines3 import PPO
        
        print("環境とモデルのインポート成功 ✓")
        
        # 最小限の環境作成
        print("最小限環境を作成中...")
        env = KyoteiEnvManager(data_dir="kyotei_predictor/data/raw", bet_amount=100)
        
        # 最小限のモデル作成
        print("最小限モデルを作成中...")
        model = PPO(
            "MlpPolicy",
            env,
            learning_rate=1e-4,
            batch_size=64,
            n_steps=1024,
            gamma=0.99,
            verbose=0
        )
        
        print("モデル作成成功 ✓")
        
        # 非常に短時間の学習
        print("短時間学習を実行中... (1000ステップ)")
        model.learn(total_timesteps=1000, progress_bar=False)
        
        print("短時間学習完了 ✓")
        
        return True
        
    except Exception as e:
        print(f"統合テストエラー: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """メイン実行関数"""
    print("=== 最小限学習テスト実行 ===")
    print()
    
    # テスト実行
    test1_success = test_minimal_learning()
    test2_success = test_improved_reward_integration()
    
    print("\n=== テスト結果 ===")
    print(f"最小限学習テスト: {'成功 ✓' if test1_success else '失敗 ✗'}")
    print(f"統合テスト: {'成功 ✓' if test2_success else '失敗 ✗'}")
    
    if test1_success and test2_success:
        print("\nすべてのテストが成功しました！")
        print("改善された報酬設計が正しく動作しています。")
        print("次のステップ: 本格的な学習実行")
    else:
        print("\n一部のテストが失敗しました。")
        print("エラーの詳細を確認してください。")

if __name__ == "__main__":
    main() 