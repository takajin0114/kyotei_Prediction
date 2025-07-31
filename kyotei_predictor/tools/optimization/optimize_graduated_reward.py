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
import time
from pathlib import Path

# プロジェクトルートを動的に取得
def get_project_root() -> Path:
    """プロジェクトルートを動的に検出"""
    current_file = Path(__file__)
    project_root = current_file.parent.parent.parent.parent
    
    # Google Colab環境の検出
    if str(project_root).startswith('/content/'):
        return Path('/content/kyotei_Prediction')
    
    return project_root

PROJECT_ROOT = get_project_root()

# プロジェクトルートをパスに追加
sys.path.append(str(PROJECT_ROOT))

from kyotei_predictor.pipelines.kyotei_env import KyoteiEnv

def create_env(data_dir=None, bet_amount=100):
    """環境を作成"""
    def make_env():
        nonlocal data_dir
        if data_dir is None:
            data_dir = PROJECT_ROOT / "kyotei_predictor" / "data" / "raw"
        env = KyoteiEnv(data_dir=str(data_dir), bet_amount=bet_amount)
        env = Monitor(env)
        return env
    
    return DummyVecEnv([make_env])

def objective(trial):
    """Optunaの目的関数"""
    
    # ハイパーパラメータの提案
    learning_rate = trial.suggest_float('learning_rate', 1e-5, 1e-3, log=True)
    n_steps = trial.suggest_categorical('n_steps', [1024, 2048, 4096])
    batch_size = trial.suggest_categorical('batch_size', [32, 64, 128])
    n_epochs = trial.suggest_int('n_epochs', 5, 20)
    gamma = trial.suggest_float('gamma', 0.9, 0.999)
    gae_lambda = trial.suggest_float('gae_lambda', 0.9, 0.999)
    clip_range = trial.suggest_float('clip_range', 0.1, 0.3)
    ent_coef = trial.suggest_float('ent_coef', 0.01, 0.1)
    vf_coef = trial.suggest_float('vf_coef', 0.5, 1.0)
    max_grad_norm = trial.suggest_float('max_grad_norm', 0.3, 0.7)
    
    # 環境作成
    env = create_env()
    eval_env = create_env()
    
    # モデル作成
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
        ent_coef=ent_coef,
        vf_coef=vf_coef,
        max_grad_norm=max_grad_norm,
        verbose=0
    )
    
    # コールバック設定
    eval_callback = EvalCallback(
        eval_env,
        best_model_save_path=str(PROJECT_ROOT / "optuna_models" / f"trial_{trial.number}"),
        log_path=str(PROJECT_ROOT / "optuna_logs" / f"trial_{trial.number}"),
        eval_freq=10000,
        deterministic=True,
        render=False
    )
    
    # 学習（テスト用に短縮）
    model.learn(total_timesteps=1000, callback=eval_callback)
    
    # 評価
    mean_reward, _ = evaluate_policy(model, eval_env, n_eval_episodes=10)
    
    return mean_reward

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

def safe_savez(filepath, *args, **kwargs):
    """OSError対策付きnp.savez（3回リトライ）"""
    for i in range(3):
        try:
            np.savez(filepath, *args, **kwargs)
            return
        except OSError as e:
            print(f"[safe_savez] ファイル保存失敗: {filepath} (リトライ{i+1}) {e}")
            time.sleep(1)
    raise

