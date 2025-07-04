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

from kyotei_predictor.prediction_engine import PredictionEngine

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
            most_likely = trifecta_result['summary']['most_likely']
            if most_likely is not None:
                print(f"🎯 最有力: {most_likely['combination']} "
                      f"({most_likely['percentage']}% / "
                      f"{most_likely['expected_odds']}倍)")
            else:
                print("🎯 最有力: データなし")
            
            # 実際の結果の順位を検索
            actual_rank = None
            actual_prob = None
            for i, combo in enumerate(trifecta_result['top_combinations'], 1):
                if combo['combination'] == actual_result:
                    actual_rank = i
                    actual_prob = combo
                    break
            
            if actual_rank and actual_prob is not None:
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

# --- 追加: pipelines.trifecta_probability のテスト ---
def test_trifecta_probability_calculator():
    """TrifectaProbabilityCalculator 単体テスト"""
    print("\n🧪 TrifectaProbabilityCalculator 単体テスト")
    from kyotei_predictor.pipelines.trifecta_probability import TrifectaProbabilityCalculator
    # 仮の予測データ
    predictions = [
        {'pit_number': 1, 'win_probability': 30.0},
        {'pit_number': 2, 'win_probability': 20.0},
        {'pit_number': 3, 'win_probability': 18.0},
        {'pit_number': 4, 'win_probability': 12.0},
        {'pit_number': 5, 'win_probability': 10.0},
        {'pit_number': 6, 'win_probability': 10.0},
    ]
    calculator = TrifectaProbabilityCalculator()
    results = calculator.calculate(predictions)
    print("上位5件:")
    for combo in results[:5]:
        print(combo)
    assert len(results) == 120, "3連単組み合わせ数は120通りであるべき"
    assert results[0]['probability'] >= results[-1]['probability'], "確率順にソートされているべき"

# --- 追加: 特徴量・重み指定のテスト ---
def test_trifecta_probability_calculator_with_features():
    """TrifectaProbabilityCalculator 特徴量・重み指定テスト"""
    print("\n🧪 TrifectaProbabilityCalculator 特徴量・重み指定テスト")
    from kyotei_predictor.pipelines.trifecta_probability import TrifectaProbabilityCalculator
    # 特徴量付きサンプルデータ
    predictions = [
        {'pit_number': 1, 'rate_in_all_stadium': 6.5, 'rate_in_event_going_stadium': 7.0, 'current_rating': 'A1', 'boat_quinella_rate': 44.0, 'motor_quinella_rate': 38.0},
        {'pit_number': 2, 'rate_in_all_stadium': 5.8, 'rate_in_event_going_stadium': 6.2, 'current_rating': 'A2', 'boat_quinella_rate': 41.0, 'motor_quinella_rate': 35.0},
        {'pit_number': 3, 'rate_in_all_stadium': 5.2, 'rate_in_event_going_stadium': 5.5, 'current_rating': 'B1', 'boat_quinella_rate': 38.0, 'motor_quinella_rate': 32.0},
        {'pit_number': 4, 'rate_in_all_stadium': 4.9, 'rate_in_event_going_stadium': 5.0, 'current_rating': 'B1', 'boat_quinella_rate': 36.0, 'motor_quinella_rate': 30.0},
        {'pit_number': 5, 'rate_in_all_stadium': 4.5, 'rate_in_event_going_stadium': 4.8, 'current_rating': 'B2', 'boat_quinella_rate': 33.0, 'motor_quinella_rate': 28.0},
        {'pit_number': 6, 'rate_in_all_stadium': 4.2, 'rate_in_event_going_stadium': 4.5, 'current_rating': 'B2', 'boat_quinella_rate': 30.0, 'motor_quinella_rate': 25.0},
    ]
    calculator = TrifectaProbabilityCalculator()
    results = calculator.calculate(predictions)
    print("上位5件:")
    for combo in results[:5]:
        print(combo)
    assert len(results) == 120, "3連単組み合わせ数は120通りであるべき"
    assert results[0]['probability'] >= results[-1]['probability'], "確率順にソートされているべき"
    # カスタム重み
    custom_weights = {
        'all_stadium_rate': 0.2,
        'event_going_rate': 0.2,
        'rating': 0.1,
        'boat_quinella_rate': 0.25,
        'motor_quinella_rate': 0.25,
    }
    calculator2 = TrifectaProbabilityCalculator(weights=custom_weights)
    results2 = calculator2.calculate(predictions)
    print("\nカスタム重みでの上位5件:")
    for combo in results2[:5]:
        print(combo)
    assert len(results2) == 120
    assert results2[0]['probability'] >= results2[-1]['probability']

