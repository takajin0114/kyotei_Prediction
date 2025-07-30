#!/usr/bin/env python3
"""
競艇オッズ情報取得ツール

metaboatrace.scrapers ライブラリを使用して
3連単オッズ情報を取得する
"""

from metaboatrace.scrapers.official.website.v1707.pages.race.odds.trifecta_page import location, scraping
from metaboatrace.models.stadium import StadiumTelCode

from datetime import date
import requests
import time
from io import StringIO
import json
import argparse
import sys
import os

def fetch_trifecta_odds(
    race_date: date,
    stadium_code: StadiumTelCode,
    race_number: int
) -> dict | None:
    """
    3連単オッズ情報を取得する関数
    
    Args:
        race_date (date): レース開催日
        stadium_code (StadiumTelCode): 競艇場コード
        race_number (int): レース番号
    
    Returns:
        dict: 取得したオッズデータ
    """
    print(f"🎰 3連単オッズ取得開始: {race_date} {stadium_code.name} 第{race_number}レース")
    
    # URLを生成
    url = location.create_odds_page_url(
        race_holding_date=race_date,
        stadium_tel_code=stadium_code,
        race_number=race_number
    )
    
    print(f"📡 URL: {url}")
    
    # レート制限
    time.sleep(5)
    
    try:
        # データ取得
        response = requests.get(url)
        response.raise_for_status()
        
        # スクレイピング実行
        html_file = StringIO(response.text)
        
        # オッズ情報抽出
        odds_data = scraping.extract_odds(html_file)
        
        print(f"✅ オッズデータ取得成功: {len(odds_data)}件")
        
        # データを辞書形式に変換
        formatted_odds = []
        for odds in odds_data:
            formatted_odds.append({
                'betting_numbers': odds.betting_numbers,
                'ratio': float(odds.ratio) if odds.ratio is not None else 0.0,
                'betting_method': str(odds.betting_method),
                'combination': f"{odds.betting_numbers[0]}-{odds.betting_numbers[1]}-{odds.betting_numbers[2]}"
            })
        
        # データ構造を確認
        if formatted_odds:
            sample_odds = formatted_odds[0]
            print(f"📊 サンプルオッズ: {sample_odds['combination']} → {sample_odds['ratio']}倍")
        
        return {
            'race_date': race_date.isoformat(),
            'stadium': stadium_code.name,
            'race_number': race_number,
            'odds_count': len(formatted_odds),
            'odds_data': formatted_odds,
            'url': url
        }
        
    except requests.exceptions.RequestException as e:
        print(f"❌ リクエストエラー: {e}")
        return None
    except Exception as e:
        print(f"❌ スクレイピングエラー: {e}")
        return None

def fetch_odds_for_race(
    race_date_str: str,
    stadium_name: str,
    race_number: int
) -> dict | None:
    """
    指定されたレースのオッズを取得
    """
    try:
        # 日付の解析
        year, month, day = map(int, race_date_str.split('-'))
        race_date = date(year, month, day)
        
        # スタジアムコードの取得
        stadium_map = {
            'KIRYU': StadiumTelCode.KIRYU,
            'TODA': StadiumTelCode.TODA,
            'EDOGAWA': StadiumTelCode.EDOGAWA
        }
        
        if stadium_name not in stadium_map:
            print(f"❌ 未対応のスタジアム: {stadium_name}")
            return None
        
        stadium_code = stadium_map[stadium_name]
        
        print(f"\n🏁 {stadium_name}競艇場 第{race_number}レース")
        print("-" * 40)
        
        odds_data = fetch_trifecta_odds(race_date, stadium_code, race_number)
        
        if odds_data:
            # ファイル保存
            filename = f"odds_data_{race_date_str}_{stadium_name}_R{race_number}.json"
            filepath = os.path.join("kyotei_predictor", "data", "raw", filename)
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(odds_data, f, ensure_ascii=False, indent=2, default=str)
            print(f"💾 ファイル保存: {filename}")
            
            # オッズ分析
            analyze_odds_data(odds_data)
            return odds_data
        else:
            print("❌ オッズデータ取得失敗")
            return None
            
    except Exception as e:
        print(f"❌ エラー: {e}")
        return None

def test_odds_fetching() -> None:
    """
    オッズ取得のテスト実行
    """
    print("🎰 競艇オッズ取得テスト")
    print("=" * 50)
    
    # テスト設定
    test_configs = [
        {
            'date': '2024-06-15',
            'stadium': 'KIRYU',
            'race_number': 1,
            'description': '桐生競艇場 第1レース (過去データ)'
        }
    ]
    
    for config in test_configs:
        fetch_odds_for_race(
            config['date'],
            config['stadium'],
            config['race_number']
        )

def analyze_odds_data(odds_data: dict) -> None:
    """
    オッズデータの分析
    """
    print(f"\n📊 オッズデータ分析:")
    print(f"   取得件数: {odds_data['odds_count']}件")
    
    if odds_data['odds_data']:
        odds_list = odds_data['odds_data']
        
        # オッズ範囲分析
        odds_values = [odds['ratio'] for odds in odds_list]
        
        if odds_values:
            print(f"   オッズ範囲: {min(odds_values):.1f} - {max(odds_values):.1f}")
            print(f"   平均オッズ: {sum(odds_values)/len(odds_values):.1f}")
            
            # 人気順表示（上位5位）
            sorted_odds = sorted(odds_list, key=lambda x: x['ratio'])
            print(f"   人気順 (上位5位):")
            for i, odds in enumerate(sorted_odds[:5], 1):
                print(f"     {i}位: {odds['combination']} → {odds['ratio']}倍")

def main() -> None:
    """
    メイン実行関数
    """
    parser = argparse.ArgumentParser(description='競艇オッズ取得ツール')
    parser.add_argument('--date', type=str, help='レース日 (YYYY-MM-DD)')
    parser.add_argument('--stadium', type=str, help='スタジアム名 (KIRYU, TODA, EDOGAWA等)')
    parser.add_argument('--race', type=int, help='レース番号')
    
    args = parser.parse_args()
    
    if args.date and args.stadium and args.race:
        # コマンドライン引数で指定された場合
        fetch_odds_for_race(args.date, args.stadium, args.race)
    else:
        # デフォルトのテスト実行
        test_odds_fetching()

if __name__ == "__main__":
    main()