#!/usr/bin/env python3
"""
全競艇場データ一括取得ツール
"""

import os
import sys
import json
import time
import requests
import argparse
import atexit
import threading
from datetime import date, timedelta, datetime
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Optional, Tuple, Any
from io import StringIO

# グローバル変数の初期化
racer_error_log_file = None
racer_error_log_lock = threading.Lock()
progress_lock = threading.Lock()

# 文字化け対策: 標準出力のエンコーディングをUTF-8に設定
if sys.platform.startswith('win'):
    import codecs
    # PowerShellでの文字化け対策
    try:
        # 環境変数でUTF-8を強制
        os.environ['PYTHONIOENCODING'] = 'utf-8'
        os.environ['PYTHONLEGACYWINDOWSSTDIO'] = 'utf-8'
        
        # 標準出力をUTF-8に設定（安全な方法）
        if hasattr(sys.stdout, 'detach'):
            sys.stdout = codecs.getwriter('utf-8')(sys.stdout.detach())
            sys.stderr = codecs.getwriter('utf-8')(sys.stderr.detach())
    except Exception:
        # エラーが発生した場合は環境変数のみ設定
        os.environ['PYTHONIOENCODING'] = 'utf-8'
        os.environ['PYTHONLEGACYWINDOWSSTDIO'] = 'utf-8'

from metaboatrace.models.stadium import StadiumTelCode
from metaboatrace.scrapers.official.website.v1707.pages.monthly_schedule_page.location import create_monthly_schedule_page_url
from metaboatrace.scrapers.official.website.v1707.pages.monthly_schedule_page.scraping import extract_events
from metaboatrace.scrapers.official.website.exceptions import RaceCanceled
from kyotei_predictor.tools.fetch.race_data_fetcher import fetch_complete_race_data
from kyotei_predictor.tools.fetch.odds_fetcher import fetch_trifecta_odds
from kyotei_predictor.utils.common import KyoteiUtils

def safe_print(message: str) -> None:
    """文字化け対策付きprint関数"""
    utils = KyoteiUtils()
    utils.safe_print(message)

def log_racer_error(error_info: dict):
    """選手名取得エラーを専用ログファイルに記録"""
    global racer_error_log_file
    if racer_error_log_file is None:
        # ログファイルを初期化
        log_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'logs', 'racer_errors')
        os.makedirs(log_dir, exist_ok=True)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        racer_error_log_file = os.path.join(log_dir, f'racer_errors_{timestamp}.jsonl')
    
    with racer_error_log_lock:
        with open(racer_error_log_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(error_info, ensure_ascii=False) + '\n')

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
            safe_print(f"❌ {stadium.name} {current_date.year}-{current_date.month} 取得エラー: {e}")
        
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

def log_info(message: str) -> None:
    """標準出力に情報を出す（flush付き）"""
    print(message, flush=True)

def make_race_file_paths(day: date, stadium: StadiumTelCode, race_no: int) -> Dict[str, str]:
    """レース・オッズ・中止ファイルのパスをまとめて返す（月ごとサブディレクトリ対応）"""
    ymd = day.strftime('%Y-%m-%d')
    month = ymd[:7]  # YYYY-MM
    base_dir = os.path.join("kyotei_predictor", "data", "raw", month)
    os.makedirs(base_dir, exist_ok=True)
    return {
        'race': os.path.join(base_dir, f"race_data_{ymd}_{stadium.name}_R{race_no}.json"),
        'odds': os.path.join(base_dir, f"odds_data_{ymd}_{stadium.name}_R{race_no}.json"),
        'canceled': os.path.join(base_dir, f"race_canceled_{ymd}_{stadium.name}_R{race_no}.json")
    }

