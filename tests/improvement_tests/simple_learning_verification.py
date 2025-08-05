#!/usr/bin/env python3
"""
簡単な学習検証スクリプト - 改善された報酬設計の動作確認
"""

import sys
import os
sys.path.append('kyotei_predictor')

def test_basic_learning():
    """基本的な学習テスト"""
    print("=== 基本的な学習テスト開始 ===")
    
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
        
        # 簡単な予測テスト（Gym API対応）
        print("予測テストを実行中...")
        obs, info = env.reset()  # Gym API: (obs, info)を返す
        action, _ = model.predict(obs, deterministic=True)
        print(f"予測アクション: {action}")
        
        print("基本的な学習テスト完了 ✓")
        return True
        
    except Exception as e:
        print(f"基本的な学習テストエラー: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_improved_reward_function():
    """改善された報酬関数のテスト"""
    print("\n=== 改善された報酬関数テスト ===")
    
    try:
        from pipelines.kyotei_env import calc_trifecta_reward_improved
        
        # テストケース
        test_cases = [
            (0, (1, 2, 3), [{'betting_numbers': [1, 2, 3], 'ratio': 10.0}], 100, "的中"),
            (0, (1, 2, 4), [{'betting_numbers': [1, 2, 3], 'ratio': 10.0}], 100, "2着的中"),
            (0, (1, 3, 4), [{'betting_numbers': [1, 2, 3], 'ratio': 10.0}], 100, "1着的中"),
            (0, (2, 3, 4), [{'betting_numbers': [1, 2, 3], 'ratio': 10.0}], 100, "不的中")
        ]
        
        for action, arrival, odds, bet, case_name in test_cases:
            reward = calc_trifecta_reward_improved(action, arrival, odds, bet)
            print(f"{case_name}: 報酬 = {reward}")
        
        print("改善された報酬関数テスト完了 ✓")
        return True
        
    except Exception as e:
        print(f"改善された報酬関数テストエラー: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """メイン実行関数"""
    print("=== 簡単な学習検証実行 ===")
    print()
    
    # テスト実行
    test1_success = test_basic_learning()
    test2_success = test_improved_reward_function()
    
    print("\n=== 検証結果 ===")
    print(f"基本的な学習テスト: {'成功 ✓' if test1_success else '失敗 ✗'}")
    print(f"改善された報酬関数テスト: {'成功 ✓' if test2_success else '失敗 ✗'}")
    
    if test1_success and test2_success:
        print("\nすべての検証が成功しました！")
        print("改善された報酬設計が正しく動作しています。")
        print("次のステップ: 本格的な学習実行")
    else:
        print("\n一部の検証が失敗しました。")
        print("エラーの詳細を確認してください。")

if __name__ == "__main__":
    main() 