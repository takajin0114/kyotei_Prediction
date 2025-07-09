#!/usr/bin/env python3
"""
実際のオッズデータと着順依存型3連単モデルによる投資価値分析ツール
"""
import os
import json
from typing import Dict, Any, List
from datetime import datetime
from kyotei_predictor.pipelines.trifecta_dependent_model import TrifectaDependentModel

def analyze_investment_with_real_odds(data_dir: str, max_races: int = 100, output_dir: str = 'kyotei_predictor/outputs'):
    """実際のオッズデータとモデル予測を組み合わせた投資価値分析"""
    
    model = TrifectaDependentModel()
    print("=== 条件付き確率・艇間相関の学習 ===")
    model.learn_conditional_probabilities(data_dir=data_dir, max_files=max_races)
    
    # レースファイルとオッズファイルのペアを取得
    race_files = [f for f in os.listdir(data_dir) if f.startswith('race_data_') and f.endswith('.json')]
    odds_files = [f for f in os.listdir(data_dir) if f.startswith('odds_data_') and f.endswith('.json')]
    
    # ファイル名からレースIDを抽出してマッチング
    race_odds_pairs = []
    for race_file in race_files:
        race_id = race_file.replace('race_data_', '').replace('.json', '')
        odds_file = f'odds_data_{race_id}.json'
        if odds_file in odds_files:
            race_odds_pairs.append((race_file, odds_file))
    
    print(f"📊 分析対象: {len(race_odds_pairs)}レース")
    
    all_results = []
    total_investment_opportunities = 0
    total_profitable_combinations = 0
    
    for i, (race_file, odds_file) in enumerate(race_odds_pairs[:max_races], 1):
        print(f"\n--- レース {i}: {race_file} ---")
        
        # レースデータ読み込み
        with open(os.path.join(data_dir, race_file), 'r', encoding='utf-8') as f:
            race_data = json.load(f)
        
        # オッズデータ読み込み
        with open(os.path.join(data_dir, odds_file), 'r', encoding='utf-8') as f:
            odds_data = json.load(f)
        
        # オッズマップ作成
        odds_map = {}
        for odds_entry in odds_data.get('odds_data', []):
            combination = odds_entry.get('combination', '')
            ratio = odds_entry.get('ratio', 0)
            odds_map[combination] = ratio
        
        # モデル予測実行
        pred = model.calculate_dependent_probabilities(race_data)
        actual = model._extract_actual_result(race_data)
        
        # 投資価値分析
        investment_opportunities = []
        profitable_combinations = 0
        
        for combo in pred['top_combinations']:
            combination = combo['combination']
            probability = combo['probability']
            odds = odds_map.get(combination, 0)
            
            if odds > 0:
                expected_value = probability * odds
                is_profitable = expected_value >= 1.0  # 期待値1.0以上を投資対象
                
                if is_profitable:
                    profitable_combinations += 1
                    investment_opportunities.append({
                        'combination': combination,
                        'probability': probability,
                        'odds': odds,
                        'expected_value': expected_value,
                        'rank': next((j+1 for j, c in enumerate(pred['top_combinations']) if c['combination'] == combination), None)
                    })
        
        # 結果集計
        race_result = {
            'race_file': race_file,
            'actual_result': actual,
            'total_combinations': len(pred['top_combinations']),
            'profitable_combinations': profitable_combinations,
            'investment_opportunities': investment_opportunities,
            'actual_in_profitable': actual in [opp['combination'] for opp in investment_opportunities],
            'actual_rank': next((i+1 for i, c in enumerate(pred['top_combinations']) if c['combination'] == actual), None)
        }
        
        all_results.append(race_result)
        total_investment_opportunities += len(investment_opportunities)
        total_profitable_combinations += profitable_combinations
        
        print(f"  投資対象組み合わせ: {profitable_combinations}件")
        print(f"  実際の結果: {actual}")
        print(f"  実際の順位: {race_result['actual_rank']}位")
        
        if i % 10 == 0:
            print(f"\n📈 進捗: {i}/{min(len(race_odds_pairs), max_races)}レース処理完了")
    
    # 全体サマリー
    total_races = len(all_results)
    hit_in_profitable = sum(1 for r in all_results if r['actual_in_profitable'])
    avg_profitable_per_race = total_profitable_combinations / total_races if total_races > 0 else 0
    
    summary = {
        'total_races': total_races,
        'total_investment_opportunities': total_investment_opportunities,
        'total_profitable_combinations': total_profitable_combinations,
        'hit_in_profitable': hit_in_profitable,
        'avg_profitable_per_race': avg_profitable_per_race,
        'hit_rate_in_profitable': hit_in_profitable / total_races if total_races > 0 else 0,
        'investment_efficiency': hit_in_profitable / total_profitable_combinations if total_profitable_combinations > 0 else 0
    }
    
    print(f"\n=== 投資価値分析サマリー ===")
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    
    # 詳細分析
    print(f"\n=== 詳細分析 ===")
    print(f"・平均投資対象組み合わせ数: {avg_profitable_per_race:.1f}件/レース")
    print(f"・投資対象内的中率: {summary['hit_rate_in_profitable']*100:.1f}%")
    print(f"・投資効率: {summary['investment_efficiency']*100:.1f}%")
    
    # オッズ分布分析
    all_odds = []
    for result in all_results:
        for opp in result['investment_opportunities']:
            all_odds.append(opp['odds'])
    
    if all_odds:
        print(f"・投資対象オッズ範囲: {min(all_odds):.1f}倍 〜 {max(all_odds):.1f}倍")
        print(f"・平均投資対象オッズ: {sum(all_odds)/len(all_odds):.1f}倍")
    
    # 保存
    os.makedirs(output_dir, exist_ok=True)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    with open(os.path.join(output_dir, f'real_odds_investment_results_{timestamp}.json'), 'w', encoding='utf-8') as f:
        json.dump(all_results, f, ensure_ascii=False, indent=2)
    
    with open(os.path.join(output_dir, f'real_odds_investment_summary_{timestamp}.json'), 'w', encoding='utf-8') as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    
    return summary

def main():
    import argparse
    parser = argparse.ArgumentParser(description='実際のオッズデータによる投資価値分析')
    parser.add_argument('--data_dir', type=str, default='kyotei_predictor/data', help='データディレクトリ')
    parser.add_argument('--max_races', type=int, default=100, help='最大レース数')
    args = parser.parse_args()
    
    analyze_investment_with_real_odds(args.data_dir, args.max_races)

if __name__ == '__main__':
    main() 