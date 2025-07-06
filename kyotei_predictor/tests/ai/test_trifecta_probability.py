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
    # テストスクリプトのあるディレクトリから見て、kyotei_predictor/data/raw/を参照
    test_dir = os.path.dirname(__file__)
    predictor_dir = os.path.abspath(os.path.join(test_dir, '../..'))  # プロジェクトルート/kyotei_predictor
    sample_path = os.path.join(predictor_dir, 'data', 'sample', filename)
    raw_path = os.path.join(predictor_dir, 'data', 'raw', filename)
    
    try:
        if os.path.exists(sample_path):
            with open(sample_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        elif os.path.exists(raw_path):
            with open(raw_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            print(f"❌ ファイルが見つかりません: {filename}")
            print(f"   試行パス1: {sample_path}")
            print(f"   試行パス2: {raw_path}")
            return None
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
                    'boat_quinella_rate': entry['boat'].get('quinella_rate', 0),
                    'motor_quinella_rate': entry['motor'].get('quinella_rate', 0)
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
                    'boat_quinella_rate': entry.get('boat_quinella_rate', 0),
                    'motor_quinella_rate': entry.get('motor_quinella_rate', 0)
                }
            })
    
    return {'race_entries': race_entries}

def test_trifecta_probability():
    """3連単確率計算のテスト"""
    print("🎯 3連単確率計算機能テスト")
    print("=" * 60)
    
    # テストデータ読み込み
    race_file = 'race_data_2025-06-30_KIRYU_R1.json'
    raw_data = load_race_data(race_file)
    
    if not raw_data:
        print("❌ テストデータ読み込み失敗")
        return
    
    # データ変換
    race_data = convert_to_prediction_format(raw_data)
    
    # 実際の結果
    actual_result = "2-1-4"  # 桐生R1の実際の結果
    
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
    odds_file = 'odds_data_2025-06-30_KIRYU_R1.json'
    odds_data = load_race_data(odds_file)
    
    if not odds_data:
        print("❌ オッズデータ読み込み失敗")
        return
    
    # レースデータ読み込み
    race_file = 'race_data_2025-06-30_KIRYU_R1.json'
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
    actual_result = "2-1-4"
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

