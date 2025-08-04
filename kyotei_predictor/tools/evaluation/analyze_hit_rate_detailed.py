#!/usr/bin/env python3
"""
3連単予想の上位的中率詳細分析スクリプト
"""

import sys
import os
# プロジェクトルートをパスに追加
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)
sys.path.insert(0, '.')  # 現在のディレクトリも追加

import argparse
import json
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime
from stable_baselines3 import PPO
from stable_baselines3.common.vec_env import DummyVecEnv

# プロジェクトルートをパスに追加（確実に実行）
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from kyotei_predictor.pipelines.kyotei_env import KyoteiEnvManager

def action_to_trifecta(action: int) -> tuple:
    """
    アクション番号を3連単予想に変換
    
    Args:
        action: アクション番号 (0-119)
    
    Returns:
        3連単予想のタプル (1着, 2着, 3着)
    """
    # 6P3 = 120通りの組み合わせを生成
    trifectas = []
    for first in range(1, 7):
        for second in range(1, 7):
            for third in range(1, 7):
                if first != second and second != third and first != third:
                    trifectas.append((first, second, third))
    
    if 0 <= action < len(trifectas):
        return trifectas[action]
    else:
        # 無効なアクションの場合はデフォルト値を返す
        return (1, 2, 3)

def analyze_hit_rate_detailed(
    model_path="./optuna_models/graduated_reward_best/best_model.zip",
    n_eval_episodes=1000,
    data_dir="kyotei_predictor/data/raw",
    top_n_list=[10, 20, 50, 100]
):
    """
    3連単予想の上位的中率を詳細分析
    
    Args:
        model_path: モデルファイルのパス
        n_eval_episodes: 評価エピソード数
        data_dir: データディレクトリ
        top_n_list: 分析する上位N位のリスト
    
    Returns:
        分析結果の辞書
    """
    print(f"=== 3連単予想上位的中率詳細分析 ===")
    print(f"モデルパス: {model_path}")
    print(f"評価エピソード数: {n_eval_episodes}")
    print(f"データディレクトリ: {data_dir}")
    print(f"分析対象: 上位{top_n_list}位")
    
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
    
    all_predictions = []
    episode_rewards = []
    
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
            
            # 各ステップの結果を記録
            trifecta = action_to_trifecta(action[0])
            arrival = info[0].get('actual', info[0].get('actual_result', None))
            
            # arrivalがNoneの場合はスキップ
            if arrival is None or len(arrival) != 3:
                continue
            
            is_win = trifecta == arrival
            first_hit = trifecta[0] == arrival[0]
            second_hit = trifecta[1] == arrival[1]
            
            prediction_data = {
                'episode': episode,
                'step': len(all_predictions),  # ステップ番号を追加
                'predicted_trifecta': trifecta,
                'actual_arrival': arrival,
                'is_exact_match': is_win,
                'first_hit': first_hit,
                'second_hit': second_hit,
                'reward': float(reward[0]),  # numpy型をfloatに変換
                'episode_reward': float(episode_reward)  # numpy型をfloatに変換
            }
            all_predictions.append(prediction_data)
        
        episode_rewards.append(episode_reward)
    
    # 上位的中率分析
    print(f"\n=== 上位的中率詳細分析 ===")
    
    hit_rate_analysis = {}
    
    for top_n in top_n_list:
        hits = []
        for pred in all_predictions:
            if pred['is_exact_match']:
                hits.append(pred['episode'])
            elif pred['first_hit'] and pred['second_hit']:
                hits.append(pred['episode'])
        
        hit_rate = len(hits) / len(all_predictions) * 100
        hit_rate_analysis[f'top_{top_n}'] = {
            'hit_count': len(hits),
            'hit_rate': hit_rate,
            'hit_episodes': hits
        }
        
        print(f"上位{top_n}位的中: {len(hits)}回 ({hit_rate:.2f}%)")
    
    # 的中エピソードの詳細分析
    print(f"\n=== 的中エピソード詳細分析 ===")
    
    exact_matches = [pred for pred in all_predictions if pred['is_exact_match']]
    first_second_hits = [pred for pred in all_predictions if pred['first_hit'] and pred['second_hit'] and not pred['is_exact_match']]
    first_only_hits = [pred for pred in all_predictions if pred['first_hit'] and not pred['second_hit']]
    
    print(f"完全的中: {len(exact_matches)}回 ({len(exact_matches)/len(all_predictions)*100:.2f}%)")
    print(f"2着的中: {len(first_second_hits)}回 ({len(first_second_hits)/len(all_predictions)*100:.2f}%)")
    print(f"1着的中: {len(first_only_hits)}回 ({len(first_only_hits)/len(all_predictions)*100:.2f}%)")
    
    # 的中エピソードの報酬分析
    if exact_matches:
        exact_match_rewards = [pred['reward'] for pred in exact_matches]
        print(f"完全的中エピソードの平均報酬: {np.mean(exact_match_rewards):.2f}")
        print(f"完全的中エピソードの最大報酬: {np.max(exact_match_rewards):.2f}")
    
    if first_second_hits:
        first_second_rewards = [pred['reward'] for pred in first_second_hits]
        print(f"2着的中エピソードの平均報酬: {np.mean(first_second_rewards):.2f}")
    
    # 的中パターンの分析
    print(f"\n=== 的中パターン分析 ===")
    
    exact_match_patterns = {}
    for pred in exact_matches:
        pattern = tuple(pred['predicted_trifecta'])
        exact_match_patterns[pattern] = exact_match_patterns.get(pattern, 0) + 1
    
    print(f"完全的中パターン数: {len(exact_match_patterns)}")
    if exact_match_patterns:
        most_common_pattern = max(exact_match_patterns.items(), key=lambda x: x[1])
        print(f"最多的中パターン: {most_common_pattern[0]} ({most_common_pattern[1]}回)")
    
    # 可視化
    create_detailed_hit_rate_plots(all_predictions, hit_rate_analysis, top_n_list)
    
    # 結果をJSONファイルに保存
    results = {
        'analysis_time': datetime.now().isoformat(),
        'model_path': model_path,
        'n_episodes': n_eval_episodes,
        'data_dir': data_dir,
        'hit_rate_analysis': hit_rate_analysis,
        'exact_matches': len(exact_matches),
        'first_second_hits': len(first_second_hits),
        'first_only_hits': len(first_only_hits),
        'all_predictions': all_predictions
    }
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_path = f"./outputs/detailed_hit_rate_analysis_{timestamp}.json"
    
    os.makedirs("./outputs", exist_ok=True)
    with open(results_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"詳細分析結果を保存しました: {results_path}")
    
    return results

