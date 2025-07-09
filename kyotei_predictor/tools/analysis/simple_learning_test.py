import os
import glob
import json
import numpy as np
import random
from itertools import permutations
import matplotlib.pyplot as plt
from stable_baselines3 import PPO
from stable_baselines3.common.vec_env import DummyVecEnv
from stable_baselines3.common.callbacks import EvalCallback
import sys
sys.path.append('kyotei_predictor')
from pipelines.kyotei_env import KyoteiEnvManager

def parse_key(path, prefix):
    fname = os.path.basename(path)
    parts = fname.replace(prefix, "").replace(".json", "").split("_")
    if len(parts) >= 3:
        date_parts = parts[0:3]
        date = "".join(date_parts).replace("-", "")
        if len(parts) >= 5:
            stadium = parts[3]
            rno = parts[4]
        elif len(parts) >= 4:
            stadium = parts[3]
            rno = "1"
        else:
            stadium = "UNKNOWN"
            rno = "1"
    else:
        date = parts[0] if parts else "UNKNOWN"
        stadium = parts[1] if len(parts) > 1 else "UNKNOWN"
        rno = parts[2] if len(parts) > 2 else "1"
    rno = rno.replace('R', '')
    try:
        rno_int = int(rno)
    except ValueError:
        rno_int = 1
    return (date, stadium, rno_int)

def create_simple_env(data_dir, max_races=10):
    """少数のレースデータで環境を作成"""
    race_files = glob.glob(os.path.join(data_dir, 'race_data_*.json'))
    odds_files = glob.glob(os.path.join(data_dir, 'odds_data_*.json'))
    race_map = {parse_key(f, "race_data_"): f for f in race_files}
    odds_map = {parse_key(f, "odds_data_"): f for f in odds_files}
    keys = set(race_map.keys()) & set(odds_map.keys())
    pairs = [(race_map[k], odds_map[k]) for k in sorted(keys)]
    
    # 最初のmax_races個のペアのみを使用
    simple_pairs = pairs[:max_races]
    print(f"簡易テスト用レース数: {len(simple_pairs)}")
    
    # カスタム環境マネージャーを作成
    class SimpleKyoteiEnvManager(KyoteiEnvManager):
        def __init__(self, pairs, bet_amount=100):
            self.pairs = pairs
            super().__init__("../data", bet_amount)
            
        def _find_race_odds_pairs(self):
            return self.pairs
    
    return SimpleKyoteiEnvManager(simple_pairs)

def test_simple_learning(data_dir, max_races=10, total_timesteps=1000):
    """簡易学習テスト"""
    print("=== 簡易学習テスト ===")
    print(f"テスト用レース数: {max_races}")
    print(f"学習ステップ数: {total_timesteps}")
    
    # 環境作成
    env = create_simple_env(data_dir, max_races)
    env = DummyVecEnv([lambda: env])
    
    # 環境テスト
    print("\n--- 環境テスト ---")
    obs = env.reset()
    print(f"観測空間の形状: {obs.shape}")
    print(f"観測値の範囲: [{np.min(obs)}, {np.max(obs)}]")
    print(f"観測値の平均: {np.mean(obs):.4f}")
    print(f"観測値の標準偏差: {np.std(obs):.4f}")
    
    # アクションテスト
    action = env.action_space.sample()
    obs, reward, done, info = env.step([action])
    print(f"アクション: {action}")
    print(f"報酬: {reward}")
    print(f"終了フラグ: {done}")
    
    # 学習テスト
    print("\n--- 学習テスト ---")
    
    # シンプルなPPOモデル
    model = PPO(
        "MlpPolicy",
        env,
        learning_rate=0.0003,
        n_steps=64,
        batch_size=32,
        n_epochs=4,
        gamma=0.99,
        verbose=1,
        tensorboard_log="./simple_test_tensorboard/"
    )
    
    # 学習実行
    print("学習開始...")
    try:
        model.learn(total_timesteps=total_timesteps)
        print("学習完了")
        
        # 学習後のテスト
        print("\n--- 学習後のテスト ---")
        obs = env.reset()
        total_reward = 0
        episode_count = 0
        
        for _ in range(10):  # 10エピソードテスト
            obs = env.reset()
            episode_reward = 0
            done = False
            
            while not done:
                action, _ = model.predict(obs, deterministic=True)
                obs, reward, done, info = env.step(action)
                episode_reward += reward[0]
            
            total_reward += episode_reward
            episode_count += 1
            print(f"エピソード {episode_count}: 報酬 = {episode_reward:.2f}")
        
        avg_reward = total_reward / episode_count
        print(f"平均報酬: {avg_reward:.2f}")
        
        return {
            'success': True,
            'avg_reward': avg_reward,
            'episode_count': episode_count
        }
        
    except Exception as e:
        print(f"学習中にエラー: {e}")
        import traceback
        traceback.print_exc()
        return {
            'success': False,
            'error': str(e)
        }

