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

# 可視化を無効化
import matplotlib
matplotlib.use('Agg')  # バックエンドをAggに設定（非表示）
import matplotlib.pyplot as plt
plt.ioff()  # インタラクティブモードを無効化

# Optunaの可視化を無効化
os.environ['OPTUNA_DISABLE_DEFAULT_LOGGER'] = '1'
os.environ['OPTUNA_DISABLE_LOGGING'] = '1'

# プロジェクトルートをパスに追加
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(project_root)
sys.path.append(os.path.join(project_root, 'kyotei_predictor'))

from pipelines.kyotei_env import KyoteiEnvManager

# 設定管理クラスをインポート
try:
    from config.improvement_config_manager import ImprovementConfigManager
    CONFIG_MANAGER = ImprovementConfigManager()
except ImportError:
    # 設定管理クラスが利用できない場合はデフォルト値を使用
    CONFIG_MANAGER = None
    print("Warning: ImprovementConfigManager not available, using default values")

def create_env(data_dir=None, bet_amount=100, year_month=None):
    """
    環境を作成
    
    Args:
        data_dir: データディレクトリ（Noneの場合はデフォルトパス）
        bet_amount: ベット金額
        year_month: 年月フィルタ（例: "2024-01"）
    """
    if data_dir is None:
        data_dir = "kyotei_predictor/data/raw"
    
    print(f"[create_env] data_dir: {data_dir}")
    print(f"[create_env] year_month: {year_month}")
    print(f"[create_env] bet_amount: {bet_amount}")
    print(f"[create_env] year_month type: {type(year_month)}")
    print(f"[create_env] year_month is None: {year_month is None}")
    
    """環境を作成"""
    def make_env():
        print(f"[make_env] Creating KyoteiEnvManager with year_month: {year_month}")
        print(f"[make_env] year_month type: {type(year_month)}")
        print(f"[make_env] year_month is None: {year_month is None}")
        env = KyoteiEnvManager(data_dir=data_dir, bet_amount=bet_amount, year_month=year_month)
        env = Monitor(env)
        return env
    
    return DummyVecEnv([make_env])