def optimize_graduated_reward(
    n_trials=50,
    study_name="graduated_reward_optimization",
    data_dir="kyotei_predictor/data/raw",
    test_mode=False,
    resume_existing=False
):
    """段階的報酬設計モデルのハイパーパラメータ最適化"""
    
    print("=== 段階的報酬設計モデルのハイパーパラメータ最適化開始 ===")
    print(f"最適化開始時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"試行回数: {n_trials}")
    print(f"既存スタディ継続: {resume_existing}")
    
    # ディレクトリ作成
    os.makedirs(PROJECT_ROOT / "optuna_models", exist_ok=True)
    os.makedirs(PROJECT_ROOT / "optuna_logs", exist_ok=True)
    os.makedirs(PROJECT_ROOT / "optuna_tensorboard", exist_ok=True)
    os.makedirs(PROJECT_ROOT / "optuna_studies", exist_ok=True)
    
    # スタディ名とストレージパスの決定
    if resume_existing:
        # 既存スタディを継続する場合
        # 既存のスタディファイルを探す
        existing_studies = []
        for file in os.listdir(PROJECT_ROOT / "optuna_studies"):
            if file.startswith(study_name) and file.endswith(".db"):
                existing_studies.append(file)
        
        if existing_studies:
            # 最新のスタディファイルを使用
            latest_study = sorted(existing_studies)[-1]
            storage_path = f"sqlite:///optuna_studies/{latest_study}"
            print(f"既存スタディを継続します: {latest_study}")
        else:
            # 既存ファイルがない場合は新規作成
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            storage_path = f"sqlite:///optuna_studies/{study_name}_{timestamp}.db"
            print(f"新規スタディを作成します: {study_name}_{timestamp}.db")
    else:
        # 新規スタディを作成する場合
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        storage_path = f"sqlite:///optuna_studies/{study_name}_{timestamp}.db"
        print(f"新規スタディを作成します: {study_name}_{timestamp}.db")
    
    # スタディ作成（既存スタディの継続対応）
    study = optuna.create_study(
        direction="maximize",
        study_name=study_name,
        storage=storage_path,
        load_if_exists=True  # 既存スタディを読み込む
    )
    
    # 既存の試行数を確認
    existing_trials = len(study.trials)
    print(f"既存の試行数: {existing_trials}")
    
    # 最適化実行
    study.optimize(objective, n_trials=n_trials, show_progress_bar=True)
    
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
    results_path = PROJECT_ROOT / "optuna_results" / f"{study_name}_{timestamp}.json"
    
    os.makedirs(PROJECT_ROOT / "optuna_results", exist_ok=True)
    with open(results_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"最適化結果を保存しました: {results_path}")
    
    # 最良モデルの詳細評価
    print("\n=== 最良モデルの詳細評価 ===")
    best_model_path = PROJECT_ROOT / "optuna_models" / f"trial_{study.best_trial.number}" / "best_model.zip"
    
    if os.path.exists(best_model_path):
        best_model = PPO.load(best_model_path)
        eval_env = create_env(data_dir=data_dir)
        
        detailed_results = evaluate_model(best_model, eval_env, n_eval_episodes=500)
        
        # print(f"詳細評価結果:")
        # print(f"  的中率: {detailed_results['hit_rate']*100:.2f}%")
        # print(f"  平均報酬: {detailed_results['mean_reward']:.2f}")
        # print(f"  報酬の標準偏差: {detailed_results['std_reward']:.2f}")
        
        # 評価結果をnpzで保存（OSError対策）
        eval_npz_path = PROJECT_ROOT / "optuna_logs" / f"trial_{study.best_trial.number}" / "evaluations.npz"
        os.makedirs(eval_npz_path.parent, exist_ok=True)
        safe_savez(eval_npz_path, **detailed_results)
        
        # 最良モデルをコピー
        import shutil
        best_model_dir = PROJECT_ROOT / "optuna_models" / "graduated_reward_best"
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
    parser.add_argument('--test-mode', action='store_true', help='テストモード（短時間設定）')
    parser.add_argument('--resume-existing', action='store_true', help='既存スタディを継続する')
    
    args = parser.parse_args()
    
    study = optimize_graduated_reward(
        n_trials=args.n_trials,
        study_name=args.study_name,
        data_dir=args.data_dir,
        test_mode=args.test_mode,
        resume_existing=args.resume_existing
    )
    
    print(f"\n=== 最適化完了 ===")
    print(f"最良の試行: {study.best_trial.number}")
    print(f"最良のスコア: {study.best_value:.4f}")
    print(f"総試行数: {len(study.trials)}")
    
    return study

if __name__ == "__main__":
    main() 