# --- 追加: コース特性・オッズ補正のテスト ---
def test_trifecta_probability_with_course_and_odds_bias():
    """コース特性・オッズ補正を含む3連単確率計算テスト"""
    print("\n🧪 TrifectaProbabilityCalculator コース・オッズ補正テスト")
    from kyotei_predictor.pipelines.trifecta_probability import TrifectaProbabilityCalculator
    predictions = [
        {'pit_number': 1, 'rate_in_all_stadium': 6.5, 'rate_in_event_going_stadium': 7.0, 'current_rating': 'A1', 'boat_quinella_rate': 44.0, 'motor_quinella_rate': 38.0, 'course_bias': 0.5, 'odds_bias': 0.1},
        {'pit_number': 2, 'rate_in_all_stadium': 5.8, 'rate_in_event_going_stadium': 6.2, 'current_rating': 'A2', 'boat_quinella_rate': 41.0, 'motor_quinella_rate': 35.0, 'course_bias': 0.3, 'odds_bias': 0.2},
        {'pit_number': 3, 'rate_in_all_stadium': 5.2, 'rate_in_event_going_stadium': 5.5, 'current_rating': 'B1', 'boat_quinella_rate': 38.0, 'motor_quinella_rate': 32.0, 'course_bias': 0.2, 'odds_bias': 0.3},
        {'pit_number': 4, 'rate_in_all_stadium': 4.9, 'rate_in_event_going_stadium': 5.0, 'current_rating': 'B1', 'boat_quinella_rate': 36.0, 'motor_quinella_rate': 30.0, 'course_bias': 0.1, 'odds_bias': 0.4},
        {'pit_number': 5, 'rate_in_all_stadium': 4.5, 'rate_in_event_going_stadium': 4.8, 'current_rating': 'B2', 'boat_quinella_rate': 33.0, 'motor_quinella_rate': 28.0, 'course_bias': 0.0, 'odds_bias': 0.5},
        {'pit_number': 6, 'rate_in_all_stadium': 4.2, 'rate_in_event_going_stadium': 4.5, 'current_rating': 'B2', 'boat_quinella_rate': 30.0, 'motor_quinella_rate': 25.0, 'course_bias': -0.1, 'odds_bias': 0.6},
    ]
    weights = {
        'all_stadium_rate': 0.2,
        'event_going_rate': 0.2,
        'rating': 0.1,
        'boat_quinella_rate': 0.2,
        'motor_quinella_rate': 0.2,
        'course_bias': 0.15,
        'odds_bias': 0.15,
    }
    calculator = TrifectaProbabilityCalculator(weights=weights)
    results = calculator.calculate(predictions)
    print("コース・オッズ補正込みの上位5件:")
    for combo in results[:5]:
        print(combo)
    assert len(results) == 120
    assert results[0]['probability'] >= results[-1]['probability']

def main():
    """メイン実行"""
    test_trifecta_probability()
    compare_with_actual_odds()
    test_trifecta_probability_calculator()
    test_trifecta_probability_calculator_with_features()
    test_trifecta_probability_with_course_and_odds_bias()
    print("\n✅ 3連単確率計算機能テスト完了")

if __name__ == "__main__":
    main()