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

def action_to_trifecta(action: int):
    """action(0-119)→(1着,2着,3着)の買い目タプル"""
    trifecta_list = list(permutations(range(1,7), 3))
    return trifecta_list[action]

def calc_old_reward(action: int, arrival_tuple, odds_data, bet_amount=100):
    """旧報酬設計（的中時のみ正の報酬）"""
    trifecta = action_to_trifecta(action)
    is_win = trifecta == arrival_tuple
    odds_map = {tuple(o['betting_numbers']): o['ratio'] for o in odds_data}
    odds = odds_map.get(trifecta, 0)
    payout = odds * bet_amount if is_win else 0
    reward = payout - bet_amount
    return reward

def calc_new_reward(action: int, arrival_tuple, odds_data, bet_amount=100):
    """新報酬設計（段階的報酬）"""
    trifecta = action_to_trifecta(action)
    is_win = trifecta == arrival_tuple
    
    if is_win:
        odds_map = {tuple(o['betting_numbers']): o['ratio'] for o in odds_data}
        odds = odds_map.get(trifecta, 0)
        payout = odds * bet_amount
        reward = payout - bet_amount
    else:
        first_hit = trifecta[0] == arrival_tuple[0]
        second_hit = trifecta[1] == arrival_tuple[1]
        
        if first_hit and second_hit:
            reward = -10  # 2着的中
        elif first_hit:
            reward = -50  # 1着的中
        else:
            reward = -100  # 不的中
    
    return reward

def analyze_graduated_reward_effect(data_dir):
    """段階的報酬設計の効果分析"""
    race_files = glob.glob(os.path.join(data_dir, 'race_data_*.json'))
    odds_files = glob.glob(os.path.join(data_dir, 'odds_data_*.json'))
    race_map = {parse_key(f, "race_data_"): f for f in race_files}
    odds_map = {parse_key(f, "odds_data_"): f for f in odds_files}
    keys = set(race_map.keys()) & set(odds_map.keys())
    pairs = [(race_map[k], odds_map[k]) for k in sorted(keys)]
    
    print("=== 段階的報酬設計の効果分析 ===")
    print(f"分析対象レース数: {len(pairs)}")
    
    old_rewards = []
    new_rewards = []
    hit_types = []  # 'win', 'first_second', 'first_only', 'miss'
    
    sample_count = min(100, len(pairs))
    
    for i, (race_path, odds_path) in enumerate(pairs[:sample_count]):
        if i % 10 == 0:
            print(f"進捗: {i}/{sample_count}")
            
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
        for action in range(120):
            old_reward = calc_old_reward(action, arrival_tuple, odds['odds_data'])
            new_reward = calc_new_reward(action, arrival_tuple, odds['odds_data'])
            
            old_rewards.append(old_reward)
            new_rewards.append(new_reward)
            
            # 的中タイプを判定
            trifecta = action_to_trifecta(action)
            is_win = trifecta == arrival_tuple
            first_hit = trifecta[0] == arrival_tuple[0]
            second_hit = trifecta[1] == arrival_tuple[1]
            
            if is_win:
                hit_types.append('win')
            elif first_hit and second_hit:
                hit_types.append('first_second')
            elif first_hit:
                hit_types.append('first_only')
            else:
                hit_types.append('miss')
    
    # 統計情報
    print(f"\n=== 報酬統計比較 ===")
    print(f"総アクション数: {len(old_rewards)}")
    
    # 旧報酬設計の統計
    old_win_count = sum(1 for r in old_rewards if r > -100)
    old_win_rate = old_win_count / len(old_rewards)
    print(f"\n【旧報酬設計】")
    print(f"的中率: {old_win_rate:.4%}")
    print(f"平均報酬: {np.mean(old_rewards):.2f}")
    print(f"報酬の分散: {np.std(old_rewards):.2f}")
    
    # 新報酬設計の統計
    new_win_count = sum(1 for r in new_rewards if r > -100)
    new_first_second_count = sum(1 for r in new_rewards if r == -10)
    new_first_only_count = sum(1 for r in new_rewards if r == -50)
    new_miss_count = sum(1 for r in new_rewards if r == -100)
    
    print(f"\n【新報酬設計】")
    print(f"的中率: {new_win_count/len(new_rewards):.4%}")
    print(f"2着的中率: {new_first_second_count/len(new_rewards):.4%}")
    print(f"1着的中率: {new_first_only_count/len(new_rewards):.4%}")
    print(f"不的中率: {new_miss_count/len(new_rewards):.4%}")
    print(f"平均報酬: {np.mean(new_rewards):.2f}")
    print(f"報酬の分散: {np.std(new_rewards):.2f}")
    
    # 学習への影響分析
    print(f"\n=== 学習への影響分析 ===")
    
    # 報酬が得られる確率
    old_positive_rate = old_win_rate
    new_positive_rate = (new_win_count + new_first_second_count + new_first_only_count) / len(new_rewards)
    
    print(f"報酬が得られる確率:")
    print(f"  旧報酬設計: {old_positive_rate:.4%}")
    print(f"  新報酬設計: {new_positive_rate:.4%}")
    print(f"  改善率: {(new_positive_rate/old_positive_rate-1)*100:.1f}%")
    
    # 報酬の分散比較
    print(f"\n報酬の分散:")
    print(f"  旧報酬設計: {np.std(old_rewards):.2f}")
    print(f"  新報酬設計: {np.std(new_rewards):.2f}")
    print(f"  分散減少率: {(1-np.std(new_rewards)/np.std(old_rewards))*100:.1f}%")
    
    # 可視化
    plt.figure(figsize=(15, 10))
    
    # 報酬分布の比較
    plt.subplot(2, 3, 1)
    plt.hist(old_rewards, bins=50, alpha=0.7, label='旧報酬設計', color='red')
    plt.title('旧報酬設計の分布')
    plt.xlabel('報酬')
    plt.ylabel('頻度')
    
    plt.subplot(2, 3, 2)
    plt.hist(new_rewards, bins=50, alpha=0.7, label='新報酬設計', color='blue')
    plt.title('新報酬設計の分布')
    plt.xlabel('報酬')
    plt.ylabel('頻度')
    
    # 的中タイプの分布
    plt.subplot(2, 3, 3)
    hit_type_counts = {}
    for hit_type in hit_types:
        hit_type_counts[hit_type] = hit_type_counts.get(hit_type, 0) + 1
    
    pie_labels = ['的中', '2着的中', '1着的中', '不的中']
    values = [hit_type_counts.get('win', 0), hit_type_counts.get('first_second', 0), 
              hit_type_counts.get('first_only', 0), hit_type_counts.get('miss', 0)]
    colors = ['green', 'orange', 'yellow', 'red']
    
    plt.pie(values, labels=pie_labels, autopct='%1.1f%%', colors=colors)
    plt.title('新報酬設計の的中タイプ分布')
    
    # 報酬の箱ひげ図比較
    plt.subplot(2, 3, 4)
    plt.boxplot([old_rewards, new_rewards], labels=['旧報酬設計', '新報酬設計'])
    plt.title('報酬の箱ひげ図比較')
    plt.ylabel('報酬')
    
    # 報酬の累積分布
    plt.subplot(2, 3, 5)
    old_sorted = np.sort(old_rewards)
    new_sorted = np.sort(new_rewards)
    plt.plot(old_sorted, np.arange(len(old_sorted))/len(old_sorted), label='旧報酬設計', color='red')
    plt.plot(new_sorted, np.arange(len(new_sorted))/len(new_sorted), label='新報酬設計', color='blue')
    plt.title('報酬の累積分布')
    plt.xlabel('報酬')
    plt.ylabel('累積確率')
    plt.legend()
    
    # 報酬の範囲比較
    plt.subplot(2, 3, 6)
    reward_ranges = ['-100', '-50', '-10', '0+']
    old_counts = [sum(1 for r in old_rewards if r == -100), 0, 0, sum(1 for r in old_rewards if r > -100)]
    new_counts = [new_miss_count, new_first_only_count, new_first_second_count, new_win_count]
    
    x = np.arange(len(reward_ranges))
    width = 0.35
    
    plt.bar(x - width/2, old_counts, width, label='旧報酬設計', color='red', alpha=0.7)
    plt.bar(x + width/2, new_counts, width, label='新報酬設計', color='blue', alpha=0.7)
    plt.title('報酬範囲別のアクション数')
    plt.xlabel('報酬範囲')
    plt.ylabel('アクション数')
    plt.xticks(x, reward_ranges)
    plt.legend()
    
    plt.tight_layout()
    plt.savefig('graduated_reward_analysis.png', dpi=300, bbox_inches='tight')
    plt.show()
    
    return {
        'old_rewards': old_rewards,
        'new_rewards': new_rewards,
        'hit_types': hit_types,
        'old_win_rate': old_win_rate,
        'new_positive_rate': new_positive_rate,
        'improvement_rate': (new_positive_rate/old_positive_rate-1)*100
    }

