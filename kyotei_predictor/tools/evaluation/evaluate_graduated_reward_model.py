#!/usr/bin/env python3
"""
段階的報酬モデルの評価スクリプト
"""

import argparse
import os
import sys
import json
import numpy as np

# 可視化を無効化
import matplotlib
matplotlib.use('Agg')  # バックエンドをAggに設定（非表示）
import matplotlib.pyplot as plt
plt.ioff()  # インタラクティブモードを無効化

# 日本語フォント設定
import matplotlib.font_manager as fm
plt.rcParams['font.family'] = ['DejaVu Sans', 'Hiragino Sans', 'Yu Gothic', 'Meiryo', 'Takao', 'IPAexGothic', 'IPAPGothic', 'VL PGothic', 'Noto Sans CJK JP']

from datetime import datetime
from stable_baselines3 import PPO
from stable_baselines3.common.vec_env import DummyVecEnv

# プロジェクトルートをパスに追加
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(project_root)
sys.path.append(os.path.join(project_root, 'kyotei_predictor'))

from pipelines.kyotei_env import KyoteiEnvManager
from pipelines.kyotei_env import action_to_trifecta

try:
    from kyotei_predictor.tools.evaluation.metrics import (
        compute_metrics_from_episodes,
        merge_info_into_episode_results,
    )
except ImportError:
    compute_metrics_from_episodes = None
    merge_info_into_episode_results = None