def fetch_race_data_parallel(
    day: date,
    stadium: StadiumTelCode,
    race_no: int,
    rate_limit_seconds: int = 1,
    max_retries: int = 3
) -> Dict[str, Any]:
    """
    1レースのデータを取得（並列用）
    Args:
        day: レース日付
        stadium: 会場コード
        race_no: レース番号
        rate_limit_seconds: レート制限秒数
        max_retries: 最大リトライ回数
    Returns:
        結果情報dict
    """
    paths = make_race_file_paths(day, stadium, race_no)
    ymd = day.strftime('%Y-%m-%d')
    result = {
        'stadium': stadium.name,
        'day': ymd,
        'race_no': race_no,
        'race_success': False,
        'odds_success': False,
        'race_file': os.path.basename(paths['race']),
        'odds_file': os.path.basename(paths['odds']),
        'race_error': None,
        'odds_error': None,
        'canceled': False
    }

    # レース中止ファイルのチェック
    if os.path.exists(paths['canceled']):
        result['canceled'] = True
        result['race_success'] = True
        result['odds_success'] = True
        log_info(f"    R{race_no}: レース中止済み - スキップ")
        return result

    # race_data取得
    if not os.path.exists(paths['race']):
        retry_count = 0
        while retry_count < max_retries:
            try:
                race_data = fetch_complete_race_data(day, stadium, race_no)
                if race_data:
                    os.makedirs(os.path.dirname(paths['race']), exist_ok=True)
                    with open(paths['race'], 'w', encoding='utf-8') as f:
                        json.dump(race_data, f, ensure_ascii=False, indent=2)
                    result['race_success'] = True
                    break
                else:
                    retry_count += 1
                    if retry_count < max_retries:
                        log_info(f"    R{race_no}: レースデータ取得失敗（リトライ {retry_count}/{max_retries}）")
            except ValueError as e:
                if "not enough values to unpack" in str(e):
                    # 選手名解析エラーは既にfetch_race_entry_data内で処理されているため、
                    # ここでは正常にデータが取得できているはずです
                    result['race_error'] = f"予期しない選手名解析エラー: {e}"
                    log_info(f"    R{race_no}: 予期しない選手名解析エラー - 詳細情報を記録")
                    
                    # エラーの詳細ログを記録
                    error_log_info = {
                        "timestamp": datetime.now().isoformat(),
                        "stadium": stadium.name,
                        "date": ymd,
                        "race_no": race_no,
                        "error_type": "unexpected_racer_name_parse_error",
                        "error_message": str(e),
                        "error_details": {
                            "args": getattr(e, 'args', []),
                            "traceback": str(e)
                        }
                    }
                    log_racer_error(error_log_info)
                    
                    # 予期しないエラーの場合はリトライ
                    retry_count += 1
                    if retry_count < max_retries:
                        log_info(f"    R{race_no}: 予期しない選手名解析エラー - リトライ {retry_count}/{max_retries}")
                        time.sleep(5)
                    else:
                        result['race_error'] = f"予期しない選手名解析エラー: {e}"
                        log_info(f"    R{race_no}: 予期しない選手名解析エラー - 最大リトライ回数に達しました")
                    continue
                else:
                    retry_count += 1
                    result['race_error'] = str(e)
                    if retry_count < max_retries:
                        log_info(f"    R{race_no}: ValueError - リトライ {retry_count}/{max_retries}")
                        time.sleep(5)
            except RaceCanceled as e:
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
                with open(paths['canceled'], 'w', encoding='utf-8') as f:
                    json.dump(canceled_data, f, ensure_ascii=False, indent=2)
                result['canceled'] = True
                result['race_success'] = True
                result['odds_success'] = True
                log_info(f"    R{race_no}: レース中止 - 専用ファイル作成、オッズ取得をスキップ")
                break
            except Exception as e:
                if "データ未公開" in str(e) or "DataNotFound" in str(e):
                    retry_count += 1
                    result['race_error'] = f"データ未公開: {e}"
                    if retry_count < max_retries:
                        log_info(f"    R{race_no}: データ未公開 - リトライ {retry_count}/{max_retries}")
                        time.sleep(5)
                    else:
                        log_info(f"    R{race_no}: データ未公開 - 次回実行時に再試行")
                    continue
                else:
                    retry_count += 1
                    result['race_error'] = str(e)
                    if retry_count < max_retries:
                        log_info(f"    R{race_no}: {type(e).__name__} - リトライ {retry_count}/{max_retries}")
                        time.sleep(5)
        if not result['race_success'] and not result['canceled']:
            log_info(f"    R{race_no}: レースデータ取得失敗（{result['race_error']}）")
        time.sleep(rate_limit_seconds)
    else:
        result['race_success'] = True

    # odds_data取得（レース中止でない場合のみ）
    if result['canceled']:
        result['odds_success'] = True
        log_info(f"    R{race_no}: レース中止のためオッズ取得をスキップ")
    elif not os.path.exists(paths['odds']):
        retry_count = 0
        while retry_count < max_retries:
            try:
                odds_data = fetch_trifecta_odds(day, stadium, race_no)
                if odds_data:
                    os.makedirs(os.path.dirname(paths['odds']), exist_ok=True)
                    with open(paths['odds'], 'w', encoding='utf-8') as f:
                        json.dump(odds_data, f, ensure_ascii=False, indent=2)
                    result['odds_success'] = True
                    break
                else:
                    retry_count += 1
                    if retry_count < max_retries:
                        log_info(f"    R{race_no}: オッズデータ取得失敗（リトライ {retry_count}/{max_retries}）")
            except RaceCanceled as e:
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
                    with open(paths['canceled'], 'w', encoding='utf-8') as f:
                        json.dump(canceled_data, f, ensure_ascii=False, indent=2)
                    result['canceled'] = True
                    result['race_success'] = True
                    result['odds_success'] = True
                    log_info(f"    R{race_no}: レース中止（オッズ取得時） - 専用ファイル作成")
                    break
            except Exception as e:
                if "データ未公開" in str(e) or "DataNotFound" in str(e):
                    retry_count += 1
                    result['odds_error'] = f"データ未公開: {e}"
                    if retry_count < max_retries:
                        log_info(f"    R{race_no}: データ未公開（オッズ取得時） - リトライ {retry_count}/{max_retries}")
                        time.sleep(5)
                    else:
                        log_info(f"    R{race_no}: データ未公開（オッズ取得時） - 次回実行時に再試行")
                    continue
                else:
                    retry_count += 1
                    result['odds_error'] = str(e)
                    if retry_count < max_retries:
                        log_info(f"    R{race_no}: オッズ取得エラー - リトライ {retry_count}/{max_retries}")
                        time.sleep(5)
        if not result['odds_success'] and not result['canceled']:
            log_info(f"    R{race_no}: オッズデータ取得失敗（{result['odds_error']}）")
        time.sleep(rate_limit_seconds)
    else:
        result['odds_success'] = True

    return result

