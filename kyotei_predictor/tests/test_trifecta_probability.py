#!/usr/bin/env python3
"""
3連単確率計算機能のテスト

Phase 2で実装した3連単確率計算機能を検証
"""

import sys
import os
import json

# パス設定
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from prediction_engine import PredictionEngine

def load_race_data(filename):
    """レースデータを読み込み"""
    filepath = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', filename)
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"❌ ファイル読み込みエラー: {e}")
        return None

def convert_to_prediction_format(raw_data):
    """生のレースデータを予測エンジン用フォーマットに変換"""
    race_entries = []
    
    if 'race_entries' in raw_data:
        for entry in raw_data['race_entries']:
            race_entries.append({
                'pit_number': entry['pit_number'],
                'racer': {
                    'name': entry['racer']['name'],
                    'current_rating': entry['racer'].get('current_rating', 'B2')
                },
                'performance': {
                    'rate_in_all_stadium': entry['performance'].get('rate_in_all_stadium', 0),
                    'rate_in_event_going_stadium': entry['performance'].get('rate_in_event_going_stadium', 0),
                    'boat_quinella_rate': entry['performance'].get('boat_quinella_rate', 0),
                    'motor_quinella_rate': entry['performance'].get('motor_quinella_rate', 0)
                }
            })
    elif 'race_entry_information' in raw_data:
        for entry in raw_data['race_entry_information']:
            race_entries.append({
                'pit_number': entry['pit_number'],
                'racer': {
                    'name': entry['racer']['name'],
                    'current_rating': entry['racer'].get('current_rating', 'B2')
                },
                'performance': {
                    'rate_in_all_stadium': entry['performance'].get('rate_in_all_stadium', 0),
                    'rate_in_event_going_stadium': entry['performance'].get('rate_in_event_going_stadium', 0),
                    'boat_quinella_rate': entry['performance'].get('boat_quinella_rate', 0),
                    'motor_quinella_rate': entry['performance'].get('motor_quinella_rate', 0)
                }
            })
    
    return {'race_entries': race_entries}

def test_trifecta_probability():
    """3連単確率計算のテスト"""
    print("🎯 3連単確率計算機能テスト")
    print("=" * 60)
    
    # テストデータ読み込み
    race_file = 'complete_race_data_20240615_KIRYU_R1.json'
    raw_data = load_race_data(race_file)
    
    if not raw_data:
        print("❌ テストデータ読み込み失敗")
        return
    
    # データ変換
    race_data = convert_to_prediction_format(raw_data)
    
    # 実際の結果
    actual_result = "3-5-6"  # 桐生R1の実際の結果
    
    print(f"🏟️ テストレース: {race_file}")
    print(f"🏆 実際の結果: {actual_result}")
    print()
    
    engine = PredictionEngine()
    
    # 各アルゴリズムで3連単確率計算
    algorithms = ['basic', 'rating_weighted', 'equipment_focused', 'comprehensive', 'relative_strength']
    
    for algorithm in algorithms:
        print(f"📊 {algorithm.upper()} アルゴリズム")
        print("-" * 40)
        
        try:
            # 3連単推奨取得
            trifecta_result = engine.get_top_trifecta_recommendations(
                race_data, 
                algorithm=algorithm, 
                top_n=10
            )
            
            print(f"🎯 最有力: {trifecta_result['summary']['most_likely']['combination']} "
                  f"({trifecta_result['summary']['most_likely']['percentage']}% / "
                  f"{trifecta_result['summary']['most_likely']['expected_odds']}倍)")
            
            # 実際の結果の順位を検索
            actual_rank = None
            actual_prob = None
            for i, combo in enumerate(trifecta_result['top_combinations'], 1):
                if combo['combination'] == actual_result:
                    actual_rank = i
                    actual_prob = combo
                    break
            
            if actual_rank:
                print(f"🏆 実際結果: {actual_rank}位 ({actual_prob['percentage']}% / {actual_prob['expected_odds']}倍)")
            else:
                print(f"🏆 実際結果: 10位圏外")
            
            # 上位5位表示
            print("🥇 上位5位:")
            for i, combo in enumerate(trifecta_result['top_combinations'][:5], 1):
                marker = "🎯" if combo['combination'] == actual_result else "  "
                print(f"{marker} {i}位: {combo['combination']} ({combo['percentage']}% / {combo['expected_odds']}倍)")
            
            print(f"📈 上位10位合計確率: {trifecta_result['summary']['total_probability']:.4f} ({trifecta_result['summary']['total_probability']*100:.2f}%)")
            print()
            
        except Exception as e:
            print(f"❌ エラー: {e}")
            print()

def compare_with_actual_odds():
    """実際のオッズとの比較"""
    print("💰 実際のオッズとの比較")
    print("=" * 60)
    
    # オッズデータ読み込み
    odds_file = 'odds_data_2024-06-15_KIRYU_R1.json'
    odds_data = load_race_data(odds_file)
    
    if not odds_data:
        print("❌ オッズデータ読み込み失敗")
        return
    
    # レースデータ読み込み
    race_file = 'complete_race_data_20240615_KIRYU_R1.json'
    raw_data = load_race_data(race_file)
    race_data = convert_to_prediction_format(raw_data)
    
    engine = PredictionEngine()
    
    # comprehensive アルゴリズムで予測
    trifecta_result = engine.get_top_trifecta_recommendations(
        race_data, 
        algorithm='comprehensive', 
        top_n=20
    )
    
    print("🔍 予測オッズ vs 実際オッズ比較 (上位10位)")
    print("-" * 50)
    
    # 実際のオッズデータから対応する組み合わせを検索
    actual_odds_map = {}
    for odds in odds_data['odds_data']:
        actual_odds_map[odds['combination']] = odds['ratio']
    
    for i, combo in enumerate(trifecta_result['top_combinations'][:10], 1):
        combination = combo['combination']
        predicted_odds = combo['expected_odds']
        actual_odds = actual_odds_map.get(combination, 'N/A')
        
        if actual_odds != 'N/A':
            diff = abs(predicted_odds - actual_odds)
            accuracy = f"(差: {diff:.1f})"
        else:
            accuracy = ""
        
        print(f"{i:2}位: {combination} | 予測: {predicted_odds:6.1f}倍 | 実際: {actual_odds:>6}倍 {accuracy}")
    
    # 実際の結果の比較
    actual_result = "3-5-6"
    actual_result_odds = actual_odds_map.get(actual_result, 'N/A')
    
    # 予測での実際結果の順位を検索
    predicted_rank = None
    predicted_odds_for_actual = None
    for i, combo in enumerate(trifecta_result['top_combinations'], 1):
        if combo['combination'] == actual_result:
            predicted_rank = i
            predicted_odds_for_actual = combo['expected_odds']
            break
    
    print(f"\n🏆 実際の結果 ({actual_result}):")
    print(f"   予測順位: {predicted_rank if predicted_rank else '20位圏外'}")
    print(f"   予測オッズ: {predicted_odds_for_actual:.1f}倍" if predicted_odds_for_actual else "   予測オッズ: N/A")
    print(f"   実際オッズ: {actual_result_odds}倍")
    
    if predicted_odds_for_actual and actual_result_odds != 'N/A':
        diff = abs(predicted_odds_for_actual - actual_result_odds)
        accuracy_rate = (1 - diff / actual_result_odds) * 100
        print(f"   予測精度: {accuracy_rate:.1f}% (差: {diff:.1f}倍)")

def main():
    """メイン実行"""
    test_trifecta_probability()
    compare_with_actual_odds()
    
    print("\n✅ 3連単確率計算機能テスト完了")

if __name__ == "__main__":
    main()