def create_detailed_hit_rate_plots(all_predictions, hit_rate_analysis, top_n_list):
    """詳細的中率分析の可視化"""
    
    plt.figure(figsize=(20, 15))
    
    # 上位的中率の比較
    plt.subplot(2, 3, 1)
    top_n_values = []
    hit_rates = []
    
    for top_n in top_n_list:
        key = f'top_{top_n}'
        if key in hit_rate_analysis:
            top_n_values.append(top_n)
            hit_rates.append(hit_rate_analysis[key]['hit_rate'])
    
    if top_n_values:
        colors = ['gold', 'silver', 'lightblue', 'lightgreen'][:len(top_n_values)]
        plt.bar(top_n_values, hit_rates, color=colors)
        plt.title('上位的中率比較')
        plt.xlabel('上位N位')
        plt.ylabel('的中率 (%)')
        plt.xticks(top_n_values)
        plt.grid(True, alpha=0.3)
    
    # 的中タイプの分布
    plt.subplot(2, 3, 2)
    exact_matches = [pred for pred in all_predictions if pred['is_exact_match']]
    first_second_hits = [pred for pred in all_predictions if pred['first_hit'] and pred['second_hit'] and not pred['is_exact_match']]
    first_only_hits = [pred for pred in all_predictions if pred['first_hit'] and not pred['second_hit']]
    misses = [pred for pred in all_predictions if not pred['first_hit']]
    
    labels = ['完全的中', '2着的中', '1着的中', '不的中']
    values = [len(exact_matches), len(first_second_hits), len(first_only_hits), len(misses)]
    colors = ['green', 'orange', 'yellow', 'red']
    
    if sum(values) > 0:  # データがある場合のみ描画
        plt.pie(values, labels=labels, autopct='%1.1f%%', colors=colors)
        plt.title('的中タイプ分布')
    
    # 的中エピソードの報酬分布
    plt.subplot(2, 3, 3)
    exact_rewards = [pred['reward'] for pred in exact_matches]
    first_second_rewards = [pred['reward'] for pred in first_second_hits]
    first_only_rewards = [pred['reward'] for pred in first_only_hits]
    
    if exact_rewards:
        plt.hist(exact_rewards, alpha=0.7, label='完全的中', color='green', bins=20)
    if first_second_rewards:
        plt.hist(first_second_rewards, alpha=0.7, label='2着的中', color='orange', bins=20)
    if first_only_rewards:
        plt.hist(first_only_rewards, alpha=0.7, label='1着的中', color='yellow', bins=20)
    
    plt.title('的中エピソードの報酬分布')
    plt.xlabel('報酬')
    plt.ylabel('頻度')
    if exact_rewards or first_second_rewards or first_only_rewards:
        plt.legend()
    plt.grid(True, alpha=0.3)
    
    # 的中の時系列
    plt.subplot(2, 3, 4)
    episodes = [pred['episode'] for pred in all_predictions]
    exact_series = [1 if pred['is_exact_match'] else 0 for pred in all_predictions]
    first_second_series = [1 if pred['first_hit'] and pred['second_hit'] and not pred['is_exact_match'] else 0 for pred in all_predictions]
    
    plt.plot(episodes, exact_series, label='完全的中', alpha=0.7, color='green')
    plt.plot(episodes, first_second_series, label='2着的中', alpha=0.7, color='orange')
    plt.title('的中の時系列')
    plt.xlabel('エピソード')
    plt.ylabel('的中')
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    # 的中率の推移
    plt.subplot(2, 3, 5)
    window_size = min(100, len(all_predictions) // 2) if len(all_predictions) > 0 else 10
    if window_size > 0 and len(all_predictions) >= window_size:
        exact_rates = []
        first_second_rates = []
        
        for i in range(window_size, len(all_predictions) + 1):
            window = all_predictions[i-window_size:i]
            exact_rate = sum(1 for pred in window if pred['is_exact_match']) / len(window)
            first_second_rate = sum(1 for pred in window if pred['first_hit'] and pred['second_hit'] and not pred['is_exact_match']) / len(window)
            
            exact_rates.append(exact_rate)
            first_second_rates.append(first_second_rate)
        
        plt.plot(range(window_size, len(all_predictions) + 1), exact_rates, label='完全的中率', color='green')
        plt.plot(range(window_size, len(all_predictions) + 1), first_second_rates, label='2着的中率', color='orange')
        plt.title(f'的中率の推移 (ウィンドウサイズ: {window_size})')
        plt.xlabel('エピソード')
        plt.ylabel('的中率')
        plt.legend()
        plt.grid(True, alpha=0.3)
    
    # 的中パターンの分析
    plt.subplot(2, 3, 6)
    exact_match_patterns = {}
    for pred in exact_matches:
        pattern = tuple(pred['predicted_trifecta'])
        exact_match_patterns[pattern] = exact_match_patterns.get(pattern, 0) + 1
    
    if exact_match_patterns:
        patterns = list(exact_match_patterns.keys())[:10]  # 上位10パターン
        counts = [exact_match_patterns[pattern] for pattern in patterns]
        
        plt.barh(range(len(patterns)), counts, color='lightgreen')
        plt.yticks(range(len(patterns)), [str(pattern) for pattern in patterns])
        plt.title('的中パターン分析 (上位10パターン)')
        plt.xlabel('的中回数')
        plt.grid(True, alpha=0.3)
    else:
        plt.text(0.5, 0.5, '的中パターンなし', ha='center', va='center', transform=plt.gca().transAxes)
        plt.title('的中パターン分析')
    
    plt.tight_layout()
    
    # 保存
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    plot_path = f"./outputs/detailed_hit_rate_analysis_plots_{timestamp}.png"
    plt.savefig(plot_path, dpi=300, bbox_inches='tight')
    plt.show()
    
    print(f"詳細分析可視化結果を保存しました: {plot_path}")

def main():
    # プロジェクトルートをパスに追加（確実に実行）
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
    
    parser = argparse.ArgumentParser(description='3連単予想の上位的中率詳細分析')
    parser.add_argument('--model-path', type=str, 
                       default="./optuna_models/graduated_reward_best/best_model.zip",
                       help='モデルファイルのパス')
    parser.add_argument('--n-eval-episodes', type=int, default=1000,
                       help='評価エピソード数')
    parser.add_argument('--data-dir', type=str, default="kyotei_predictor/data/raw",
                       help='データディレクトリ')
    parser.add_argument('--top-n-list', type=int, nargs='+', default=[10, 20, 50, 100],
                       help='分析する上位N位のリスト')
    
    args = parser.parse_args()
    
    try:
        results = analyze_hit_rate_detailed(
            model_path=args.model_path,
            n_eval_episodes=args.n_eval_episodes,
            data_dir=args.data_dir,
            top_n_list=args.top_n_list
        )
        
        if results:
            print(f"\n=== 詳細分析完了 ===")
            print(f"上位10位的中率: {results['hit_rate_analysis']['top_10']['hit_rate']:.2f}%")
            print(f"上位20位的中率: {results['hit_rate_analysis']['top_20']['hit_rate']:.2f}%")
            print(f"完全的中率: {results['exact_matches']/len(results['all_predictions'])*100:.2f}%")
        else:
            print("詳細分析に失敗しました")
            sys.exit(1)
            
    except Exception as e:
        print(f"詳細分析中にエラーが発生しました: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 