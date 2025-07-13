#!/usr/bin/env python3
"""
シンプルなレース予測テスト

複数のレースデータで予測アルゴリズムの基本動作を確認
"""

import json
import os
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from kyotei_predictor.data_integration import DataIntegration
from kyotei_predictor.prediction_engine import PredictionEngine
# from kyotei_predictor.race_data_fetcher import load_race_data

def load_and_test_race(filename, description):
    """
    レースファイルを読み込んで予測テスト
    """
    print(f"\n🏁 {description}")
    print("=" * 50)
    
    # ファイル読み込み
    filepath = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', filename)
    if not os.path.exists(filepath):
        print(f"❌ ファイルが見つかりません: {filename}")
        return
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            race_data = json.load(f)
    except Exception as e:
        print(f"❌ ファイル読み込みエラー: {e}")
        return
    
    # レース基本情報
    race_info = race_data.get('race_info', {})
    print(f"📅 日付: {race_info.get('date', 'N/A')}")
    print(f"🏟️ 競艇場: {race_info.get('stadium', 'N/A')}")
    print(f"🏁 レース: {race_info.get('title', 'N/A')}")
    
    # 出走表
    entries = race_data.get('race_entries', [])
    print(f"🚤 出走艇数: {len(entries)}艇")
    
    # 実際の結果
    results = race_data.get('race_records', [])
    if results:
        print("🏆 実際の結果:")
        for record in sorted(results, key=lambda x: x.get('arrival', 999)):
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
    
    # データ変換
    converted_data = {
        'race_info': race_data.get('race_info', {}),
        'race_entries': race_data.get('race_entries', []),
        'weather_condition': race_data.get('weather_condition', {}),
        'race_records': race_data.get('race_records', []),
        'payoffs': race_data.get('payoffs', [])
    }
    
    # 予測実行
    engine = PredictionEngine()
    
    for algorithm in ['basic', 'rating_weighted']:
        print(f"\n📊 {algorithm}アルゴリズム予測:")
        
        try:
            result = engine.predict(converted_data, algorithm)
            predictions = result['predictions']
            
            print("   予測順位:")
            for i, pred in enumerate(predictions[:3], 1):
                print(f"   {i}位: {pred['pit_number']}号艇 {pred['racer_name']} "
                      f"({pred['rating']}級) スコア:{pred['prediction_score']:.3f} "
                      f"勝率:{pred['win_probability']}%")
            
            # 本命の的中確認
            if results:
                favorite_pit = predictions[0]['pit_number']
                winner_pit = None
                for record in results:
                    if record.get('arrival') == 1:
                        winner_pit = record.get('pit_number')
                        break
                
                if winner_pit:
                    if favorite_pit == winner_pit:
                        print(f"   🎯 本命的中！ {favorite_pit}号艇が1着")
                    else:
                        print(f"   ❌ 本命外れ: 予測{favorite_pit}号艇 → 実際{winner_pit}号艇が1着")
                        
                        # 実際の勝者の予測順位を確認
                        winner_pred_rank = None
                        for pred in predictions:
                            if pred['pit_number'] == winner_pit:
                                winner_pred_rank = pred['rank']
                                break
                        
                        if winner_pred_rank:
                            print(f"   📊 実際の勝者は予測{winner_pred_rank}位でした")
            
        except Exception as e:
            print(f"   ❌ 予測エラー: {str(e)}")

def main():
    """
    メイン実行
    """
    print("🔮 シンプルレース予測テスト")
    print("=" * 50)
    
    # テスト対象ファイル
    test_files = [
        ('complete_race_data_20240615_KIRYU_R1.json', '桐生競艇場 第1レース'),
        ('race_data_2024-06-15_KIRYU_R2.json', '桐生競艇場 第2レース'),
        ('race_data_2024-06-15_TODA_R1.json', '戸田競艇場 第1レース')
    ]
    
    for filename, description in test_files:
        load_and_test_race(filename, description)
    
    print("\n✅ テスト完了")

if __name__ == "__main__":
    main()