def test_trifecta_parameter_sweep():
    """重み・パラメータ最適化のためのスイープテスト（minmax/softmax/temperature比較）"""
    print("\n🧪 重み・パラメータ最適化スイープテスト（minmax/softmax/temperature比較）")
    from kyotei_predictor.pipelines.trifecta_probability import TrifectaProbabilityCalculator

    # テストデータ
    race_file = 'race_data_2025-06-30_KIRYU_R1.json'
    raw_data = load_race_data(race_file)
    if not raw_data:
        print("❌ テストデータ読み込み失敗")
        return
    race_entries = raw_data['race_entries']
    # 特徴量抽出
    predictions = []
    for entry in race_entries:
        predictions.append({
            'pit_number': entry['pit_number'],
            'rate_in_all_stadium': entry['performance'].get('rate_in_all_stadium', 0),
            'rate_in_event_going_stadium': entry['performance'].get('rate_in_event_going_stadium', 0),
            'current_rating': entry['racer'].get('current_rating', 'B2'),
            'boat_quinella_rate': entry['boat'].get('quinella_rate', 0),
            'motor_quinella_rate': entry['motor'].get('quinella_rate', 0),
        })

    # sweep対象パラメータ
    weight_patterns = [
        {'all_stadium_rate': 0.4, 'event_going_rate': 0.2, 'rating': 0.1, 'boat_quinella_rate': 0.15, 'motor_quinella_rate': 0.15},
        {'all_stadium_rate': 0.2, 'event_going_rate': 0.4, 'rating': 0.1, 'boat_quinella_rate': 0.15, 'motor_quinella_rate': 0.15},
        {'all_stadium_rate': 0.2, 'event_going_rate': 0.2, 'rating': 0.2, 'boat_quinella_rate': 0.2, 'motor_quinella_rate': 0.2},
        {'all_stadium_rate': 0.1, 'event_going_rate': 0.1, 'rating': 0.1, 'boat_quinella_rate': 0.35, 'motor_quinella_rate': 0.35},
    ]
    second_weights = [0.8, 0.7, 0.6]
    third_weights = [0.6, 0.5, 0.4]
    normalizations = ['minmax', 'softmax']
    temperatures = [1.0, 0.7, 0.5, 0.3, 0.1]
    actual_result = "2-1-4"

    best_rank = 999
    best_setting = None
    print("\n--- 正規化: minmax ---")
    for weights in weight_patterns:
        for second in second_weights:
            for third in third_weights:
                calculator = TrifectaProbabilityCalculator(
                    second_weight=second, third_weight=third, weights=weights, normalization='minmax')
                results = calculator.calculate(predictions)
                rank = None
                for i, combo in enumerate(results, 1):
                    if combo['combination'] == actual_result:
                        rank = i
                        break
                print(f"Pattern {weight_patterns.index(weights)+1}, 2nd={second}, 3rd={third} => 実際結果順位: {rank if rank else '圏外'} 上位5: {[c['combination'] for c in results[:5]]}")
                if rank and rank < best_rank:
                    best_rank = rank
                    best_setting = ('minmax', weights, second, third)
    print()
    print("--- 正規化: softmax (温度パラメータ) ---")
    for weights in weight_patterns:
        for second in second_weights:
            for third in third_weights:
                for temp in temperatures:
                    calculator = TrifectaProbabilityCalculator(
                        second_weight=second, third_weight=third, weights=weights, normalization='softmax', temperature=temp)
                    results = calculator.calculate(predictions)
                    rank = None
                    for i, combo in enumerate(results, 1):
                        if combo['combination'] == actual_result:
                            rank = i
                            break
                    print(f"Pattern {weight_patterns.index(weights)+1}, 2nd={second}, 3rd={third}, temp={temp} => 実際結果順位: {rank if rank else '圏外'} 上位5: {[c['combination'] for c in results[:5]]}")
                    if rank and rank < best_rank:
                        best_rank = rank
                        best_setting = ('softmax', weights, second, third, temp)
    print(f"\n最良パターン: {best_setting}, 実際結果順位: {best_rank}")
    print("✅ 3連単確率計算機能テスト完了")

