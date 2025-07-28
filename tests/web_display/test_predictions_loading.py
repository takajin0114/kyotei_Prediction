#!/usr/bin/env python3
"""
予測データ読み込みとオッズ情報表示のテスト
"""

import requests
import json
import time
from pathlib import Path

def test_predictions_endpoint():
    """予測データエンドポイントのテスト"""
    print("=== 予測データエンドポイントテスト ===")
    
    try:
        # 予測データの取得
        response = requests.get('http://localhost:5000/outputs/predictions_latest.json', timeout=10)
        print(f"予測データ取得: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"予測日: {data.get('prediction_date')}")
            print(f"会場数: {data.get('execution_summary', {}).get('total_venues')}")
            print(f"レース数: {data.get('execution_summary', {}).get('total_races')}")
            print("✅ 予測データ取得成功")
            return data
        else:
            print(f"❌ 予測データ取得失敗: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"❌ 予測データ取得エラー: {e}")
        return None

def test_odds_endpoint():
    """オッズデータエンドポイントのテスト"""
    print("\n=== オッズデータエンドポイントテスト ===")
    
    try:
        # KARATSU R1のオッズデータをテスト
        url = 'http://localhost:5000/kyotei_predictor/data/raw/odds_data_2025-07-18_KARATSU_R1.json'
        response = requests.get(url, timeout=10)
        print(f"オッズデータ取得 (R1): {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"オッズデータ形式: {type(data)}")
            if 'odds_data' in data:
                print(f"オッズデータ件数: {len(data['odds_data'])}")
                if data['odds_data']:
                    print(f"サンプルオッズ: {data['odds_data'][0]}")
            print("✅ オッズデータ取得成功")
            return True
        else:
            print(f"❌ オッズデータ取得失敗: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ オッズデータ取得エラー: {e}")
        return False

def test_predictions_page():
    """予測ページのテスト"""
    print("\n=== 予測ページテスト ===")
    
    try:
        # 予測ページの取得
        response = requests.get('http://localhost:5000/predictions', timeout=10)
        print(f"予測ページ取得: {response.status_code}")
        
        if response.status_code == 200:
            content = response.text
            if 'predictions.js' in content:
                print("✅ 予測ページ読み込み成功")
                return True
            else:
                print("❌ JavaScriptファイルが見つかりません")
                return False
        else:
            print(f"❌ 予測ページ取得失敗: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ 予測ページ取得エラー: {e}")
        return False

def test_js_file():
    """JavaScriptファイルのテスト"""
    print("\n=== JavaScriptファイルテスト ===")
    
    try:
        # JavaScriptファイルの取得
        response = requests.get('http://localhost:5000/static/js/predictions.js?v=20250718_25', timeout=10)
        print(f"JavaScriptファイル取得: {response.status_code}")
        
        if response.status_code == 200:
            content = response.text
            if 'class PredictionsViewer' in content:
                print("✅ JavaScriptファイル読み込み成功")
                return True
            else:
                print("❌ PredictionsViewerクラスが見つかりません")
                return False
        else:
            print(f"❌ JavaScriptファイル取得失敗: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ JavaScriptファイル取得エラー: {e}")
        return False

def check_data_files():
    """データファイルの存在確認"""
    print("\n=== データファイル確認 ===")
    
    # 予測ファイルの確認
    predictions_file = Path('outputs/predictions_latest.json')
    if predictions_file.exists():
        print(f"✅ 予測ファイル存在: {predictions_file}")
        try:
            with open(predictions_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                print(f"   予測日: {data.get('prediction_date')}")
                print(f"   レース数: {data.get('execution_summary', {}).get('total_races')}")
        except Exception as e:
            print(f"❌ 予測ファイル読み込みエラー: {e}")
    else:
        print(f"❌ 予測ファイル不存在: {predictions_file}")
    
    # オッズファイルの確認
    odds_dir = Path('kyotei_predictor/data/raw')
    if odds_dir.exists():
        odds_files = list(odds_dir.glob('odds_data_2025-07-18_KARATSU_*.json'))
        print(f"✅ オッズファイル数: {len(odds_files)}")
        for file in odds_files[:3]:  # 最初の3ファイルのみ表示
            print(f"   {file.name}")
    else:
        print(f"❌ オッズディレクトリ不存在: {odds_dir}")

def main():
    """メイン関数"""
    print("予測データ読み込みとオッズ情報表示のテスト開始")
    print("=" * 50)
    
    # データファイル確認
    check_data_files()
    
    # エンドポイントテスト
    predictions_data = test_predictions_endpoint()
    odds_success = test_odds_endpoint()
    page_success = test_predictions_page()
    js_success = test_js_file()
    
    # 結果サマリー
    print("\n" + "=" * 50)
    print("テスト結果サマリー:")
    print(f"予測データ: {'✅' if predictions_data else '❌'}")
    print(f"オッズデータ: {'✅' if odds_success else '❌'}")
    print(f"予測ページ: {'✅' if page_success else '❌'}")
    print(f"JavaScript: {'✅' if js_success else '❌'}")
    
    if all([predictions_data, odds_success, page_success, js_success]):
        print("\n🎉 すべてのテストが成功しました！")
        print("ブラウザで http://localhost:5000/predictions にアクセスしてください。")
    else:
        print("\n⚠️  一部のテストが失敗しました。")
        print("ブラウザの開発者ツールでエラーを確認してください。")

if __name__ == "__main__":
    main() 