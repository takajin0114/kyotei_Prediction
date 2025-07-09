import os
import glob
import json
import numpy as np
from itertools import permutations
import matplotlib.pyplot as plt
import seaborn as sns

def parse_key(path, prefix):
    fname = os.path.basename(path)
    parts = fname.replace(prefix, "").replace(".json", "").split("_")
    if len(parts) >= 3:
        date_parts = parts[0:3]
        date = "".join(date_parts).replace("-", "")
        if len(parts) >= 5:
            stadium = parts[3]
            rno = parts[4]
        elif len(parts) >= 4:
            stadium = parts[3]
            rno = "1"
        else:
            stadium = "UNKNOWN"
            rno = "1"
    else:
        date = parts[0] if parts else "UNKNOWN"
        stadium = parts[1] if len(parts) > 1 else "UNKNOWN"
        rno = parts[2] if len(parts) > 2 else "1"
    rno = rno.replace('R', '')
    try:
        rno_int = int(rno)
    except ValueError:
        rno_int = 1
    return (date, stadium, rno_int)

def calc_trifecta_reward(action, arrival_tuple, odds_data, bet_amount=100):
    """報酬計算関数（kyotei_env.pyと同じ）"""
    trifecta_list = list(permutations(range(1,7), 3))
    trifecta = trifecta_list[action]
    is_win = trifecta == arrival_tuple
    odds_map = {tuple(o['betting_numbers']): o['ratio'] for o in odds_data}
    odds = odds_map.get(trifecta, 0)
    payout = odds * bet_amount if is_win else 0
    reward = payout - bet_amount
    return reward

def analyze_reward_distribution(data_dir):
    """報酬分布の詳細分析"""
    race_files = glob.glob(os.path.join(data_dir, 'race_data_*.json'))
    odds_files = glob.glob(os.path.join(data_dir, 'odds_data_*.json'))
    race_map = {parse_key(f, "race_data_"): f for f in race_files}
    odds_map = {parse_key(f, "odds_data_"): f for f in odds_files}
    keys = set(race_map.keys()) & set(odds_map.keys())
    pairs = [(race_map[k], odds_map[k]) for k in sorted(keys)]
    
    all_rewards = []
    win_rewards = []
    lose_rewards = []
    win_count = 0
    total_count = 0
    
    print("=== 報酬分布分析 ===")
    print(f"分析対象レース数: {len(pairs)}")
    
    for i, (race_path, odds_path) in enumerate(pairs[:100]):  # 最初の100レースで分析
        if i % 10 == 0:
            print(f"進捗: {i}/{min(100, len(pairs))}")
            
        with open(race_path, encoding='utf-8') as f:
            race = json.load(f)
        with open(odds_path, encoding='utf-8') as f:
            odds = json.load(f)
            
        # 正解着順を取得
        valid_records = [r for r in race['race_records'] if r.get('arrival') is not None]
        if len(valid_records) < 3:
            continue
            
        sorted_records = sorted(valid_records, key=lambda x: x['arrival'])
        arrival_tuple = tuple(r['pit_number'] for r in sorted_records[:3])
        
        # 全120通りのactionで報酬を計算
        race_rewards = []
        for action in range(120):
            reward = calc_trifecta_reward(action, arrival_tuple, odds['odds_data'])
            race_rewards.append(reward)
            all_rewards.append(reward)
            
            if reward > -100:  # 的中
                win_rewards.append(reward)
                win_count += 1
            else:
                lose_rewards.append(reward)
            total_count += 1
    
    print(f"\n=== 報酬統計 ===")
    print(f"総アクション数: {total_count}")
    print(f"的中アクション数: {win_count}")
    print(f"的中率: {win_count/total_count:.4%}")
    
    if win_rewards:
        print(f"的中時の報酬統計:")
        print(f"  平均: {np.mean(win_rewards):.2f}")
        print(f"  最小: {np.min(win_rewards):.2f}")
        print(f"  最大: {np.max(win_rewards):.2f}")
        print(f"  標準偏差: {np.std(win_rewards):.2f}")
    
    print(f"不的中時の報酬: -100 (固定)")
    
    print(f"\n=== 報酬分布の詳細 ===")
    unique_rewards, counts = np.unique(all_rewards, return_counts=True)
    print("報酬値とその出現回数:")
    for reward, count in zip(unique_rewards, counts):
        print(f"  {reward}: {count}回 ({count/len(all_rewards):.4%})")
    
    # ヒストグラム作成
    plt.figure(figsize=(12, 8))
    
    plt.subplot(2, 2, 1)
    plt.hist(all_rewards, bins=50, alpha=0.7, color='blue')
    plt.title('全報酬の分布')
    plt.xlabel('報酬')
    plt.ylabel('頻度')
    
    plt.subplot(2, 2, 2)
    if win_rewards:
        plt.hist(win_rewards, bins=20, alpha=0.7, color='green')
        plt.title('的中時の報酬分布')
        plt.xlabel('報酬')
        plt.ylabel('頻度')
    
    plt.subplot(2, 2, 3)
    plt.hist(lose_rewards, bins=1, alpha=0.7, color='red')
    plt.title('不的中時の報酬分布')
    plt.xlabel('報酬')
    plt.ylabel('頻度')
    
    plt.subplot(2, 2, 4)
    reward_types = ['的中', '不的中']
    reward_counts = [len(win_rewards), len(lose_rewards)]
    plt.pie(reward_counts, labels=reward_types, autopct='%1.1f%%')
    plt.title('的中/不的中の比率')
    
    plt.tight_layout()
    plt.savefig('reward_analysis.png', dpi=300, bbox_inches='tight')
    plt.show()
    
    return {
        'total_actions': total_count,
        'win_actions': win_count,
        'win_rate': win_count/total_count,
        'win_rewards': win_rewards,
        'all_rewards': all_rewards
    }

def analyze_reward_problems():
    """報酬設計の問題点分析"""
    print("\n=== 報酬設計の問題点分析 ===")
    
    print("1. 報酬の疎性:")
    print("   - 的中率が非常に低い（約0.83%）")
    print("   - 学習初期に報酬が得られにくい")
    print("   - 探索が困難")
    
    print("\n2. 報酬のスケール:")
    print("   - 的中時: 大きな正の報酬（数百〜数千）")
    print("   - 不的中時: 固定の負の報酬（-100）")
    print("   - 報酬の分散が大きすぎる")
    
    print("\n3. 学習への影響:")
    print("   - 初期の探索で報酬が得られない")
    print("   - 勾配が不安定になる可能性")
    print("   - 学習が収束しにくい")
    
    print("\n4. 改善提案:")
    print("   - 段階的報酬（部分的中、順位予測など）")
    print("   - 報酬の正規化")
    print("   - 負の報酬の調整")
    print("   - 探索奨励のためのボーナス報酬")

if __name__ == "__main__":
    import sys
    data_dir = sys.argv[1] if len(sys.argv) > 1 else "kyotei_predictor/data/raw"
    
    # 報酬分布分析
    results = analyze_reward_distribution(data_dir)
    
    # 問題点分析
    analyze_reward_problems() 