def objective(trial, data_dir=None, test_mode=False, minimal_mode=False, year_month=None):
    """
    最適化の目的関数
    
    Args:
        trial: Optunaの試行オブジェクト
        data_dir: データディレクトリ（Noneの場合はデフォルトパス）
        test_mode: テストモード
        minimal_mode: 最小限モード
        year_month: 年月フィルタ（例: "2024-01"）
    """
    if data_dir is None:
        data_dir = "kyotei_predictor/data/raw"
    print(f"[objective] Trial {trial.number} started")
    
    # データディレクトリの確認
    if data_dir is None:
        data_dir = "kyotei_predictor/data/raw"
    print(f"[objective] data_dir: {data_dir}")
    print(f"[objective] year_month filter: {year_month}")
    print(f"[objective] year_month type: {type(year_month)}")
    print(f"[objective] year_month is None: {year_month is None}")
    
    # 設定ファイルからハイパーパラメータ範囲を取得
    if CONFIG_MANAGER is not None:
        hyperparams = CONFIG_MANAGER.get_hyperparameters("phase2")
        
        # ハイパーパラメータの提案
        learning_rate = trial.suggest_float(
            'learning_rate', 
            hyperparams.get("learning_rate", {}).get("min", 5e-6), 
            hyperparams.get("learning_rate", {}).get("max", 5e-3), 
            log=hyperparams.get("learning_rate", {}).get("log", True)
        )
        batch_size = trial.suggest_categorical('batch_size', hyperparams.get("batch_size", [64, 128, 256]))
        n_steps = trial.suggest_categorical('n_steps', hyperparams.get("n_steps", [2048, 4096, 8192]))
        gamma = trial.suggest_float(
            'gamma', 
            hyperparams.get("gamma", {}).get("min", 0.95), 
            hyperparams.get("gamma", {}).get("max", 0.999)
        )
        gae_lambda = trial.suggest_float(
            'gae_lambda', 
            hyperparams.get("gae_lambda", {}).get("min", 0.9), 
            hyperparams.get("gae_lambda", {}).get("max", 0.99)
        )
        n_epochs = trial.suggest_int(
            'n_epochs', 
            hyperparams.get("n_epochs", {}).get("min", 10), 
            hyperparams.get("n_epochs", {}).get("max", 25)
        )
        clip_range = trial.suggest_float(
            'clip_range', 
            hyperparams.get("clip_range", {}).get("min", 0.1), 
            hyperparams.get("clip_range", {}).get("max", 0.3)
        )
        ent_coef = trial.suggest_float(
            'ent_coef', 
            hyperparams.get("ent_coef", {}).get("min", 0.0), 
            hyperparams.get("ent_coef", {}).get("max", 0.05)
        )
        vf_coef = trial.suggest_float(
            'vf_coef', 
            hyperparams.get("vf_coef", {}).get("min", 0.5), 
            hyperparams.get("vf_coef", {}).get("max", 1.0)
        )
        max_grad_norm = trial.suggest_float(
            'max_grad_norm', 
            hyperparams.get("max_grad_norm", {}).get("min", 0.3), 
            hyperparams.get("max_grad_norm", {}).get("max", 0.8)
        )
    else:
        # デフォルト値（設定ファイルが利用できない場合）
        learning_rate = trial.suggest_float('learning_rate', 5e-6, 5e-3, log=True)
        batch_size = trial.suggest_categorical('batch_size', [64, 128, 256])
        n_steps = trial.suggest_categorical('n_steps', [2048, 4096, 8192])
        gamma = trial.suggest_float('gamma', 0.95, 0.999)
        gae_lambda = trial.suggest_float('gae_lambda', 0.9, 0.99)
        n_epochs = trial.suggest_int('n_epochs', 10, 25)
        clip_range = trial.suggest_float('clip_range', 0.1, 0.3)
        ent_coef = trial.suggest_float('ent_coef', 0.0, 0.05)
        vf_coef = trial.suggest_float('vf_coef', 0.5, 1.0)
        max_grad_norm = trial.suggest_float('max_grad_norm', 0.3, 0.8)
    
    print(f"[objective] Hyperparams: lr={learning_rate}, batch={batch_size}, n_steps={n_steps}, gamma={gamma}")
    print(f"[objective] Creating train_env with year_month: {year_month}")
    train_env = create_env(data_dir=data_dir, year_month=year_month)
    print(f"[objective] Creating eval_env with year_month: {year_month}")
    eval_env = create_env(data_dir=data_dir, year_month=year_month)
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
        tensorboard_log=None  # TensorBoardログを無効化
    )
    
    # 設定ファイルから学習パラメータを取得
    if CONFIG_MANAGER is not None:
        if minimal_mode:
            learning_params = CONFIG_MANAGER.get_learning_params("phase2", "minimal_mode")
        elif test_mode:
            learning_params = CONFIG_MANAGER.get_learning_params("phase2", "test_mode")
        else:
            learning_params = CONFIG_MANAGER.get_learning_params("phase2", "normal")
        
        total_timesteps = learning_params.get("total_timesteps", 200000)
        n_eval_episodes = learning_params.get("n_eval_episodes", 5000)
    else:
        # デフォルト値（設定ファイルが利用できない場合）
        if minimal_mode:
            total_timesteps = 5000
            n_eval_episodes = 50
        elif test_mode:
            total_timesteps = 20000
            n_eval_episodes = 200
        else:
            total_timesteps = 200000
            n_eval_episodes = 5000
    
    try:
        print(f"[objective] model.learn start (timesteps: {total_timesteps})")
        model.learn(
            total_timesteps=total_timesteps,
            callback=[eval_callback, checkpoint_callback],
            progress_bar=False  # ProgressBarを無効化
        )
        print(f"[objective] model.learn end")
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
        import datetime
        now_str = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        log_dir = "outputs/logs"
        os.makedirs(log_dir, exist_ok=True)
        log_path = f"{log_dir}/optimize_objective_error_{now_str}_trial{trial.number}.log"
        with open(log_path, "w", encoding="utf-8") as f:
            f.write(f"[Trial {trial.number}] Exception: {e}\n")
            traceback.print_exc(file=f)
        traceback.print_exc()
        return -1000.0

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
    data_dir=None,
    test_mode=False,
    minimal_mode=False,
    resume_existing=False,
    year_month=None
):
    """
    段階的報酬設計モデルの最適化を実行
    
    Args:
        n_trials: 試行回数
        study_name: 研究名
        data_dir: データディレクトリ（Noneの場合はデフォルトパス）
        test_mode: テストモード
        minimal_mode: 最小限モード
        resume_existing: 既存の研究を再開するかどうか
    """
    if data_dir is None:
        data_dir = "kyotei_predictor/data/raw"
    """段階的報酬設計モデルのハイパーパラメータ最適化"""
    
    print("=== 段階的報酬設計モデルのハイパーパラメータ最適化開始 ===")
    print(f"最適化開始時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"試行回数: {n_trials}")
    print(f"テストモード: {test_mode}")
    print(f"最小モード: {minimal_mode}")
    print(f"既存スタディ継続: {resume_existing}")
    
    # ディレクトリ作成
    os.makedirs("./optuna_models", exist_ok=True)
    os.makedirs("./optuna_logs", exist_ok=True)
    os.makedirs("./optuna_tensorboard", exist_ok=True)
    os.makedirs("./optuna_studies", exist_ok=True)
    
    # スタディ名とストレージパスの決定
    if resume_existing:
        # 既存スタディを継続する場合
        # 既存のスタディファイルを探す
        existing_studies = []
        for file in os.listdir("./optuna_studies"):
            if file.endswith(".db") and study_name in file:
                existing_studies.append(file)
        
        if existing_studies:
            # 最新のスタディファイルを使用
            latest_study = max(existing_studies, key=lambda x: os.path.getmtime(os.path.join("./optuna_studies", x)))
            storage_path = f"sqlite:///./optuna_studies/{latest_study}"
            print(f"既存スタディを使用: {latest_study}")
        else:
            # 既存スタディが見つからない場合は新規作成
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            storage_path = f"sqlite:///./optuna_studies/{study_name}_{timestamp}.db"
            print(f"新規スタディを作成: {study_name}_{timestamp}.db")
    else:
        # 新規スタディを作成
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        storage_path = f"sqlite:///./optuna_studies/{study_name}_{timestamp}.db"
        print(f"新規スタディを作成: {study_name}_{timestamp}.db")
    
    # スタディの作成または読み込み
    study = optuna.create_study(
        study_name=study_name,
        storage=storage_path,
        load_if_exists=True,
        direction="maximize"
    )
    
    existing_trials = len(study.trials)
    print(f"既存の試行数: {existing_trials}")
    
    # 最適化の実行（可視化を無効化）
    print(f"最適化開始: データディレクトリ={data_dir}, 年月フィルタ={year_month}")
    study.optimize(
        lambda trial: objective(trial, data_dir=data_dir, test_mode=test_mode, minimal_mode=minimal_mode, year_month=year_month),
        n_trials=n_trials,
        show_progress_bar=False,
        callbacks=None  # コールバックを無効化して可視化を防ぐ
    )
    
    print(f"\n=== 最適化完了 ===")
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
        'test_mode': test_mode,
        'minimal_mode': minimal_mode,
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
        eval_env = create_env(data_dir=data_dir, year_month=year_month)
        
        detailed_results = evaluate_model(best_model, eval_env, n_eval_episodes=500)
        
        # print(f"詳細評価結果:")
        # print(f"  的中率: {detailed_results['hit_rate']*100:.2f}%")
        # print(f"  平均報酬: {detailed_results['mean_reward']:.2f}")
        # print(f"  報酬の標準偏差: {detailed_results['std_reward']:.2f}")
        
        # 評価結果をnpzで保存（OSError対策）
        eval_npz_path = f"./optuna_logs/trial_{study.best_trial.number}/evaluations.npz"
        os.makedirs(os.path.dirname(eval_npz_path), exist_ok=True)
        safe_savez(eval_npz_path, **detailed_results)
        
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
    parser.add_argument('--year-month', type=str, help='年月フィルタ（例: 2024-01）')
    parser.add_argument('--study-name', type=str, default="graduated_reward_optimization", help='Optunaスタディ名')
    parser.add_argument('--n-trials', type=int, default=50, help='試行回数')
    parser.add_argument('--test-mode', action='store_true', help='テストモード（短時間設定）')
    parser.add_argument('--minimal', action='store_true', help='最小限のテストモード（1試行、非常に短い学習時間）')
    parser.add_argument('--resume-existing', action='store_true', help='既存スタディを継続する')
    
    args = parser.parse_args()
    
    # デバッグ情報を追加
    print(f"[DEBUG] main() called with args:")
    print(f"[DEBUG]   --data-dir: {args.data_dir}")
    print(f"[DEBUG]   --year-month: {args.year_month}")
    print(f"[DEBUG]   --minimal: {args.minimal}")
    print(f"[DEBUG]   --test-mode: {args.test_mode}")
    print(f"[DEBUG]   --n-trials: {args.n_trials}")
    print(f"[DEBUG]   sys.argv: {sys.argv}")
    
    # 環境変数からデータディレクトリを取得、コマンドライン引数を優先
    data_dir = os.environ.get('DATA_DIR', args.data_dir)
    print(f"使用するデータディレクトリ: {data_dir}")
    
    # 年月フィルタの確認
    year_month = args.year_month
    print(f"[DEBUG] year_month from args: {year_month}")
    print(f"[DEBUG] year_month type: {type(year_month)}")
    print(f"[DEBUG] year_month is None: {year_month is None}")
    if year_month:
        print(f"使用する年月フィルタ: {year_month}")
    else:
        print("年月フィルタなし: 全期間のデータを使用")
    
    # 最小限モードの場合は設定を調整
    if args.minimal:
        args.n_trials = 1
        print("最小限テストモード: 試行回数1回、非常に短い学習時間")
    
    study = optimize_graduated_reward(
        n_trials=args.n_trials,
        study_name=args.study_name,
        data_dir=data_dir,
        test_mode=args.test_mode,
        minimal_mode=args.minimal,
        resume_existing=args.resume_existing,
        year_month=year_month
    )
    
    print(f"\n=== 最適化完了 ===")
    print(f"最良の試行: {study.best_trial.number}")
    print(f"最良のスコア: {study.best_value:.4f}")
    print(f"総試行数: {len(study.trials)}")
    
    return study

if __name__ == "__main__":
    main() 