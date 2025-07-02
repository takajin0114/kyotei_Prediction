import os
import sys
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
from stable_baselines3 import PPO
from stable_baselines3.common.results_plotter import plot_results
from stable_baselines3.common.monitor import load_results
import tensorboard
from tensorboard.backend.event_processing.event_accumulator import EventAccumulator
import glob

# パス調整
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, '..', 'pipelines'))
sys.path.append(PARENT_DIR)

from pipelines.kyotei_env import KyoteiEnvManager as BaseKyoteiEnvManager
import gymnasium as gym

class KyoteiEnvManager(BaseKyoteiEnvManager, gym.Env):
    def __init__(self, data_dir="../data", bet_amount=100):
        BaseKyoteiEnvManager.__init__(self, data_dir=data_dir, bet_amount=bet_amount)
        gym.Env.__init__(self)
    def reset(self, *, seed=None, options=None):
        return super().reset()
    def step(self, action):
        return super().step(action)
    @property
    def action_space(self):
        return super().action_space
    @property
    def observation_space(self):
        return super().observation_space

def load_tensorboard_logs(log_dir):
    """TensorBoardログから学習データを読み込み"""
    try:
        ea = EventAccumulator(log_dir)
        ea.Reload()
        
        # 利用可能なスカラーイベントを確認
        print(f"Available scalars: {ea.Tags()['scalars']}")
        
        # 報酬データを取得
        if 'train/episode_reward' in ea.Tags()['scalars']:
            reward_events = ea.Scalars('train/episode_reward')
            rewards = [event.value for event in reward_events]
            steps = [event.step for event in reward_events]
            return pd.DataFrame({'step': steps, 'reward': rewards})
        else:
            print("No episode_reward data found in TensorBoard logs")
            return None
    except Exception as e:
        print(f"Error loading TensorBoard logs: {e}")
        return None