def analyze_learning_improvement():
    """学習改善効果の分析"""
    print("\n=== 学習改善効果の分析 ===")
    
    print("1. 報酬の疎性の改善:")
    print("   - 旧報酬設計: 的中時のみ報酬（0.83%）")
    print("   - 新報酬設計: 部分的中でも報酬（約16.7%）")
    print("   - 効果: 学習初期から報酬が得られやすくなる")
    
    print("\n2. 探索の促進:")
    print("   - 1着的中: -50（従来の-100より改善）")
    print("   - 2着的中: -10（大幅な改善）")
    print("   - 効果: より積極的な探索が可能")
    
    print("\n3. 学習の安定性:")
    print("   - 報酬の分散が減少")
    print("   - 極端な値の頻度が低下")
    print("   - 効果: より安定した学習が期待")
    
    print("\n4. 期待される学習効果:")
    print("   - 初期学習の加速")
    print("   - 的中率の向上")
    print("   - 学習の収束性向上")

if __name__ == "__main__":
    import sys
    data_dir = sys.argv[1] if len(sys.argv) > 1 else "kyotei_predictor/data/raw"
    
    # 段階的報酬設計の効果分析
    results = analyze_graduated_reward_effect(data_dir)
    
    # 学習改善効果の分析
    analyze_learning_improvement()
    
    print(f"\n=== 分析結果サマリー ===")
    print(f"報酬が得られる確率の改善: {results['improvement_rate']:.1f}%")
    print(f"学習初期の探索が大幅に改善されることが期待されます。") 