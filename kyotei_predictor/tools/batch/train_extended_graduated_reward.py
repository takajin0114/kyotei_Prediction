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

from kyotei_predictor.pipelines.kyotei_env import KyoteiEnvManager

def create_env(data_dir=None, bet_amount=100):
    """環境を作成"""
    def make_env():
        if data_dir is None:
            data_dir = PROJECT_ROOT / "kyotei_predictor" / "data" / "raw"
        env = KyoteiEnvManager(data_dir=str(data_dir), bet_amount=bet_amount)
        env = Monitor(env)
        return env
    
    return DummyVecEnv([make_env])

def train_extended_graduated_reward(
    total_timesteps=1000000,  # 100万ステップ
    eval_freq=50000,  # 5万ステップごとに評価
    save_freq=50000,  # 5万ステップごとに保存
    data_dir=None,
    bet_amount=100,
    model_path=None  # 既存モデルから継続学習する場合
):
    """
    段階的報酬設計モデルの拡張学習
    
    Args:
        total_timesteps: 総学習ステップ数
        eval_freq: 評価頻度
        save_freq: 保存頻度
        data_dir: データディレクトリ
        bet_amount: ベット金額
        model_path: 既存モデルのパス
        
    Returns:
        学習済みモデル
    """
    
    # 環境作成
    env = create_env(data_dir, bet_amount)
    eval_env = create_env(data_dir, bet_amount)
    
    # モデル作成（既存モデルから継続学習する場合）
    if model_path and os.path.exists(model_path):
        print(f"既存モデルから継続学習: {model_path}")
        model = PPO.load(model_path, env=env)
    else:
        print("新規モデルを作成")
        model = PPO(
            "MlpPolicy",
            env,
            learning_rate=3e-4,
            n_steps=2048,
            batch_size=64,
            n_epochs=10,
            gamma=0.99,
            gae_lambda=0.95,
            clip_range=0.2,
            ent_coef=0.01,
            vf_coef=0.5,
            max_grad_norm=0.5,
            verbose=1
        )
    
    # コールバック設定
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # チェックポイント保存パス
    checkpoint_path = PROJECT_ROOT / "optuna_models" / f"extended_graduated_reward_{timestamp}"
    checkpoint_path.mkdir(parents=True, exist_ok=True)
    
    # 評価ログパス
    eval_log_path = PROJECT_ROOT / "optuna_logs" / f"extended_graduated_reward_{timestamp}"
    eval_log_path.mkdir(parents=True, exist_ok=True)
    
    eval_callback = EvalCallback(
        eval_env,
        best_model_save_path=str(checkpoint_path),
        log_path=str(eval_log_path),
        eval_freq=eval_freq,
        deterministic=True,
        render=False
    )
    
    checkpoint_callback = CheckpointCallback(
        save_freq=save_freq,
        save_path=str(checkpoint_path),
        name_prefix="extended_checkpoint"
    )
    
    # 学習
    print(f"拡張学習開始: {total_timesteps}ステップ")
    start_time = datetime.now()
    
    model.learn(
        total_timesteps=total_timesteps,
        callback=[eval_callback, checkpoint_callback]
    )
    
    end_time = datetime.now()
    training_time = end_time - start_time
    print(f"拡張学習完了: {training_time}")
    
    # 最終モデルを保存
    final_model_path = PROJECT_ROOT / "optuna_models" / f"extended_graduated_reward_final_{timestamp}.zip"
    model.save(str(final_model_path))
    print(f"最終モデルを保存: {final_model_path}")
    
    # 学習結果を保存
    results = {
        'training_time': str(training_time),
        'total_timesteps': total_timesteps,
        'eval_freq': eval_freq,
        'save_freq': save_freq,
        'bet_amount': bet_amount,
        'model_path': str(final_model_path),
        'timestamp': timestamp
    }
    
    results_path = PROJECT_ROOT / "optuna_results" / f"extended_graduated_reward_{timestamp}.json"
    results_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(results_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"学習結果を保存: {results_path}")
    
    return model

def main():
    """メイン関数"""
    # 学習パラメータ
    params = {
        'total_timesteps': 1000000,
        'eval_freq': 50000,
        'save_freq': 50000,
        'bet_amount': 100
    }
    
    # 学習実行
    model = train_extended_graduated_reward(**params)
    
    print("拡張学習完了！")

if __name__ == "__main__":
    main() 