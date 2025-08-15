#!/usr/bin/env python3
"""
予測結果クイックビューアー
"""

import os
import sys
import json
import argparse
from pathlib import Path
from typing import Dict, List, Optional

# 文字化け対策: 標準出力のエンコーディングをUTF-8に設定
if sys.platform.startswith('win'):
    import codecs
    # PowerShellでの文字化け対策
    try:
        # 環境変数でUTF-8を強制
        os.environ['PYTHONIOENCODING'] = 'utf-8'
        os.environ['PYTHONLEGACYWINDOWSSTDIO'] = 'utf-8'
        
        # 標準出力をUTF-8に設定（安全な方法）
        if hasattr(sys.stdout, 'detach'):
            sys.stdout = codecs.getwriter('utf-8')(sys.stdout.detach())
            sys.stderr = codecs.getwriter('utf-8')(sys.stderr.detach())
    except Exception:
        # エラーが発生した場合は環境変数のみ設定
        os.environ['PYTHONIOENCODING'] = 'utf-8'
        os.environ['PYTHONLEGACYWINDOWSSTDIO'] = 'utf-8'

from kyotei_predictor.utils.common import KyoteiUtils

def safe_print(message: str) -> None:
    """文字化け対策付きprint関数"""
    utils = KyoteiUtils()
    utils.safe_print(message)

def show_sample_predictions():
    """サンプル予想結果を表示"""
    # 最新の検証結果ファイルを探す
    output_dir = os.path.join('kyotei_predictor', 'outputs')
    json_files = [f for f in os.listdir(output_dir) if f.startswith('bulk_validation_results_') and f.endswith('.json')]
    
    if not json_files:
        safe_print("❌ 検証結果ファイルが見つかりません")
        return
    
    # 最新のファイルを使用
    latest_file = sorted(json_files)[-1]
    json_path = os.path.join(output_dir, latest_file)
    
    with open(json_path, 'r', encoding='utf-8') as f:
        results = json.load(f)
    
    safe_print("🎯 具体的な予想結果サンプル")
    safe_print("=" * 60)
    
    # 最初の5レースを表示
    for i in range(min(5, len(results['results']))):
        race = results['results'][i]
        safe_print(f"\n🏁 レース {i+1}: {race['file']}")
        safe_print(f"📊 実際の結果: {race['actual_result']} (1着: {race['actual_winner']}号艇)")
        safe_print()
        
        # equipment_focusedアルゴリズムの結果を詳しく表示
        pred = race['predictions']['equipment_focused']
        status = "✅ 的中" if pred['predicted_rank'] == 1 else "❌ 外れ"
        safe_print(f"🔧 equipment_focused: {status}")
        safe_print(f"   予想順位: {pred['predicted_rank']}位")
        safe_print(f"   予想確率: {pred['predicted_probability']:.1f}%")
        safe_print(f"   1位予想: {pred['top_prediction']}号艇")
        
        # 他のアルゴリズムとの比較
        safe_print("   他のアルゴリズム:")
        for algo_name, algo_pred in race['predictions'].items():
            if algo_name != 'equipment_focused':
                algo_status = "✅" if algo_pred['predicted_rank'] == 1 else "❌"
                safe_print(f"     {algo_name:15}: {algo_pred['top_prediction']}号艇({algo_pred['predicted_rank']}位) {algo_status}")
        safe_print("-" * 40)

def show_best_hits():
    """的中した予想の詳細"""
    output_dir = os.path.join('kyotei_predictor', 'outputs')
    json_files = [f for f in os.listdir(output_dir) if f.startswith('bulk_validation_results_') and f.endswith('.json')]
    
    if not json_files:
        safe_print("❌ 検証結果ファイルが見つかりません")
        return
    
    latest_file = sorted(json_files)[-1]
    json_path = os.path.join(output_dir, latest_file)
    
    with open(json_path, 'r', encoding='utf-8') as f:
        results = json.load(f)
    
    safe_print("\n🏆 equipment_focusedアルゴリズムの的中例")
    safe_print("=" * 60)
    
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
        safe_print(f"{i+1}. {hit['file']}")
        safe_print(f"   実際: {hit['actual']} | 予想: {hit['predicted']}号艇 | 確率: {hit['probability']:.1f}%")
        safe_print()

def show_miss_examples():
    """外れた予想の詳細"""
    output_dir = os.path.join('kyotei_predictor', 'outputs')
    json_files = [f for f in os.listdir(output_dir) if f.startswith('bulk_validation_results_') and f.endswith('.json')]
    
    if not json_files:
        safe_print("❌ 検証結果ファイルが見つかりません")
        return
    
    latest_file = sorted(json_files)[-1]
    json_path = os.path.join(output_dir, latest_file)
    
    with open(json_path, 'r', encoding='utf-8') as f:
        results = json.load(f)
    
    safe_print("\n💥 equipment_focusedアルゴリズムの外れ例")
    safe_print("=" * 60)
    
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
        safe_print(f"{i+1}. {miss['file']}")
        safe_print(f"   実際: {miss['actual']} | 予想: {miss['predicted']}号艇({miss['predicted_rank']}位) | 確率: {miss['probability']:.1f}%")
        safe_print()

if __name__ == "__main__":
    show_sample_predictions()
    show_best_hits()
    show_miss_examples() 