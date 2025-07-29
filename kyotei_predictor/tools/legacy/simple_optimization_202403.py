#!/usr/bin/env python3
"""
2024年3月データを使用したシンプルな最適化スクリプト
"""

import os
import sys
import json
import numpy as np
import optuna
from datetime import datetime
from stable_baselines3 import PPO
from stable_baselines3.common.monitor import Monitor
from stable_baselines3.common.vec_env import DummyVecEnv
from stable_baselines3.common.callbacks import EvalCallback
import time

# プロジェクトルートをパスに追加
sys.path.append('.')

from kyotei_predictor.pipelines.kyotei_env import KyoteiEnvManager

def create_env(data_dir="kyotei_predictor/data/raw/2024-03", bet_amount=100):
    """環境を作成"""
    def make_env():
        env = KyoteiEnvManager(data_dir=data_dir, bet_amount=bet_amount)
        env = Monitor(env)
        return env
    
    return DummyVecEnv([make_env])

def objective(trial):
    """最適化の目的関数"""
    print(f"[objective] Trial {trial.number} started")
    
    try:
        # ハイパーパラメータの提案
        learning_rate = trial.suggest_float('learning_rate', 1e-5, 1e-2, log=True)
        batch_size = trial.suggest_categorical('batch_size', [32, 64, 128])
        n_steps = trial.suggest_categorical('n_steps', [1024, 2048])
        gamma = trial.suggest_float('gamma', 0.9, 0.999)
        n_epochs = trial.suggest_int('n_epochs', 3, 10)
        clip_range = trial.suggest_float('clip_range', 0.1, 0.4)
        ent_coef = trial.suggest_float('ent_coef', 0.0, 0.1)
        
        print(f"[objective] Hyperparams: lr={learning_rate}, batch={batch_size}, n_steps={n_steps}")
        
        # 環境作成
        train_env = create_env()
        eval_env = create_env()
        
        # モデル作成
        model = PPO(
            "MlpPolicy",
            train_env,
            learning_rate=learning_rate,
            batch_size=batch_size,
            n_steps=n_steps,
            gamma=gamma,
            n_epochs=n_epochs,
            clip_range=clip_range,
            ent_coef=ent_coef,
            verbose=0,
            tensorboard_log=None
        )
        
        # 学習（短時間）
        print(f"[objective] model.learn start")
        model.learn(total_timesteps=3000, progress_bar=False)
        print(f"[objective] model.learn end")
        
        # 評価
        print(f"[objective] evaluate_model start")
        eval_results = evaluate_model(model, eval_env, n_eval_episodes=20)
        print(f"[objective] evaluate_model end: {eval_results}")
        
        hit_rate = eval_results['hit_rate']
        mean_reward = eval_results['mean_reward']
        score = hit_rate * 100 + mean_reward / 1000
        
        print(f"[objective] Trial {trial.number} score: {score}")
        return score
        
    except Exception as e:
        print(f"[objective] Trial {trial.number} error: {e}")
        return -1000.0

def evaluate_model(model, env, n_eval_episodes=20):
    """モデルを評価"""
    print(f"[evaluate_model] Starting evaluation with {n_eval_episodes} episodes")
    
    rewards = []
    hits = []
    total_bets = 0
    
    for episode in range(n_eval_episodes):
        obs = env.reset()
        done = False
        episode_reward = 0
        episode_hits = 0
        episode_bets = 0
        
        while not done:
            action, _ = model.predict(obs, deterministic=True)
            obs, reward, done, info = env.step(action)
            episode_reward += reward
            
            # 的中判定
            if 'hit' in info:
                episode_hits += info['hit']
            if 'bet' in info:
                episode_bets += info['bet']
        
        rewards.append(episode_reward)
        hits.append(episode_hits)
        total_bets += episode_bets
    
    mean_reward = np.mean(rewards)
    total_hits = sum(hits)
    hit_rate = total_hits / total_bets if total_bets > 0 else 0
    
    print(f"[evaluate_model] Results: hit_rate={hit_rate:.4f}, mean_reward={mean_reward:.4f}")
    
    return {
        'hit_rate': hit_rate,
        'mean_reward': mean_reward,
        'total_hits': total_hits,
        'total_bets': total_bets
    }

def main():
    """メイン実行関数"""
    print("=== 2024年3月データを使用したシンプルな最適化開始 ===")
    print(f"開始時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # データ確認
    try:
        env = KyoteiEnvManager(data_dir="kyotei_predictor/data/raw/2024-03")
        print(f"データペア数: {len(env.pairs)}")
        if len(env.pairs) == 0:
            print("エラー: データペアが存在しません")
            return None
    except Exception as e:
        print(f"データ読み込みエラー: {e}")
        return None
    
    # ディレクトリ作成
    os.makedirs("./optuna_studies", exist_ok=True)
    os.makedirs("./optuna_results", exist_ok=True)
    
    # スタディ作成
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    study_name = f"opt_202403_simple_{timestamp}"
    storage_path = f"sqlite:///optuna_studies/{study_name}.db"
    
    study = optuna.create_study(
        direction="maximize",
        study_name=study_name,
        storage=storage_path,
        load_if_exists=True
    )
    
    print(f"スタディ名: {study_name}")
    print("最適化を開始します...")
    
    # 最適化実行
    study.optimize(objective, n_trials=3, show_progress_bar=True)
    
    # 結果表示
    print("\n=== 最適化結果 ===")
    print(f"最良の試行: {study.best_trial.number}")
    print(f"最良のスコア: {study.best_value:.4f}")
    print(f"最良のパラメータ:")
    for key, value in study.best_params.items():
        print(f"  {key}: {value}")
    
    # 結果をJSONファイルに保存
    results = {
        'optimization_time': datetime.now().isoformat(),
        'study_name': study_name,
        'data_dir': "kyotei_predictor/data/raw/2024-03",
        'n_trials': 3,
        'best_trial': {
            'number': study.best_trial.number,
            'value': float(study.best_value),
            'params': study.best_params
        },
        'all_trials': []
    }
    
    for trial in study.trials:
        results['all_trials'].append({
            'number': trial.number,
            'value': float(trial.value) if trial.value is not None else None,
            'params': trial.params,
            'state': trial.state.name
        })
    
    results_path = f"./optuna_results/graduated_reward_optimization_202403_simple_{timestamp}.json"
    
    with open(results_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"最適化結果を保存しました: {results_path}")
    print(f"最適化完了時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    return study

if __name__ == "__main__":
    main()