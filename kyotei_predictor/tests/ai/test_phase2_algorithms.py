#!/usr/bin/env python3
"""
Phase 2 アルゴリズムの実データテスト

実際のレースデータを使用してPhase 2の新しいアルゴリズムを検証
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
    """
    生のレースデータを予測エンジン用フォーマットに変換
    """
    race_entries = []
    
    # race_entriesが直接存在する場合
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
    
    # 古い形式のデータの場合
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

def test_phase2_with_real_data():
    """
    実際のレースデータでPhase 2アルゴリズムをテスト
    """
    print("🏁 Phase 2 アルゴリズム実データテスト")
    print("=" * 60)
    
    # 実際のレースデータを読み込み
    race_files = [
        'complete_race_data_20240615_KIRYU_R1.json',
        'race_data_2024-06-15_KIRYU_R2.json',
        'race_data_2024-06-15_TODA_R1.json'
    ]
    
    engine = PredictionEngine()
    
    algorithms = ['basic', 'rating_weighted', 'equipment_focused', 'comprehensive', 'relative_strength']
    
    for race_file in race_files:
        print(f"\n🏟️ レースファイル: {race_file}")
        print("-" * 50)
        
        # レースデータ読み込み
        raw_data = load_race_data(race_file)
        if not raw_data:
            print("❌ データ読み込み失敗")
            continue
        
        # データ統合（簡易版）
        try:
            integrated_data = convert_to_prediction_format(raw_data)
        except Exception as e:
            print(f"❌ データ変換エラー: {e}")
            continue
        
        # 実際の結果を取得
        actual_result = None
        if 'race_records' in raw_data:
            result_order = {}
            for record in raw_data['race_records']:
                pit_number = record.get('pit_number')
                arrival = record.get('arrival')
                if pit_number and arrival:
                    result_order[arrival] = pit_number
            
            if len(result_order) >= 3:
                actual_result = f"{result_order[1]}-{result_order[2]}-{result_order[3]}"
        
        print(f"🏆 実際の結果: {actual_result if actual_result else '不明'}")
        
        # 各アルゴリズムで予測
        results = {}
        for algorithm in algorithms:
            try:
                result = engine.predict(integrated_data, algorithm)
                results[algorithm] = result
                
                # 予測結果の表示
                favorite = result['summary']['favorite']
                top3 = [pred['pit_number'] for pred in result['predictions'][:3]]
                predicted_combination = f"{top3[0]}-{top3[1]}-{top3[2]}"
                
                # 的中判定
                hit_status = "🎯" if predicted_combination == actual_result else "❌"
                if actual_result and str(result_order[1]) == str(top3[0]):
                    hit_status = "🥇"  # 本命的中
                
                print(f"  {algorithm:15}: {predicted_combination} {hit_status} (本命: {favorite['pit_number']}号艇 {favorite['win_probability']}%)")
                
            except Exception as e:
                print(f"  {algorithm:15}: ❌ エラー - {e}")
        
        # アルゴリズム比較分析
        if results:
            print(f"\n📊 アルゴリズム特徴分析:")
            
            # 本命の一致度
            favorites = {}
            for algo, result in results.items():
                fav_pit = result['summary']['favorite']['pit_number']
                if fav_pit not in favorites:
                    favorites[fav_pit] = []
                favorites[fav_pit].append(algo)
            
            for pit, algos in favorites.items():
                print(f"    {pit}号艇本命: {', '.join(algos)}")
            
            # 信頼度比較
            print(f"  信頼度:")
            for algo, result in results.items():
                confidence = result['summary']['confidence_level']
                print(f"    {algo:15}: {confidence}")

def analyze_algorithm_characteristics():
    """
    アルゴリズムの特徴分析
    """
    print(f"\n" + "="*60)
    print("🔍 Phase 2 アルゴリズム特徴分析")
    print("="*60)
    
    characteristics = {
        'basic': {
            'focus': '選手の勝率重視',
            'strength': 'シンプルで安定',
            'weakness': '機材・環境を考慮しない',
            'use_case': '基本的な予測、ベンチマーク'
        },
        'rating_weighted': {
            'focus': '級別を重視した勝率評価',
            'strength': 'A級選手を適切に評価',
            'weakness': '機材差を軽視',
            'use_case': '格上選手重視の予測'
        },
        'equipment_focused': {
            'focus': 'ボート・モーター成績重視',
            'strength': '機材の調子を反映',
            'weakness': '選手の実力を軽視',
            'use_case': '機材差が大きいレース'
        },
        'comprehensive': {
            'focus': '選手・機材・級別のバランス',
            'strength': '総合的な評価',
            'weakness': '特徴が薄い',
            'use_case': '標準的な予測'
        },
        'relative_strength': {
            'focus': 'レース内での相対的優位性',
            'strength': 'レース特性を反映',
            'weakness': '絶対的な実力を軽視',
            'use_case': '混戦レースの予測'
        }
    }
    
    for algo, char in characteristics.items():
        print(f"\n🔧 {algo.upper()}")
        print(f"  焦点: {char['focus']}")
        print(f"  強み: {char['strength']}")
        print(f"  弱み: {char['weakness']}")
        print(f"  用途: {char['use_case']}")

def main():
    """メイン実行"""
    test_phase2_with_real_data()
    analyze_algorithm_characteristics()
    
    print(f"\n✅ Phase 2 アルゴリズム実データテスト完了")

if __name__ == "__main__":
    main()