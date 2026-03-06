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

# プロジェクトルートをパスに追加（bootstrap 後は Settings を利用）
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(project_root)
sys.path.append(os.path.join(project_root, 'kyotei_predictor'))
try:
    from kyotei_predictor.config.settings import Settings
    project_root = str(Settings.PROJECT_ROOT)
except Exception:
    pass

from pipelines.kyotei_env import KyoteiEnvManager, action_to_trifecta
from kyotei_predictor.utils.logger import get_logging_formatter
try:
    from kyotei_predictor.tools.evaluation.metrics import (
        compute_metrics_from_episodes,
        objective_from_metrics,
        merge_info_into_episode_results,
        OPTIMIZE_FOR_HYBRID,
    )
except ImportError:
    compute_metrics_from_episodes = objective_from_metrics = merge_info_into_episode_results = None
    OPTIMIZE_FOR_HYBRID = "hybrid"

# 学習用ロガー（main内でファイルハンドラを付与。UTF-8でファイル出力し文字化けを避ける）
_opt_logger = logging.getLogger("kyotei_predictor.tools.optimization.optimize_graduated_reward")

# 設定管理クラスをインポート（パッケージ基準で実行ディレクトリに依存しない）
try:
    from kyotei_predictor.config.improvement_config_manager import ImprovementConfigManager
    CONFIG_MANAGER = ImprovementConfigManager()
except ImportError:
    CONFIG_MANAGER = None
    print("Warning: ImprovementConfigManager not available, using default values")

def _log_debug(msg, *args):
    """UTF-8ファイルにのみ出す詳細ログ（コンソールはサマリーのみでログ量・文字化けを抑える）"""
    if args:
        _opt_logger.debug(msg, *args)
    else:
        _opt_logger.debug(msg)


def create_env(data_dir=None, bet_amount=100, year_month=None, data_source="file", db_path=None):
    """
    環境を作成

    Args:
        data_dir: データディレクトリ（data_source=file のとき）
        bet_amount: ベット金額
        year_month: 年月フィルタ（例: "2024-01"）
        data_source: "file" または "db"
        db_path: data_source=db のときの SQLite パス
    """
    if data_dir is None:
        data_dir = "kyotei_predictor/data/raw"
    _log_debug("[create_env] data_dir: %s year_month: %s data_source: %s", data_dir, year_month, data_source)
    def make_env():
        _log_debug("[make_env] Creating KyoteiEnvManager year_month: %s data_source: %s", year_month, data_source)
        env = KyoteiEnvManager(
            data_dir=data_dir,
            bet_amount=bet_amount,
            year_month=year_month,
            data_source=data_source,
            db_path=db_path,
        )
        env = Monitor(env)
        return env
    return DummyVecEnv([make_env])

