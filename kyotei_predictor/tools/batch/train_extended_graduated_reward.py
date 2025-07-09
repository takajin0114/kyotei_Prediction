#!/usr/bin/env python3
"""
段階的報酬設計モデルの拡張学習スクリプト
"""

import os
import sys
import json
import numpy as np
from datetime import datetime
from stable_baselines3 import PPO
from stable_baselines3.common.monitor import Monitor
from stable_baselines3.common.vec_env import DummyVecEnv
from stable_baselines3.common.callbacks import EvalCallback, CheckpointCallback

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

def train_extended_graduated_reward(
    total_timesteps=1000000,  # 100万ステップ
    eval_freq=50000,  # 5万ステップごとに評価
    save_freq=50000,  # 5万ステップごとに保存
    data_dir="kyotei_predictor/data/raw",
    bet_amount=100,
    model_path=None  # 既存モデルから継続学習する場合
):
    """段階的報酬設計モデルの拡張学習"""
    
    print("=== 段階的報酬設計モデルの拡張学習開始 ===")
    print(f"学習開始時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"総ステップ数: {total_timesteps:,}")
    print(f"評価頻度: {eval_freq:,}ステップ")
    print(f"保存頻度: {save_freq:,}ステップ")
    
    # ディレクトリ作成
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    model_dir = f"./optuna_models/extended_graduated_reward_{timestamp}"
    log_dir = f"./optuna_logs/extended_graduated_reward_{timestamp}"
    tensorboard_dir = f"./ppo_tensorboard/extended_graduated_reward_{timestamp}"
    
    os.makedirs(model_dir, exist_ok=True)
    os.makedirs(log_dir, exist_ok=True)
    os.makedirs(tensorboard_dir, exist_ok=True)
    
    # 環境作成
    print("環境を作成中...")
    train_env = create_env(data_dir=data_dir, bet_amount=bet_amount)
    eval_env = create_env(data_dir=data_dir, bet_amount=bet_amount)
    
    # コールバック設定
    eval_callback = EvalCallback(
        eval_env,
        best_model_save_path=f"{model_dir}/",
        log_path=log_dir,
        eval_freq=eval_freq,
        deterministic=True,
        render=False
    )
    
    checkpoint_callback = CheckpointCallback(
        save_freq=save_freq,
        save_path=f"{model_dir}/",
        name_prefix="checkpoint"
    )
    
    # モデル作成または読み込み
    if model_path and os.path.exists(model_path):
        print(f"既存モデルを読み込み中: {model_path}")
        model = PPO.load(model_path)
        model.set_env(train_env)
        print("既存モデルからの継続学習を開始します")
    else:
        print("新しいモデルを作成中...")
        model = PPO(
            "MlpPolicy",
            train_env,
            learning_rate=3e-4,
            batch_size=64,
            n_steps=2048,
            gamma=0.99,
            gae_lambda=0.95,
            n_epochs=10,
            clip_range=0.2,
            ent_coef=0.01,
            vf_coef=0.5,
            max_grad_norm=0.5,
            verbose=1,
            tensorboard_log=tensorboard_dir
        )
        print("新しいモデルの学習を開始します")
    
    # 学習実行
    print("学習を開始します...")
    try:
        model.learn(
            total_timesteps=total_timesteps,
            callback=[eval_callback, checkpoint_callback],
            progress_bar=True
        )
        
        # 最終モデルを保存
        final_model_path = f"{model_dir}/final_model.zip"
        model.save(final_model_path)
        print(f"最終モデルを保存しました: {final_model_path}")
        
        # 学習結果の評価
        print("\n=== 学習結果の評価 ===")
        eval_results = evaluate_model(model, eval_env, n_eval_episodes=500)
        
        print(f"評価結果:")
        print(f"  的中率: {eval_results['hit_rate']*100:.2f}%")
        print(f"  平均報酬: {eval_results['mean_reward']:.2f}")
        print(f"  報酬の標準偏差: {eval_results['std_reward']:.2f}")
        print(f"  正の報酬率: {eval_results['positive_reward_rate']*100:.2f}%")
        
        # 結果をJSONファイルに保存
        results = {
            'training_time': datetime.now().isoformat(),
            'total_timesteps': total_timesteps,
            'eval_freq': eval_freq,
            'save_freq': save_freq,
            'model_dir': model_dir,
            'log_dir': log_dir,
            'tensorboard_dir': tensorboard_dir,
            'evaluation_results': eval_results
        }
        
        results_path = f"./outputs/extended_graduated_reward_results_{timestamp}.json"
        os.makedirs("./outputs", exist_ok=True)
        with open(results_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        print(f"学習結果を保存しました: {results_path}")
        
        return model, results
        
    except Exception as e:
        print(f"学習中にエラーが発生しました: {e}")
        return None, None

def evaluate_model(model, env, n_eval_episodes=500):
    """モデルの評価"""
    
    rewards = []
    hit_count = 0
    positive_reward_count = 0
    
    for episode in range(n_eval_episodes):
        if episode % 100 == 0:
            print(f"評価進捗: {episode}/{n_eval_episodes}")
        
        obs = env.reset()
        episode_reward = 0
        done = False
        
        while not done:
            action, _ = model.predict(obs, deterministic=True)
            obs, reward, done, info = env.step(action)
            episode_reward += reward[0]
            
            if done:
                # 的中判定
                trifecta = action_to_trifecta(action[0])
                arrival = info[0].get('arrival', (1, 2, 3))
                
                if len(arrival) == 3 and trifecta == arrival:
                    hit_count += 1
                
                if episode_reward > -100:
                    positive_reward_count += 1
        
        rewards.append(episode_reward)
    
    rewards = np.array(rewards)
    
    return {
        'hit_rate': hit_count / n_eval_episodes,
        'mean_reward': float(np.mean(rewards)),
        'std_reward': float(np.std(rewards)),
        'max_reward': float(np.max(rewards)),
        'min_reward': float(np.min(rewards)),
        'positive_reward_rate': positive_reward_count / n_eval_episodes
    }

def action_to_trifecta(action: int):
    """action(0-119)→(1着,2着,3着)の買い目タプル"""
    from itertools import permutations
    trifecta_list = list(permutations(range(1,7), 3))
    return trifecta_list[action]

def main():
    """メイン実行関数"""
    print("段階的報酬設計モデルの拡張学習を開始します")
    
    # 学習実行
    model, results = train_extended_graduated_reward(
        total_timesteps=1000000,  # 100万ステップ
        eval_freq=50000,  # 5万ステップごとに評価
        save_freq=50000   # 5万ステップごとに保存
    )
    
    if model and results:
        print("\n=== 拡張学習完了 ===")
        print(f"的中率: {results['evaluation_results']['hit_rate']*100:.2f}%")
        print(f"平均報酬: {results['evaluation_results']['mean_reward']:.2f}")
        print(f"正の報酬率: {results['evaluation_results']['positive_reward_rate']*100:.2f}%")
        
        print("\n次のステップ:")
        print("1. アンサンブル学習の実装")
        print("2. リアルタイム予測システムの構築")
        print("3. 特徴量エンジニアリングの改善")
    else:
        print("学習が失敗しました")

if __name__ == "__main__":
    main() 