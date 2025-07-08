#!/usr/bin/env python3
"""
着順依存型3連単モデルによる大量データ検証ツール
"""
import os
import json
from typing import Dict, Any, List
from datetime import datetime
from kyotei_predictor.pipelines.trifecta_dependent_model import TrifectaDependentModel

def bulk_validate(data_dir: str, max_races: int = 1000, output_dir: str = 'kyotei_predictor/outputs'):
    model = TrifectaDependentModel()
    print("=== 条件付き確率・艇間相関の学習 ===")
    model.learn_conditional_probabilities(data_dir=data_dir, max_files=max_races)
    race_files = [f for f in os.listdir(data_dir) if f.startswith('race_data_') and f.endswith('.json')]
    results = []
    for i, race_file in enumerate(race_files[:max_races], 1):
        with open(os.path.join(data_dir, race_file), 'r', encoding='utf-8') as f:
            race_data = json.load(f)
        pred = model.calculate_dependent_probabilities(race_data)
        actual = model._extract_actual_result(race_data)
        # 全組合せpredictionsリストを作成
        predictions = [
            {
                'combination': c['combination'],
                'probability': c['probability'],
                'hit': (c['combination'] == actual)
            }
            for c in pred['top_combinations']
        ]
        # actual_rankを計算
        actual_rank = None
        if actual:
            for idx, c in enumerate(pred['top_combinations']):
                if c['combination'] == actual:
                    actual_rank = idx + 1
                    break
        results.append({
            'file': race_file,
            'predictions': predictions,
            'actual': actual,
            'actual_rank': actual_rank
        })
        if i % 100 == 0:
            print(f"...{i}レース処理")
    # 集計
    total = len(results)
    try:
        hit1 = sum(1 for r in results if r.get('actual_rank') == 1)
        hit3 = sum(1 for r in results if r.get('actual_rank') and r.get('actual_rank') <= 3)
        hit5 = sum(1 for r in results if r.get('actual_rank') and r.get('actual_rank') <= 5)
        hit10 = sum(1 for r in results if r.get('actual_rank') and r.get('actual_rank') <= 10)
        avg_rank_list = [r.get('actual_rank') for r in results if r.get('actual_rank') is not None]
        avg_rank = sum(avg_rank_list) / len(avg_rank_list) if avg_rank_list else None
        print(f"1着的中: {hit1}件, 3着以内的中: {hit3}件, 5着以内: {hit5}件, 10着以内: {hit10}件, 平均順位: {avg_rank}")
    except Exception as e:
        print(f"[WARN] サマリー集計時にエラー: {e} (一部データにactual_rank欠損)")
    report = {
        'total': total,
        'hit1': hit1,
        'hit3': hit3,
        'hit5': hit5,
        'hit10': hit10,
        'avg_rank': avg_rank,
        'hit1_rate': hit1/total,
        'hit3_rate': hit3/total,
        'hit5_rate': hit5/total,
        'hit10_rate': hit10/total
    }
    print("\n=== 検証結果サマリー ===")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    os.makedirs(output_dir, exist_ok=True)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    with open(os.path.join(output_dir, f'trifecta_dependent_bulk_results_{timestamp}.json'), 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    with open(os.path.join(output_dir, f'trifecta_dependent_bulk_report_{timestamp}.json'), 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

def main():
    import argparse
    parser = argparse.ArgumentParser(description='着順依存型3連単モデル大量検証')
    parser.add_argument('--data_dir', type=str, default='kyotei_predictor/data', help='データディレクトリ')
    parser.add_argument('--max_races', type=int, default=1000, help='最大レース数')
    args = parser.parse_args()
    bulk_validate(args.data_dir, args.max_races)

if __name__ == '__main__':
    main() 