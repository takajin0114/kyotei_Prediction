#!/usr/bin/env python3
"""
強化版機材重視アルゴリズムのテスト

機材相性、時系列分析、組み合わせ効果を考慮した
equipment_focused_enhancedアルゴリズムの検証
"""

import sys
import os
import json

# パス設定
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from kyotei_predictor.prediction_engine import PredictionEngine

def load_race_data(filename):
    """レースデータを読み込み"""
    test_dir = os.path.dirname(__file__)
    predictor_dir = os.path.abspath(os.path.join(test_dir, '../..'))
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
    
    return {'race_entries': race_entries}

def test_equipment_focused_enhanced():
    """強化版機材重視アルゴリズムのテスト"""
    print("🔧 強化版機材重視アルゴリズムテスト")
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
    actual_result = "2-1-4"
    
    print(f"🏟️ テストレース: {race_file}")
    print(f"🏆 実際の結果: {actual_result}")
    print()
    
    engine = PredictionEngine()
    
    # 強化版機材重視アルゴリズムで予測
    print("📊 EQUIPMENT_FOCUSED_ENHANCED アルゴリズム")
    print("-" * 50)
    
    try:
        # 予測実行
        result = engine.predict(race_data, algorithm='equipment_focused')
        
        # 予測結果の表示
        predictions = result['predictions']
        predictions.sort(key=lambda x: x['prediction_score'], reverse=True)
        
        print(f"🎯 最有力: {predictions[0]['pit_number']}号艇 "
              f"({predictions[0]['win_probability']:.2f}%)")
        
        # 実際の結果の順位を検索
        actual_rank = None
        for i, pred in enumerate(predictions, 1):
            if pred['pit_number'] == 2:  # 実際の1着艇
                actual_rank = i
                break
        
        if actual_rank:
            print(f"🏆 実際結果: {actual_rank}位 ({predictions[actual_rank-1]['win_probability']:.2f}%)")
        else:
            print(f"🏆 実際結果: 圏外")
        
        # 上位5位表示
        print("🥇 上位5位:")
        for i, pred in enumerate(predictions[:5], 1):
            marker = "🎯" if pred['pit_number'] == 2 else "  "
            print(f"{marker} {i}位: {pred['pit_number']}号艇 "
                  f"({pred['win_probability']:.2f}%) "
                  f"[機材スコア: {pred['details']['total_equipment_score']:.3f}]")
        
        # 詳細分析
        print("\n🔍 機材詳細分析:")
        for pred in predictions:
            details = pred['details']
            print(f"  {pred['pit_number']}号艇:")
            print(f"    基本機材: {details['base_equipment_score']:.3f}")
            print(f"    相性スコア: {details['compatibility_score']:.3f}")
            print(f"    トレンド: {details['trend_score']:.3f}")
            print(f"    組み合わせ: {details['combination_bonus']:.3f}")
            print(f"    適応性: {details['racer_adaptability']:.3f}")
            print(f"    総合機材: {details['total_equipment_score']:.3f}")
            print()
        
        print(f"📈 上位10位合計確率: {sum(p['win_probability'] for p in predictions[:10]):.2f}%")
        print()
        
    except Exception as e:
        print(f"❌ エラー: {e}")
        print()

def test_equipment_compatibility_analysis():
    """機材相性分析の詳細テスト"""
    print("\n🔗 機材相性分析テスト")
    print("=" * 40)
    
    # テストデータ読み込み
    race_file = 'race_data_2025-06-30_KIRYU_R1.json'
    raw_data = load_race_data(race_file)
    
    if not raw_data:
        print("❌ テストデータ読み込み失敗")
        return
    
    race_data = convert_to_prediction_format(raw_data)
    engine = PredictionEngine()
    
    # 機材相性マトリックスの計算
    compatibility_scores = engine._calculate_equipment_compatibility(race_data['race_entries'])
    trend_scores = engine._analyze_equipment_trends(race_data['race_entries'])
    
    print("📊 機材相性スコア:")
    for pit_number in sorted(compatibility_scores.keys()):
        entry = next(e for e in race_data['race_entries'] if e['pit_number'] == pit_number)
        performance = entry['performance']
        boat_rate = performance.get('boat_quinella_rate', 0) / 100
        motor_rate = performance.get('motor_quinella_rate', 0) / 100
        
        print(f"  {pit_number}号艇:")
        print(f"    ボート2連率: {boat_rate:.3f}")
        print(f"    モーター2連率: {motor_rate:.3f}")
        print(f"    相性スコア: {compatibility_scores[pit_number]:.3f}")
        print(f"    トレンド: {trend_scores[pit_number]:.3f}")
        print()

