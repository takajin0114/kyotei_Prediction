#!/usr/bin/env python3
"""
競艇データ取得テスト - metaboatrace.scrapers ライブラリ使用
Phase 1 Week 1 の成果物
"""

from metaboatrace.scrapers.official.website.v1707.pages.race.result_page import location, scraping
from metaboatrace.models.stadium import StadiumTelCode
from datetime import date
import requests
import time
from io import StringIO
import json

def fetch_race_data(race_date, stadium_code, race_number):
    """
    1レース分のデータを取得する関数
    
    Args:
        race_date (date): レース開催日
        stadium_code (StadiumTelCode): 競艇場コード
        race_number (int): レース番号
    
    Returns:
        dict: 取得したレースデータ
    """
    print(f"データ取得開始: {race_date} {stadium_code.name} 第{race_number}レース")
    
    # URLを生成
    url = location.create_race_result_page_url(
        race_holding_date=race_date,
        stadium_tel_code=stadium_code,
        race_number=race_number
    )
    
    print(f"URL: {url}")
    
    # レート制限
    time.sleep(5)
    
    try:
        # データ取得
        response = requests.get(url)
        response.raise_for_status()
        
        # スクレイピング実行
        html_file = StringIO(response.text)
        
        race_records = scraping.extract_race_records(html_file)
        html_file.seek(0)
        weather_condition = scraping.extract_weather_condition(html_file)
        html_file.seek(0)
        payoffs = scraping.extract_race_payoffs(html_file)
        
        # データを辞書形式に変換
        result = {
            "race_info": {
                "date": race_date.isoformat(),
                "stadium": stadium_code.name,
                "race_number": race_number,
                "url": url
            },
            "race_records": [
                {
                    "pit_number": record.pit_number,
                    "start_course": record.start_course,
                    "start_time": record.start_time,
                    "total_time": record.total_time,
                    "arrival": record.arrival,
                    "winning_trick": record.winning_trick.name if record.winning_trick else None
                }
                for record in race_records
            ],
            "weather_condition": {
                "weather": weather_condition.weather.name,
                "wind_velocity": weather_condition.wind_velocity,
                "wind_angle": weather_condition.wind_angle,
                "air_temperature": weather_condition.air_temperature,
                "water_temperature": weather_condition.water_temperature,
                "wavelength": weather_condition.wavelength
            },
            "payoffs": [
                {
                    "betting_method": payoff.betting_method.name,
                    "betting_numbers": payoff.betting_numbers,
                    "amount": payoff.amount
                }
                for payoff in payoffs
            ]
        }
        
        print(f"✅ データ取得成功: {len(race_records)}艇, 払戻{len(payoffs)}件")
        return result
        
    except Exception as e:
        print(f"❌ エラー: {e}")
        return None

def main():
    """メイン実行関数"""
    print("🏁 競艇データ取得テスト")
    print("=" * 50)
    
    # テスト条件
    test_date = date(2024, 6, 15)
    stadium = StadiumTelCode.KIRYU
    race_num = 1
    
    # データ取得
    race_data = fetch_race_data(test_date, stadium, race_num)
    
    if race_data:
        # 結果表示
        print(f"\n📊 取得結果:")
        print(f"  日付: {race_data['race_info']['date']}")
        print(f"  競艇場: {race_data['race_info']['stadium']}")
        print(f"  レース番号: {race_data['race_info']['race_number']}")
        
        print(f"\n🏁 レース結果:")
        for i, record in enumerate(race_data['race_records']):
            print(f"  {record['arrival']}着: {record['pit_number']}号艇 (ST:{record['start_time']})")
        
        print(f"\n🌤️ 天候:")
        weather = race_data['weather_condition']
        print(f"  {weather['weather']}, 風速{weather['wind_velocity']}m/s, 気温{weather['air_temperature']}℃")
        
        print(f"\n💰 払戻:")
        for payoff in race_data['payoffs']:
            method_name = {
                'TRIFECTA': '3連単',
                'TRIO': '3連複',
                'EXACTA': '2連単',
                'QUINELLA': '2連複'
            }.get(payoff['betting_method'], payoff['betting_method'])
            numbers = '-'.join(map(str, payoff['betting_numbers']))
            print(f"  {method_name} {numbers}: {payoff['amount']:,}円")
        
        # JSONファイルに保存
        output_file = f"race_data_{test_date.strftime('%Y%m%d')}_{stadium.name}_R{race_num}.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(race_data, f, ensure_ascii=False, indent=2)
        
        print(f"\n💾 データを保存しました: {output_file}")
        print("\n✅ テスト完了！metaboatrace.scrapers ライブラリが正常に動作しています。")
    
    else:
        print("\n❌ データ取得に失敗しました。")

if __name__ == "__main__":
    main()