#!/usr/bin/env python3
"""
複数レースでの予測アルゴリズム検証

取得した複数のレースデータを使用して、
予測アルゴリズムの汎用性と精度を検証する。
"""

import json
import os
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from kyotei_predictor.data_integration import DataIntegration
from kyotei_predictor.prediction_engine import PredictionEngine
# from kyotei_predictor.race_data_fetcher import load_race_data, convert_to_integration_format, analyze_prediction_accuracy, test_race_prediction, main


def load_race_data(filename):
    """
    レースデータファイルを読み込み
    """
    filepath = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', filename)
    if not os.path.exists(filepath):
        print(f"❌ ファイルが見つかりません: {filename}")
        return None
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"❌ ファイル読み込みエラー: {e}")
        return None

def convert_to_integration_format(race_data):
    """
    レースデータをDataIntegration形式に変換
    """
    if not race_data:
        return None
    
    # DataIntegrationが期待する形式に変換
    converted_data = {
        'race_info': race_data.get('race_info', {}),
        'race_entries': race_data.get('race_entries', []),
        'weather_condition': race_data.get('weather_condition', {}),
        'race_records': race_data.get('race_records', []),
        'payoffs': race_data.get('payoffs', [])
    }
    
    return converted_data

def analyze_prediction_accuracy(predictions, actual_results):
    """
    予測精度の分析
    """
    if not actual_results:
        return {
            'status': 'no_results',
            'message': 'レース結果がないため精度分析不可'
        }
    
    # 実際の着順を取得
    actual_order = {}
    for record in actual_results:
        pit_number = record.get('pit_number')
        arrival = record.get('arrival')
        if pit_number and arrival:
            actual_order[pit_number] = arrival
    
    # 予測順位と実際の着順を比較
    accuracy_data = {
        'predictions': [],
        'exact_matches': 0,
        'top3_accuracy': 0,
        'correlation_score': 0
    }
    
    for pred in predictions:
        pit_number = pred['pit_number']
        predicted_rank = pred['rank']  # 'predicted_rank' -> 'rank'
        actual_rank = actual_order.get(pit_number, None)
        
        pred_analysis = {
            'pit_number': pit_number,
            'racer_name': pred['racer_name'],
            'rating': pred['rating'],
            'predicted_rank': predicted_rank,
            'actual_rank': actual_rank,
            'rank_diff': abs(predicted_rank - actual_rank) if actual_rank else None,
            'is_exact_match': predicted_rank == actual_rank if actual_rank else False,
            'is_top3_correct': (predicted_rank <= 3 and actual_rank <= 3) if actual_rank else False
        }
        
        accuracy_data['predictions'].append(pred_analysis)
        
        if pred_analysis['is_exact_match']:
            accuracy_data['exact_matches'] += 1
        if pred_analysis['is_top3_correct']:
            accuracy_data['top3_accuracy'] += 1
    
    # 精度計算
    total_boats = len(predictions)
    accuracy_data['exact_match_rate'] = accuracy_data['exact_matches'] / total_boats * 100
    accuracy_data['top3_accuracy_rate'] = accuracy_data['top3_accuracy'] / min(3, total_boats) * 100
    
    return accuracy_data

