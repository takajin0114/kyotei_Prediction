#!/usr/bin/env python3
"""
全24会場のバッチデータ取得スクリプト（完全並列版）
レース情報取得も並列化して大幅高速化
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

def fetch_race_data_parallel(day, stadium, race_no, rate_limit_seconds=1, max_retries=3):
    """1レースのデータを取得（並列用）"""
    ymd = day.strftime('%Y-%m-%d')
    race_fname = f"race_data_{ymd}_{stadium.name}_R{race_no}.json"
    odds_fname = f"odds_data_{ymd}_{stadium.name}_R{race_no}.json"
    canceled_fname = f"race_canceled_{ymd}_{stadium.name}_R{race_no}.json"
    race_fpath = os.path.join("kyotei_predictor", "data", "raw", race_fname)
    odds_fpath = os.path.join("kyotei_predictor", "data", "raw", odds_fname)
    canceled_fpath = os.path.join("kyotei_predictor", "data", "raw", canceled_fname)
    
    result = {
        'stadium': stadium.name,
        'day': ymd,
        'race_no': race_no,
        'race_success': False,
        'odds_success': False,
        'race_file': race_fname,
        'odds_file': odds_fname,
        'race_error': None,
        'odds_error': None,
        'canceled': False
    }
    
    # レース中止ファイルのチェック
    if os.path.exists(canceled_fpath):
        result['canceled'] = True
        result['race_success'] = True  # 中止として成功扱い
        result['odds_success'] = True  # 中止として成功扱い
        print(f"    ⏭️  R{race_no}: レース中止済み - スキップ")
        return result
    
    # race_data取得
    if not os.path.exists(race_fpath):
        retry_count = 0
        while retry_count < max_retries:
            try:
                race_data = fetch_complete_race_data(day, stadium, race_no)
                if race_data:
                    with open(race_fpath, 'w', encoding='utf-8') as f:
                        json.dump(race_data, f, ensure_ascii=False, indent=2)
                    result['race_success'] = True
                    break
                else:
                    retry_count += 1
                    if retry_count < max_retries:
                        print(f"    ⚠️  R{race_no}: レースデータ取得失敗（リトライ {retry_count}/{max_retries}）")
            except ValueError as e:
                # 選手名解析エラーの場合は特別処理
                if "not enough values to unpack" in str(e):
                    result['race_error'] = f"選手名解析エラー: {e}"
                    print(f"    ⚠️  R{race_no}: 選手名解析エラー - スキップ")
                    break
                else:
                    retry_count += 1
                    result['race_error'] = str(e)
                    if retry_count < max_retries:
                        print(f"    ⚠️  R{race_no}: ValueError - リトライ {retry_count}/{max_retries}")
                        time.sleep(5)
            except Exception as e:
                # レース中止の場合は特別処理
                if "RaceCanceled" in str(type(e)):
                    # レース中止ファイルを作成
                    canceled_data = {
                        "status": "canceled",
                        "race_info": {
                            "date": ymd,
                            "stadium": stadium.name,
                            "race_number": race_no,
                            "title": f"{stadium.name} 第{race_no}レース"
                        },
                        "canceled_at": datetime.now().isoformat(),
                        "reason": "レース中止"
                    }
                    with open(canceled_fpath, 'w', encoding='utf-8') as f:
                        json.dump(canceled_data, f, ensure_ascii=False, indent=2)
                    result['canceled'] = True
                    result['race_success'] = True  # 中止として成功扱い
                    result['odds_success'] = True  # 中止として成功扱い
                    print(f"    ⏭️  R{race_no}: レース中止 - 専用ファイル作成")
                    break
                # データ未公開の場合は特別処理
                elif "DataNotFound" in str(type(e)):
                    # データ未公開は一時的なエラーとして扱い、リトライを継続
                    retry_count += 1
                    result['race_error'] = f"データ未公開: {e}"
                    if retry_count < max_retries:
                        print(f"    ⚠️  R{race_no}: データ未公開 - リトライ {retry_count}/{max_retries}")
                        time.sleep(5)
                    else:
                        print(f"    ⏭️  R{race_no}: データ未公開 - 次回実行時に再試行")
                    continue
                else:
                    retry_count += 1
                    result['race_error'] = str(e)
                    if retry_count < max_retries:
                        print(f"    ⚠️  R{race_no}: {type(e).__name__} - リトライ {retry_count}/{max_retries}")
                        time.sleep(5)
        
        if not result['race_success'] and not result['canceled']:
            print(f"    ❌ R{race_no}: レースデータ取得失敗（{result['race_error']}）")
        
        time.sleep(rate_limit_seconds)  # レート制限対策
    else:
        result['race_success'] = True  # 既存ファイルあり
    
    # odds_data取得（レース中止でない場合のみ）
    if not result['canceled'] and not os.path.exists(odds_fpath):
        retry_count = 0
        while retry_count < max_retries:
            try:
                odds_data = fetch_trifecta_odds(day, stadium, race_no)
                if odds_data:
                    with open(odds_fpath, 'w', encoding='utf-8') as f:
                        json.dump(odds_data, f, ensure_ascii=False, indent=2)
                    result['odds_success'] = True
                    break
                else:
                    retry_count += 1
                    if retry_count < max_retries:
                        print(f"    ⚠️  R{race_no}: オッズデータ取得失敗（リトライ {retry_count}/{max_retries}）")
            except Exception as e:
                # レース中止の場合は特別処理
                if "RaceCanceled" in str(type(e)):
                    # レース中止ファイルを作成（まだ作成されていない場合）
                    if not result['canceled']:
                        canceled_data = {
                            "status": "canceled",
                            "race_info": {
                                "date": ymd,
                                "stadium": stadium.name,
                                "race_number": race_no,
                                "title": f"{stadium.name} 第{race_no}レース"
                            },
                            "canceled_at": datetime.now().isoformat(),
                            "reason": "レース中止（オッズ取得時）"
                        }
                        with open(canceled_fpath, 'w', encoding='utf-8') as f:
                            json.dump(canceled_data, f, ensure_ascii=False, indent=2)
                        result['canceled'] = True
                        result['race_success'] = True  # 中止として成功扱い
                        result['odds_success'] = True  # 中止として成功扱い
                        print(f"    ⏭️  R{race_no}: レース中止（オッズ取得時） - 専用ファイル作成")
                        break
                # データ未公開の場合は特別処理
                elif "DataNotFound" in str(type(e)):
                    # データ未公開は一時的なエラーとして扱い、リトライを継続
                    retry_count += 1
                    result['odds_error'] = f"データ未公開: {e}"
                    if retry_count < max_retries:
                        print(f"    ⚠️  R{race_no}: データ未公開（オッズ取得時） - リトライ {retry_count}/{max_retries}")
                        time.sleep(5)
                    else:
                        print(f"    ⏭️  R{race_no}: データ未公開（オッズ取得時） - 次回実行時に再試行")
                    continue
                else:
                    retry_count += 1
                    result['odds_error'] = str(e)
                    if retry_count < max_retries:
                        print(f"    ⚠️  R{race_no}: オッズ取得エラー - リトライ {retry_count}/{max_retries}")
                        time.sleep(5)
        
        if not result['odds_success'] and not result['canceled']:
            print(f"    ❌ R{race_no}: オッズデータ取得失敗（{result['odds_error']}）")
        
        time.sleep(rate_limit_seconds)  # レート制限対策
    elif result['canceled']:
        result['odds_success'] = True  # 中止として成功扱い
    else:
        result['odds_success'] = True  # 既存ファイルあり
    
    return result

def fetch_day_races_parallel(day, stadium, race_numbers, rate_limit_seconds=1, max_retries=3, max_workers=6):
    """1日分の全レースを並列取得"""
    ymd = day.strftime('%Y-%m-%d')
    print(f"\n  📅 {stadium.name} {ymd} の並列処理開始: {datetime.now()}")
    
    results = []
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # 12レースを並列実行
        future_to_race = {
            executor.submit(fetch_race_data_parallel, day, stadium, race_no, rate_limit_seconds, max_retries): race_no
            for race_no in race_numbers
        }
        
        # 完了したタスクから結果を取得
        for future in as_completed(future_to_race):
            result = future.result()
            results.append(result)
            
            # 進捗表示
            if result['canceled']:
                print(f"    R{result['race_no']}: ⏭️ レース中止")
            else:
                race_status = "✅" if result['race_success'] else "❌"
                odds_status = "✅" if result['odds_success'] else "❌"
                print(f"    R{result['race_no']}: {race_status}race {odds_status}odds")
    
    # 統計
    race_success = sum(1 for r in results if r['race_success'])
    odds_success = sum(1 for r in results if r['odds_success'])
    canceled_count = sum(1 for r in results if r['canceled'])
    
    print(f"  📅 {stadium.name} {ymd} の並列処理終了: {datetime.now()}")
    if canceled_count > 0:
        print(f"    結果: レース{race_success}/12, オッズ{odds_success}/12, 中止{canceled_count}件")
    else:
        print(f"    結果: レース{race_success}/12, オッズ{odds_success}/12")
    
    return results

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
    RATE_LIMIT_SECONDS = 1  # レート制限
    MAX_RETRIES = 3  # エラー時のリトライ回数
    SCHEDULE_WORKERS = 8  # 開催日取得の並列数
    RACE_WORKERS = 6  # レース取得の並列数（1日12レースを6並列）
    
    print(f"全24会場バッチフェッチ開始（完全並列版）")
    print(f"期間: {start_date} 〜 {end_date}")
    print(f"対象会場数: {len(stadiums)}")
    print(f"レート制限: {RATE_LIMIT_SECONDS}秒")
    print(f"開催日取得並列数: {SCHEDULE_WORKERS}")
    print(f"レース取得並列数: {RACE_WORKERS}")
    
    # 開催日リスト取得（並列処理）
    all_event_days = get_all_event_days_parallel(stadiums, start_date, end_date, SCHEDULE_WORKERS)
    
    # 統計情報
    total_days = sum(len(days) for days in all_event_days.values())
    print(f"\n📊 開催日統計:")
    print(f"総開催日数: {total_days}日")
    print(f"平均開催日数: {total_days/len(stadiums):.1f}日/会場")
    
    # データ取得処理（並列版）
    total_races = 0
    total_odds = 0
    success_races = 0
    success_odds = 0
    
    for stadium in stadiums:
        event_days = all_event_days[stadium]
        if not event_days:
            print(f"\n{stadium.name}: 開催日なし - スキップ")
            continue
            
        print(f"\n=== {stadium.name} 並列データ取得開始 ===")
        
        for day in event_days:
            # 1日分の全レースを並列取得
            day_results = fetch_day_races_parallel(
                day, stadium, race_numbers, 
                RATE_LIMIT_SECONDS, MAX_RETRIES, RACE_WORKERS
            )
            
            # 統計更新
            for result in day_results:
                total_races += 1
                total_odds += 1
                if result['race_success']:
                    success_races += 1
                if result['odds_success']:
                    success_odds += 1
    
    # 結果サマリー
    print(f"\n=== バッチフェッチ完了（完全並列版） ===")
    print(f"対象期間: {start_date} 〜 {end_date}")
    print(f"対象会場: {len(stadiums)}会場")
    print(f"総リクエスト数: レース{total_races}件, オッズ{total_odds}件")
    print(f"成功数: レース{success_races}件, オッズ{success_odds}件")
    if total_races > 0 and total_odds > 0:
        print(f"成功率: レース{success_races/total_races*100:.1f}%, オッズ{success_odds/total_odds*100:.1f}%")
        print(f"失敗数: レース{total_races-success_races}件, オッズ{total_odds-success_odds}件")
    else:
        print("成功率: 計算不可")
    
    # エラー統計
    print(f"\n📊 エラーハンドリング改善:")
    print(f"  - 選手名解析エラー: 自動スキップ処理")
    print(f"  - レース中止: 自動検出・スキップ")
    print(f"  - ネットワークエラー: 最大{MAX_RETRIES}回リトライ")
    print(f"  - レート制限: {RATE_LIMIT_SECONDS}秒間隔")

    end_time = datetime.now()
    print(f"バッチ処理終了: {end_time}")
    print(f"所要時間: {end_time - start_time}")

if __name__ == "__main__":
    main() 