def objective(trial, data_dir=None, test_mode=False, minimal_mode=False, year_month=None, fast_mode=False, medium_mode=False, data_source="file", db_path=None):
    """
    最適化の目的関数

    Args:
        trial: Optunaの試行オブジェクト
        data_dir: データディレクトリ（data_source=file のとき）
        data_source: "file" または "db"
        db_path: data_source=db のときの SQLite パス
    """
    if data_dir is None:
        data_dir = "kyotei_predictor/data/raw"
    _log_debug("[objective] Trial %s started data_dir=%s year_month=%s data_source=%s", trial.number, data_dir, year_month, data_source)
    
    # 設定ファイルからハイパーパラメータ範囲を取得
    if CONFIG_MANAGER is not None:
        if fast_mode:
            # 高速モード：狭いパラメータ範囲で高速化
            learning_rate = trial.suggest_float('learning_rate', 1e-05, 0.001, log=True)
            batch_size = trial.suggest_categorical('batch_size', [64, 128])
            n_steps = trial.suggest_categorical('n_steps', [1024, 2048])
            gamma = trial.suggest_float('gamma', 0.95, 0.99)
            gae_lambda = trial.suggest_float('gae_lambda', 0.9, 0.95)
            n_epochs = trial.suggest_int('n_epochs', 5, 10)
            clip_range = trial.suggest_float('clip_range', 0.1, 0.2)
            ent_coef = trial.suggest_float('ent_coef', 0.0, 0.03)
            vf_coef = trial.suggest_float('vf_coef', 0.5, 0.8)
            max_grad_norm = trial.suggest_float('max_grad_norm', 0.3, 0.6)
        elif medium_mode:
            # 中速モード：学習ステップ数と評価エピソード数を中程度に設定
            learning_rate = trial.suggest_float('learning_rate', 1e-05, 0.001, log=True)
            batch_size = trial.suggest_categorical('batch_size', [64, 128])
            n_steps = trial.suggest_categorical('n_steps', [1024, 2048])
            gamma = trial.suggest_float('gamma', 0.95, 0.99)
            gae_lambda = trial.suggest_float('gae_lambda', 0.9, 0.95)
            n_epochs = trial.suggest_int('n_epochs', 5, 10)
            clip_range = trial.suggest_float('clip_range', 0.1, 0.2)
            ent_coef = trial.suggest_float('ent_coef', 0.0, 0.03)
            vf_coef = trial.suggest_float('vf_coef', 0.5, 0.8)
            max_grad_norm = trial.suggest_float('max_grad_norm', 0.3, 0.6)
        else:
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
        if fast_mode:
            # 高速モード：狭いパラメータ範囲で高速化
            learning_rate = trial.suggest_float('learning_rate', 1e-05, 0.001, log=True)
            batch_size = trial.suggest_categorical('batch_size', [64, 128])
            n_steps = trial.suggest_categorical('n_steps', [1024, 2048])
            gamma = trial.suggest_float('gamma', 0.95, 0.99)
            gae_lambda = trial.suggest_float('gae_lambda', 0.9, 0.95)
            n_epochs = trial.suggest_int('n_epochs', 5, 10)
            clip_range = trial.suggest_float('clip_range', 0.1, 0.2)
            ent_coef = trial.suggest_float('ent_coef', 0.0, 0.03)
            vf_coef = trial.suggest_float('vf_coef', 0.5, 0.8)
            max_grad_norm = trial.suggest_float('max_grad_norm', 0.3, 0.6)
        elif medium_mode:
            # 中速モード：学習ステップ数と評価エピソード数を中程度に設定
            learning_rate = trial.suggest_float('learning_rate', 1e-05, 0.001, log=True)
            batch_size = trial.suggest_categorical('batch_size', [64, 128])
            n_steps = trial.suggest_categorical('n_steps', [1024, 2048])
            gamma = trial.suggest_float('gamma', 0.95, 0.99)
            gae_lambda = trial.suggest_float('gae_lambda', 0.9, 0.95)
            n_epochs = trial.suggest_int('n_epochs', 5, 10)
            clip_range = trial.suggest_float('clip_range', 0.1, 0.2)
            ent_coef = trial.suggest_float('ent_coef', 0.0, 0.03)
            vf_coef = trial.suggest_float('vf_coef', 0.5, 0.8)
            max_grad_norm = trial.suggest_float('max_grad_norm', 0.3, 0.6)
        else:
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
    
    _log_debug("[objective] Hyperparams: lr=%s batch=%s n_steps=%s gamma=%s", learning_rate, batch_size, n_steps, gamma)
    train_env = create_env(data_dir=data_dir, year_month=year_month, data_source=data_source, db_path=db_path)
    eval_env = create_env(data_dir=data_dir, year_month=year_month, data_source=data_source, db_path=db_path)
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
        if fast_mode:
            # 高速モード：学習ステップ数と評価エピソード数を大幅削減
            total_timesteps = 5000
            n_eval_episodes = 50
        elif medium_mode:
            # 中速モード：学習ステップ数と評価エピソード数を中程度に設定
            total_timesteps = 25000
            n_eval_episodes = 250
        elif minimal_mode:
            learning_params = CONFIG_MANAGER.get_learning_params("phase2", "minimal_mode")
            total_timesteps = learning_params.get("total_timesteps", 5000)
            n_eval_episodes = learning_params.get("n_eval_episodes", 50)
        elif test_mode:
            learning_params = CONFIG_MANAGER.get_learning_params("phase2", "test_mode")
            total_timesteps = learning_params.get("total_timesteps", 20000)
            n_eval_episodes = learning_params.get("n_eval_episodes", 200)
        else:
            learning_params = CONFIG_MANAGER.get_learning_params("phase2", "normal")
            total_timesteps = learning_params.get("total_timesteps", 200000)
            n_eval_episodes = learning_params.get("n_eval_episodes", 5000)
    else:
        # デフォルト値（設定ファイルが利用できない場合）
        if fast_mode:
            total_timesteps = 5000
            n_eval_episodes = 50
        elif medium_mode:
            total_timesteps = 25000
            n_eval_episodes = 250
        elif minimal_mode:
            total_timesteps = 5000
            n_eval_episodes = 50
        elif test_mode:
            total_timesteps = 20000
            n_eval_episodes = 200
        else:
            total_timesteps = 200000
            n_eval_episodes = 5000
    
    try:
        _log_debug("[objective] model.learn start timesteps=%s", total_timesteps)
        model.learn(
            total_timesteps=total_timesteps,
            callback=[eval_callback, checkpoint_callback],
            progress_bar=False  # ProgressBarを無効化
        )
        _log_debug("[objective] model.learn end; evaluate_model start episodes=%s", n_eval_episodes)
        eval_results = evaluate_model(model, eval_env, n_eval_episodes=n_eval_episodes)
        if objective_from_metrics is not None and CONFIG_MANAGER is not None:
            optimize_for = CONFIG_MANAGER.get_optimize_for()
            score = objective_from_metrics(eval_results, optimize_for)
        else:
            hit_rate = eval_results["hit_rate"]
            mean_reward = eval_results["mean_reward"]
            score = hit_rate * 100 + mean_reward / 1000
        _log_debug("[objective] Trial %s score: %s eval=%s", trial.number, score, eval_results)
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
    """
    モデルの評価。指標を分離して返す（hit_rate, mean_reward, ROI, 投資額, 払戻額 等）。
    info に payout, bet_amount, hit が含まれる場合は ROI も計算する。
    """
    rewards = []
    episode_infos = []

    for episode in range(n_eval_episodes):
        obs = env.reset()
        episode_reward = 0
        done = False
        last_info = None
        while not done:
            action, _ = model.predict(obs, deterministic=True)
            obs, reward, done, info = env.step(action)
            episode_reward += reward[0]
            last_info = info
        rewards.append(episode_reward)
        episode_infos.append(last_info if last_info is not None else {})

    if merge_info_into_episode_results is not None and compute_metrics_from_episodes is not None:
        hit_count, payouts, bet_amounts = merge_info_into_episode_results(rewards, episode_infos)
        metrics = compute_metrics_from_episodes(rewards, hit_count, payouts, bet_amounts)
    else:
        hit_count = 0
        for inf in episode_infos:
            i = inf[0] if isinstance(inf, (list, tuple)) and len(inf) > 0 else inf
            if isinstance(i, dict):
                hit_count += i.get("hit", 0)
        metrics = {
            "hit_rate": hit_count / n_eval_episodes if n_eval_episodes else 0.0,
            "mean_reward": float(np.mean(rewards)) if rewards else 0.0,
            "std_reward": float(np.std(rewards)) if len(rewards) > 1 else 0.0,
            "roi_pct": 0.0,
            "total_bet": 0.0,
            "total_payout": 0.0,
            "hit_count": hit_count,
            "n_episodes": n_eval_episodes,
        }
    metrics["std_reward"] = metrics.get("std_reward", float(np.std(rewards)) if len(rewards) > 1 else 0.0)
    return metrics

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
    data_source="file",
    db_path=None,
    test_mode=False,
    minimal_mode=False,
    fast_mode=False,
    medium_mode=False,
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
    
    print("=== Optimization start ===")
    _opt_logger.info("最適化開始時刻: %s 試行回数: %s test=%s minimal=%s fast=%s medium=%s resume=%s",
                    datetime.now().strftime('%Y-%m-%d %H:%M:%S'), n_trials, test_mode, minimal_mode, fast_mode, medium_mode, resume_existing)
    
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
            latest_study = max(existing_studies, key=lambda x: os.path.getmtime(os.path.join("./optuna_studies", x)))
            storage_path = f"sqlite:///./optuna_studies/{latest_study}"
            _opt_logger.info("既存スタディを使用: %s", latest_study)
        else:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            storage_path = f"sqlite:///./optuna_studies/{study_name}_{timestamp}.db"
            _opt_logger.info("新規スタディを作成: %s", study_name + "_" + timestamp + ".db")
    else:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        storage_path = f"sqlite:///./optuna_studies/{study_name}_{timestamp}.db"
        _opt_logger.info("新規スタディを作成: %s", study_name + "_" + timestamp + ".db")
    
    # スタディの作成または読み込み
    study = optuna.create_study(
        study_name=study_name,
        storage=storage_path,
        load_if_exists=True,
        direction="maximize"
    )
    
    existing_trials = len(study.trials)
    _opt_logger.info("既存の試行数: %s", existing_trials)
    _opt_logger.info("最適化開始: データディレクトリ=%s 年月フィルタ=%s", data_dir, year_month)
    study.optimize(
        lambda trial: objective(trial, data_dir=data_dir, data_source=data_source, db_path=db_path, test_mode=test_mode, minimal_mode=minimal_mode, fast_mode=fast_mode, medium_mode=medium_mode, year_month=year_month),
        n_trials=n_trials,
        show_progress_bar=False,
        callbacks=None  # コールバックを無効化して可視化を防ぐ
    )
    
    _opt_logger.info("最適化完了 最良試行=%s 最良スコア=%s 最良パラメータ=%s", study.best_trial.number, study.best_value, study.best_params)
    # 結果をJSONファイルに保存
    results = {
        'optimization_time': datetime.now().isoformat(),
        'study_name': study_name,
        'n_trials': n_trials,
        'existing_trials': existing_trials,
        'total_trials': len(study.trials),
        'test_mode': test_mode,
        'minimal_mode': minimal_mode,
        'fast_mode': fast_mode,
        'medium_mode': medium_mode,
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
    
    _opt_logger.info("最適化結果を保存: %s", results_path)
    
    # 最良モデルの詳細評価
    _opt_logger.info("最良モデルの詳細評価開始")
    best_model_path = f"./optuna_models/trial_{study.best_trial.number}/best_model.zip"
    
    if os.path.exists(best_model_path):
        best_model = PPO.load(best_model_path)
        eval_env = create_env(data_dir=data_dir, year_month=year_month, data_source=data_source, db_path=db_path)
        
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

def _setup_optimization_log(project_root):
    """学習ログをUTF-8ファイルに出力（コンソール文字化け・ログ量抑制のため）"""
    log_dir = os.path.join(project_root, "kyotei_predictor", "logs")
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, f"optimize_graduated_reward_{datetime.now().strftime('%Y%m%d')}.log")
    fh = logging.FileHandler(log_file, encoding="utf-8")
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(get_logging_formatter())
    _opt_logger.setLevel(logging.DEBUG)
    _opt_logger.addHandler(fh)
    _opt_logger.info("Log file: %s", log_file)
    return log_file


