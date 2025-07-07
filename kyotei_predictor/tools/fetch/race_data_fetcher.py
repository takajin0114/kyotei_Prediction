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
import re
from typing import List, Optional, Any, Union
import os

def safe_extract_racers(html_file) -> List[Any]:
    """
    選手データを安全に抽出する関数（エラーハンドリング付き）
    
    Args:
        html_file: HTMLファイルオブジェクト
    
    Returns:
        list: 選手データのリスト（エラーが発生した場合は空のリスト）
    """
    try:
        return entry_scraping.extract_racers(html_file)
    except ValueError as e:
        if "not enough values to unpack" in str(e):
            print(f"⚠️  選手名解析エラー: 名前の形式が予期しない形式です - {e}")
            print("⚠️  選手データの取得をスキップします")
            return []
        else:
            raise e
    except Exception as e:
        print(f"⚠️  選手データ抽出エラー: {e}")
        return []

def safe_extract_race_entries(html_file) -> List[Any]:
    """
    レース出走データを安全に抽出する関数（エラーハンドリング付き）
    
    Args:
        html_file: HTMLファイルオブジェクト
    
    Returns:
        list: レース出走データのリスト（エラーが発生した場合は空のリスト）
    """
    try:
        return entry_scraping.extract_race_entries(html_file)
    except Exception as e:
        print(f"⚠️  レース出走データ抽出エラー: {e}")
        return []

def safe_extract_racer_performances(html_file) -> List[Any]:
    """
    選手成績データを安全に抽出する関数（エラーハンドリング付き）
    
    Args:
        html_file: HTMLファイルオブジェクト
    
    Returns:
        list: 選手成績データのリスト（エラーが発生した場合は空のリスト）
    """
    try:
        return entry_scraping.extract_racer_performances(html_file)
    except Exception as e:
        print(f"⚠️  選手成績データ抽出エラー: {e}")
        return []

def safe_extract_boat_performances(html_file) -> List[Any]:
    """
    ボート成績データを安全に抽出する関数（エラーハンドリング付き）
    
    Args:
        html_file: HTMLファイルオブジェクト
    
    Returns:
        list: ボート成績データのリスト（エラーが発生した場合は空のリスト）
    """
    try:
        return entry_scraping.extract_boat_performances(html_file)
    except Exception as e:
        print(f"⚠️  ボート成績データ抽出エラー: {e}")
        return []

def safe_extract_motor_performances(html_file) -> List[Any]:
    """
    モーター成績データを安全に抽出する関数（エラーハンドリング付き）
    
    Args:
        html_file: HTMLファイルオブジェクト
    
    Returns:
        list: モーター成績データのリスト（エラーが発生した場合は空のリスト）
    """
    try:
        return entry_scraping.extract_motor_performances(html_file)
    except Exception as e:
        print(f"⚠️  モーター成績データ抽出エラー: {e}")
        return []

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
        
        # 安全なデータ抽出
        race_entries = safe_extract_race_entries(html_file)
        html_file.seek(0)
        racers = safe_extract_racers(html_file)
        html_file.seek(0)
        racer_performances = safe_extract_racer_performances(html_file)
        html_file.seek(0)
        boat_performances = safe_extract_boat_performances(html_file)
        html_file.seek(0)
        motor_performances = safe_extract_motor_performances(html_file)
        
        # データの整合性チェック
        if not race_entries:
            print("❌ レース出走データが取得できませんでした")
            return None
        
        # 各データの長さを揃える（不足している場合は空のデータで補完）
        max_length = len(race_entries)
        
        if len(racers) < max_length:
            print(f"⚠️  選手データが不足しています（{len(racers)}/{max_length}）")
            racers.extend([None] * (max_length - len(racers)))
        
        if len(racer_performances) < max_length:
            print(f"⚠️  選手成績データが不足しています（{len(racer_performances)}/{max_length}）")
            racer_performances.extend([None] * (max_length - len(racer_performances)))
        
        if len(boat_performances) < max_length:
            print(f"⚠️  ボート成績データが不足しています（{len(boat_performances)}/{max_length}）")
            boat_performances.extend([None] * (max_length - len(boat_performances)))
        
        if len(motor_performances) < max_length:
            print(f"⚠️  モーター成績データが不足しています（{len(motor_performances)}/{max_length}）")
            motor_performances.extend([None] * (max_length - len(motor_performances)))
        
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
            "race_entries": []
        }
        
        # 各艇のデータを安全に処理
        for i, entry in enumerate(race_entries):
            racer = racers[i] if i < len(racers) else None
            racer_perf = racer_performances[i] if i < len(racer_performances) else None
            boat_perf = boat_performances[i] if i < len(boat_performances) else None
            motor_perf = motor_performances[i] if i < len(motor_performances) else None
            
            entry_data = {
                "pit_number": entry.pit_number,
                "racer": {
                    "name": f"{racer.last_name} {racer.first_name}" if racer else "不明",
                    "registration_number": racer.registration_number if racer else None,
                    "current_rating": racer.current_rating.name if racer and racer.current_rating else None,
                    "branch": racer.branch if racer else None,
                    "born_prefecture": racer.born_prefecture if racer else None,
                    "birth_date": racer.birth_date.isoformat() if racer and racer.birth_date else None,
                    "height": racer.height if racer else None,
                    "gender": racer.gender.name if racer and racer.gender else None
                },
                "performance": {
                    "rate_in_all_stadium": racer_perf.rate_in_all_stadium if racer_perf else None,
                    "rate_in_event_going_stadium": racer_perf.rate_in_event_going_stadium if racer_perf else None
                },
                "boat": {
                    "number": boat_perf.number if boat_perf else None,
                    "quinella_rate": boat_perf.quinella_rate if boat_perf else None,
                    "trio_rate": boat_perf.trio_rate if boat_perf else None
                },
                "motor": {
                    "number": motor_perf.number if motor_perf else None,
                    "quinella_rate": motor_perf.quinella_rate if motor_perf else None,
                    "trio_rate": motor_perf.trio_rate if motor_perf else None
                }
            }
            result["race_entries"].append(entry_data)
        
        print(f"✅ 出走表データ取得成功: {len(race_entries)}艇")
        return result
        
    except Exception as e:
        import traceback
        # レース中止の場合は特別処理
        if "RaceCanceled" in str(type(e)):
            print(f"❌ レース中止: {race_date} {stadium_code.name} 第{race_number}レース")
            return None
        print(f"❌ エラー: {type(e).__name__}: {e}")
        print(f"❌ 詳細: {traceback.format_exc()}")
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
        import traceback
        # レース中止の場合は特別処理
        if "RaceCanceled" in str(type(e)):
            print(f"❌ レース中止: {race_date} {stadium_code.name} 第{race_number}レース")
            return None
        print(f"❌ エラー: {type(e).__name__}: {e}")
        print(f"❌ 詳細: {traceback.format_exc()}")
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
        output_file = os.path.join("kyotei_predictor", "data", "raw", f"complete_race_data_{test_date.strftime('%Y%m%d')}_{stadium.name}_R{race_num}.json")
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(complete_data, f, ensure_ascii=False, indent=2)
        
        print(f"\n💾 完全データを保存しました: {output_file}")
        print("\n✅ 出走表 + レース結果の完全データ取得に成功しました！")
    
    else:
        print("\n❌ データ取得に失敗しました。")

if __name__ == "__main__":
    main()