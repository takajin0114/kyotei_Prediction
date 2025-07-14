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
from metaboatrace.scrapers.official.website.exceptions import RaceCanceled, DataNotFound
from kyotei_predictor.tools.fetch.race_data_fetcher import fetch_complete_race_data
from kyotei_predictor.tools.fetch.odds_fetcher import fetch_trifecta_odds
from metaboatrace.scrapers.official.website.v1707.pages.monthly_schedule_page.location import create_monthly_schedule_page_url
from metaboatrace.scrapers.official.website.v1707.pages.monthly_schedule_page.scraping import extract_events
import argparse
import threading
import subprocess

# グローバル進捗カウンタ
progress_lock = threading.Lock()
progress_total = 0
progress_done = 0

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
            print(f"{stadium.name}: {len(event_days)}日分の開催日")
    
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
        print(f"    R{race_no}: レース中止済み - スキップ")
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
                        print(f"    R{race_no}: レースデータ取得失敗（リトライ {retry_count}/{max_retries}）")
            except ValueError as e:
                # 選手名解析エラーの場合は特別処理
                if "not enough values to unpack" in str(e):
                    result['race_error'] = f"選手名解析エラー: {e}"
                    print(f"    R{race_no}: 選手名解析エラー - スキップ")
                    break
                else:
                    retry_count += 1
                    result['race_error'] = str(e)
                    if retry_count < max_retries:
                        print(f"    R{race_no}: ValueError - リトライ {retry_count}/{max_retries}")
                        time.sleep(5)
            except RaceCanceled as e:
                # レース中止の場合は特別処理
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
                print(f"    R{race_no}: レース中止 - 専用ファイル作成、オッズ取得をスキップ")
                break
            except DataNotFound as e:
                # データ未公開の場合は特別処理
                retry_count += 1
                result['race_error'] = f"データ未公開: {e}"
                if retry_count < max_retries:
                    print(f"    R{race_no}: データ未公開 - リトライ {retry_count}/{max_retries}")
                    time.sleep(5)
                else:
                    print(f"    R{race_no}: データ未公開 - 次回実行時に再試行")
                continue
            except Exception as e:
                retry_count += 1
                result['race_error'] = str(e)
                if retry_count < max_retries:
                    print(f"    R{race_no}: {type(e).__name__} - リトライ {retry_count}/{max_retries}")
                    time.sleep(5)
        
        if not result['race_success'] and not result['canceled']:
            print(f"    R{race_no}: レースデータ取得失敗（{result['race_error']}）")
        
        time.sleep(rate_limit_seconds)  # レート制限対策
    else:
        result['race_success'] = True  # 既存ファイルあり
    
    # odds_data取得（レース中止でない場合のみ）
    if result['canceled']:
        # レース中止の場合はオッズ取得を完全にスキップ
        result['odds_success'] = True  # 中止として成功扱い
        print(f"    R{race_no}: レース中止のためオッズ取得をスキップ")
    elif not os.path.exists(odds_fpath):
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
                        print(f"    R{race_no}: オッズデータ取得失敗（リトライ {retry_count}/{max_retries}）")
            except RaceCanceled as e:
                # レース中止の場合は特別処理
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
                    print(f"    R{race_no}: レース中止（オッズ取得時） - 専用ファイル作成")
                    break
            except DataNotFound as e:
                # データ未公開の場合は特別処理
                retry_count += 1
                result['odds_error'] = f"データ未公開: {e}"
                if retry_count < max_retries:
                    print(f"    R{race_no}: データ未公開（オッズ取得時） - リトライ {retry_count}/{max_retries}")
                    time.sleep(5)
                else:
                    print(f"    R{race_no}: データ未公開（オッズ取得時） - 次回実行時に再試行")
                continue
            except Exception as e:
                retry_count += 1
                result['odds_error'] = str(e)
                if retry_count < max_retries:
                    print(f"    R{race_no}: オッズ取得エラー - リトライ {retry_count}/{max_retries}")
                    time.sleep(5)
        
        if not result['odds_success'] and not result['canceled']:
            print(f"    R{race_no}: オッズデータ取得失敗（{result['odds_error']}）")
        
        time.sleep(rate_limit_seconds)  # レート制限対策
    else:
        result['odds_success'] = True  # 既存ファイルあり
    
    return result

def fetch_day_races_parallel(day, stadium, race_numbers, rate_limit_seconds=1, max_retries=3, max_workers=6):
    global progress_done
    ymd = day.strftime('%Y-%m-%d')
    print(f"\n  {stadium.name} {ymd} の並列処理開始: {datetime.now()}", flush=True)
    
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
            with progress_lock:
                progress_done += 1
                # 分母が0の場合は進捗率を表示しない
                if progress_total > 0:
                    percent = progress_done / progress_total * 100
                    print(f"[進捗] {progress_done}/{progress_total} ({percent:.1f}%) 完了", flush=True)
                else:
                    print(f"[進捗] {progress_done} 完了", flush=True)
            if result['canceled']:
                print(f"    R{result['race_no']}: レース中止", flush=True)
            else:
                race_status = "成功" if result['race_success'] else "失敗"
                odds_status = "成功" if result['odds_success'] else "失敗"
                print(f"    R{result['race_no']}: {race_status}race {odds_status}odds", flush=True)
    
    # 統計
    race_success = sum(1 for r in results if r['race_success'])
    odds_success = sum(1 for r in results if r['odds_success'])
    canceled_count = sum(1 for r in results if r['canceled'])
    
    print(f"  {stadium.name} {ymd} の並列処理終了: {datetime.now()}", flush=True)
    if canceled_count > 0:
        print(f"    結果: レース{race_success}/12, オッズ{odds_success}/12, 中止{canceled_count}件", flush=True)
    else:
        print(f"    結果: レース{race_success}/12, オッズ{odds_success}/12", flush=True)
    
    # 会場ごと進捗
    with progress_lock:
        # 分母が0の場合は進捗率を表示しない
        if progress_total > 0:
            percent = progress_done / progress_total * 100
            print(f"[会場進捗] {stadium.name} {progress_done}/{progress_total} ({percent:.1f}%)", flush=True)
        else:
            print(f"[会場進捗] {stadium.name} {progress_done}", flush=True)
    return results

