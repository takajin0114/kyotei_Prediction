#!/usr/bin/env python3
"""
未来日の出走表のみを高速取得するスクリプト
予測用データ取得に特化
"""
import os
import sys
import json
import time
from datetime import date, timedelta, datetime
import requests
from io import StringIO
from metaboatrace.models.stadium import StadiumTelCode
from kyotei_predictor.tools.fetch.race_data_fetcher import fetch_race_entry_data
from metaboatrace.scrapers.official.website.v1707.pages.monthly_schedule_page.location import create_monthly_schedule_page_url
from metaboatrace.scrapers.official.website.v1707.pages.monthly_schedule_page.scraping import extract_events

def get_future_event_days(stadium: StadiumTelCode, days_ahead: int = 7):
    """未来N日間の開催日を取得"""
    future_days = []
    today = date.today()
    
    for i in range(1, days_ahead + 1):
        check_date = today + timedelta(days=i)
        url = create_monthly_schedule_page_url(check_date.year, check_date.month)
        try:
            resp = requests.get(url)
            resp.raise_for_status()
            events = extract_events(StringIO(resp.text))
            for event in events:
                if event.stadium_tel_code == stadium:
                    for d in range(event.days):
                        day = event.starts_on + timedelta(days=d)
                        if day == check_date:
                            future_days.append(day)
        except Exception as e:
            print(f"[WARN] {stadium.name} {check_date} 開催日確認失敗: {e}")
        time.sleep(0.5)  # 軽いレート制限
    
    return sorted(future_days)

def get_all_stadiums():
    """全24会場のStadiumTelCodeを返す"""
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
    start_time = datetime.now()
    print(f"🚀 未来日出走表高速取得開始: {start_time}")
    
    # 設定
    DAYS_AHEAD = 7  # 未来7日間
    RATE_LIMIT_SECONDS = 0.5  # 0.5秒間隔（高速化）
    stadiums = get_all_stadiums()
    
    print(f"対象期間: 今日から{DAYS_AHEAD}日間")
    print(f"対象会場数: {len(stadiums)}")
    print(f"レート制限: {RATE_LIMIT_SECONDS}秒")
    
    data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'future_entries')
    os.makedirs(data_dir, exist_ok=True)
    
    total_entries = 0
    success_entries = 0
    
    for stadium in stadiums:
        print(f"\n=== {stadium.name} 未来日取得開始 ===")
        
        future_days = get_future_event_days(stadium, DAYS_AHEAD)
        if not future_days:
            print(f"{stadium.name}: 未来の開催日なし - スキップ")
            continue
        
        print(f"{stadium.name}: {len(future_days)}日分の未来開催日")
        print(f"  開催日: {[day.strftime('%Y-%m-%d') for day in future_days]}")
        
        for day in future_days:
            ymd = day.strftime('%Y-%m-%d')
            venue_day_start_time = datetime.now()
            print(f"\n  📅 {stadium.name} {ymd} の処理開始: {venue_day_start_time}")
            
            for race_no in range(1, 13):  # 1R-12R
                entry_fname = f"future_entry_{ymd}_{stadium.name}_R{race_no}.json"
                entry_fpath = os.path.join(data_dir, entry_fname)
                
                # 既存ファイルチェック
                if os.path.exists(entry_fpath):
                    print(f"    R{race_no}: 既存ファイルあり - スキップ")
                    continue
                
                print(f"    R{race_no}: 出走表取得中...")
                
                try:
                    entry_data = fetch_race_entry_data(day, stadium, race_no)
                    if entry_data:
                        with open(entry_fpath, 'w', encoding='utf-8') as f:
                            json.dump(entry_data, f, ensure_ascii=False, indent=2)
                        print(f"      ✅ 出走表保存: {entry_fname}")
                        success_entries += 1
                    else:
                        print(f"      ❌ 出走表取得失敗: {entry_fname}")
                except Exception as e:
                    print(f"      ❌ 出走表取得エラー: {type(e).__name__}: {e}")
                
                total_entries += 1
                time.sleep(RATE_LIMIT_SECONDS)
            
            venue_day_end_time = datetime.now()
            print(f"  📅 {stadium.name} {ymd} の処理終了: {venue_day_end_time} (所要時間: {venue_day_end_time - venue_day_start_time})")
    
    # 結果サマリー
    end_time = datetime.now()
    print(f"\n=== 未来日出走表取得完了 ===")
    print(f"対象期間: 今日から{DAYS_AHEAD}日間")
    print(f"対象会場: {len(stadiums)}会場")
    print(f"総リクエスト数: {total_entries}件")
    print(f"成功数: {success_entries}件")
    print(f"成功率: {success_entries/total_entries*100:.1f}%" if total_entries > 0 else "成功率: 計算不可")
    print(f"バッチ処理開始: {start_time}")
    print(f"バッチ処理終了: {end_time}")
    print(f"所要時間: {end_time - start_time}")

if __name__ == "__main__":
    main() 