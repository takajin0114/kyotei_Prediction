#!/usr/bin/env python3
"""
競艇データ取得ツール - レース前情報 + レース結果
metaboatrace.scrapers ライブラリ使用
"""

from metaboatrace.scrapers.official.website.v1707.pages.race.entry_page import location as entry_location, scraping as entry_scraping
from metaboatrace.scrapers.official.website.v1707.pages.race.result_page import location as result_location, scraping as result_scraping
from metaboatrace.models.stadium import StadiumTelCode
from datetime import date
import requests
import time
from io import StringIO
import json

def fetch_race_entry_data(race_date, stadium_code, race_number):
    """
    レース前情報（出走表）を取得する関数
    
    Args:
        race_date (date): レース開催日
        stadium_code (StadiumTelCode): 競艇場コード
        race_number (int): レース番号
    
    Returns:
        dict: 取得した出走表データ
    """
    print(f"出走表データ取得開始: {race_date} {stadium_code.name} 第{race_number}レース")
    
    # URLを生成
    url = entry_location.create_race_entry_page_url(
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
        
        race_information = entry_scraping.extract_race_information(html_file)
        html_file.seek(0)
        race_entries = entry_scraping.extract_race_entries(html_file)
        html_file.seek(0)
        racers = entry_scraping.extract_racers(html_file)
        html_file.seek(0)
        racer_performances = entry_scraping.extract_racer_performances(html_file)
        html_file.seek(0)
        boat_performances = entry_scraping.extract_boat_performances(html_file)
        html_file.seek(0)
        motor_performances = entry_scraping.extract_motor_performances(html_file)
        
        # データを辞書形式に変換
        result = {
            "race_info": {
                "date": race_date.isoformat(),
                "stadium": stadium_code.name,
                "race_number": race_number,
                "url": url,
                "title": race_information.title,
                "deadline_at": race_information.deadline_at.isoformat() if race_information.deadline_at else None,
                "number_of_laps": race_information.number_of_laps,
                "is_course_fixed": race_information.is_course_fixed
            },
            "race_entries": [
                {
                    "pit_number": entry.pit_number,
                    "racer": {
                        "name": f"{racer.last_name} {racer.first_name}",
                        "registration_number": racer.registration_number,
                        "current_rating": racer.current_rating.name if racer.current_rating else None,
                        "branch": racer.branch,
                        "born_prefecture": racer.born_prefecture,
                        "birth_date": racer.birth_date.isoformat() if racer.birth_date else None,
                        "height": racer.height,
                        "gender": racer.gender.name if racer.gender else None
                    },
                    "performance": {
                        "rate_in_all_stadium": racer_perf.rate_in_all_stadium,
                        "rate_in_event_going_stadium": racer_perf.rate_in_event_going_stadium
                    },
                    "boat": {
                        "number": boat_perf.number,
                        "quinella_rate": boat_perf.quinella_rate,
                        "trio_rate": boat_perf.trio_rate
                    },
                    "motor": {
                        "number": motor_perf.number,
                        "quinella_rate": motor_perf.quinella_rate,
                        "trio_rate": motor_perf.trio_rate
                    }
                }
                for entry, racer, racer_perf, boat_perf, motor_perf in 
                zip(race_entries, racers, racer_performances, boat_performances, motor_performances)
            ]
        }
        
        print(f"✅ 出走表データ取得成功: {len(race_entries)}艇")
        return result
        
    except Exception as e:
        print(f"❌ エラー: {e}")
        return None

def fetch_race_result_data(race_date, stadium_code, race_number):
    """
    レース結果を取得する関数
    
    Args:
        race_date (date): レース開催日
        stadium_code (StadiumTelCode): 競艇場コード
        race_number (int): レース番号
    
    Returns:
        dict: 取得したレース結果データ
    """
    print(f"レース結果データ取得開始: {race_date} {stadium_code.name} 第{race_number}レース")
    
    # URLを生成
    url = result_location.create_race_result_page_url(
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
        
        race_records = result_scraping.extract_race_records(html_file)
        html_file.seek(0)
        weather_condition = result_scraping.extract_weather_condition(html_file)
        html_file.seek(0)
        payoffs = result_scraping.extract_race_payoffs(html_file)
        
        # データを辞書形式に変換
        result = {
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
        
        print(f"✅ レース結果データ取得成功: {len(race_records)}艇, 払戻{len(payoffs)}件")
        return result
        
    except Exception as e:
        print(f"❌ エラー: {e}")
        return None

def fetch_complete_race_data(race_date, stadium_code, race_number):
    """
    1レースの完全なデータ（出走表 + 結果）を取得する関数
    
    Args:
        race_date (date): レース開催日
        stadium_code (StadiumTelCode): 競艇場コード
        race_number (int): レース番号
    
    Returns:
        dict: 完全なレースデータ
    """
    print(f"🏁 完全レースデータ取得: {race_date} {stadium_code.name} 第{race_number}レース")
    print("=" * 60)
    
    # 出走表データ取得
    entry_data = fetch_race_entry_data(race_date, stadium_code, race_number)
    if not entry_data:
        return None
    
    # レース結果データ取得
    result_data = fetch_race_result_data(race_date, stadium_code, race_number)
    if not result_data:
        return None
    
    # データを統合
    complete_data = {
        **entry_data,
        **result_data
    }
    
    return complete_data

def main():
    """メイン実行関数"""
    print("🏁 競艇完全データ取得テスト")
    print("=" * 50)
    
    # テスト条件
    test_date = date(2024, 6, 15)
    stadium = StadiumTelCode.KIRYU
    race_num = 1
    
    # 完全データ取得
    complete_data = fetch_complete_race_data(test_date, stadium, race_num)
    
    if complete_data:
        # 結果表示
        print(f"\n📊 取得結果サマリー:")
        print(f"  日付: {complete_data['race_info']['date']}")
        print(f"  競艇場: {complete_data['race_info']['stadium']}")
        print(f"  レース: {complete_data['race_info']['title']}")
        print(f"  締切時刻: {complete_data['race_info']['deadline_at']}")
        
        print(f"\n🚤 出走表:")
        for entry in complete_data['race_entries']:
            print(f"  {entry['pit_number']}号艇: {entry['racer']['name']} ({entry['racer']['current_rating']})")
            print(f"    全国勝率: {entry['performance']['rate_in_all_stadium']}")
        
        print(f"\n🏁 レース結果:")
        sorted_records = sorted(complete_data['race_records'], key=lambda x: x['arrival'])
        for record in sorted_records:
            print(f"  {record['arrival']}着: {record['pit_number']}号艇 (ST:{record['start_time']})")
        
        print(f"\n🌤️ 天候:")
        weather = complete_data['weather_condition']
        print(f"  {weather['weather']}, 風速{weather['wind_velocity']}m/s, 気温{weather['air_temperature']}℃")
        
        print(f"\n💰 払戻:")
        for payoff in complete_data['payoffs']:
            method_name = {
                'TRIFECTA': '3連単',
                'TRIO': '3連複',
                'EXACTA': '2連単',
                'QUINELLA': '2連複'
            }.get(payoff['betting_method'], payoff['betting_method'])
            numbers = '-'.join(map(str, payoff['betting_numbers']))
            print(f"  {method_name} {numbers}: {payoff['amount']:,}円")
        
        # JSONファイルに保存
        output_file = f"complete_race_data_{test_date.strftime('%Y%m%d')}_{stadium.name}_R{race_num}.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(complete_data, f, ensure_ascii=False, indent=2)
        
        print(f"\n💾 完全データを保存しました: {output_file}")
        print("\n✅ 出走表 + レース結果の完全データ取得に成功しました！")
    
    else:
        print("\n❌ データ取得に失敗しました。")

if __name__ == "__main__":
    main()