def test_trifecta_probability_with_course_and_environment_features():
    """コース特性・環境要因を含む3連単確率計算テスト"""
    print("\n🌊 コース特性・環境要因を含む3連単確率計算テスト")
    from kyotei_predictor.pipelines.trifecta_probability import TrifectaProbabilityCalculator

    # テストデータ読み込み
    race_file = 'race_data_2025-06-30_KIRYU_R1.json'
    raw_data = load_race_data(race_file)
    if not raw_data:
        print("❌ テストデータ読み込み失敗")
        return

    # 基本特徴量に加えて、コース・環境要因を追加
    predictions = []
    for i, entry in enumerate(raw_data['race_entries']):
        # 基本特徴量
        base_features = {
            'pit_number': entry['pit_number'],
            'rate_in_all_stadium': entry['performance'].get('rate_in_all_stadium', 0),
            'rate_in_event_going_stadium': entry['performance'].get('rate_in_event_going_stadium', 0),
            'current_rating': entry['racer'].get('current_rating', 'B2'),
            'boat_quinella_rate': entry['boat'].get('quinella_rate', 0),
            'motor_quinella_rate': entry['motor'].get('quinella_rate', 0),
        }
        
        # コース・環境要因を追加（シミュレーション）
        # 実際のデータにはないため、選手の特性に基づいて推定
        course_bias = 0.0  # コース特性（0: 中立, 正: 有利, 負: 不利）
        wind_effect = 0.0  # 風の影響（0: 中立, 正: 追い風有利, 負: 向かい風有利）
        wave_effect = 0.0  # 波の影響（0: 中立, 正: 高波有利, 負: 低波有利）
        temperature_effect = 0.0  # 気温の影響（0: 中立, 正: 高温有利, 負: 低温有利）
        
        # 選手の特性に基づいて環境要因を設定
        if entry['pit_number'] in [1, 2]:  # 内側コース
            course_bias = 0.1  # 内側コース有利
        elif entry['pit_number'] in [5, 6]:  # 外側コース
            course_bias = -0.05  # 外側コースやや不利
        
        # 選手の勝率に基づいて環境適応性を推定
        win_rate = entry['performance'].get('rate_in_all_stadium', 0)
        if win_rate > 0.06:  # 高勝率選手
            wind_effect = 0.05  # 追い風に強い
            wave_effect = 0.03  # 高波に強い
        elif win_rate < 0.04:  # 低勝率選手
            wind_effect = -0.03  # 向かい風に弱い
            wave_effect = -0.02  # 高波に弱い
        
        # 気温効果（夏場のレース想定）
        temperature_effect = 0.02 if win_rate > 0.05 else -0.01
        
        # 統合特徴量
        predictions.append({
            **base_features,
            'course_bias': course_bias,
            'wind_effect': wind_effect,
            'wave_effect': wave_effect,
            'temperature_effect': temperature_effect,
        })

    # 基本重み（機材重視）
    base_weights = {
        'all_stadium_rate': 0.1,
        'event_going_rate': 0.1,
        'rating': 0.1,
        'boat_quinella_rate': 0.35,
        'motor_quinella_rate': 0.35,
    }
    
    # 環境要因を含む重みパターン
    weight_patterns = [
        # パターン1: 基本重みのみ
        base_weights,
        # パターン2: コース特性重視
        {**base_weights, 'course_bias': 0.2},
        # パターン3: 風の影響重視
        {**base_weights, 'wind_effect': 0.15},
        # パターン4: 波の影響重視
        {**base_weights, 'wave_effect': 0.15},
        # パターン5: 気温の影響重視
        {**base_weights, 'temperature_effect': 0.15},
        # パターン6: 全環境要因バランス
        {**base_weights, 'course_bias': 0.1, 'wind_effect': 0.1, 'wave_effect': 0.1, 'temperature_effect': 0.1},
    ]
    
    actual_result = "2-1-4"
    best_rank = 999
    best_setting = None
    
    print("--- 環境要因を含む重みパターンテスト ---")
    for i, weights in enumerate(weight_patterns, 1):
        calculator = TrifectaProbabilityCalculator(
            second_weight=0.8, third_weight=0.5, 
            weights=weights, normalization='softmax', temperature=0.1)
        results = calculator.calculate(predictions)
        
        rank = None
        for j, combo in enumerate(results, 1):
            if combo['combination'] == actual_result:
                rank = j
                break
        
        pattern_name = f"Pattern {i}"
        if i == 1:
            pattern_name = "基本重みのみ"
        elif i == 2:
            pattern_name = "コース特性重視"
        elif i == 3:
            pattern_name = "風の影響重視"
        elif i == 4:
            pattern_name = "波の影響重視"
        elif i == 5:
            pattern_name = "気温の影響重視"
        elif i == 6:
            pattern_name = "全環境要因バランス"
        
        print(f"{pattern_name} => 実際結果順位: {rank if rank else '圏外'} 上位5: {[c['combination'] for c in results[:5]]}")
        
        if rank and rank < best_rank:
            best_rank = rank
            best_setting = (pattern_name, weights)
    
    print(f"\n最良パターン: {best_setting}, 実際結果順位: {best_rank}")
    print("✅ コース特性・環境要因テスト完了")

def main():
    """メイン実行"""
    if len(sys.argv) > 1 and sys.argv[1] == '--sweep':
        # パラメータスイープテストのみ実行
        test_trifecta_parameter_sweep()
        test_trifecta_probability_with_course_and_environment_features()
    else:
        # 全テスト実行
        test_trifecta_probability()
        compare_with_actual_odds()
        test_trifecta_probability_calculator()
        test_trifecta_probability_calculator_with_features()
        test_trifecta_probability_with_course_and_odds_bias()
        test_trifecta_parameter_sweep()
        test_trifecta_probability_with_course_and_environment_features()

if __name__ == "__main__":
    main()