def _run_race_prediction(filename, description):
    """
    単一レースの予測実行（main から呼ぶヘルパー。pytest では収集しない）
    """
    print(f"\n🏁 {description}")
    print("=" * 60)
    
    # データ読み込み
    race_data = load_race_data(filename)
    if not race_data:
        return None
    
    # データ変換
    converted_data = convert_to_integration_format(race_data)
    
    # 予測エンジン初期化
    engine = PredictionEngine()
    
    # レース基本情報表示
    race_info = race_data.get('race_info', {})
    print(f"📅 日付: {race_info.get('date', 'N/A')}")
    print(f"🏟️ 競艇場: {race_info.get('stadium', 'N/A')}")
    print(f"🏁 レース: {race_info.get('title', 'N/A')}")
    
    # 天候情報表示
    weather = race_data.get('weather_condition', {})
    print(f"🌤️ 天候: {weather.get('weather', 'N/A')}")
    print(f"💨 風速: {weather.get('wind_velocity', 'N/A')}m/s")
    
    # 出走表情報
    entries = race_data.get('race_entries', [])
    print(f"🚤 出走艇数: {len(entries)}艇")
    
    # 級別分布
    rating_count = {}
    for entry in entries:
        rating = entry.get('racer', {}).get('current_rating', 'Unknown')
        rating_count[rating] = rating_count.get(rating, 0) + 1
    
    print("🏆 級別分布:", end=" ")
    for rating in ['A1', 'A2', 'B1', 'B2']:
        count = rating_count.get(rating, 0)
        if count > 0:
            print(f"{rating}:{count}名", end=" ")
    print()
    
    # 実際の結果表示
    actual_results = race_data.get('race_records', [])
    if actual_results:
        print("\n🏆 実際の結果:")
        for record in sorted(actual_results, key=lambda x: x.get('arrival', 999)):
            pit_num = record.get('pit_number')
            arrival = record.get('arrival')
            
            # 選手名を取得
            racer_name = 'Unknown'
            racer_rating = 'Unknown'
            for entry in entries:
                if entry.get('pit_number') == pit_num:
                    racer_name = entry.get('racer', {}).get('name', 'Unknown')
                    racer_rating = entry.get('racer', {}).get('current_rating', 'Unknown')
                    break
            
            print(f"   {arrival}着: {pit_num}号艇 {racer_name} ({racer_rating}級)")
    
    # 予測実行
    print("\n🔮 予測実行:")
    
    results = {}
    for algorithm in ['basic', 'rating_weighted']:
        print(f"\n📊 {algorithm}アルゴリズム:")
        
        try:
            prediction_result = engine.predict(converted_data, algorithm)
            predictions = prediction_result['predictions']
            
            # 予測結果表示
            print("   予測順位:")
            for pred in predictions[:3]:  # 上位3位まで表示
                print(f"   {pred['rank']}位: {pred['pit_number']}号艇 {pred['racer_name']} "
                      f"({pred['rating']}級) スコア:{pred['prediction_score']:.3f} "
                      f"勝率:{pred['win_probability']}%")
            
            # 精度分析
            accuracy = analyze_prediction_accuracy(predictions, actual_results)
            if accuracy['status'] != 'no_results':
                print(f"   📈 精度分析:")
                print(f"      完全一致: {accuracy['exact_matches']}/{len(predictions)}艇 "
                      f"({accuracy['exact_match_rate']:.1f}%)")
                print(f"      3連対的中: {accuracy['top3_accuracy']}/3艇 "
                      f"({accuracy['top3_accuracy_rate']:.1f}%)")
                
                # 本命の的中状況
                favorite = predictions[0]
                fav_actual = None
                for record in actual_results:
                    if record.get('pit_number') == favorite['pit_number']:
                        fav_actual = record.get('arrival')
                        break
                
                if fav_actual:
                    if fav_actual == 1:
                        print(f"      🎯 本命的中: {favorite['pit_number']}号艇が1着")
                    else:
                        print(f"      ❌ 本命外れ: {favorite['pit_number']}号艇は{fav_actual}着")
            
            results[algorithm] = {
                'prediction_result': prediction_result,
                'accuracy': accuracy
            }
            
        except Exception as e:
            print(f"   ❌ 予測エラー: {str(e)}")
            results[algorithm] = None
    
    return results

def main():
    """
    メイン実行関数
    """
    print("🔮 複数レース予測アルゴリズム検証")
    print("=" * 60)
    
    # テスト対象のレースファイル
    test_races = [
        {
            'filename': 'complete_race_data_20240615_KIRYU_R1.json',
            'description': '桐生競艇場 第1レース (既存データ)'
        },
        {
            'filename': 'race_data_2024-06-15_KIRYU_R2.json',
            'description': '桐生競艇場 第2レース (新規取得)'
        },
        {
            'filename': 'race_data_2024-06-15_TODA_R1.json',
            'description': '戸田競艇場 第1レース (新規取得)'
        }
    ]
    
    all_results = {}
    
    # 各レースでテスト実行
    for race in test_races:
        results = _run_race_prediction(race['filename'], race['description'])
        if results:
            all_results[race['description']] = results
    
    # 総合分析
    print("\n" + "=" * 60)
    print("📊 総合分析結果")
    print("=" * 60)
    
    if all_results:
        total_races = len(all_results)
        algorithm_stats = {'basic': [], 'rating_weighted': []}
        
        for race_desc, race_results in all_results.items():
            print(f"\n🏁 {race_desc}:")
            
            for algorithm in ['basic', 'rating_weighted']:
                if race_results.get(algorithm):
                    accuracy = race_results[algorithm]['accuracy']
                    if accuracy.get('status') != 'no_results':
                        exact_rate = accuracy['exact_match_rate']
                        top3_rate = accuracy['top3_accuracy_rate']
                        print(f"   {algorithm}: 完全一致{exact_rate:.1f}% 3連対{top3_rate:.1f}%")
                        
                        algorithm_stats[algorithm].append({
                            'exact_match_rate': exact_rate,
                            'top3_accuracy_rate': top3_rate
                        })
        
        # アルゴリズム別平均精度
        print(f"\n📈 アルゴリズム別平均精度 (対象レース数: {total_races}):")
        for algorithm, stats in algorithm_stats.items():
            if stats:
                avg_exact = sum(s['exact_match_rate'] for s in stats) / len(stats)
                avg_top3 = sum(s['top3_accuracy_rate'] for s in stats) / len(stats)
                print(f"   {algorithm}: 完全一致{avg_exact:.1f}% 3連対{avg_top3:.1f}%")
    
    print("\n✅ 検証完了")

if __name__ == "__main__":
    main()