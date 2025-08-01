#!/usr/bin/env python3
"""
汎用的な段階的報酬設計モデルのハイパーパラメータ最適化スクリプト
月別データに対応
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
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from kyotei_predictor.pipelines.kyotei_env import KyoteiEnvManager

def create_env(data_dir, bet_amount=100):
    """環境を作成"""
    def make_env():
        env = KyoteiEnvManager(data_dir=data_dir, bet_amount=bet_amount)
        env = Monitor(env)
        return env
    
    return DummyVecEnv([make_env])

def create_env_with_pairs(data_dir, pairs, bet_amount=100):
    """事前検索されたペア情報を使用して環境を作成"""
    def make_env():
        # 事前検索されたペア情報を直接渡す
        env = KyoteiEnvManager(data_dir=data_dir, bet_amount=bet_amount, pairs=pairs)
        env = Monitor(env)
        return env
    
    return DummyVecEnv([make_env])

def objective(trial, data_dir, test_mode=False, data_check_env=None):
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
        
        # 事前作成された環境のペア情報を再利用
        if data_check_env is not None:
            train_env = create_env_with_pairs(data_dir=data_dir, pairs=data_check_env.pairs)
            eval_env = create_env_with_pairs(data_dir=data_dir, pairs=data_check_env.pairs)
        else:
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
            verbose=0,  # 冗長性を減らす
            tensorboard_log=None
        )
        
        # テストモードの場合は短時間設定
        if test_mode:
            total_timesteps = 1000   # テスト用（少し増加）
            n_eval_episodes = 10     # テスト用（少し増加）
        else:
            total_timesteps = 500000  # 本番用（大幅増加）
            n_eval_episodes = 200     # 本番用（元の設定）
        
        print(f"[objective] model.learn start (timesteps: {total_timesteps})")
        model.learn(
            total_timesteps=total_timesteps,
            callback=[eval_callback, checkpoint_callback],
            progress_bar=False
        )
        print(f"[objective] model.learn end")
        
        # 評価
        print(f"[objective] evaluation start (episodes: {n_eval_episodes})")
        eval_results = evaluate_model(model, eval_env, n_eval_episodes)
        print(f"[objective] evaluation end")
        
        # スコア計算（的中率を主要指標とする）
        score = eval_results['hit_rate'] * 100  # パーセンテージに変換
        
        print(f"[objective] Trial {trial.number} completed with score: {score:.4f}")
        return score
        
    except Exception as e:
        print(f"[objective] Trial {trial.number} failed with error: {e}")
        import traceback
        traceback.print_exc()
        return -1000.0  # エラーの場合は低いスコアを返す

def evaluate_model(model, env, n_eval_episodes=200):
    """モデルの評価（改善版）"""
    rewards = []
    hit_types = []
    episode_lengths = []
    detailed_results = []
    
    for episode in range(n_eval_episodes):
        obs = env.reset()
        done = False
        episode_reward = 0
        episode_steps = 0
        episode_hits = 0
        episode_bets = 0
        episode_results = []
        
        while not done:
            action, _ = model.predict(obs, deterministic=True)
            obs, reward, done, info = env.step(action)
            episode_reward += reward
            episode_steps += 1
            
            # 詳細な的中情報を記録
            if 'hit' in info[0]:
                episode_hits += info[0]['hit']
            if 'bet' in info[0]:
                episode_bets += info[0]['bet']
            
            # 的中タイプを記録
            if 'hit_type' in info[0]:
                hit_types.append(info[0]['hit_type'])
            else:
                hit_types.append('unknown')
            
            # 詳細結果を記録
            if 'predicted' in info[0] and 'actual' in info[0]:
                episode_results.append({
                    'predicted': info[0]['predicted'],
                    'actual': info[0]['actual'],
                    'hit': info[0].get('hit', 0),
                    'reward': reward
                })
        
        rewards.append(episode_reward)
        episode_lengths.append(episode_steps)
        detailed_results.append(episode_results)
    
    # 統計計算
    mean_reward = np.mean(rewards)
    std_reward = np.std(rewards)
    mean_episode_length = np.mean(episode_lengths)
    
    # 的中率の詳細計算
    total_hits = sum(1 for hit_type in hit_types if hit_type in ['win', 'first_second', 'first_only'])
    total_bets = len(hit_types)
    hit_rate = total_hits / total_bets if total_bets > 0 else 0
    
    # 的中タイプ別の分析
    hit_type_counts = {}
    for hit_type in hit_types:
        hit_type_counts[hit_type] = hit_type_counts.get(hit_type, 0) + 1
    
    # 詳細な的中分析
    detailed_hit_analysis = {
        'win': hit_type_counts.get('win', 0),
        'first_second': hit_type_counts.get('first_second', 0),
        'first_only': hit_type_counts.get('first_only', 0),
        'miss': hit_type_counts.get('miss', 0),
        'unknown': hit_type_counts.get('unknown', 0)
    }
    
    # 的中率の詳細
    hit_rates = {
        'overall': hit_rate * 100,
        'win': (detailed_hit_analysis['win'] / total_bets * 100) if total_bets > 0 else 0,
        'first_second': (detailed_hit_analysis['first_second'] / total_bets * 100) if total_bets > 0 else 0,
        'first_only': (detailed_hit_analysis['first_only'] / total_bets * 100) if total_bets > 0 else 0
    }
    
    return {
        'mean_reward': mean_reward,
        'std_reward': std_reward,
        'hit_rate': hit_rate * 100,  # パーセンテージで返す
        'hit_rates': hit_rates,
        'detailed_hit_analysis': detailed_hit_analysis,
        'total_hits': total_hits,
        'total_bets': total_bets,
        'mean_episode_length': mean_episode_length,
        'rewards': rewards,
        'hit_types': hit_types,
        'episode_lengths': episode_lengths,
        'detailed_results': detailed_results
    }

def action_to_trifecta(action: int):
    """アクションを三連複に変換"""
    # 6艇の組み合わせを生成
    boats = list(range(1, 7))
    trifectas = []
    for i in range(len(boats)):
        for j in range(i + 1, len(boats)):
            for k in range(j + 1, len(boats)):
                trifectas.append((boats[i], boats[j], boats[k]))
    
    if 0 <= action < len(trifectas):
        return trifectas[action]
    else:
        return (1, 2, 3)  # デフォルト

def safe_savez(filepath, *args, **kwargs):
    """安全なnpz保存（OSError対策）"""
    try:
        np.savez(filepath, *args, **kwargs)
    except OSError as e:
        print(f"npz保存エラー: {e}")
        # 代替ファイル名で保存
        import uuid
        alt_filepath = f"{filepath}_{uuid.uuid4().hex[:8]}.npz"
        np.savez(alt_filepath, *args, **kwargs)
        print(f"代替ファイルに保存: {alt_filepath}")

def optimize_graduated_reward_generic(
    data_month: str,  # "2024-01", "2024-02" など
    n_trials=10,
    study_name=None,
    test_mode=True,
    resume_existing=False
):
    """汎用的な段階的報酬設計モデルのハイパーパラメータ最適化"""
    
    # データディレクトリの構築
    data_dir = f"kyotei_predictor/data/raw/{data_month}"
    
    # スタディ名の自動生成
    if study_name is None:
        study_name = f"graduated_reward_optimization_{data_month.replace('-', '')}"
    
    print(f"=== {data_month}データを使用した段階的報酬設計モデルのハイパーパラメータ最適化開始 ===")
    print(f"最適化開始時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"データディレクトリ: {data_dir}")
    print(f"試行回数: {n_trials}")
    print(f"テストモード: {test_mode}")
    print(f"既存スタディ継続: {resume_existing}")
    
    # データ確認と環境の事前作成
    try:
        # データ確認用の環境を作成（後で再利用）
        data_check_env = KyoteiEnvManager(data_dir=data_dir)
        print(f"データペア数: {len(data_check_env.pairs)}")
        if len(data_check_env.pairs) == 0:
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
    
    # 重要な結果ファイル用の専用ディレクトリ
    os.makedirs("./results", exist_ok=True)
    os.makedirs("./final_results", exist_ok=True)
    
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
        lambda trial: objective(trial, data_dir, test_mode, data_check_env), 
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
        'data_month': data_month,
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
    results_path = f"./optuna_results/{study_name}_{timestamp}.json"
    
    with open(results_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"最適化結果を保存しました: {results_path}")
    
    # 重要な結果ファイルを専用ディレクトリにもコピー
    final_results_path = f"./final_results/{study_name}_{timestamp}_final.json"
    with open(final_results_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"最終結果を保存しました: {final_results_path}")
    
    # 最良モデルの詳細評価
    print("\n=== 最良モデルの詳細評価 ===")
    best_model_path = f"./optuna_models/trial_{study.best_trial.number}/best_model.zip"
    
    if os.path.exists(best_model_path):
        best_model = PPO.load(best_model_path)
        # 事前作成された環境のペア情報を再利用
        if data_check_env is not None:
            eval_env = create_env_with_pairs(data_dir=data_dir, pairs=data_check_env.pairs)
        else:
            eval_env = create_env(data_dir=data_dir)
        
        detailed_results = evaluate_model(best_model, eval_env, n_eval_episodes=200)
        
        print(f"詳細評価結果:")
        print(f"  的中率: {detailed_results['hit_rate']:.2f}%")
        print(f"  平均報酬: {detailed_results['mean_reward']:.2f}")
        print(f"  報酬の標準偏差: {detailed_results['std_reward']:.2f}")
        print(f"  平均エピソード長: {detailed_results['mean_episode_length']:.2f}")
        
        # 的中タイプ別の詳細分析
        print(f"\n=== 的中タイプ別分析 ===")
        hit_analysis = detailed_results['detailed_hit_analysis']
        print(f"  完全的中: {hit_analysis['win']}回 ({detailed_results['hit_rates']['win']:.2f}%)")
        print(f"  2着的中: {hit_analysis['first_second']}回 ({detailed_results['hit_rates']['first_second']:.2f}%)")
        print(f"  1着的中: {hit_analysis['first_only']}回 ({detailed_results['hit_rates']['first_only']:.2f}%)")
        print(f"  不的中: {hit_analysis['miss']}回")
        print(f"  不明: {hit_analysis['unknown']}回")
        
        # 総合的中率
        total_hit_rate = detailed_results['hit_rates']['overall']
        print(f"\n=== 総合的中率 ===")
        print(f"  総的中率: {total_hit_rate:.2f}%")
        print(f"  総的中数: {detailed_results['total_hits']}回")
        print(f"  総ベット数: {detailed_results['total_bets']}回")
        
        # 評価結果をnpzで保存（OSError対策）
        eval_npz_path = f"./optuna_logs/trial_{study.best_trial.number}/evaluations.npz"
        os.makedirs(os.path.dirname(eval_npz_path), exist_ok=True)
        safe_savez(eval_npz_path, **detailed_results)
        
        # 最良モデルをコピー
        import shutil
        best_model_dir = f"./optuna_models/graduated_reward_best_{data_month.replace('-', '')}"
        os.makedirs(best_model_dir, exist_ok=True)
        shutil.copy2(best_model_path, f"{best_model_dir}/best_model.zip")
        
        print(f"最良モデルを保存しました: {best_model_dir}/best_model.zip")
        
        # 詳細評価結果を専用ディレクトリにも保存
        detailed_results_path = f"./results/{study_name}_{timestamp}_detailed.json"
        with open(detailed_results_path, 'w', encoding='utf-8') as f:
            json.dump(detailed_results, f, indent=2, ensure_ascii=False)
        
        print(f"詳細評価結果を保存しました: {detailed_results_path}")
    
    return study

def main():
    """メイン実行関数（コマンドライン引数対応）"""
    parser = argparse.ArgumentParser(description="汎用的な段階的報酬設計モデルのハイパーパラメータ最適化")
    parser.add_argument('--data-month', type=str, required=True, help='データ月（例: 2024-01）')
    parser.add_argument('--study-name', type=str, help='Optunaスタディ名（省略時は自動生成）')
    parser.add_argument('--n-trials', type=int, default=50, help='試行回数')
    parser.add_argument('--test-mode', action='store_true', help='テストモード（短時間設定）')
    parser.add_argument('--resume-existing', action='store_true', help='既存スタディを継続する')
    
    args = parser.parse_args()
    
    study = optimize_graduated_reward_generic(
        data_month=args.data_month,
        n_trials=args.n_trials,
        study_name=args.study_name,
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