def fetch_day_races_parallel(
    day: date,
    stadium: StadiumTelCode,
    race_numbers: range,
    rate_limit_seconds: int = 1,
    max_retries: int = 3,
    max_workers: int = 6
) -> list[dict]:
    """
    1日分の全レースを並列取得
    Args:
        day: レース日付
        stadium: 会場コード
        race_numbers: レース番号のrange
        rate_limit_seconds: レート制限秒数
        max_retries: 最大リトライ回数
        max_workers: 並列数
    Returns:
        各レースの取得結果リスト
    """
    global progress_done
    ymd = day.strftime('%Y-%m-%d')
    log_info(f"\n  {stadium.name} {ymd} の並列処理開始: {datetime.now()}")

    results = []
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_race = {
            executor.submit(fetch_race_data_parallel, day, stadium, race_no, rate_limit_seconds, max_retries): race_no
            for race_no in race_numbers
        }
        for future in as_completed(future_to_race):
            result = future.result()
            results.append(result)
            # 進捗表示
            with progress_lock:
                progress_done += 1
                if progress_total > 0:
                    percent = progress_done / progress_total * 100
                    log_info(f"[進捗] {progress_done}/{progress_total} ({percent:.1f}%) 完了")
                else:
                    log_info(f"[進捗] {progress_done} 完了")
            if result['canceled']:
                log_info(f"    R{result['race_no']}: レース中止")
            else:
                race_status = "成功" if result['race_success'] else "失敗"
                odds_status = "成功" if result['odds_success'] else "失敗"
                log_info(f"    R{result['race_no']}: {race_status}race {odds_status}odds")

    # 統計
    race_success = sum(1 for r in results if r['race_success'])
    odds_success = sum(1 for r in results if r['odds_success'])
    canceled_count = sum(1 for r in results if r['canceled'])

    log_info(f"  {stadium.name} {ymd} の並列処理終了: {datetime.now()}")
    if canceled_count > 0:
        log_info(f"    結果: レース{race_success}/12, オッズ{odds_success}/12, 中止{canceled_count}件")
    else:
        log_info(f"    結果: レース{race_success}/12, オッズ{odds_success}/12")

    # 会場ごと進捗
    with progress_lock:
        if progress_total > 0:
            percent = progress_done / progress_total * 100
            log_info(f"[会場進捗] {stadium.name} {progress_done}/{progress_total} ({percent:.1f}%)")
        else:
            log_info(f"[会場進捗] {stadium.name} {progress_done}")
    return results

