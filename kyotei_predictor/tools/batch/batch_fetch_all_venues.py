#!/usr/bin/env python3
"""
全24会場・直近1年分の開催日リストを取得し、
実在する日・場のみrace_data/odds_dataを取得するバッチスクリプト
"""
import os
import sys
import json
import time
from datetime import date, timedelta
import requests
from io import StringIO
from metaboatrace.models.stadium import StadiumTelCode
from kyotei_predictor.tools.race_data_fetcher import fetch_complete_race_data
from kyotei_predictor.tools.odds_fetcher import fetch_trifecta_odds
from metaboatrace.scrapers.official.website.v1707.pages.monthly_schedule_page.location import create_monthly_schedule_page_url
from metaboatrace.scrapers.official.website.v1707.pages.monthly_schedule_page.scraping import extract_events

def get_event_days_for_stadium(stadium: StadiumTelCode, start_date: date, end_date: date):
    """
    指定期間・場の開催日リストを返す
    """
    event_days = set()
    current = date(start_date.year, start_date.month, 1)
    while current <= end_date:
        url = create_monthly_schedule_page_url(current.year, current.month)
        try:
            resp = requests.get(url)
            resp.raise_for_status()
            events = extract_events(StringIO(resp.text))
            for event in events:
                if event.stadium_tel_code == stadium:
                    for d in range(event.days):
                        day = event.starts_on + timedelta(days=d)
                        if start_date <= day <= end_date:
                            event_days.add(day)
        except Exception as e:
            print(f"[WARN] {stadium.name} {current.year}-{current.month:02d} 開催日取得失敗: {e}")
        current = (current.replace(day=1) + timedelta(days=32)).replace(day=1)
    return sorted(event_days)

def get_all_stadiums():
    """
    全24会場のStadiumTelCodeを返す
    """
    return [
        StadiumTelCode.KIRYU,      # 01: 桐生
        StadiumTelCode.TODA,       # 02: 戸田
        StadiumTelCode.EDOGAWA,    # 03: 江戸川
        StadiumTelCode.HEIWAJIMA,  # 04: 平和島
        StadiumTelCode.TAMAGAWA,   # 05: 多摩川
        StadiumTelCode.HAMANAKO,   # 06: 浜名湖
        StadiumTelCode.GAMAGORI,   # 07: 蒲郡
        StadiumTelCode.TOKONAME,   # 08: 常滑
        StadiumTelCode.TSU,        # 09: 津
        StadiumTelCode.MIKUNI,     # 10: 三国
        StadiumTelCode.BIWAKO,     # 11: びわこ
        StadiumTelCode.SUMINOE,    # 12: 住之江
        StadiumTelCode.AMAGASAKI,  # 13: 尼崎
        StadiumTelCode.NARUTO,     # 14: 鳴門
        StadiumTelCode.MARUGAME,   # 15: 丸亀
        StadiumTelCode.KOJIMA,     # 16: 児島
        StadiumTelCode.MIYAJIMA,   # 17: 宮島
        StadiumTelCode.TOKUYAMA,   # 18: 徳山
        StadiumTelCode.SHIMONOSEKI, # 19: 下関
        StadiumTelCode.WAKAMATSU,  # 20: 若松
        StadiumTelCode.ASHIYA,     # 21: 芦屋
        StadiumTelCode.FUKUOKA,    # 22: 福岡
        StadiumTelCode.KARATSU,    # 23: 唐津
        StadiumTelCode.OMURA,      # 24: 大村
    ]

def main():
    # 設定
    end_date = date.today()
    start_date = end_date - timedelta(days=30)  # 直近30日
    race_numbers = range(1, 13)
    stadiums = get_all_stadiums()
    
    print(f"全24会場バッチフェッチ開始")
    print(f"期間: {start_date} 〜 {end_date}")
    print(f"対象会場数: {len(stadiums)}")
    
    data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')
    os.makedirs(data_dir, exist_ok=True)

    # 各会場の開催日を取得
    all_event_days = {}
    for stadium in stadiums:
        print(f"\n=== {stadium.name} 開催日リスト取得 ===")
        event_days = get_event_days_for_stadium(stadium, start_date, end_date)
        all_event_days[stadium] = event_days
        print(f"{stadium.name}: {len(event_days)}日分の開催日")
        if event_days:
            print(f"  開催日: {[day.strftime('%Y-%m-%d') for day in event_days]}")
        time.sleep(1)  # レート制限対策

    # データ取得
    total_races = 0
    total_odds = 0
    success_races = 0
    success_odds = 0
    
    for stadium in stadiums:
        event_days = all_event_days[stadium]
        if not event_days:
            print(f"\n{stadium.name}: 開催日なし - スキップ")
            continue
            
        print(f"\n=== {stadium.name} データ取得開始 ===")
        
        for day in event_days:
            ymd = day.strftime('%Y-%m-%d')
            print(f"\n  📅 {ymd}")
            
            for race_no in race_numbers:
                race_fname = f"race_data_{ymd}_{stadium.name}_R{race_no}.json"
                odds_fname = f"odds_data_{ymd}_{stadium.name}_R{race_no}.json"
                race_fpath = os.path.join(data_dir, race_fname)
                odds_fpath = os.path.join(data_dir, odds_fname)
                
                # 既存ファイルチェック
                if os.path.exists(race_fpath) and os.path.exists(odds_fpath):
                    print(f"    R{race_no}: 既存ファイルあり - スキップ")
                    continue
                
                print(f"    R{race_no}: データ取得中...")
                
                # race_data取得
                if not os.path.exists(race_fpath):
                    try:
                        race_data = fetch_complete_race_data(day, stadium, race_no)
                        if race_data:
                            with open(race_fpath, 'w', encoding='utf-8') as f:
                                json.dump(race_data, f, ensure_ascii=False, indent=2)
                            print(f"      ✅ race_data保存: {race_fname}")
                            success_races += 1
                        else:
                            print(f"      ❌ race_data取得失敗: {race_fname}")
                    except Exception as e:
                        print(f"      ❌ race_data取得エラー: {type(e).__name__}: {e}")
                    total_races += 1
                    time.sleep(2)  # レート制限対策
                
                # odds_data取得
                if not os.path.exists(odds_fpath):
                    try:
                        odds_data = fetch_trifecta_odds(day, stadium, race_no)
                        if odds_data:
                            with open(odds_fpath, 'w', encoding='utf-8') as f:
                                json.dump(odds_data, f, ensure_ascii=False, indent=2)
                            print(f"      ✅ odds_data保存: {odds_fname}")
                            success_odds += 1
                        else:
                            print(f"      ❌ odds_data取得失敗: {odds_fname}")
                    except Exception as e:
                        print(f"      ❌ odds_data取得エラー: {type(e).__name__}: {e}")
                    total_odds += 1
                    time.sleep(2)  # レート制限対策

    # 結果サマリー
    print(f"\n=== バッチフェッチ完了 ===")
    print(f"対象期間: {start_date} 〜 {end_date}")
    print(f"対象会場: {len(stadiums)}会場")
    print(f"総リクエスト数: レース{total_races}件, オッズ{total_odds}件")
    print(f"成功数: レース{success_races}件, オッズ{success_odds}件")
    print(f"成功率: レース{success_races/total_races*100:.1f}%, オッズ{success_odds/total_odds*100:.1f}%" if total_races > 0 and total_odds > 0 else "成功率: 計算不可")

if __name__ == "__main__":
    main() 