def evaluate_graduated_reward_model(
    model_path=None,
    n_eval_episodes=1000,
    data_dir=None
):
    """
    段階的報酬モデルの評価を実行
    
    Args:
        model_path: モデルファイルのパス（Noneの場合はデフォルトパス）
        n_eval_episodes: 評価エピソード数
        data_dir: データディレクトリ（Noneの場合はデフォルトパス）
    
    Returns:
        評価結果の辞書
    """
    # デフォルトパスの設定
    if model_path is None:
        model_path = os.path.join(os.getcwd(), "optuna_models", "graduated_reward_best", "best_model.zip")
    
    if data_dir is None:
        data_dir = "kyotei_predictor/data/raw"
    """
    段階的報酬モデルの評価を実行
    
    Args:
        model_path: モデルファイルのパス
        n_eval_episodes: 評価エピソード数
        data_dir: データディレクトリ
    
    Returns:
        評価結果の辞書
    """
    print(f"=== 段階的報酬モデル評価 ===")
    print(f"モデルパス: {model_path}")
    print(f"評価エピソード数: {n_eval_episodes}")
    print(f"データディレクトリ: {data_dir}")
    
    # モデルの読み込み
    try:
        model = PPO.load(model_path)
        print(f"モデルを読み込みました: {model_path}")
    except Exception as e:
        print(f"モデル読み込みエラー: {e}")
        return None
    
    # 環境の作成
    try:
        env_manager = KyoteiEnvManager(data_dir=data_dir)
        eval_env = DummyVecEnv([lambda: env_manager])
        print(f"評価環境を作成しました")
    except Exception as e:
        print(f"環境作成エラー: {e}")
        return None
    
    # 評価実行
    print(f"\n評価を開始します...")
    
    rewards = []
    actions = []
    arrival_tuples = []
    hit_types = []
    episode_infos = []

    for episode in range(n_eval_episodes):
        if episode % 100 == 0:
            print(f"評価進捗: {episode}/{n_eval_episodes}")
        
        obs = eval_env.reset()
        episode_reward = 0
        done = False
        last_info = None
        while not done:
            action, _ = model.predict(obs, deterministic=True)
            obs, reward, done, info = eval_env.step(action)
            episode_reward += reward[0]
            last_info = info
            if done:
                actions.append(action[0])
                if 'arrival' in info[0]:
                    arrival_tuples.append(info[0]['arrival'])
                trifecta = action_to_trifecta(action[0])
                arrival = info[0].get('arrival', (1, 2, 3))
                if len(arrival) == 3:
                    is_win = trifecta == arrival
                    first_hit = trifecta[0] == arrival[0]
                    second_hit = trifecta[1] == arrival[1]
                    if is_win:
                        hit_types.append('win')
                    elif first_hit and second_hit:
                        hit_types.append('first_second')
                    elif first_hit:
                        hit_types.append('first_only')
                    else:
                        hit_types.append('miss')
                else:
                    hit_types.append('miss')
        rewards.append(episode_reward)
        episode_infos.append(last_info if last_info is not None else {})
    
    # 評価指標の分離（ROI, 投資額, 払戻額 等）
    if merge_info_into_episode_results is not None and compute_metrics_from_episodes is not None:
        hit_count, payouts, bet_amounts = merge_info_into_episode_results(rewards, episode_infos)
        metrics = compute_metrics_from_episodes(rewards, hit_count, payouts, bet_amounts)
    else:
        hit_count = sum(1 for t in hit_types if t == 'win')
        metrics = {
            "hit_rate": hit_count / len(rewards) if rewards else 0.0,
            "mean_reward": float(np.mean(rewards)) if rewards else 0.0,
            "std_reward": float(np.std(rewards)) if len(rewards) > 1 else 0.0,
            "roi_pct": 0.0,
            "total_bet": 0.0,
            "total_payout": 0.0,
            "hit_count": hit_count,
            "n_episodes": len(rewards),
        }

    # 統計分析
    print("\n=== 評価結果統計 ===")
    
    rewards_arr = np.array(rewards)
    print(f"総エピソード数: {len(rewards_arr)}")
    print(f"平均報酬: {np.mean(rewards_arr):.2f}")
    print(f"報酬の標準偏差: {np.std(rewards_arr):.2f}")
    print(f"最大報酬: {np.max(rewards_arr):.2f}")
    print(f"最小報酬: {np.min(rewards_arr):.2f}")
    print(f"的中件数: {metrics.get('hit_count', 0)}  hit_rate: {metrics.get('hit_rate', 0)*100:.2f}%")
    print(f"ROI: {metrics.get('roi_pct', 0):.2f}%  投資額: {metrics.get('total_bet', 0):.0f}  払戻額: {metrics.get('total_payout', 0):.2f}")
    
    # 的中率分析
    hit_type_counts = {}
    for hit_type in hit_types:
        hit_type_counts[hit_type] = hit_type_counts.get(hit_type, 0) + 1
    
    print(f"\n=== 的中率分析 ===")
    print(f"的中: {hit_type_counts.get('win', 0)}回 ({hit_type_counts.get('win', 0)/len(hit_types)*100:.2f}%)")
    print(f"2着的中: {hit_type_counts.get('first_second', 0)}回 ({hit_type_counts.get('first_second', 0)/len(hit_types)*100:.2f}%)")
    print(f"1着的中: {hit_type_counts.get('first_only', 0)}回 ({hit_type_counts.get('first_only', 0)/len(hit_types)*100:.2f}%)")
    print(f"不的中: {hit_type_counts.get('miss', 0)}回 ({hit_type_counts.get('miss', 0)/len(hit_types)*100:.2f}%)")
    
    # 報酬分布分析
    print(f"\n=== 報酬分布分析 ===")
    positive_rewards = rewards_arr[rewards_arr > -100]
    negative_rewards = rewards_arr[rewards_arr <= -100]
    
    print(f"正の報酬: {len(positive_rewards)}回 ({len(positive_rewards)/len(rewards_arr)*100:.2f}%)")
    print(f"負の報酬: {len(negative_rewards)}回 ({len(negative_rewards)/len(rewards_arr)*100:.2f}%)")
    
    if len(positive_rewards) > 0:
        print(f"正の報酬の平均: {np.mean(positive_rewards):.2f}")
        print(f"正の報酬の最大: {np.max(positive_rewards):.2f}")
    
    # 可視化
    print("\n=== 結果の可視化 ===")
    create_evaluation_plots(rewards_arr.tolist(), hit_types, model_path)
    
    # 結果をJSONファイルに保存（分解指標を含む）
    results = {
        'evaluation_time': datetime.now().isoformat(),
        'model_path': model_path,
        'n_episodes': n_eval_episodes,
        'statistics': {
            'mean_reward': float(np.mean(rewards)),
            'std_reward': float(np.std(rewards)),
            'max_reward': float(np.max(rewards)),
            'min_reward': float(np.min(rewards)),
            'hit_rate': hit_type_counts.get('win', 0) / len(hit_types) if hit_types else 0,
            'first_second_rate': hit_type_counts.get('first_second', 0) / len(hit_types) if hit_types else 0,
            'first_only_rate': hit_type_counts.get('first_only', 0) / len(hit_types) if hit_types else 0,
            'miss_rate': hit_type_counts.get('miss', 0) / len(hit_types) if hit_types else 0,
            'positive_reward_rate': len(positive_rewards) / len(rewards) if rewards else 0,
            'roi_pct': metrics.get('roi_pct', 0),
            'total_bet': metrics.get('total_bet', 0),
            'total_payout': metrics.get('total_payout', 0),
            'hit_count': metrics.get('hit_count', 0),
        },
        'hit_type_counts': hit_type_counts,
        'metrics': metrics,
    }
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = os.path.join(os.getcwd(), "outputs")
    results_path = os.path.join(output_dir, f"graduated_reward_evaluation_{timestamp}.json")
    
    os.makedirs(output_dir, exist_ok=True)
    with open(results_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"評価結果を保存しました: {results_path}")
    
    return results