def get_all_stadiums():
    """全24会場のリストを取得"""
    return list(StadiumTelCode)

def create_lockfile(lockfile: str) -> None:
    """ロックファイルを作成し、atexitで削除を登録"""
    with open(lockfile, 'w') as f:
        f.write(f"pid={os.getpid()}\n")
        f.write(f"start={datetime.now().isoformat()}\n")
        f.write(f"cmd={' '.join(sys.argv)}\n")
    def remove_lockfile():
        if os.path.exists(lockfile):
            os.remove(lockfile)
    atexit.register(remove_lockfile)

def parse_args() -> argparse.Namespace:
    """コマンドライン引数をパース"""
    parser = argparse.ArgumentParser(description="全会場バッチデータ取得（完全並列版）")
    parser.add_argument('--start-date', type=str, required=True, help='取得開始日 (YYYY-MM-DD)')
    parser.add_argument('--end-date', type=str, required=True, help='取得終了日 (YYYY-MM-DD)')
    parser.add_argument('--stadiums', type=str, required=True, help='対象会場名（カンマ区切り, 例: KIRYU,EDOGAWA）')
    parser.add_argument('--schedule-workers', type=int, default=8, help='開催日取得の並列数（デフォルト: 8）')
    parser.add_argument('--race-workers', type=int, default=8, help='レース取得の並列数（デフォルト: 8）')
    parser.add_argument('--is-child', action='store_true', help='サブプロセス起動時の多重起動判定除外用フラグ')
    return parser.parse_args()