def get_all_stadiums():
    """全24会場のリストを取得"""
    return list(StadiumTelCode)

def main():
    global progress_total, progress_done
    is_child = '--is-child' in sys.argv
    if not is_child:
        # 多重起動チェックや進捗カウンタ初期化は親プロセスのみ
        import os
        import platform
        if platform.system() == "Windows":
            cmdline = f"batch_fetch_all_venues --start-date {sys.argv[sys.argv.index('--start-date')+1]}"
            import subprocess
            result = subprocess.run(f'wmic process where "CommandLine like \'%{cmdline}%\'" get ProcessId,CommandLine /FORMAT:LIST', shell=True, capture_output=True, text=True)
            lines = [l for l in result.stdout.splitlines() if l.strip() and 'wmic' not in l and str(os.getpid()) not in l]
            if len(lines) > 0:
                print("[警告] すでに同じバッチが起動中です。多重起動は進捗表示が見えなくなる原因となります。", flush=True)
                print("このウィンドウで進捗を見たい場合は、他のバッチを停止してから再実行してください。", flush=True)
                sys.exit(1)
        print("[INFO] このウィンドウで進捗がリアルタイム表示されます。", flush=True)
    
    parser = argparse.ArgumentParser(description="全会場バッチデータ取得（完全並列版）")
    parser.add_argument('--start-date', type=str, required=True, help='取得開始日 (YYYY-MM-DD)')
    parser.add_argument('--end-date', type=str, required=True, help='取得終了日 (YYYY-MM-DD)')
    parser.add_argument('--stadiums', type=str, required=True, help='対象会場名（カンマ区切り, 例: KIRYU,EDOGAWA）')
    parser.add_argument('--schedule-workers', type=int, default=8, help='開催日取得の並列数（デフォルト: 8）')
    parser.add_argument('--race-workers', type=int, default=8, help='レース取得の並列数（デフォルト: 8）')
    parser.add_argument('--is-child', action='store_true', help='サブプロセス起動時の多重起動判定除外用フラグ')
    args = parser.parse_args()

    try:
        start_date = datetime.strptime(args.start_date, '%Y-%m-%d').date()
        end_date = datetime.strptime(args.end_date, '%Y-%m-%d').date()
    except Exception:
        print('日付形式はYYYY-MM-DDで指定してください')
        sys.exit(1)
    if start_date > end_date:
        print('開始日は終了日以前で指定してください')
        sys.exit(1)

    # 会場名リストを取得
    all_stadiums = {s.name: s for s in get_all_stadiums()}
    if args.stadiums.strip().upper() == 'ALL':
        stadiums = list(all_stadiums.values())
    else:
        stadium_names = [s.strip().upper() for s in args.stadiums.split(',') if s.strip()]
        invalid = [s for s in stadium_names if s not in all_stadiums]
        if invalid:
            print(f'不正な会場名: {invalid}. 有効な会場名: {list(all_stadiums.keys())}')
            sys.exit(1)
        stadiums = [all_stadiums[s] for s in stadium_names]

    start_time = datetime.now()
    print(f"バッチ処理開始: {start_time}")
    race_numbers = range(1, 13)
    # 高速化設定
    RATE_LIMIT_SECONDS = 1
    MAX_RETRIES = 3
    SCHEDULE_WORKERS = args.schedule_workers
    RACE_WORKERS = args.race_workers
    print(f"全{len(stadiums)}会場バッチフェッチ開始（完全並列版）")
    print(f"期間: {start_date} 〜 {end_date}")
    print(f"対象会場数: {len(stadiums)}")
    print(f"レート制限: {RATE_LIMIT_SECONDS}秒")
    print(f"開催日取得並列数: {SCHEDULE_WORKERS}")
    print(f"レース取得並列数: {RACE_WORKERS}")
    all_event_days = get_all_event_days_parallel(stadiums, start_date, end_date, SCHEDULE_WORKERS)
    
    # 統計情報
    total_days = sum(len(days) for days in all_event_days.values())
    print(f"\n開催日統計:")
    print(f"総開催日数: {total_days}日")
    print(f"平均開催日数: {total_days/len(stadiums):.1f}日/会場")
    
    # 進捗カウンタ初期化（全プロセスで実行）
    progress_total = sum(len(days) * 12 for days in all_event_days.values())
    progress_done = 0
    print(f"全体レース数: {progress_total}", flush=True)

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