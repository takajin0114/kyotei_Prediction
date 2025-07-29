#!/usr/bin/env python3
"""
2024年3月データを使用した最適化スクリプト
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

def objective(trial, data_dir="kyotei_predictor/data/raw/2024-03", test_mode=False):
    """最適化の目的関数"""
    print(f"[objective] Trial {trial.number} started")
    
    try:
        # ハイパーパラメータの提案
        learning_rate = trial.suggest_float('learning_rate', 1e-5, 1e-2, log=True)
        batch_size = trial.suggest_categorical('batch_size', [32, 64, 128, 256])
        n_steps = trial.suggest_categorical('n_steps', [1024, 2048, 4096])
        gamma = trial.suggest_float('gamma', 0.9, 0.999)
        gae_lambda = trial.suggest_float('gae_lambda', 0.8, 0.99)
        n_epochs = trial.suggest_int('n_epochs', 3, 20)
        clip_range = trial.suggest_float('clip_range', 0.1, 0.4)
        ent_coef = trial.suggest_float('ent_coef', 0.0, 0.1)
        vf_coef = trial.suggest_float('vf_coef', 0.1, 1.0)
        max_grad_norm = trial.suggest_float('max_grad_norm', 0.1, 1.0)
        
        print(f"[objective] Hyperparams: lr={learning_rate}, batch={batch_size}, n_steps={n_steps}, gamma={gamma}")
        
        # 環境作成
        train_env = create_env(data_dir=data_dir)
        eval_env = create_env(data_dir=data_dir)
        
        # モデル作成
        model = PPO(
            "MlpPolicy",
            train_env,
            learning_rate=learning_rate,
            batch_size=batch_size,
            n_steps=n_steps,
            gamma=gamma,
            gae_lambda=gae_lambda,
            n_epochs=n_epochs,
            clip_range=clip_range,
            ent_coef=ent_coef,
            vf_coef=vf_coef,
            max_grad_norm=max_grad_norm,
            verbose=0,
            tensorboard_log=None
        )
        
        # 学習時間設定
        if test_mode:
            total_timesteps = 5000
            n_eval_episodes = 50
        else:
            total_timesteps = 100000
            n_eval_episodes = 2000
        
        print(f"[objective] model.learn start (timesteps: {total_timesteps})")
        model.learn(total_timesteps=total_timesteps, progress_bar=False)
        print(f"[objective] model.learn end")
        
        # 評価
        print(f"[objective] evaluate_model start (episodes: {n_eval_episodes})")
        eval_results = evaluate_model(model, eval_env, n_eval_episodes=n_eval_episodes)
        print(f"[objective] evaluate_model end: {eval_results}")
        
        hit_rate = eval_results['hit_rate']
        mean_reward = eval_results['mean_reward']
        score = hit_rate * 100 + mean_reward / 1000
        
        print(f"[objective] Trial {trial.number} score: {score}")
        return score
        
    except Exception as e:
        import traceback
        print(f"[objective] Trial {trial.number} error: {e}")
        traceback.print_exc()
        return -1000.0

def evaluate_model(model, env, n_eval_episodes=100):
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
    std_reward = np.std(rewards)
    total_hits = sum(hits)
    hit_rate = total_hits / total_bets if total_bets > 0 else 0
    
    print(f"[evaluate_model] Results: hit_rate={hit_rate:.4f}, mean_reward={mean_reward:.4f}")
    
    return {
        'hit_rate': hit_rate,
        'mean_reward': mean_reward,
        'std_reward': std_reward,
        'total_hits': total_hits,
        'total_bets': total_bets
    }

def optimize_202403(
    n_trials=10,
    study_name="opt_202403",
    data_dir="kyotei_predictor/data/raw/2024-03",
    test_mode=True,
    resume_existing=False
):
    """2024年3月データを使用した最適化"""
    
    print("=== 2024年3月データを使用した最適化開始 ===")
    print(f"最適化開始時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"データディレクトリ: {data_dir}")
    print(f"試行回数: {n_trials}")
    print(f"テストモード: {test_mode}")
    print(f"既存スタディ継続: {resume_existing}")
    
    # データ確認
    try:
        env = KyoteiEnvManager(data_dir=data_dir)
        print(f"データペア数: {len(env.pairs)}")
        if len(env.pairs) == 0:
            print("エラー: データペアが存在しません")
            return None
    except Exception as e:
        print(f"データ読み込みエラー: {e}")
        return None
    
    # ディレクトリ作成
    os.makedirs("./optuna_models", exist_ok=True)
    os.makedirs("./optuna_logs", exist_ok=True)
    os.makedirs("./optuna_tensorboard", exist_ok=True)
    os.makedirs("./optuna_studies", exist_ok=True)
    os.makedirs("./optuna_results", exist_ok=True)
    
    # スタディ名とストレージパスの決定
    if resume_existing:
        existing_studies = []
        for file in os.listdir("./optuna_studies"):
            if file.startswith(study_name) and file.endswith(".db"):
                existing_studies.append(file)
        
        if existing_studies:
            latest_study = sorted(existing_studies)[-1]
            storage_path = f"sqlite:///optuna_studies/{latest_study}"
            print(f"既存スタディを継続します: {latest_study}")
        else:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            storage_path = f"sqlite:///optuna_studies/{study_name}_{timestamp}.db"
            print(f"新規スタディを作成します: {study_name}_{timestamp}.db")
    else:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        storage_path = f"sqlite:///optuna_studies/{study_name}_{timestamp}.db"
        print(f"新規スタディを作成します: {study_name}_{timestamp}.db")
    
    # スタディ作成
    study = optuna.create_study(
        direction="maximize",
        study_name=study_name,
        storage=storage_path,
        load_if_exists=True
    )
    
    existing_trials = len(study.trials)
    print(f"既存の試行数: {existing_trials}")
    
    # 最適化実行
    print("最適化を開始します...")
    study.optimize(
        lambda trial: objective(trial, data_dir, test_mode), 
        n_trials=n_trials, 
        show_progress_bar=True
    )
    
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
        'data_dir': data_dir,
        'n_trials': n_trials,
        'test_mode': test_mode,
        'existing_trials': existing_trials,
        'total_trials': len(study.trials),
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
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_path = f"./optuna_results/graduated_reward_optimization_202403_{timestamp}.json"
    
    with open(results_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"最適化結果を保存しました: {results_path}")
    
    return study

def main():
    """メイン実行関数"""
    print("=== 2024年3月データを使用した最適化開始 ===")
    
    # 最適化実行
    study = optimize_202403(
        n_trials=5,
        study_name="opt_202403",
        data_dir="kyotei_predictor/data/raw/2024-03",
        test_mode=True,
        resume_existing=False
    )
    
    if study:
        print(f"\n=== 最適化完了 ===")
        print(f"最良の試行: {study.best_trial.number}")
        print(f"最良のスコア: {study.best_value:.4f}")
        print(f"総試行数: {len(study.trials)}")
        print(f"最適化完了時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    else:
        print("最適化に失敗しました")
    
    return study

if __name__ == "__main__":
    main()