def main() -> None:
    """
    バッチ全体のエントリポイント。引数パース、ロックファイル、進捗カウンタ、全体フローを管理。
    """
    global progress_total, progress_done
    args = parse_args()
    lockfile = 'batch_fetch_all_venues.lock'
    is_child = args.is_child
    if not is_child:
        if os.path.exists(lockfile):
            log_info(f"[警告] すでにロックファイル {lockfile} が存在します。多重起動はできません。")
            log_info("このウィンドウで進捗を見たい場合は、他のバッチを停止してロックファイルを削除してから再実行してください。")
            sys.exit(1)
        create_lockfile(lockfile)
    log_info("[INFO] このウィンドウで進捗がリアルタイム表示されます。")

    try:
        start_date = datetime.strptime(args.start_date, '%Y-%m-%d').date()
        end_date = datetime.strptime(args.end_date, '%Y-%m-%d').date()
    except Exception:
        log_info('日付形式はYYYY-MM-DDで指定してください')
        sys.exit(1)
    if start_date > end_date:
        log_info('開始日は終了日以前で指定してください')
        sys.exit(1)

    all_stadiums = {s.name: s for s in get_all_stadiums()}
    if args.stadiums.strip().upper() == 'ALL':
        stadiums = list(all_stadiums.values())
    else:
        stadium_names = [s.strip().upper() for s in args.stadiums.split(',') if s.strip()]
        invalid = [s for s in stadium_names if s not in all_stadiums]
        if invalid:
            log_info(f'不正な会場名: {invalid}. 有効な会場名: {list(all_stadiums.keys())}')
            sys.exit(1)
        stadiums = [all_stadiums[s] for s in stadium_names]

    start_time = datetime.now()
    log_info(f"バッチ処理開始: {start_time}")
    race_numbers = range(1, 13)
    RATE_LIMIT_SECONDS = 1
    MAX_RETRIES = 3
    SCHEDULE_WORKERS = args.schedule_workers
    RACE_WORKERS = args.race_workers
    log_info(f"全{len(stadiums)}会場バッチフェッチ開始（完全並列版）")
    log_info(f"期間: {start_date} 〜 {end_date}")
    log_info(f"対象会場数: {len(stadiums)}")
    log_info(f"レート制限: {RATE_LIMIT_SECONDS}秒")
    log_info(f"開催日取得並列数: {SCHEDULE_WORKERS}")
    log_info(f"レース取得並列数: {RACE_WORKERS}")
    all_event_days = get_all_event_days_parallel(stadiums, start_date, end_date, SCHEDULE_WORKERS)

    total_days = sum(len(days) for days in all_event_days.values())
    log_info(f"\n開催日統計:")
    log_info(f"総開催日数: {total_days}日")
    log_info(f"平均開催日数: {total_days/len(stadiums):.1f}日/会場")

    progress_total = sum(len(days) * 12 for days in all_event_days.values())
    progress_done = 0
    log_info(f"全体レース数: {progress_total}")

    total_races = 0
    total_odds = 0
    success_races = 0
    success_odds = 0
    racer_parse_errors = 0  # 選手名解析エラー数

    for stadium in stadiums:
        event_days = all_event_days[stadium]
        if not event_days:
            log_info(f"\n{stadium.name}: 開催日なし - スキップ")
            continue
        log_info(f"\n=== {stadium.name} 並列データ取得開始 ===")
        for day in event_days:
            day_results = fetch_day_races_parallel(
                day, stadium, race_numbers, 
                RATE_LIMIT_SECONDS, MAX_RETRIES, RACE_WORKERS
            )
            for result in day_results:
                total_races += 1
                total_odds += 1
                if result['race_success']:
                    success_races += 1
                if result['odds_success']:
                    success_odds += 1
                # 選手名解析エラーのカウント
                if result.get('race_error') and '選手名解析エラー' in result['race_error']:
                    racer_parse_errors += 1

    log_info(f"\n=== バッチフェッチ完了（完全並列版） ===")
    log_info(f"対象期間: {start_date} 〜 {end_date}")
    log_info(f"対象会場: {len(stadiums)}会場")
    log_info(f"総リクエスト数: レース{total_races}件, オッズ{total_odds}件")
    log_info(f"成功数: レース{success_races}件, オッズ{success_odds}件")
    if total_races > 0 and total_odds > 0:
        log_info(f"成功率: レース{success_races/total_races*100:.1f}%, オッズ{success_odds/total_odds*100:.1f}%")
        log_info(f"失敗数: レース{total_races-success_races}件, オッズ{total_odds-success_odds}件")
    else:
        log_info("成功率: 計算不可")
    
    # 選手名解析エラーの統計
    if racer_parse_errors > 0:
        log_info(f"\n📊 選手名解析エラー統計:")
        log_info(f"  選手名解析エラー数: {racer_parse_errors}件")
        log_info(f"  エラー率: {racer_parse_errors/total_races*100:.1f}%")
        if racer_error_log_file:
            log_info(f"  詳細ログ: {racer_error_log_file}")
    
    log_info(f"\n📊 エラーハンドリング改善:")
    log_info(f"  - 選手名解析エラー: 自動スキップ処理 + 部分データ保存")
    log_info(f"  - レース中止: 自動検出・スキップ")
    log_info(f"  - ネットワークエラー: 最大{MAX_RETRIES}回リトライ")
    log_info(f"  - レート制限: {RATE_LIMIT_SECONDS}秒間隔")

    end_time = datetime.now()
    log_info(f"バッチ処理終了: {end_time}")
    log_info(f"所要時間: {end_time - start_time}")

if __name__ == "__main__":
    main() 