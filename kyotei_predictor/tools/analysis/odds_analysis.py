#!/usr/bin/env python3
"""
オッズ分析ツール
"""

import os
import sys
import json
from typing import Dict, List, Optional, Tuple

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

def load_odds_data(filename):
    """オッズデータを読み込み"""
    filepath = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', filename)
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        safe_print(f"❌ ファイル読み込みエラー: {e}")
        return None

def load_race_data(filename):
    """レースデータを読み込み"""
    filepath = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', filename)
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        safe_print(f"❌ ファイル読み込みエラー: {e}")
        return None

def analyze_odds_vs_result():
    """
    オッズと実際の結果を比較分析
    """
    safe_print("🎰 オッズ vs 実際の結果 分析")
    safe_print("=" * 50)
    
    # データ読み込み
    odds_data = load_odds_data('odds_data_2024-06-15_KIRYU_R1.json')
    race_data = load_race_data('complete_race_data_20240615_KIRYU_R1.json')
    
    if not odds_data or not race_data:
        safe_print("❌ データ読み込み失敗")
        return
    
    # 実際の結果を取得
    race_records = race_data.get('race_records', [])
    if not race_records:
        safe_print("❌ レース結果データなし")
        return
    
    # 着順を取得
    result_order = {}
    for record in race_records:
        pit_number = record.get('pit_number')
        arrival = record.get('arrival')
        if pit_number and arrival:
            result_order[arrival] = pit_number
    
    if len(result_order) < 3:
        safe_print("❌ 3着までの結果が不完全")
        return
    
    # 実際の3連単組み合わせ
    actual_combination = f"{result_order[1]}-{result_order[2]}-{result_order[3]}"
    safe_print(f"🏆 実際の結果: {actual_combination}")
    
    # オッズデータから該当組み合わせを検索
    odds_list = odds_data.get('odds_data', [])
    actual_odds = None
    
    for odds in odds_list:
        if odds['combination'] == actual_combination:
            actual_odds = odds
            break
    
    if actual_odds:
        safe_print(f"💰 実際のオッズ: {actual_odds['ratio']}倍")
        
        # 人気順位を計算
        sorted_odds = sorted(odds_list, key=lambda x: x['ratio'])
        popularity_rank = None
        for i, odds in enumerate(sorted_odds, 1):
            if odds['combination'] == actual_combination:
                popularity_rank = i
                break
        
        safe_print(f"📊 人気順位: {popularity_rank}位 / {len(odds_list)}通り")
        safe_print(f"📈 人気度: {(len(odds_list) - popularity_rank + 1) / len(odds_list) * 100:.1f}%")
        
        # 配当分析
        if actual_odds['ratio'] < 20:
            safe_print("🎯 低配当 (人気決着)")
        elif actual_odds['ratio'] < 100:
            safe_print("🎲 中配当 (やや波乱)")
        else:
            safe_print("💥 高配当 (大波乱)")
    else:
        safe_print(f"❌ オッズデータに該当組み合わせなし: {actual_combination}")
    
    # 人気上位の分析
    safe_print(f"\n📊 人気上位5位の分析:")
    sorted_odds = sorted(odds_list, key=lambda x: x['ratio'])
    for i, odds in enumerate(sorted_odds[:5], 1):
        marker = "🏆" if odds['combination'] == actual_combination else "  "
        safe_print(f"{marker} {i}位: {odds['combination']} → {odds['ratio']}倍")
    
    # 予測との比較
    safe_print(f"\n🔮 予測アルゴリズムとの比較:")
    
    # 予測結果（既知）
    predicted_combinations = [
        "5-6-4",  # basic予測
        "5-6-4"   # rating_weighted予測
    ]
    
    for i, pred_combo in enumerate(predicted_combinations):
        algorithm = ["basic", "rating_weighted"][i]
        
        # 予測組み合わせのオッズを検索
        pred_odds = None
        for odds in odds_list:
            if odds['combination'] == pred_combo:
                pred_odds = odds
                break
        
        if pred_odds:
            safe_print(f"   {algorithm}: {pred_combo} → {pred_odds['ratio']}倍")
        else:
            safe_print(f"   {algorithm}: {pred_combo} → オッズなし")

def main():
    """メイン実行"""
    analyze_odds_vs_result()

if __name__ == "__main__":
    main()