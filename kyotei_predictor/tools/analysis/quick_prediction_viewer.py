#!/usr/bin/env python3
"""
簡単予想結果ビューアー

具体的な予想結果を簡単に確認
"""

import json
import os

def show_sample_predictions():
    """サンプル予想結果を表示"""
    # 最新の検証結果ファイルを探す
    output_dir = os.path.join('kyotei_predictor', 'outputs')
    json_files = [f for f in os.listdir(output_dir) if f.startswith('bulk_validation_results_') and f.endswith('.json')]
    
    if not json_files:
        print("❌ 検証結果ファイルが見つかりません")
        return
    
    # 最新のファイルを使用
    latest_file = sorted(json_files)[-1]
    json_path = os.path.join(output_dir, latest_file)
    
    with open(json_path, 'r', encoding='utf-8') as f:
        results = json.load(f)
    
    print("🎯 具体的な予想結果サンプル")
    print("=" * 60)
    
    # 最初の5レースを表示
    for i in range(min(5, len(results['results']))):
        race = results['results'][i]
        print(f"\n🏁 レース {i+1}: {race['file']}")
        print(f"📊 実際の結果: {race['actual_result']} (1着: {race['actual_winner']}号艇)")
        print()
        
        # equipment_focusedアルゴリズムの結果を詳しく表示
        pred = race['predictions']['equipment_focused']
        status = "✅ 的中" if pred['predicted_rank'] == 1 else "❌ 外れ"
        print(f"🔧 equipment_focused: {status}")
        print(f"   予想順位: {pred['predicted_rank']}位")
        print(f"   予想確率: {pred['predicted_probability']:.1f}%")
        print(f"   1位予想: {pred['top_prediction']}号艇")
        
        # 他のアルゴリズムとの比較
        print("   他のアルゴリズム:")
        for algo_name, algo_pred in race['predictions'].items():
            if algo_name != 'equipment_focused':
                algo_status = "✅" if algo_pred['predicted_rank'] == 1 else "❌"
                print(f"     {algo_name:15}: {algo_pred['top_prediction']}号艇({algo_pred['predicted_rank']}位) {algo_status}")
        print("-" * 40)

def show_best_hits():
    """的中した予想の詳細"""
    output_dir = os.path.join('kyotei_predictor', 'outputs')
    json_files = [f for f in os.listdir(output_dir) if f.startswith('bulk_validation_results_') and f.endswith('.json')]
    
    if not json_files:
        print("❌ 検証結果ファイルが見つかりません")
        return
    
    latest_file = sorted(json_files)[-1]
    json_path = os.path.join(output_dir, latest_file)
    
    with open(json_path, 'r', encoding='utf-8') as f:
        results = json.load(f)
    
    print("\n🏆 equipment_focusedアルゴリズムの的中例")
    print("=" * 60)
    
    # 的中したレースを抽出
    hits = []
    for race in results['results']:
        pred = race['predictions']['equipment_focused']
        if pred['predicted_rank'] == 1:
            hits.append({
                'file': race['file'],
                'actual': race['actual_result'],
                'predicted': pred['top_prediction'],
                'probability': pred['predicted_probability']
            })
    
    # 確率順でソートして上位5件を表示
    hits.sort(key=lambda x: x['probability'], reverse=True)
    
    for i, hit in enumerate(hits[:5]):
        print(f"{i+1}. {hit['file']}")
        print(f"   実際: {hit['actual']} | 予想: {hit['predicted']}号艇 | 確率: {hit['probability']:.1f}%")
        print()

def show_miss_examples():
    """外れた予想の詳細"""
    output_dir = os.path.join('kyotei_predictor', 'outputs')
    json_files = [f for f in os.listdir(output_dir) if f.startswith('bulk_validation_results_') and f.endswith('.json')]
    
    if not json_files:
        print("❌ 検証結果ファイルが見つかりません")
        return
    
    latest_file = sorted(json_files)[-1]
    json_path = os.path.join(output_dir, latest_file)
    
    with open(json_path, 'r', encoding='utf-8') as f:
        results = json.load(f)
    
    print("\n💥 equipment_focusedアルゴリズムの外れ例")
    print("=" * 60)
    
    # 外れたレースを抽出（4位以下）
    misses = []
    for race in results['results']:
        pred = race['predictions']['equipment_focused']
        if pred['predicted_rank'] >= 4:
            misses.append({
                'file': race['file'],
                'actual': race['actual_result'],
                'predicted': pred['top_prediction'],
                'predicted_rank': pred['predicted_rank'],
                'probability': pred['predicted_probability']
            })
    
    # 順位順でソートして上位5件を表示
    misses.sort(key=lambda x: x['predicted_rank'], reverse=True)
    
    for i, miss in enumerate(misses[:5]):
        print(f"{i+1}. {miss['file']}")
        print(f"   実際: {miss['actual']} | 予想: {miss['predicted']}号艇({miss['predicted_rank']}位) | 確率: {miss['probability']:.1f}%")
        print()

if __name__ == "__main__":
    show_sample_predictions()
    show_best_hits()
    show_miss_examples() 