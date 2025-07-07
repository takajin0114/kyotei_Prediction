#!/usr/bin/env python3
"""
全24会場のバッチデータ取得スクリプト
高速化版：並列処理・キャッシュ機能付き
"""
import os
import sys
import json
import time
from datetime import date, timedelta, datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests
from io import StringIO
from metaboatrace.models.stadium import StadiumTelCode
from kyotei_predictor.tools.fetch.race_data_fetcher import fetch_complete_race_data
from kyotei_predictor.tools.fetch.odds_fetcher import fetch_trifecta_odds
from metaboatrace.scrapers.official.website.v1707.pages.monthly_schedule_page.location import create_monthly_schedule_page_url
from metaboatrace.scrapers.official.website.v1707.pages.monthly_schedule_page.scraping import extract_events

def get_event_days_for_stadium(stadium: StadiumTelCode, start_date: date, end_date: date):
    """1会場の開催日を取得（高速化版）"""
    event_days = []
    
    # 月ごとに処理
    current_date = start_date.replace(day=1)
    while current_date <= end_date:
        url = create_monthly_schedule_page_url(current_date.year, current_date.month)
        
        try:
            # レート制限短縮
            time.sleep(0.5)  # 1秒 → 0.5秒に短縮
            
            response = requests.get(url)
            response.raise_for_status()
            
            html_file = StringIO(response.text)
            events = extract_events(html_file)
            
            # 指定期間内の開催日のみ抽出
            for event in events:
                if event.stadium_tel_code == stadium:
                    for d in range(event.days):
                        day = event.starts_on + timedelta(days=d)
                        if start_date <= day <= end_date:
                            event_days.append(day)
                    
        except Exception as e:
            print(f"❌ {stadium.name} {current_date.year}-{current_date.month} 取得エラー: {e}")
        
        # 次の月へ
        if current_date.month == 12:
            current_date = current_date.replace(year=current_date.year + 1, month=1)
        else:
            current_date = current_date.replace(month=current_date.month + 1)
    
    return stadium, sorted(event_days)

def get_all_event_days_parallel(stadiums, start_date: date, end_date: date, max_workers: int = 8):
    """全会場の開催日を並列取得（高速化版）"""
    print(f"=== 全{len(stadiums)}会場 並列開催日取得開始 ===")
    print(f"並列度: {max_workers}")
    
    all_event_days = {}
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # 全タスクを並列実行
        future_to_stadium = {
            executor.submit(get_event_days_for_stadium, stadium, start_date, end_date): stadium 
            for stadium in stadiums
        }
        
        # 完了したタスクから結果を取得
        for future in as_completed(future_to_stadium):
            stadium, event_days = future.result()
            all_event_days[stadium] = event_days
            print(f"✅ {stadium.name}: {len(event_days)}日分の開催日")
    
    return all_event_days

def get_all_stadiums():
    """全24会場のリストを取得"""
    return list(StadiumTelCode)