def test_combination_effects():
    """機材組み合わせ効果のテスト"""
    print("\n⚡ 機材組み合わせ効果テスト")
    print("=" * 40)
    
    engine = PredictionEngine()
    
    # 様々な組み合わせパターンをテスト
    test_cases = [
        (0.08, 0.08, "高-高"),
        (0.06, 0.06, "中-中"),
        (0.04, 0.04, "低-低"),
        (0.08, 0.02, "高-低"),
        (0.02, 0.08, "低-高"),
        (0.01, 0.01, "極低-極低")
    ]
    
    print("📊 組み合わせ効果:")
    for boat_rate, motor_rate, description in test_cases:
        bonus = engine._calculate_combination_bonus(boat_rate, motor_rate)
        print(f"  {description} (ボート:{boat_rate:.3f}, モーター:{motor_rate:.3f})")
        print(f"    ボーナス: {bonus:.3f}")
        print()

def test_racer_adaptability():
    """選手適応性のテスト"""
    print("\n👤 選手適応性テスト")
    print("=" * 40)
    
    engine = PredictionEngine()
    
    # 様々な選手パターンをテスト
    test_cases = [
        (0.06, 0.06, "A1", "安定-高級"),
        (0.06, 0.04, "A1", "不安定-高級"),
        (0.04, 0.04, "B1", "安定-中級"),
        (0.04, 0.02, "B1", "不安定-中級"),
        (0.02, 0.02, "B2", "安定-低級"),
        (0.02, 0.01, "B2", "不安定-低級")
    ]
    
    print("📊 選手適応性:")
    for all_rate, local_rate, rating, description in test_cases:
        adaptability = engine._calculate_racer_adaptability(all_rate, local_rate, rating)
        print(f"  {description} (全国:{all_rate:.3f}, 当地:{local_rate:.3f}, 級別:{rating})")
        print(f"    適応性: {adaptability:.3f}")
        print()

def compare_algorithms():
    """新旧アルゴリズムの比較"""
    print("\n🔄 新旧アルゴリズム比較")
    print("=" * 40)
    
    # テストデータ読み込み
    race_file = 'race_data_2025-06-30_KIRYU_R1.json'
    raw_data = load_race_data(race_file)
    
    if not raw_data:
        print("❌ テストデータ読み込み失敗")
        return
    
    race_data = convert_to_prediction_format(raw_data)
    engine = PredictionEngine()
    
    # 実際の結果
    actual_result = "2-1-4"
    
    # 各アルゴリズムで予測
    algorithms = ['basic', 'equipment_focused', 'comprehensive']
    
    for algorithm in algorithms:
        print(f"\n📊 {algorithm.upper()} アルゴリズム")
        print("-" * 30)
        
        try:
            result = engine.predict(race_data, algorithm=algorithm)
            predictions = result['predictions']
            predictions.sort(key=lambda x: x['prediction_score'], reverse=True)
            
            # 実際の結果の順位を検索
            actual_rank = None
            for i, pred in enumerate(predictions, 1):
                if pred['pit_number'] == 2:  # 実際の1着艇
                    actual_rank = i
                    break
            
            if actual_rank:
                print(f"🏆 実際結果: {actual_rank}位")
            else:
                print(f"🏆 実際結果: 圏外")
            
            # 上位3位表示
            print("🥇 上位3位:")
            for i, pred in enumerate(predictions[:3], 1):
                print(f"  {i}位: {pred['pit_number']}号艇 ({pred['win_probability']:.2f}%)")
            
        except Exception as e:
            print(f"❌ エラー: {e}")

def main():
    """メイン実行"""
    test_equipment_focused_enhanced()
    test_equipment_compatibility_analysis()
    test_combination_effects()
    test_racer_adaptability()
    compare_algorithms()
    print("\n✅ 強化版機材重視アルゴリズムテスト完了")

if __name__ == "__main__":
    main() 