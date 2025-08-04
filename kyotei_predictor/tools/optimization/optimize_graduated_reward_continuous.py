#!/usr/bin/env python3
"""
継続学習機能を統合した段階的報酬設計モデルのハイパーパラメータ最適化スクリプト
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

# プロジェクトルートをパスに追加
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))
sys.path.insert(0, project_root)

from kyotei_predictor.pipelines.kyotei_env import KyoteiEnvManager
from kyotei_predictor.tools.ai.enhanced_training_system import create_enhanced_training_system

def create_env(data_dir="kyotei_predictor/data/raw/2024-01", bet_amount=100):
    """環境を作成"""
    def make_env():
        env = KyoteiEnvManager(data_dir=data_dir, bet_amount=bet_amount)
        env = Monitor(env)
        return env
    
    return DummyVecEnv([make_env])

def objective(trial, data_dir="kyotei_predictor/data/raw/2024-01", test_mode=False):
    print(f"[objective] Trial {trial.number} started")
    try:
        # 継続学習システムの初期化（一度だけ）
        enhanced_system = create_enhanced_training_system(
            model_dir="./optuna_models",
            history_file="./optuna_results/training_history.json",
            curriculum_file="./optuna_results/curriculum_config.json"
        )
        
        # 適応的パラメータの取得
        base_params = {
            'learning_rate': trial.suggest_float('learning_rate', 1e-5, 1e-2, log=True),
            'batch_size': trial.suggest_categorical('batch_size', [32, 64, 128, 256]),
            'n_steps': trial.suggest_categorical('n_steps', [1024, 2048, 4096]),
            'gamma': trial.suggest_float('gamma', 0.9, 0.99),
            'gae_lambda': trial.suggest_float('gae_lambda', 0.9, 0.99),
            'clip_range': trial.suggest_float('clip_range', 0.1, 0.3),
            'ent_coef': trial.suggest_float('ent_coef', 0.001, 0.1, log=True),
            'vf_coef': trial.suggest_float('vf_coef', 0.1, 1.0),
            'max_grad_norm': trial.suggest_float('max_grad_norm', 0.1, 1.0)
        }
        
        adaptive_params = enhanced_system.get_adaptive_training_parameters(base_params)
        
        # 環境の設定
        env_manager = KyoteiEnvManager(data_dir=data_dir)
        env = env_manager
        
        # PPOモデルの初期化
        model = PPO(
            "MlpPolicy",
            env,
            learning_rate=adaptive_params['learning_rate'],
            n_steps=adaptive_params['n_steps'],
            batch_size=adaptive_params['batch_size'],
            gamma=adaptive_params['gamma'],
            gae_lambda=adaptive_params['gae_lambda'],
            clip_range=adaptive_params['clip_range'],
            ent_coef=adaptive_params['ent_coef'],
            vf_coef=adaptive_params['vf_coef'],
            max_grad_norm=adaptive_params['max_grad_norm'],
            verbose=0
        )
        
        # 学習の実行
        model.learn(total_timesteps=10000 if test_mode else 50000)
        
        # 評価
        mean_reward = evaluate_model(model, env, n_eval_episodes=10)
        
        # 学習履歴の記録
        performance_metrics = {
            'mean_reward': mean_reward,
            'trial_number': trial.number,
            'parameters': adaptive_params
        }
        
        # モデル保存パス
        model_path = f"./optuna_models/trial_{trial.number}/checkpoint_{adaptive_params['n_steps']}_steps.zip"
        
        # 学習履歴を記録
        enhanced_system.continuous_manager.record_training_history(model_path, performance_metrics)
        
        # 段階的学習の完了判定
        if enhanced_system.curriculum.check_completion_criteria(performance_metrics):
            enhanced_system.curriculum.complete_current_stage(performance_metrics)
        
        print(f"[objective] Trial {trial.number} completed with reward: {mean_reward}")
        return mean_reward
        
    except Exception as e:
        print(f"[objective] Trial {trial.number} failed: {e}")
        return -1000.0  # 失敗時のペナルティ

def evaluate_model(model, env, n_eval_episodes=100):
    """モデルを評価"""
    try:
        mean_reward = 0.0
        for _ in range(n_eval_episodes):
            obs, info = env.reset()
            done = False
            episode_reward = 0.0
            
            while not done:
                action, _ = model.predict(obs, deterministic=True)
                obs, reward, done, truncated, info = env.step(action)
                episode_reward += reward
                if truncated:
                    done = True
            
            mean_reward += episode_reward
        
        return mean_reward / n_eval_episodes
        
    except Exception as e:
        print(f"Evaluation error: {e}")
        return -1000.0

def action_to_trifecta(action: int):
    """アクションを三連複に変換"""
    # 6艇の組み合わせを生成
    combinations = []
    for i in range(6):
        for j in range(6):
            for k in range(6):
                if i != j and j != k and i != k:
                    combinations.append((i+1, j+1, k+1))
    
    if 0 <= action < len(combinations):
        return combinations[action]
    else:
        return (1, 2, 3)  # デフォルト

def safe_savez(filepath, *args, **kwargs):
    """安全なファイル保存"""
    try:
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        np.savez(filepath, *args, **kwargs)
        return True
    except Exception as e:
        print(f"ファイル保存エラー: {e}")
        return False

def optimize_graduated_reward_continuous(
    n_trials=10,
    study_name="continuous_opt_202401",
    data_dir="kyotei_predictor/data/raw/2024-01",
    test_mode=True,
    resume_existing=False
):
    """継続学習機能を統合した段階的報酬設計モデルのハイパーパラメータ最適化"""
    
    print("=== 継続学習機能を統合した段階的報酬設計モデルのハイパーパラメータ最適化開始 ===")
    print(f"最適化開始時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"データディレクトリ: {data_dir}")
    print(f"試行回数: {n_trials}")
    print(f"テストモード: {test_mode}")
    print(f"既存スタディ継続: {resume_existing}")
    
    # 継続学習システムの初期化
    enhanced_system = create_enhanced_training_system(
        model_dir="./optuna_models",
        history_file="./optuna_results/training_history.json",
        curriculum_file="./optuna_results/curriculum_config.json"
    )
    
    # 段階的学習の初期化
    enhanced_system.curriculum.create_default_curriculum()
    
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
    
    # 継続学習の状況を表示
    training_status = enhanced_system.get_training_status()
    print(f"継続学習状況: {training_status}")
    
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
    
    # 継続学習の最終状況を表示
    try:
        final_status = enhanced_system.get_training_status()
        print(f"\n=== 継続学習最終状況 ===")
        print(f"学習セッション数: {final_status.get('overall_progress', {}).get('total_training_sessions', 0)}")
        print(f"カリキュラム完了率: {final_status.get('overall_progress', {}).get('curriculum_completion_rate', 0.0):.1f}%")
    except Exception as e:
        print(f"\n=== 継続学習最終状況 ===")
        print(f"学習状況取得エラー: {e}")
        print(f"学習セッション数: 0")
        print(f"カリキュラム完了率: 0.0%")
    
    # 学習進捗の可視化
    enhanced_system.visualize_training_progress("./optuna_results/training_progress.png")
    
    # 学習データのエクスポート
    enhanced_system.export_training_data("./optuna_results/training_data_export.json")
    
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
        'continuous_learning_status': final_status if 'final_status' in locals() else {},
        'all_trials': []
    }
    
    for trial in study.trials:
        results['all_trials'].append({
            'number': trial.number,
            'value': float(trial.value) if trial.value is not None else None,
            'params': trial.params,
            'state': trial.state.name
        })
    
    # 結果を保存
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_file = f"./optuna_results/{study_name}_{timestamp}.json"
    
    with open(results_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print(f"結果を保存しました: {results_file}")
    
    return study

def main():
    """メイン関数"""
    parser = argparse.ArgumentParser(description='継続学習機能を統合した最適化スクリプト')
    parser.add_argument('--n_trials', type=int, default=10, help='試行回数')
    parser.add_argument('--study_name', type=str, default='continuous_opt_202401', help='スタディ名')
    parser.add_argument('--data_dir', type=str, default='kyotei_predictor/data/raw/2024-01', help='データディレクトリ')
    parser.add_argument('--test_mode', action='store_true', help='テストモード')
    parser.add_argument('--resume_existing', action='store_true', help='既存スタディを継続')
    
    args = parser.parse_args()
    
    # ログ設定
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 最適化実行
    study = optimize_graduated_reward_continuous(
        n_trials=args.n_trials,
        study_name=args.study_name,
        data_dir=args.data_dir,
        test_mode=args.test_mode,
        resume_existing=args.resume_existing
    )
    
    if study:
        print("最適化が正常に完了しました")
    else:
        print("最適化中にエラーが発生しました")

if __name__ == "__main__":
    main() 