#!/usr/bin/env python3
"""
3連単確率デバッガー

3連単確率の詳細を確認し、投資価値分析の原因を調査
"""

import sys
import os
import json
from typing import Dict, List, Any

# パス設定
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from kyotei_predictor.prediction_engine import PredictionEngine

def debug_trifecta_probabilities(race_file: str):
    """3連単確率の詳細をデバッグ"""
    print(f"🔍 3連単確率デバッグ開始: {race_file}")
    print("=" * 60)
    
    # レースデータ読み込み
    with open(race_file, 'r', encoding='utf-8') as f:
        race_data = json.load(f)
    
    engine = PredictionEngine()
    
    # 3連単予測実行
    trifecta_result = engine.get_top_trifecta_recommendations(
        race_data, 
        algorithm='equipment_focused', 
        top_n=120
    )
    
    print(f"📊 3連単予測結果:")
    print(f"  - 総組み合わせ数: {len(trifecta_result['top_combinations'])}")
    print(f"  - 最有力組み合わせ: {trifecta_result['summary']['most_likely']['combination']}")
    print(f"  - 最有力確率: {trifecta_result['summary']['most_likely']['percentage']:.4f}%")
    print(f"  - 平均期待オッズ: {trifecta_result['summary']['average_odds']:.1f}倍")
    
    print(f"\n🎯 上位10位の組み合わせ:")
    print("-" * 60)
    for i, combo in enumerate(trifecta_result['top_combinations'][:10], 1):
        print(f"{i:2d}位: {combo['combination']} - {combo['percentage']:.4f}% ({combo['expected_odds']:.1f}倍)")
    
    print(f"\n📈 確率分布分析:")
    print("-" * 60)
    
    # 確率分布の統計
    probabilities = [combo['probability'] for combo in trifecta_result['top_combinations']]
    percentages = [combo['percentage'] for combo in trifecta_result['top_combinations']]
    
    print(f"  - 最高確率: {max(probabilities):.6f} ({max(percentages):.4f}%)")
    print(f"  - 最低確率: {min(probabilities):.6f} ({min(percentages):.4f}%)")
    print(f"  - 平均確率: {sum(probabilities)/len(probabilities):.6f} ({sum(percentages)/len(percentages):.4f}%)")
    
    # 期待値の計算（サンプルオッズで）
    print(f"\n💰 期待値分析（サンプルオッズ使用）:")
    print("-" * 60)
    
    # サンプルオッズデータ
    sample_odds = {
        '1-2-3': 120.5, '1-2-4': 150.2, '1-2-5': 180.0, '1-2-6': 200.0,
        '1-3-2': 130.0, '1-3-4': 160.0, '1-3-5': 190.0, '1-3-6': 210.0,
        '2-1-3': 140.0, '2-1-4': 170.0, '2-1-5': 200.0, '2-1-6': 220.0,
        '2-3-1': 150.0, '2-3-4': 180.0, '2-3-5': 210.0, '2-3-6': 230.0,
        '3-1-2': 160.0, '3-1-4': 190.0, '3-1-5': 220.0, '3-1-6': 240.0,
        '3-2-1': 170.0, '3-2-4': 200.0, '3-2-5': 230.0, '3-2-6': 250.0,
    }
    
    # 期待値の高い組み合わせを抽出
    high_ev_combinations = []
    for combo in trifecta_result['top_combinations']:
        combination = combo['combination']
        probability = combo['probability']
        odds = sample_odds.get(combination, combo['expected_odds'])
        expected_value = probability * odds
        
        if expected_value >= 0.5:  # 期待値0.5以上の組み合わせ
            high_ev_combinations.append({
                'combination': combination,
                'probability': probability,
                'percentage': combo['percentage'],
                'odds': odds,
                'expected_value': expected_value
            })
    
    print(f"  - 期待値0.5以上の組み合わせ: {len(high_ev_combinations)}件")
    
    if high_ev_combinations:
        print(f"\n🎯 期待値の高い組み合わせ（上位10位）:")
        for i, combo in enumerate(sorted(high_ev_combinations, key=lambda x: x['expected_value'], reverse=True)[:10], 1):
            print(f"{i:2d}位: {combo['combination']} - 確率{combo['percentage']:.4f}% × オッズ{combo['odds']:.1f}倍 = 期待値{combo['expected_value']:.3f}")
    else:
        print(f"  - 期待値0.5以上の組み合わせはありません")
    
    # 投資価値分析の閾値テスト
    print(f"\n🔍 投資価値分析の閾値テスト:")
    print("-" * 60)
    
    thresholds = [0.1, 0.2, 0.5, 1.0, 1.2, 1.5]
    for threshold in thresholds:
        count = sum(1 for combo in trifecta_result['top_combinations'] 
                   if combo['probability'] * sample_odds.get(combo['combination'], combo['expected_odds']) >= threshold)
        print(f"  - 期待値{threshold}以上: {count}件")
    
    print(f"\n✅ デバッグ完了")

def main():
    """メイン処理"""
    import argparse
    
    parser = argparse.ArgumentParser(description='3連単確率デバッガー')
    parser.add_argument('--race_file', type=str, required=True, help='レースデータファイル')
    args = parser.parse_args()
    
    debug_trifecta_probabilities(args.race_file)

if __name__ == "__main__":
    main() 