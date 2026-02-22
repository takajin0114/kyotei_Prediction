#!/usr/bin/env python3
"""
予測詳細ビューアー
"""
import kyotei_predictor.utils.common  # noqa: F401 -- Windows UTF-8 stdio

import os
import sys
import json
import argparse
from pathlib import Path
from typing import Dict, List, Optional, Any

from kyotei_predictor.utils.common import KyoteiUtils

def safe_print(message: str) -> None:
    """文字化け対策付きprint関数"""
    utils = KyoteiUtils()
    utils.safe_print(message)

def load_validation_results(json_file: str) -> Dict[str, Any]:
    """検証結果を読み込み"""
    with open(json_file, 'r', encoding='utf-8') as f:
        return json.load(f)

def show_race_details(results: Dict[str, Any], race_index: int = 0):
    """特定レースの詳細を表示"""
    if race_index >= len(results['results']):
        safe_print(f"❌ レースインデックス {race_index} は存在しません")
        return
    
    race = results['results'][race_index]
    
    safe_print(f"🏁 レース詳細: {race['file']}")
    safe_print("=" * 60)
    safe_print(f"📊 実際の結果: {race['actual_result']} (1着: {race['actual_winner']}号艇)")
    safe_print()
    
    safe_print("🎯 各アルゴリズムの予想結果:")
    safe_print("-" * 60)
    
    for algo_name, prediction in race['predictions'].items():
        status = "✅ 的中" if prediction['predicted_rank'] == 1 else "❌ 外れ"
        safe_print(f"{algo_name:20} | {status}")
        safe_print(f"  予想順位: {prediction['predicted_rank']}位")
        safe_print(f"  予想確率: {prediction['predicted_probability']:.1f}%")
        safe_print(f"  1位予想: {prediction['top_prediction']}号艇")
        safe_print(f"  実行時間: {prediction['execution_time']:.3f}秒")
        safe_print()

def show_best_predictions(results: Dict[str, Any], top_n: int = 10):
    """最も的中率の高い予想を表示"""
    safe_print(f"🏆 的中率トップ{top_n}の予想")
    safe_print("=" * 60)
    
    # equipment_focusedアルゴリズムの的中したレースを抽出
    hits = []
    for i, race in enumerate(results['results']):
        pred = race['predictions']['equipment_focused']
        if pred['predicted_rank'] == 1:
            hits.append({
                'index': i,
                'file': race['file'],
                'actual': race['actual_result'],
                'predicted': pred['top_prediction'],
                'probability': pred['predicted_probability']
            })
    
    # 確率順でソート
    hits.sort(key=lambda x: x['probability'], reverse=True)
    
    for i, hit in enumerate(hits[:top_n]):
        safe_print(f"{i+1:2d}. {hit['file']}")
        safe_print(f"    実際: {hit['actual']} | 予想: {hit['predicted']}号艇 | 確率: {hit['probability']:.1f}%")
        safe_print()

def show_worst_predictions(results: Dict[str, Any], top_n: int = 10):
    """最も外れた予想を表示"""
    safe_print(f"💥 外れ率トップ{top_n}の予想")
    safe_print("=" * 60)
    
    # equipment_focusedアルゴリズムの外れたレースを抽出
    misses = []
    for i, race in enumerate(results['results']):
        pred = race['predictions']['equipment_focused']
        if pred['predicted_rank'] >= 4:  # 4位以下を外れとする
            misses.append({
                'index': i,
                'file': race['file'],
                'actual': race['actual_result'],
                'predicted': pred['top_prediction'],
                'predicted_rank': pred['predicted_rank'],
                'probability': pred['predicted_probability']
            })
    
    # 順位順でソート（悪い順）
    misses.sort(key=lambda x: x['predicted_rank'], reverse=True)
    
    for i, miss in enumerate(misses[:top_n]):
        safe_print(f"{i+1:2d}. {miss['file']}")
        safe_print(f"    実際: {miss['actual']} | 予想: {miss['predicted']}号艇({miss['predicted_rank']}位) | 確率: {miss['probability']:.1f}%")
        safe_print()

def show_algorithm_comparison(results: Dict[str, Any]):
    """アルゴリズム別の詳細比較"""
    safe_print("📊 アルゴリズム別詳細比較")
    safe_print("=" * 60)
    
    algorithms = ['basic', 'rating_weighted', 'equipment_focused', 'comprehensive', 'relative_strength']
    
    for algo in algorithms:
        safe_print(f"\n🔍 {algo} アルゴリズム:")
        safe_print("-" * 40)
        
        # 統計計算
        total_races = len(results['results'])
        hits = sum(1 for race in results['results'] if race['predictions'][algo]['predicted_rank'] == 1)
        top3_hits = sum(1 for race in results['results'] if race['predictions'][algo]['predicted_rank'] <= 3)
        
        avg_prob = sum(race['predictions'][algo]['predicted_probability'] for race in results['results']) / total_races
        avg_rank = sum(race['predictions'][algo]['predicted_rank'] for race in results['results']) / total_races
        
        safe_print(f"  1位的中率: {hits}/{total_races} ({hits/total_races*100:.1f}%)")
        safe_print(f"  上位3位的中率: {top3_hits}/{total_races} ({top3_hits/total_races*100:.1f}%)")
        safe_print(f"  平均予想確率: {avg_prob:.1f}%")
        safe_print(f"  平均予想順位: {avg_rank:.1f}位")

def main():
    """メイン処理"""
    # 最新の検証結果ファイルを探す
    output_dir = os.path.join('kyotei_predictor', 'outputs')
    json_files = [f for f in os.listdir(output_dir) if f.startswith('bulk_validation_results_') and f.endswith('.json')]
    
    if not json_files:
        safe_print("❌ 検証結果ファイルが見つかりません")
        return
    
    # 最新のファイルを使用
    latest_file = sorted(json_files)[-1]
    json_path = os.path.join(output_dir, latest_file)
    
    safe_print(f"📁 読み込みファイル: {latest_file}")
    results = load_validation_results(json_path)
    
    safe_print(f"📊 総レース数: {results['total_races']}")
    safe_print(f"⏱️ 実行時間: {results['execution_time']:.2f}秒")
    safe_print()
    
    while True:
        safe_print("\n" + "=" * 60)
        safe_print("🎯 予想結果詳細ビューアー")
        safe_print("=" * 60)
        safe_print("1. 特定レースの詳細表示")
        safe_print("2. 的中率トップ10表示")
        safe_print("3. 外れ率トップ10表示")
        safe_print("4. アルゴリズム別詳細比較")
        safe_print("5. 終了")
        safe_print("-" * 60)
        
        choice = input("選択してください (1-5): ").strip()
        
        if choice == '1':
            try:
                index = int(input("レースインデックス (0-94): "))
                show_race_details(results, index)
            except ValueError:
                safe_print("❌ 無効な入力です")
        
        elif choice == '2':
            show_best_predictions(results)
        
        elif choice == '3':
            show_worst_predictions(results)
        
        elif choice == '4':
            show_algorithm_comparison(results)
        
        elif choice == '5':
            safe_print("👋 終了します")
            break
        
        else:
            safe_print("❌ 無効な選択です")

if __name__ == "__main__":
    main() 