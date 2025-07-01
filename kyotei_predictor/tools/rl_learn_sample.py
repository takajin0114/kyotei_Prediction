import os
import sys
import gymnasium as gym
import numpy as np
from stable_baselines3 import PPO
from stable_baselines3.common.env_checker import check_env
from kyotei_predictor.pipelines.kyotei_env import KyoteiEnvManager as BaseKyoteiEnvManager

# パス調整（kyotei_env.pyのあるディレクトリをimport対象に）
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, '..', 'pipelines'))
sys.path.append(PARENT_DIR)

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

if __name__ == '__main__':
    # --- 環境初期化 ---
    data_dir = os.path.abspath(os.path.join(SCRIPT_DIR, '..', 'data'))
    env = KyoteiEnvManager(data_dir=data_dir, bet_amount=100)

    # --- PPOエージェント初期化 ---
    model = PPO('MlpPolicy', env, verbose=1, tensorboard_log="./ppo_tensorboard/")

    # --- 学習 ---
    model.learn(total_timesteps=10000)

    # --- 学習済みモデル保存 ---
    model.save("ppo_kyotei_sample")

    # --- サンプル推論 ---
    obs, info = env.reset()
    total_reward = 0
    for _ in range(1):  # 1レースのみ
        action, _states = model.predict(obs, deterministic=True)
        obs, reward, done, truncated, info = env.step(action)
        total_reward += reward
        if done or truncated:
            break
    print(f"Sample total reward: {total_reward}") 