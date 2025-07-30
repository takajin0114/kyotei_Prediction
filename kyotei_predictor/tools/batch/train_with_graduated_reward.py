#!/usr/bin/env python3
"""
段階的報酬設計を使用したPPO学習スクリプト
"""

import os
import sys
import time
from datetime import datetime
import numpy as np
import matplotlib.pyplot as plt
from stable_baselines3 import PPO
from stable_baselines3.common.callbacks import EvalCallback, CheckpointCallback
from stable_baselines3.common.monitor import Monitor
from stable_baselines3.common.vec_env import DummyVecEnv
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

def train_with_graduated_reward(
    total_timesteps=1000000,
    learning_rate=3e-4,
    n_steps=2048,
    batch_size=64,
    n_epochs=10,
    gamma=0.99,
    gae_lambda=0.95,
    clip_range=0.2,
    clip_range_vf=None,
    ent_coef=0.01,
    vf_coef=0.5,
    max_grad_norm=0.5,
    use_sde=False,
    sde_sample_freq=-1,
    target_kl=None,
    tensorboard_log=None,
    verbose=1,
    seed=None,
    device="auto",
    _init_setup_model=True
):
    """
    段階的報酬設計を使用したPPO学習
    
    Args:
        total_timesteps: 総学習ステップ数
        learning_rate: 学習率
        n_steps: バッチサイズ
        batch_size: ミニバッチサイズ
        n_epochs: エポック数
        gamma: 割引率
        gae_lambda: GAEラムダ
        clip_range: クリップ範囲
        clip_range_vf: 価値関数のクリップ範囲
        ent_coef: エントロピー係数
        vf_coef: 価値関数係数
        max_grad_norm: 最大勾配ノルム
        use_sde: SDE使用フラグ
        sde_sample_freq: SDEサンプリング頻度
        target_kl: 目標KL
        tensorboard_log: TensorBoardログパス
        verbose: 詳細度
        seed: シード
        device: デバイス
        _init_setup_model: モデル初期化フラグ
        
    Returns:
        学習済みモデル
    """
    
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
        clip_range_vf=clip_range_vf,
        ent_coef=ent_coef,
        vf_coef=vf_coef,
        max_grad_norm=max_grad_norm,
        use_sde=use_sde,
        sde_sample_freq=sde_sample_freq,
        target_kl=target_kl,
        tensorboard_log=tensorboard_log,
        verbose=verbose,
        seed=seed,
        device=device,
        _init_setup_model=_init_setup_model
    )
    
    # コールバック設定
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # チェックポイント保存パス
    checkpoint_path = PROJECT_ROOT / "optuna_models" / f"graduated_reward_{timestamp}"
    checkpoint_path.mkdir(parents=True, exist_ok=True)
    
    # 評価ログパス
    eval_log_path = PROJECT_ROOT / "optuna_logs" / f"graduated_reward_{timestamp}"
    eval_log_path.mkdir(parents=True, exist_ok=True)
    
    eval_callback = EvalCallback(
        eval_env,
        best_model_save_path=str(checkpoint_path),
        log_path=str(eval_log_path),
        eval_freq=max(n_steps // 4, 1),
        deterministic=True,
        render=False
    )
    
    checkpoint_callback = CheckpointCallback(
        save_freq=max(n_steps // 4, 1),
        save_path=str(checkpoint_path),
        name_prefix="checkpoint"
    )
    
    # 学習
    print(f"学習開始: {total_timesteps}ステップ")
    start_time = time.time()
    
    model.learn(
        total_timesteps=total_timesteps,
        callback=[eval_callback, checkpoint_callback]
    )
    
    end_time = time.time()
    print(f"学習完了: {end_time - start_time:.2f}秒")
    
    # 最終モデルを保存
    final_model_path = PROJECT_ROOT / "optuna_models" / f"graduated_reward_final_{timestamp}.zip"
    model.save(str(final_model_path))
    print(f"最終モデルを保存: {final_model_path}")
    
    return model

def main():
    """メイン関数"""
    # 学習パラメータ
    params = {
        'total_timesteps': 1000000,
        'learning_rate': 3e-4,
        'n_steps': 2048,
        'batch_size': 64,
        'n_epochs': 10,
        'gamma': 0.99,
        'gae_lambda': 0.95,
        'clip_range': 0.2,
        'ent_coef': 0.01,
        'vf_coef': 0.5,
        'max_grad_norm': 0.5,
        'verbose': 1
    }
    
    # 学習実行
    model = train_with_graduated_reward(**params)
    
    print("学習完了！")

if __name__ == "__main__":
    main() 