def create_evaluation_plots(rewards, hit_types, model_path):
    """評価結果の可視化"""
    
    plt.figure(figsize=(15, 10))
    
    # 報酬分布
    plt.subplot(2, 3, 1)
    plt.hist(rewards, bins=50, alpha=0.7, color='blue')
    plt.title('報酬分布')
    plt.xlabel('報酬')
    plt.ylabel('頻度')
    plt.grid(True)
    
    # 的中タイプの分布
    plt.subplot(2, 3, 2)
    hit_type_counts = {}
    for hit_type in hit_types:
        hit_type_counts[hit_type] = hit_type_counts.get(hit_type, 0) + 1
    
    labels = ['的中', '2着的中', '1着的中', '不的中']
    values = [hit_type_counts.get('win', 0), hit_type_counts.get('first_second', 0), 
              hit_type_counts.get('first_only', 0), hit_type_counts.get('miss', 0)]
    colors = ['green', 'orange', 'yellow', 'red']
    
    plt.pie(values, labels=labels, autopct='%1.1f%%', colors=colors)
    plt.title('的中タイプ分布')
    
    # 報酬の時系列
    plt.subplot(2, 3, 3)
    plt.plot(rewards)
    plt.title('報酬の時系列')
    plt.xlabel('エピソード')
    plt.ylabel('報酬')
    plt.grid(True)
    
    # 報酬の累積平均
    plt.subplot(2, 3, 4)
    cumulative_avg = np.cumsum(rewards) / np.arange(1, len(rewards) + 1)
    plt.plot(cumulative_avg)
    plt.title('報酬の累積平均')
    plt.xlabel('エピソード')
    plt.ylabel('累積平均報酬')
    plt.grid(True)
    
    # 報酬の箱ひげ図
    plt.subplot(2, 3, 5)
    plt.boxplot(rewards)
    plt.title('報酬の箱ひげ図')
    plt.ylabel('報酬')
    plt.grid(True)
    
    # 的中率の推移
    plt.subplot(2, 3, 6)
    window_size = 100
    hit_rates = []
    for i in range(window_size, len(hit_types) + 1):
        window = hit_types[i-window_size:i]
        hit_rate = window.count('win') / len(window)
        hit_rates.append(hit_rate)
    
    plt.plot(range(window_size, len(hit_types) + 1), hit_rates)
    plt.title(f'的中率の推移 (ウィンドウサイズ: {window_size})')
    plt.xlabel('エピソード')
    plt.ylabel('的中率')
    plt.grid(True)
    
    plt.tight_layout()
    
    # 保存（表示なし）
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = os.path.join(os.getcwd(), "outputs")
    os.makedirs(output_dir, exist_ok=True)
    plot_path = os.path.join(output_dir, f"graduated_reward_evaluation_plots_{timestamp}.png")
    plt.savefig(plot_path, dpi=300, bbox_inches='tight')
    plt.close()  # メモリを解放
    
    print(f"可視化結果を保存しました: {plot_path}")

def main():
    parser = argparse.ArgumentParser(description='段階的報酬モデルの評価')
    parser.add_argument('--model-path', type=str, 
                       default=None,
                       help='モデルファイルのパス（Noneの場合はデフォルトパス）')
    parser.add_argument('--n-eval-episodes', type=int, default=1000,
                       help='評価エピソード数')
    parser.add_argument('--data-dir', type=str, default="kyotei_predictor/data/raw",
                       help='データディレクトリ')
    
    args = parser.parse_args()
    
    # 環境変数からデータディレクトリを取得、コマンドライン引数を優先
    data_dir = os.environ.get('DATA_DIR', args.data_dir)
    print(f"使用するデータディレクトリ: {data_dir}")
    
    results = evaluate_graduated_reward_model(
        model_path=args.model_path,
        n_eval_episodes=args.n_eval_episodes,
        data_dir=data_dir
    )
    
    if results:
        print(f"\n=== 評価完了 ===")
        print(f"的中率: {results['statistics']['hit_rate']:.4f} ({results['statistics']['hit_rate']*100:.2f}%)")
        print(f"平均報酬: {results['statistics']['mean_reward']:.2f}")

if __name__ == "__main__":
    main() 