def plot_learning_curves(log_dir, save_path=None):
    """学習曲線をプロット"""
    # stable-baselines3の標準プロット関数を使用
    try:
        plot_results([log_dir], 1e5, "timesteps", "PPO Kyotei")
        if save_path:
            plt.savefig(save_path)
        plt.show()
    except Exception as e:
        print(f"Error plotting with stable-baselines3: {e}")
        # フォールバック: 手動でプロット
        df = load_tensorboard_logs(log_dir)
        if df is not None:
            plt.figure(figsize=(12, 8))
            plt.subplot(2, 2, 1)
            plt.plot(df['step'], df['reward'])
            plt.title('Episode Reward')
            plt.xlabel('Steps')
            plt.ylabel('Reward')
            plt.grid(True)
            
            # 移動平均
            window = min(100, len(df) // 10)
            if window > 1:
                plt.subplot(2, 2, 2)
                plt.plot(df['step'], df['reward'].rolling(window=window).mean())
                plt.title(f'Episode Reward (Moving Average, window={window})')
                plt.xlabel('Steps')
                plt.ylabel('Reward')
                plt.grid(True)
            
            if save_path:
                plt.savefig(save_path)
            plt.show()

def calculate_roi(rewards, bet_amount=100):
    """回収率を計算"""
    total_bet = len(rewards) * bet_amount
    total_return = sum([r + bet_amount for r in rewards if r > -bet_amount])
    roi = (total_return - total_bet) / total_bet * 100
    return roi

def plot_roi_analysis(rewards, bet_amount=100, save_path=None):
    """回収率分析をプロット"""
    cumulative_rewards = np.cumsum(rewards)
    cumulative_bets = np.arange(1, len(rewards) + 1) * bet_amount
    roi_series = (cumulative_rewards + cumulative_bets - cumulative_bets) / cumulative_bets * 100
    
    plt.figure(figsize=(15, 10))
    
    # 累積損益
    plt.subplot(2, 2, 1)
    plt.plot(cumulative_rewards)
    plt.title('Cumulative Rewards')
    plt.xlabel('Episodes')
    plt.ylabel('Cumulative Reward')
    plt.grid(True)
    
    # 回収率推移
    plt.subplot(2, 2, 2)
    plt.plot(roi_series)
    plt.title('ROI (%) Over Time')
    plt.xlabel('Episodes')
    plt.ylabel('ROI (%)')
    plt.axhline(y=0, color='r', linestyle='--', alpha=0.5)
    plt.grid(True)
    
    # エピソード別損益
    plt.subplot(2, 2, 3)
    plt.hist(rewards, bins=50, alpha=0.7)
    plt.title('Reward Distribution')
    plt.xlabel('Reward')
    plt.ylabel('Frequency')
    plt.grid(True)
    
    # 勝率・負率
    wins = sum(1 for r in rewards if r > 0)
    losses = sum(1 for r in rewards if r < 0)
    ties = sum(1 for r in rewards if r == 0)
    total = len(rewards)
    
    plt.subplot(2, 2, 4)
    labels = ['Wins', 'Losses', 'Ties']
    sizes = [wins, losses, ties]
    colors = ['green', 'red', 'gray']
    plt.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%')
    plt.title('Win/Loss Distribution')
    
    plt.tight_layout()
    if save_path:
        plt.savefig(save_path)
    plt.show()
    
    # 統計情報を表示
    print(f"Total Episodes: {total}")
    print(f"Wins: {wins} ({wins/total*100:.1f}%)")
    print(f"Losses: {losses} ({losses/total*100:.1f}%)")
    print(f"Ties: {ties} ({ties/total*100:.1f}%)")
    print(f"Overall ROI: {roi_series[-1]:.2f}%")
    print(f"Average Reward: {np.mean(rewards):.2f}")
    print(f"Reward Std: {np.std(rewards):.2f}")

def run_learning_with_visualization(total_timesteps=50000):
    """学習実行と可視化"""
    # 環境初期化
    data_dir = os.path.abspath(os.path.join(SCRIPT_DIR, '..', 'data'))
    env = KyoteiEnvManager(data_dir=data_dir, bet_amount=100)
    
    # ログディレクトリ
    log_dir = "./ppo_kyotei_visualization/"
    os.makedirs(log_dir, exist_ok=True)
    
    # PPOエージェント初期化
    model = PPO('MlpPolicy', env, verbose=1, tensorboard_log=log_dir)
    
    # 学習
    print(f"Starting training for {total_timesteps} timesteps...")
    model.learn(total_timesteps=total_timesteps)
    
    # モデル保存
    model.save(os.path.join(log_dir, "ppo_kyotei_final"))
    
    # 可視化
    print("Generating visualizations...")
    plot_learning_curves(log_dir, os.path.join(log_dir, "learning_curves.png"))
    
    # 回収率分析
    print("Analyzing ROI...")
    # テスト用にいくつかのエピソードを実行して報酬を収集
    test_rewards = []
    for _ in range(100):
        obs, info = env.reset()
        action, _states = model.predict(obs, deterministic=True)
        obs, reward, done, truncated, info = env.step(action)
        test_rewards.append(reward)
    
    plot_roi_analysis(test_rewards, bet_amount=100, save_path=os.path.join(log_dir, "roi_analysis.png"))
    
    print(f"Visualization completed. Check {log_dir} for results.")

if __name__ == '__main__':
    # 既存のログがある場合は読み込み
    existing_logs = glob.glob("./ppo_tensorboard/*")
    if existing_logs:
        print("Found existing TensorBoard logs:")
        for log in existing_logs:
            print(f"  - {log}")
        choice = input("Use existing logs? (y/n): ").lower()
        if choice == 'y':
            for log in existing_logs:
                print(f"\nAnalyzing {log}...")
                plot_learning_curves(log, f"{log}_analysis.png")
        else:
            run_learning_with_visualization()
    else:
        run_learning_with_visualization() 