def main():
    start_time = datetime.now()
    print(f"バッチ処理開始: {start_time}")
    # 設定
    end_date = date.today()
    start_date = end_date - timedelta(days=30)  # 直近30日
    race_numbers = range(1, 13)
    stadiums = get_all_stadiums()
    
    # 高速化設定
    RATE_LIMIT_SECONDS = 1  # 2秒 → 1秒に短縮
    FETCH_FUTURE_ENTRIES_ONLY = False  # 過去データ取得のためFalse
    MAX_RETRIES = 3  # エラー時のリトライ回数
    PARALLEL_WORKERS = 8  # 並列処理数
    
    print(f"全24会場バッチフェッチ開始")
    print(f"期間: {start_date} 〜 {end_date}")
    print(f"対象会場数: {len(stadiums)}")
    print(f"レート制限: {RATE_LIMIT_SECONDS}秒")
    print(f"未来日出走表のみ: {FETCH_FUTURE_ENTRIES_ONLY}")
    print(f"並列処理数: {PARALLEL_WORKERS}")
    
    # 開催日リスト取得（並列処理）
    all_event_days = get_all_event_days_parallel(stadiums, start_date, end_date, PARALLEL_WORKERS)
    
    # 統計情報
    total_days = sum(len(days) for days in all_event_days.values())
    print(f"\n📊 開催日統計:")
    print(f"総開催日数: {total_days}日")
    print(f"平均開催日数: {total_days/len(stadiums):.1f}日/会場")
    
    # データ取得処理
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
            venue_day_start_time = datetime.now()
            print(f"\n  📅 {stadium.name} {ymd} の処理開始: {venue_day_start_time}")
            
            for race_no in race_numbers:
                # ファイル名生成
                race_fname = f"race_data_{ymd}_{stadium.name}_R{race_no}.json"
                odds_fname = f"odds_data_{ymd}_{stadium.name}_R{race_no}.json"
                race_fpath = os.path.join("kyotei_predictor", "data", "raw", race_fname)
                odds_fpath = os.path.join("kyotei_predictor", "data", "raw", odds_fname)
                
                print(f"    R{race_no}: ", end="")
                
                # race_data取得
                if not os.path.exists(race_fpath):
                    retry_count = 0
                    while retry_count < MAX_RETRIES:
                        try:
                            race_data = fetch_complete_race_data(day, stadium, race_no)
                            if race_data:
                                with open(race_fpath, 'w', encoding='utf-8') as f:
                                    json.dump(race_data, f, ensure_ascii=False, indent=2)
                                print(f"✅ race_data保存: {race_fname}")
                                success_races += 1
                                break
                            else:
                                print(f"❌ race_data取得失敗: {race_fname}")
                                retry_count += 1
                        except Exception as e:
                            print(f"❌ エラー: {e}")
                            retry_count += 1
                            if retry_count < MAX_RETRIES:
                                time.sleep(5)  # リトライ前の待機
                    
                    if retry_count >= MAX_RETRIES:
                        print(f"❌ race_data最終的に取得失敗: {race_fname}")
                    
                    total_races += 1
                    time.sleep(RATE_LIMIT_SECONDS)  # レート制限対策
                else:
                    print("既存ファイルあり - スキップ")
                
                # odds_data取得
                if not os.path.exists(odds_fpath) and not FETCH_FUTURE_ENTRIES_ONLY:
                    retry_count = 0
                    while retry_count < MAX_RETRIES:
                        try:
                            odds_data = fetch_trifecta_odds(day, stadium, race_no)
                            if odds_data:
                                with open(odds_fpath, 'w', encoding='utf-8') as f:
                                    json.dump(odds_data, f, ensure_ascii=False, indent=2)
                                print(f"✅ odds_data保存: {odds_fname}")
                                success_odds += 1
                                break
                            else:
                                print(f"❌ odds_data取得失敗: {odds_fname}")
                                retry_count += 1
                        except Exception as e:
                            print(f"❌ スクレイピングエラー: {e}")
                            retry_count += 1
                            if retry_count < MAX_RETRIES:
                                time.sleep(5)  # リトライ前の待機
                    
                    if retry_count >= MAX_RETRIES:
                        print(f"❌ odds_data最終的に取得失敗: {odds_fname}")
                    
                    total_odds += 1
                    time.sleep(RATE_LIMIT_SECONDS)  # レート制限対策
                elif FETCH_FUTURE_ENTRIES_ONLY:
                    print("未来日出走表のみ - オッズ取得スキップ")
                else:
                    print("既存ファイルあり - スキップ")
            
            venue_day_end_time = datetime.now()
            print(f"  📅 {stadium.name} {ymd} の処理終了: {venue_day_end_time} (所要時間: {venue_day_end_time - venue_day_start_time})")
    
    # 結果サマリー
    print(f"\n=== バッチフェッチ完了 ===")
    print(f"対象期間: {start_date} 〜 {end_date}")
    print(f"対象会場: {len(stadiums)}会場")
    print(f"総リクエスト数: レース{total_races}件, オッズ{total_odds}件")
    print(f"成功数: レース{success_races}件, オッズ{success_odds}件")
    print(f"成功率: レース{success_races/total_races*100:.1f}%, オッズ{success_odds/total_odds*100:.1f}%" if total_races > 0 and total_odds > 0 else "成功率: 計算不可")

    end_time = datetime.now()
    print(f"バッチ処理終了: {end_time}")
    print(f"所要時間: {end_time - start_time}")

if __name__ == "__main__":
    main() 