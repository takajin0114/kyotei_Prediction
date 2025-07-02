#!/usr/bin/env python3
"""
RL環境のテストスクリプト
"""

from pipelines.kyotei_env import KyoteiEnvManager
import gymnasium as gym

def test_environment():
    """環境の基本動作をテスト"""
    print("Testing KyoteiEnvManager...")
    
    # 環境初期化
    env = KyoteiEnvManager(data_dir='data', bet_amount=100)
    print("✓ Environment created successfully")
    
    # アクション空間とオブザベーション空間の確認
    print(f"✓ Action space: {env.action_space}")
    print(f"✓ Observation space: {env.observation_space}")
    
    # リセットテスト
    obs, info = env.reset()
    print(f"✓ State shape: {obs.shape}")
    print(f"✓ Info: {info}")
    
    # ステップテスト
    action = 0  # 最初のアクション
    obs, reward, done, truncated, info = env.step(action)
    print(f"✓ Step completed - Reward: {reward}, Done: {done}")
    print(f"✓ Arrival info: {info}")
    
    print("✓ All environment tests passed!")

if __name__ == "__main__":
    test_environment() 