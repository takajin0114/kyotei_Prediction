#!/usr/bin/env python3
"""
段階的報酬設計を使用したPPO学習スクリプト
"""

import os
import sys
import time
from datetime import datetime
import numpy as np
import matplotlib.pyplot as plt
from stable_baselines3 import PPO
from stable_baselines3.common.callbacks import EvalCallback, CheckpointCallback
from stable_baselines3.common.monitor import Monitor
from stable_baselines3.common.vec_env import DummyVecEnv

# プロジェクトルートをパスに追加
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from kyotei_predictor.pipelines.kyotei_env import KyoteiEnvManager

def create_env(data_dir="kyotei_predictor/data/raw", bet_amount=100):
    """環境を作成"""
    def make_env():
        env = KyoteiEnvManager(data_dir=data_dir, bet_amount=bet_amount)
        env = Monitor(env)
        return env
    
    return DummyVecEnv([make_env])

def train_with_graduated_reward(
    total_timesteps=1000000,
    learning_rate=3e-4,
    n_steps=2048,
    batch_size=64,
    n_epochs=10,
    gamma=0.99,
    gae_lambda=0.95,
    clip_range=0.2,
    clip_range_vf=None,
    ent_coef=0.01,
    vf_coef=0.5,
    max_grad_norm=0.5,
    use_sde=False,
    sde_sample_freq=-1,
    target_kl=None,
    tensorboard_log=None,
    verbose=1,
    seed=None,
    device="auto",
    _init_setup_model=True
):
    """段階的報酬設計を使用したPPO学習"""
    
    print("=== 段階的報酬設計を使用したPPO学習開始 ===")
    print(f"学習開始時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 環境作成
    print("環境を作成中...")
    env = create_env()
    eval_env = create_env()
    
    # コールバック設定
    eval_callback = EvalCallback(
        eval_env,
        best_model_save_path="./optuna_models/graduated_reward_best/",
        log_path="./optuna_logs/graduated_reward/",
        eval_freq=max(total_timesteps // 10, 1),
        deterministic=True,
        render=False
    )
    
    checkpoint_callback = CheckpointCallback(
        save_freq=max(total_timesteps // 20, 1),
        save_path="./optuna_models/graduated_reward_checkpoints/",
        name_prefix="graduated_reward_model"
    )
    
    # PPOモデル作成
    print("PPOモデルを作成中...")
    model = PPO(
        "MlpPolicy",
        env,
        learning_rate=learning_rate,
        n_steps=n_steps,
        batch_size=batch_size,
        n_epochs=n_epochs,
        gamma=gamma,
        gae_lambda=gae_lambda,
        clip_range=clip_range,
        clip_range_vf=clip_range_vf,
        ent_coef=ent_coef,
        vf_coef=vf_coef,
        max_grad_norm=max_grad_norm,
        use_sde=use_sde,
        sde_sample_freq=sde_sample_freq,
        target_kl=target_kl,
        tensorboard_log=tensorboard_log,
        verbose=verbose,
        seed=seed,
        device=device,
        _init_setup_model=_init_setup_model
    )
    
    # 学習実行
    print(f"学習を開始します（総ステップ数: {total_timesteps:,}）...")
    start_time = time.time()
    
    model.learn(
        total_timesteps=total_timesteps,
        callback=[eval_callback, checkpoint_callback],
        progress_bar=True
    )
    
    end_time = time.time()
    training_time = end_time - start_time
    
    print(f"\n=== 学習完了 ===")
    print(f"学習終了時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"学習時間: {training_time:.2f}秒 ({training_time/3600:.2f}時間)")
    
    # 最終評価
    print("\n最終評価を実行中...")
    mean_reward, std_reward = evaluate_model(model, eval_env, n_eval_episodes=100)
    print(f"最終評価結果: 平均報酬 = {mean_reward:.2f} ± {std_reward:.2f}")
    
    # モデル保存
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    model_path = f"./optuna_models/graduated_reward_final_{timestamp}.zip"
    model.save(model_path)
    print(f"モデルを保存しました: {model_path}")
    
    return model, mean_reward, std_reward

def evaluate_model(model, env, n_eval_episodes=100):
    """モデルの評価"""
    rewards = []
    
    for episode in range(n_eval_episodes):
        obs = env.reset()
        episode_reward = 0
        done = False
        
        while not done:
            action, _ = model.predict(obs, deterministic=True)
            obs, reward, done, _ = env.step(action)
            episode_reward += reward[0]
        
        rewards.append(episode_reward)
        
        if (episode + 1) % 10 == 0:
            print(f"評価進捗: {episode + 1}/{n_eval_episodes}")
    
    mean_reward = np.mean(rewards)
    std_reward = np.std(rewards)
    
    return mean_reward, std_reward

def analyze_training_results(log_path="./optuna_logs/graduated_reward/"):
    """学習結果の分析"""
    print("\n=== 学習結果分析 ===")
    
    # ログファイルの確認
    if os.path.exists(log_path):
        print(f"ログディレクトリ: {log_path}")
        log_files = os.listdir(log_path)
        print(f"ログファイル数: {len(log_files)}")
        
        # 評価結果の可視化
        eval_results = []
        for file in log_files:
            if file.endswith('.monitor.csv'):
                file_path = os.path.join(log_path, file)
                try:
                    data = np.genfromtxt(file_path, delimiter=',', skip_header=1)
                    if len(data) > 0:
                        eval_results.extend(data[:, 1])  # 報酬列
                except:
                    continue
        
        if eval_results:
            eval_results = np.array(eval_results)
            print(f"評価回数: {len(eval_results)}")
            print(f"平均報酬: {np.mean(eval_results):.2f}")
            print(f"報酬の標準偏差: {np.std(eval_results):.2f}")
            print(f"最大報酬: {np.max(eval_results):.2f}")
            print(f"最小報酬: {np.min(eval_results):.2f}")
            
            # 学習曲線の可視化
            plt.figure(figsize=(12, 8))
            
            plt.subplot(2, 2, 1)
            plt.plot(eval_results)
            plt.title('学習曲線（評価報酬）')
            plt.xlabel('評価回数')
            plt.ylabel('平均報酬')
            plt.grid(True)
            
            plt.subplot(2, 2, 2)
            plt.hist(eval_results, bins=30, alpha=0.7)
            plt.title('報酬分布')
            plt.xlabel('報酬')
            plt.ylabel('頻度')
            plt.grid(True)
            
            plt.subplot(2, 2, 3)
            # 移動平均
            window_size = max(1, len(eval_results) // 10)
            moving_avg = np.convolve(eval_results, np.ones(window_size)/window_size, mode='valid')
            plt.plot(moving_avg)
            plt.title(f'移動平均（ウィンドウサイズ: {window_size}）')
            plt.xlabel('評価回数')
            plt.ylabel('移動平均報酬')
            plt.grid(True)
            
            plt.subplot(2, 2, 4)
            # 報酬の改善率
            if len(eval_results) > 1:
                improvements = np.diff(eval_results)
                plt.plot(improvements)
                plt.title('報酬の改善率')
                plt.xlabel('評価回数')
                plt.ylabel('改善量')
                plt.axhline(y=0, color='r', linestyle='--')
                plt.grid(True)
            
            plt.tight_layout()
            plt.savefig('graduated_reward_training_analysis.png', dpi=300, bbox_inches='tight')
            plt.show()
            
            return eval_results
        else:
            print("評価結果が見つかりませんでした。")
            return None
    else:
        print(f"ログディレクトリが見つかりません: {log_path}")
        return None

def main():
    """メイン実行関数"""
    print("段階的報酬設計を使用したPPO学習を開始します")
    
    # 学習パラメータ
    total_timesteps = 500000  # 50万ステップ
    learning_rate = 3e-4
    n_steps = 2048
    batch_size = 64
    n_epochs = 10
    gamma = 0.99
    gae_lambda = 0.95
    clip_range = 0.2
    ent_coef = 0.01
    vf_coef = 0.5
    max_grad_norm = 0.5
    
    # 学習実行
    model, mean_reward, std_reward = train_with_graduated_reward(
        total_timesteps=total_timesteps,
        learning_rate=learning_rate,
        n_steps=n_steps,
        batch_size=batch_size,
        n_epochs=n_epochs,
        gamma=gamma,
        gae_lambda=gae_lambda,
        clip_range=clip_range,
        ent_coef=ent_coef,
        vf_coef=vf_coef,
        max_grad_norm=max_grad_norm,
        verbose=1
    )
    
    # 学習結果分析
    eval_results = analyze_training_results()
    
    # 結果サマリー
    print("\n=== 学習結果サマリー ===")
    print(f"段階的報酬設計を使用したPPO学習が完了しました")
    print(f"最終評価結果: {mean_reward:.2f} ± {std_reward:.2f}")
    
    if eval_results is not None:
        print(f"学習改善: {eval_results[-1] - eval_results[0]:.2f}")
        print(f"最大報酬: {np.max(eval_results):.2f}")
    
    print("\n次のステップ:")
    print("1. 学習曲線を確認して学習の収束性を評価")
    print("2. 必要に応じて学習時間を延長")
    print("3. ハイパーパラメータの調整を検討")

if __name__ == "__main__":
    main() 