#!/usr/bin/env python3
"""
段階的報酬設計モデルのハイパーパラメータ最適化スクリプト
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
from stable_baselines3.common.callbacks import EvalCallback, CheckpointCallback
import argparse
import logging

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

def objective(trial, data_dir="kyotei_predictor/data/raw"):
    print(f"[objective] Trial {trial.number} started")
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
    train_env = create_env(data_dir=data_dir)
    eval_env = create_env(data_dir=data_dir)
    print(f"[objective] Environments created")
    eval_callback = EvalCallback(
        eval_env,
        best_model_save_path=f"./optuna_models/trial_{trial.number}/",
        log_path=f"./optuna_logs/trial_{trial.number}/",
        eval_freq=max(n_steps // 4, 1),
        deterministic=True,
        render=False
    )
    checkpoint_callback = CheckpointCallback(
        save_freq=max(n_steps // 4, 1),
        save_path=f"./optuna_models/trial_{trial.number}/",
        name_prefix="checkpoint"
    )
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
        verbose=1,
        tensorboard_log=f"./optuna_tensorboard/trial_{trial.number}/"
    )
    total_timesteps = 10000  # 学習量を10倍に増加
    try:
        print(f"[objective] model.learn start")
        model.learn(
            total_timesteps=total_timesteps,
            callback=[eval_callback, checkpoint_callback],
            progress_bar=True
        )
        print(f"[objective] model.learn end")
        print(f"[objective] evaluate_model start")
        eval_results = evaluate_model(model, eval_env, n_eval_episodes=10)  # 評価エピソード数を10に増加
        print(f"[objective] evaluate_model end: {eval_results}")
        hit_rate = eval_results['hit_rate']
        mean_reward = eval_results['mean_reward']
        score = hit_rate * 100 + mean_reward / 1000
        print(f"[objective] Trial {trial.number} score: {score}")
        return score
    except Exception as e:
        import traceback
        print(f"Trial {trial.number} failed with error: {e}")
        print("Full traceback:")
        traceback.print_exc()
        logging.warning(f"Trial {trial.number} failed: {e}", exc_info=True)
        return -1000  # 失敗時は低いスコア

def evaluate_model(model, env, n_eval_episodes=100):
    """モデルの評価"""
    
    rewards = []
    hit_count = 0
    
    for episode in range(n_eval_episodes):
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
        
        rewards.append(episode_reward)
    
    return {
        'hit_rate': hit_count / n_eval_episodes,
        'mean_reward': np.mean(rewards),
        'std_reward': np.std(rewards)
    }

def action_to_trifecta(action: int):
    """action(0-119)→(1着,2着,3着)の買い目タプル"""
    from itertools import permutations
    trifecta_list = list(permutations(range(1,7), 3))
    return trifecta_list[action]

def optimize_graduated_reward(
    n_trials=50,
    study_name="graduated_reward_optimization",
    data_dir="kyotei_predictor/data/raw"
):
    """段階的報酬設計モデルのハイパーパラメータ最適化"""
    
    print("=== 段階的報酬設計モデルのハイパーパラメータ最適化開始 ===")
    print(f"最適化開始時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"試行回数: {n_trials}")
    
    # ディレクトリ作成
    os.makedirs("./optuna_models", exist_ok=True)
    os.makedirs("./optuna_logs", exist_ok=True)
    os.makedirs("./optuna_tensorboard", exist_ok=True)
    os.makedirs("./optuna_studies", exist_ok=True)
    
    # スタディ作成
    study = optuna.create_study(
        direction="maximize",
        study_name=study_name,
        storage=f"sqlite:///optuna_studies/{study_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
    )
    
    # 最適化実行
    study.optimize(lambda trial: objective(trial, data_dir), n_trials=n_trials, show_progress_bar=True)
    
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
        'n_trials': n_trials,
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
    results_path = f"./optuna_results/graduated_reward_optimization_{timestamp}.json"
    
    os.makedirs("./optuna_results", exist_ok=True)
    with open(results_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"最適化結果を保存しました: {results_path}")
    
    # 最良モデルの詳細評価
    print("\n=== 最良モデルの詳細評価 ===")
    best_model_path = f"./optuna_models/trial_{study.best_trial.number}/best_model.zip"
    
    if os.path.exists(best_model_path):
        best_model = PPO.load(best_model_path)
        eval_env = create_env(data_dir=data_dir)
        
        detailed_results = evaluate_model(best_model, eval_env, n_eval_episodes=500)
        
        # print(f"詳細評価結果:")
        # print(f"  的中率: {detailed_results['hit_rate']*100:.2f}%")
        # print(f"  平均報酬: {detailed_results['mean_reward']:.2f}")
        # print(f"  報酬の標準偏差: {detailed_results['std_reward']:.2f}")
        
        # 最良モデルをコピー
        import shutil
        best_model_dir = f"./optuna_models/graduated_reward_best"
        os.makedirs(best_model_dir, exist_ok=True)
        shutil.copy2(best_model_path, f"{best_model_dir}/best_model.zip")
        
        # print(f"最良モデルを保存しました: {best_model_dir}/best_model.zip")
    
    return study

def main():
    """メイン実行関数（コマンドライン引数対応）"""
    parser = argparse.ArgumentParser(description="段階的報酬設計モデルのハイパーパラメータ最適化")
    parser.add_argument('--data-dir', type=str, default="kyotei_predictor/data/raw", help='データディレクトリ')
    parser.add_argument('--study-name', type=str, default="graduated_reward_optimization", help='Optunaスタディ名')
    parser.add_argument('--n-trials', type=int, default=50, help='試行回数')
    args = parser.parse_args()
    print("段階的報酬設計モデルのハイパーパラメータ最適化を開始します")
    logging.debug(f"[main] args.data_dir: {args.data_dir}")
    # 最適化実行
    study = optimize_graduated_reward(
        n_trials=args.n_trials,
        study_name=args.study_name,
        data_dir=args.data_dir
    )
    print("\n=== 最適化完了 ===")

if __name__ == "__main__":
    main() 