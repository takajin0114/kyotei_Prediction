#!/usr/bin/env python3
"""
段階的報酬設計を使用したPPO学習スクリプト

データソース: file（raw の JSON）または db（SQLite）。
  --data-source db --db-path kyotei_predictor/data/kyotei_races.sqlite --year-month 2025-01
"""

import os
import sys
import argparse
import time
from datetime import datetime
from typing import Optional

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from stable_baselines3 import PPO
from stable_baselines3.common.callbacks import EvalCallback, CheckpointCallback
from stable_baselines3.common.monitor import Monitor
from stable_baselines3.common.vec_env import DummyVecEnv

# プロジェクトルートをパスに追加
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# ログ設定を config.json で一律適用（日時分秒を出す）
import logging
from kyotei_predictor.utils.logger import setup_root_logger_from_config
setup_root_logger_from_config()

from kyotei_predictor.pipelines.kyotei_env import KyoteiEnvManager

# root の設定に従い、重複出力を避けるため propagate のみ使用
logger = logging.getLogger(__name__)


def create_env(
    data_dir: str = "kyotei_predictor/data/raw",
    bet_amount: int = 100,
    year_month: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    data_source: str = "file",
    db_path: Optional[str] = None,
):
    """環境を作成。data_source='db' のときは db_path で SQLite を参照する。"""
    def make_env():
        env = KyoteiEnvManager(
            data_dir=data_dir,
            bet_amount=bet_amount,
            year_month=year_month,
            date_from=date_from,
            date_to=date_to,
            data_source=data_source,
            db_path=db_path,
        )
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
    _init_setup_model=True,
    data_dir: str = "kyotei_predictor/data/raw",
    year_month: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    data_source: str = "file",
    db_path: Optional[str] = None,
):
    """段階的報酬設計を使用したPPO学習。data_source='db' のときは db_path の SQLite を使用。"""
    logger.info("=== 段階的報酬設計を使用したPPO学習開始 ===")
    logger.info("学習開始時刻: %s", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    logger.info("データソース: %s%s", data_source, f"  DB: {db_path}" if data_source == "db" else f"  ディレクトリ: {data_dir}")
    if year_month:
        logger.info("年月フィルタ: %s", year_month)
    if date_from or date_to:
        logger.info("日付範囲: %s ～ %s", date_from or "（なし）", date_to or "（なし）")

    # 環境作成
    logger.info("環境を作成中...")
    env = create_env(data_dir=data_dir, year_month=year_month, date_from=date_from, date_to=date_to, data_source=data_source, db_path=db_path)
    eval_env = create_env(data_dir=data_dir, year_month=year_month, date_from=date_from, date_to=date_to, data_source=data_source, db_path=db_path)
    
    # コールバック設定
    eval_callback = EvalCallback(
        eval_env,
        best_model_save_path="./optuna_models/graduated_reward_best/",
        log_path="./optuna_logs/graduated_reward/",
        eval_freq=max(total_timesteps // 10, 1),
        deterministic=True,
        render=False
    )
    
    checkpoint_callback = CheckpointCallback(
        save_freq=max(total_timesteps // 20, 1),
        save_path="./optuna_models/graduated_reward_checkpoints/",
        name_prefix="graduated_reward_model"
    )
    
    # PPOモデル作成
    logger.info("PPOモデルを作成中...")
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
    
    # 学習実行
    logger.info("学習を開始します（総ステップ数: %s）...", f"{total_timesteps:,}")
    start_time = time.time()
    
    model.learn(
        total_timesteps=total_timesteps,
        callback=[eval_callback, checkpoint_callback],
        progress_bar=True
    )
    
    end_time = time.time()
    training_time = end_time - start_time
    
    logger.info("=== 学習完了 ===")
    logger.info("学習終了時刻: %s", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    logger.info("学習時間: %.2f秒 (%.2f時間)", training_time, training_time / 3600)

    # 最終評価
    logger.info("最終評価を実行中...")
    mean_reward, std_reward = evaluate_model(model, eval_env, n_eval_episodes=100)
    logger.info("最終評価結果: 平均報酬 = %.2f ± %.2f", mean_reward, std_reward)
    
    # モデル保存
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    model_path = f"./optuna_models/graduated_reward_final_{timestamp}.zip"
    model.save(model_path)
    logger.info("モデルを保存しました: %s", model_path)
    
    return model, mean_reward, std_reward

def evaluate_model(model, env, n_eval_episodes=100):
    """モデルの評価"""
    rewards = []
    
    for episode in range(n_eval_episodes):
        obs = env.reset()
        episode_reward = 0
        done = False
        
        while not done:
            action, _ = model.predict(obs, deterministic=True)
            obs, reward, done, _ = env.step(action)
            episode_reward += reward[0]
        
        rewards.append(episode_reward)
        
        if (episode + 1) % 10 == 0:
            logger.info("評価進捗: %s/%s", episode + 1, n_eval_episodes)
    
    mean_reward = np.mean(rewards)
    std_reward = np.std(rewards)
    
    return mean_reward, std_reward

def analyze_training_results(log_path="./optuna_logs/graduated_reward/"):
    """学習結果の分析"""
    logger.info("=== 学習結果分析 ===")

    # ログファイルの確認
    if os.path.exists(log_path):
        logger.info("ログディレクトリ: %s", log_path)
        log_files = os.listdir(log_path)
        logger.info("ログファイル数: %s", len(log_files))
        
        # 評価結果の可視化
        eval_results = []
        for file in log_files:
            if file.endswith('.monitor.csv'):
                file_path = os.path.join(log_path, file)
                try:
                    data = np.genfromtxt(file_path, delimiter=',', skip_header=1)
                    if len(data) > 0:
                        eval_results.extend(data[:, 1])  # 報酬列
                except:
                    continue
        
        if eval_results:
            eval_results = np.array(eval_results)
            logger.info("評価回数: %s", len(eval_results))
            logger.info("平均報酬: %.2f", np.mean(eval_results))
            logger.info("報酬の標準偏差: %.2f", np.std(eval_results))
            logger.info("最大報酬: %.2f", np.max(eval_results))
            logger.info("最小報酬: %.2f", np.min(eval_results))
            
            # 学習曲線の可視化
            plt.figure(figsize=(12, 8))
            
            plt.subplot(2, 2, 1)
            plt.plot(eval_results)
            plt.title('学習曲線（評価報酬）')
            plt.xlabel('評価回数')
            plt.ylabel('平均報酬')
            plt.grid(True)
            
            plt.subplot(2, 2, 2)
            plt.hist(eval_results, bins=30, alpha=0.7)
            plt.title('報酬分布')
            plt.xlabel('報酬')
            plt.ylabel('頻度')
            plt.grid(True)
            
            plt.subplot(2, 2, 3)
            # 移動平均
            window_size = max(1, len(eval_results) // 10)
            moving_avg = np.convolve(eval_results, np.ones(window_size)/window_size, mode='valid')
            plt.plot(moving_avg)
            plt.title(f'移動平均（ウィンドウサイズ: {window_size}）')
            plt.xlabel('評価回数')
            plt.ylabel('移動平均報酬')
            plt.grid(True)
            
            plt.subplot(2, 2, 4)
            # 報酬の改善率
            if len(eval_results) > 1:
                improvements = np.diff(eval_results)
                plt.plot(improvements)
                plt.title('報酬の改善率')
                plt.xlabel('評価回数')
                plt.ylabel('改善量')
                plt.axhline(y=0, color='r', linestyle='--')
                plt.grid(True)
            
            plt.tight_layout()
            plt.savefig('graduated_reward_training_analysis.png', dpi=300, bbox_inches='tight')
            plt.show()
            
            return eval_results
        else:
            logger.info("評価結果が見つかりませんでした。")
            return None
    else:
        logger.info("ログディレクトリが見つかりません: %s", log_path)
        return None

def main():
    """メイン実行関数（コマンドライン引数でデータソース・DBパス・年月を指定可能）"""
    parser = argparse.ArgumentParser(description="段階的報酬設計を使用したPPO学習")
    parser.add_argument("--data-dir", type=str, default="kyotei_predictor/data/raw", help="データディレクトリ（data-source=file のとき）")
    parser.add_argument("--data-source", type=str, choices=["file", "db"], default="file", help="データソース: file=JSON, db=SQLite")
    parser.add_argument("--db-path", type=str, default=None, help="data-source=db のときの SQLite パス（未指定時: kyotei_predictor/data/kyotei_races.sqlite）")
    parser.add_argument("--year-month", type=str, default=None, help="年月フィルタ（例: 2025-01）")
    parser.add_argument("--date-from", type=str, default=None, help="日付範囲の開始（例: 2025-01-01）")
    parser.add_argument("--date-to", type=str, default=None, help="日付範囲の終了（例: 2025-12-31）")
    parser.add_argument("--total-timesteps", type=int, default=500000, help="総学習ステップ数")
    args = parser.parse_args()

    # このファイルは kyotei_predictor/tools/batch/ にあるので、2階層上で kyotei_predictor
    kyotei_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    db_path = args.db_path
    if args.data_source == "db" and not db_path:
        db_path = os.path.join(kyotei_root, "data", "kyotei_races.sqlite")

    logger.info("段階的報酬設計を使用したPPO学習を開始します")
    if args.data_source == "db":
        logger.info("  DB: %s", db_path)
    else:
        logger.info("  データディレクトリ: %s", args.data_dir)

    # 学習実行
    model, mean_reward, std_reward = train_with_graduated_reward(
        total_timesteps=args.total_timesteps,
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
        verbose=1,
        data_dir=args.data_dir,
        year_month=args.year_month,
        date_from=args.date_from,
        date_to=args.date_to,
        data_source=args.data_source,
        db_path=db_path,
    )
    
    # 学習結果分析
    eval_results = analyze_training_results()
    
    # 結果サマリー
    logger.info("=== 学習結果サマリー ===")
    logger.info("段階的報酬設計を使用したPPO学習が完了しました")
    logger.info("最終評価結果: %.2f ± %.2f", mean_reward, std_reward)

    if eval_results is not None:
        logger.info("学習改善: %.2f", eval_results[-1] - eval_results[0])
        logger.info("最大報酬: %.2f", np.max(eval_results))

    logger.info("次のステップ:")
    logger.info("1. 学習曲線を確認して学習の収束性を評価")
    logger.info("2. 必要に応じて学習時間を延長")
    logger.info("3. ハイパーパラメータの調整を検討")

if __name__ == "__main__":
    main() 