def main():
    """メイン実行関数（コマンドライン引数対応）"""
    parser = argparse.ArgumentParser(description="段階的報酬設計モデルのハイパーパラメータ最適化")
    parser.add_argument('--data-dir', type=str, default="kyotei_predictor/data/raw", help='データディレクトリ（data-source=file のとき）')
    parser.add_argument('--data-source', type=str, choices=['file', 'db'], default='db', help='データソース: file=JSON, db=SQLite（デフォルト: db）')
    parser.add_argument('--db-path', type=str, default=None, help='data-source=db のときの SQLite パス（未指定時は kyotei_predictor/data/kyotei_races.sqlite）')
    parser.add_argument('--year-month', type=str, help='年月フィルタ（例: 2024-01）')
    parser.add_argument('--study-name', type=str, default="graduated_reward_optimization", help='Optunaスタディ名')
    parser.add_argument('--n-trials', type=int, default=50, help='試行回数')
    parser.add_argument('--test-mode', action='store_true', help='テストモード（短時間設定）')
    parser.add_argument('--minimal', action='store_true', help='最小限のテストモード（1試行、非常に短い学習時間）')
    parser.add_argument('--fast-mode', action='store_true', help='高速モード（学習ステップ数と評価エピソード数を大幅削減）')
    parser.add_argument('--medium-mode', action='store_true', help='中速モード（学習ステップ数と評価エピソード数を中程度に設定）')
    parser.add_argument('--resume-existing', action='store_true', help='既存スタディを継続する')
    
    args = parser.parse_args()
    _setup_optimization_log(project_root)

    _log_debug("main() args: data_dir=%s data_source=%s db_path=%s year_month=%s", args.data_dir, getattr(args, 'data_source', 'file'), getattr(args, 'db_path', None), args.year_month)
    data_dir = os.environ.get('DATA_DIR', args.data_dir)
    data_source = getattr(args, 'data_source', 'file')
    db_path = getattr(args, 'db_path', None)
    if data_source == 'db' and not db_path:
        db_path = os.path.join(project_root, "kyotei_predictor", "data", "kyotei_races.sqlite")
    print("Data dir: " + data_dir)
    if data_source == 'db':
        print("Data source: db  path: " + (db_path or ""))
    _opt_logger.info("使用するデータ: data_source=%s data_dir=%s db_path=%s", data_source, data_dir, db_path)

    year_month = args.year_month
    if year_month:
        print("Year-month: " + year_month)
        _opt_logger.info("使用する年月フィルタ: %s", year_month)
    else:
        print("Year-month: (all)")
        _opt_logger.info("年月フィルタなし: 全期間のデータを使用")

    if args.minimal:
        args.n_trials = 1
        print("Minimal mode: 1 trial")
        _opt_logger.info("最小限テストモード: 試行回数1回")

    study = optimize_graduated_reward(
        n_trials=args.n_trials,
        study_name=args.study_name,
        data_dir=data_dir,
        data_source=data_source,
        db_path=db_path,
        test_mode=args.test_mode,
        minimal_mode=args.minimal,
        fast_mode=args.fast_mode,
        medium_mode=args.medium_mode,
        resume_existing=args.resume_existing,
        year_month=year_month
    )
    
    print("\n=== Optimization done ===")
    print("Best trial: " + str(study.best_trial.number))
    print("Best score: " + str(round(study.best_value, 4)))
    print("Total trials: " + str(len(study.trials)))
    _opt_logger.info("最適化完了 最良試行=%s 最良スコア=%s 総試行数=%s", study.best_trial.number, study.best_value, len(study.trials))

    # 2.1.4 学習ログの記録: 各実行の短いサマリを logs/ に残す
    run_ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    summary = {
        "timestamp": run_ts,
        "data_dir": data_dir,
        "year_month": year_month or "(all)",
        "data_source": data_source,
        "n_trials": len(study.trials),
        "best_trial": study.best_trial.number,
        "best_value": float(study.best_value),
        "best_model_path": f"./optuna_models/trial_{study.best_trial.number}/best_model.zip",
        "best_model_copied_to": "./optuna_models/graduated_reward_best/best_model.zip",
    }
    log_dir = os.path.join(project_root, "logs")
    os.makedirs(log_dir, exist_ok=True)
    summary_path = os.path.join(log_dir, f"learning_run_{run_ts}.json")
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    _opt_logger.info("学習 Run サマリ: %s", summary_path)

    return study

if __name__ == "__main__":
    main() 