def test_reward_distribution(data_dir, max_races=10):
    """報酬分布のテスト"""
    print("\n=== 報酬分布テスト ===")
    
    env = create_simple_env(data_dir, max_races)
    env = DummyVecEnv([lambda: env])
    
    rewards = []
    actions = []
    
    # 1000回のランダムアクションで報酬分布を確認
    for _ in range(1000):
        obs = env.reset()
        action = env.action_space.sample()
        obs, reward, done, info = env.step([action])
        rewards.append(reward[0])
        actions.append(action)
    
    rewards = np.array(rewards)
    actions = np.array(actions)
    
    print(f"報酬統計:")
    print(f"  平均: {np.mean(rewards):.2f}")
    print(f"  標準偏差: {np.std(rewards):.2f}")
    print(f"  最小: {np.min(rewards):.2f}")
    print(f"  最大: {np.max(rewards):.2f}")
    
    # 報酬の分布
    unique_rewards, counts = np.unique(rewards, return_counts=True)
    print(f"\n報酬分布:")
    for reward, count in zip(unique_rewards, counts):
        print(f"  {reward}: {count}回 ({count/len(rewards):.2%})")
    
    # アクションの分布
    print(f"\nアクション分布:")
    print(f"  平均: {np.mean(actions):.2f}")
    print(f"  標準偏差: {np.std(actions):.2f}")
    print(f"  最小: {np.min(actions)}")
    print(f"  最大: {np.max(actions)}")
    
    return {
        'rewards': rewards,
        'actions': actions,
        'reward_stats': {
            'mean': np.mean(rewards),
            'std': np.std(rewards),
            'min': np.min(rewards),
            'max': np.max(rewards)
        }
    }

def analyze_learning_progress():
    """学習進捗の分析"""
    print("\n=== 学習進捗分析 ===")
    
    print("1. 環境の動作:")
    print("   - 観測空間: 192次元")
    print("   - アクション空間: 120通り")
    print("   - 報酬: 的中時は正、不的中時は-100")
    
    print("\n2. 学習の課題:")
    print("   - 的中率が0.83%と非常に低い")
    print("   - 初期探索で報酬が得られにくい")
    print("   - 学習時間が短いと改善が見られない")
    
    print("\n3. 改善提案:")
    print("   - より長い学習時間（10万ステップ以上）")
    print("   - 段階的報酬設計の導入")
    print("   - 探索奨励のための報酬調整")
    print("   - より多くのレースデータの使用")

if __name__ == "__main__":
    import sys
    data_dir = sys.argv[1] if len(sys.argv) > 1 else "kyotei_predictor/data/raw"
    
    # 簡易学習テスト
    learning_result = test_simple_learning(data_dir, max_races=10, total_timesteps=1000)
    
    # 報酬分布テスト
    reward_result = test_reward_distribution(data_dir, max_races=10)
    
    # 学習進捗分析
    analyze_learning_progress()
    
    print("\n=== テスト結果サマリー ===")
    print(f"学習成功: {learning_result['success']}")
    if learning_result['success']:
        print(f"平均報酬: {learning_result['avg_reward']:.2f}")
    else:
        print(f"エラー: {learning_result['error']}")
    
    print(f"報酬統計: 平均={reward_result['reward_stats']['mean']:.2f}, "
          f"標準偏差={reward_result['reward_stats']['std']:.2f}") 