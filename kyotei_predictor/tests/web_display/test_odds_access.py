"""
オッズデータアクセスのテスト
"""
import requests
import json

def test_odds_data_access():
    """オッズデータへのアクセステスト"""
    print("=== オッズデータアクセステスト開始 ===")
    
    base_url = "http://localhost:51932"
    
    # 1. 予測データの確認
    try:
        response = requests.get(f"{base_url}/outputs/predictions_latest.json")
        if response.status_code == 200:
            predictions = response.json()
            print("✓ 予測データにアクセス成功")
            
            # 最初のレース情報を取得
            if 'predictions' in predictions and len(predictions['predictions']) > 0:
                first_race = predictions['predictions'][0]
                venue = first_race['venue']
                race_number = first_race['race_number']
                prediction_date = predictions['prediction_date']
                
                print(f"  会場: {venue}")
                print(f"  レース番号: {race_number}")
                print(f"  予測日: {prediction_date}")
                
                # 2. オッズデータへのアクセステスト
                odds_filename = f"odds_data_{prediction_date}_{venue}_R{race_number}.json"
                odds_url = f"{base_url}/kyotei_predictor/data/raw/{odds_filename}"
                
                print(f"  オッズデータURL: {odds_url}")
                
                odds_response = requests.get(odds_url)
                if odds_response.status_code == 200:
                    odds_data = odds_response.json()
                    print("✓ オッズデータにアクセス成功")
                    
                    # オッズデータの内容確認
                    if 'odds_data' in odds_data:
                        print(f"  組み合わせ数: {len(odds_data['odds_data'])}")
                        
                        # 最初の組み合わせを表示
                        if len(odds_data['odds_data']) > 0:
                            first_combo = odds_data['odds_data'][0]
                            print(f"  最初の組み合わせ: {first_combo.get('combination', 'N/A')}")
                            print(f"  オッズ: {first_combo.get('ratio', 'N/A')}")
                    elif 'combinations' in odds_data:
                        print(f"  組み合わせ数: {len(odds_data['combinations'])}")
                        
                        # 最初の組み合わせを表示
                        if len(odds_data['combinations']) > 0:
                            first_combo = odds_data['combinations'][0]
                            print(f"  最初の組み合わせ: {first_combo.get('combination', 'N/A')}")
                            print(f"  オッズ: {first_combo.get('odds', 'N/A')}")
                    else:
                        print("⚠ オッズデータにodds_dataまたはcombinationsが含まれていません")
                        
                else:
                    print(f"✗ オッズデータにアクセス失敗: {odds_response.status_code}")
                    print(f"  レスポンス: {odds_response.text[:200]}")
                    
            else:
                print("⚠ 予測データにレース情報が含まれていません")
                
        else:
            print(f"✗ 予測データにアクセス失敗: {response.status_code}")
            
    except Exception as e:
        print(f"✗ テストでエラーが発生: {e}")
        return False
    
    print("=== オッズデータアクセステスト完了 ===")
    return True

if __name__ == "__main__":
    success = test_odds_data_access()
    if success:
        print("✓ テストが成功しました")
    else:
        print("✗ テストが失敗しました") 