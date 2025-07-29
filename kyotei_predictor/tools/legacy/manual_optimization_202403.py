#!/usr/bin/env python3
"""
2024年3月データを使用した手動最適化スクリプト
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
import time

# プロジェクトルートをパスに追加
sys.path.append('.')

from kyotei_predictor.pipelines.kyotei_env import KyoteiEnvManager

def test_data_loading():
    """データ読み込みテスト"""
    print("=== データ読み込みテスト ===")
    try:
        env = KyoteiEnvManager(data_dir="kyotei_predictor/data/raw/2024-03")
        print(f"データペア数: {len(env.pairs)}")
        if len(env.pairs) > 0:
            print("データ読み込み成功")
            return True
        else:
            print("データペアが存在しません")
            return False
    except Exception as e:
        print(f"データ読み込みエラー: {e}")
        return False

def test_environment():
    """環境テスト"""
    print("=== 環境テスト ===")
    try:
        def make_env():
            env = KyoteiEnvManager(data_dir="kyotei_predictor/data/raw/2024-03")
            env = Monitor(env)
            return env
        
        env = DummyVecEnv([make_env])
        obs = env.reset()
        print(f"環境作成成功: 観測形状 = {obs.shape}")
        return True
    except Exception as e:
        print(f"環境作成エラー: {e}")
        return False

def test_model_creation():
    """モデル作成テスト"""
    print("=== モデル作成テスト ===")
    try:
        def make_env():
            env = KyoteiEnvManager(data_dir="kyotei_predictor/data/raw/2024-03")
            env = Monitor(env)
            return env
        
        env = DummyVecEnv([make_env])
        
        model = PPO(
            "MlpPolicy",
            env,
            learning_rate=0.001,
            batch_size=64,
            n_steps=1024,
            gamma=0.95,
            n_epochs=10,
            clip_range=0.2,
            ent_coef=0.01,
            verbose=0,
            tensorboard_log=None
        )
        print("モデル作成成功")
        return True
    except Exception as e:
        print(f"モデル作成エラー: {e}")
        return False

def test_training():
    """学習テスト"""
    print("=== 学習テスト ===")
    try:
        def make_env():
            env = KyoteiEnvManager(data_dir="kyotei_predictor/data/raw/2024-03")
            env = Monitor(env)
            return env
        
        env = DummyVecEnv([make_env])
        
        model = PPO(
            "MlpPolicy",
            env,
            learning_rate=0.001,
            batch_size=64,
            n_steps=1024,
            gamma=0.95,
            n_epochs=10,
            clip_range=0.2,
            ent_coef=0.01,
            verbose=0,
            tensorboard_log=None
        )
        
        print("学習開始...")
        model.learn(total_timesteps=1000, progress_bar=False)
        print("学習完了")
        
        # 簡単な評価
        obs = env.reset()
        action, _ = model.predict(obs, deterministic=True)
        print(f"予測アクション: {action}")
        
        return True
    except Exception as e:
        print(f"学習テストエラー: {e}")
        return False

def run_simple_optimization():
    """シンプルな最適化実行"""
    print("=== シンプルな最適化実行 ===")
    
    def objective(trial):
        print(f"[objective] Trial {trial.number} started")
        
        try:
            # ハイパーパラメータ
            learning_rate = trial.suggest_float('learning_rate', 1e-4, 1e-2, log=True)
            batch_size = trial.suggest_categorical('batch_size', [32, 64, 128])
            n_steps = trial.suggest_categorical('n_steps', [512, 1024])
            
            # 環境作成
            def make_env():
                env = KyoteiEnvManager(data_dir="kyotei_predictor/data/raw/2024-03")
                env = Monitor(env)
                return env
            
            env = DummyVecEnv([make_env])
            
            # モデル作成
            model = PPO(
                "MlpPolicy",
                env,
                learning_rate=learning_rate,
                batch_size=batch_size,
                n_steps=n_steps,
                gamma=0.95,
                n_epochs=5,
                clip_range=0.2,
                ent_coef=0.01,
                verbose=0,
                tensorboard_log=None
            )
            
            # 学習
            model.learn(total_timesteps=2000, progress_bar=False)
            
            # 簡単な評価
            rewards = []
            for _ in range(10):
                obs = env.reset()
                done = False
                episode_reward = 0
                while not done:
                    action, _ = model.predict(obs, deterministic=True)
                    obs, reward, done, _ = env.step(action)
                    episode_reward += reward
                rewards.append(episode_reward)
            
            mean_reward = np.mean(rewards)
            print(f"[objective] Trial {trial.number} mean_reward: {mean_reward:.4f}")
            return mean_reward
            
        except Exception as e:
            print(f"[objective] Trial {trial.number} error: {e}")
            return -1000.0
    
    # スタディ作成
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    study_name = f"opt_202403_manual_{timestamp}"
    storage_path = f"sqlite:///optuna_studies/{study_name}.db"
    
    os.makedirs("./optuna_studies", exist_ok=True)
    os.makedirs("./optuna_results", exist_ok=True)
    
    study = optuna.create_study(
        direction="maximize",
        study_name=study_name,
        storage=storage_path,
        load_if_exists=True
    )
    
    print(f"スタディ名: {study_name}")
    print("最適化を開始します...")
    
    # 最適化実行
    study.optimize(objective, n_trials=2, show_progress_bar=True)
    
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
        'n_trials': 2,
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
    
    results_path = f"./optuna_results/graduated_reward_optimization_202403_manual_{timestamp}.json"
    
    with open(results_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"最適化結果を保存しました: {results_path}")
    
    return study

def main():
    """メイン実行関数"""
    print("=== 2024年3月データを使用した手動最適化開始 ===")
    print(f"開始時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 段階的テスト
    if not test_data_loading():
        print("データ読み込みテストに失敗しました")
        return None
    
    if not test_environment():
        print("環境テストに失敗しました")
        return None
    
    if not test_model_creation():
        print("モデル作成テストに失敗しました")
        return None
    
    if not test_training():
        print("学習テストに失敗しました")
        return None
    
    # 最適化実行
    study = run_simple_optimization()
    
    print(f"最適化完了時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    return study

if __name__ == "__main__":
    main()