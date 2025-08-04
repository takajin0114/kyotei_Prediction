#!/usr/bin/env python3
"""
段階的報酬モデルの評価スクリプト
"""

import sys
import os
# プロジェクトルートをパスに追加
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

import argparse
import json
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime
from stable_baselines3 import PPO
from stable_baselines3.common.vec_env import DummyVecEnv
from kyotei_predictor.pipelines.kyotei_env import KyoteiEnvManager
from kyotei_predictor.pipelines.kyotei_env import action_to_trifecta

def evaluate_graduated_reward_model(
    model_path="./optuna_models/graduated_reward_best/best_model.zip",
    n_eval_episodes=1000,
    data_dir="kyotei_predictor/data/raw"
):
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
    
    for episode in range(n_eval_episodes):
        if episode % 100 == 0:
            print(f"評価進捗: {episode}/{n_eval_episodes}")
        
        obs = eval_env.reset()
        episode_reward = 0
        done = False
        
        while not done:
            action, _ = model.predict(obs, deterministic=True)
            obs, reward, done, info = eval_env.step(action)
            episode_reward += reward[0]
            
            # 詳細情報を記録
            if done:
                actions.append(action[0])
                if 'arrival' in info[0]:
                    arrival_tuples.append(info[0]['arrival'])
                
                # 的中タイプを判定
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
    
    # 統計分析
    print("\n=== 評価結果統計 ===")
    
    rewards = np.array(rewards)
    print(f"総エピソード数: {len(rewards)}")
    print(f"平均報酬: {np.mean(rewards):.2f}")
    print(f"報酬の標準偏差: {np.std(rewards):.2f}")
    print(f"最大報酬: {np.max(rewards):.2f}")
    print(f"最小報酬: {np.min(rewards):.2f}")
    
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
    positive_rewards = rewards[rewards > -100]
    negative_rewards = rewards[rewards <= -100]
    
    print(f"正の報酬: {len(positive_rewards)}回 ({len(positive_rewards)/len(rewards)*100:.2f}%)")
    print(f"負の報酬: {len(negative_rewards)}回 ({len(negative_rewards)/len(rewards)*100:.2f}%)")
    
    if len(positive_rewards) > 0:
        print(f"正の報酬の平均: {np.mean(positive_rewards):.2f}")
        print(f"正の報酬の最大: {np.max(positive_rewards):.2f}")
    
    # 可視化
    print("\n=== 結果の可視化 ===")
    create_evaluation_plots(rewards, hit_types, model_path)
    
    # 結果をJSONファイルに保存
    results = {
        'evaluation_time': datetime.now().isoformat(),
        'model_path': model_path,
        'n_episodes': n_eval_episodes,
        'statistics': {
            'mean_reward': float(np.mean(rewards)),
            'std_reward': float(np.std(rewards)),
            'max_reward': float(np.max(rewards)),
            'min_reward': float(np.min(rewards)),
            'hit_rate': hit_type_counts.get('win', 0) / len(hit_types),
            'first_second_rate': hit_type_counts.get('first_second', 0) / len(hit_types),
            'first_only_rate': hit_type_counts.get('first_only', 0) / len(hit_types),
            'miss_rate': hit_type_counts.get('miss', 0) / len(hit_types),
            'positive_reward_rate': len(positive_rewards) / len(rewards)
        },
        'hit_type_counts': hit_type_counts
    }
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_path = f"./outputs/graduated_reward_evaluation_{timestamp}.json"
    
    os.makedirs("./outputs", exist_ok=True)
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
    
    # 保存
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    plot_path = f"./outputs/graduated_reward_evaluation_plots_{timestamp}.png"
    plt.savefig(plot_path, dpi=300, bbox_inches='tight')
    plt.show()
    
    print(f"可視化結果を保存しました: {plot_path}")

def main():
    # プロジェクトルートをパスに追加（確実に実行）
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
    
    parser = argparse.ArgumentParser(description='段階的報酬モデルの評価')
    parser.add_argument('--model-path', type=str, 
                       default="./optuna_models/graduated_reward_best/best_model.zip",
                       help='モデルファイルのパス')
    parser.add_argument('--n-eval-episodes', type=int, default=1000,
                       help='評価エピソード数')
    parser.add_argument('--data-dir', type=str, default="kyotei_predictor/data/raw",
                       help='データディレクトリ')
    
    args = parser.parse_args()
    
    try:
        results = evaluate_graduated_reward_model(
            model_path=args.model_path,
            n_eval_episodes=args.n_eval_episodes,
            data_dir=args.data_dir
        )
        
        if results:
            print(f"\n=== 評価完了 ===")
            print(f"的中率: {results['statistics']['hit_rate']:.4f} ({results['statistics']['hit_rate']*100:.2f}%)")
            print(f"平均報酬: {results['statistics']['mean_reward']:.2f}")
        else:
            print("評価に失敗しました")
            sys.exit(1)
            
    except Exception as e:
        print(f"評価中にエラーが発生しました: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 