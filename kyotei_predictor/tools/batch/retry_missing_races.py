import os
import json
import re
from kyotei_predictor.tools.fetch.race_data_fetcher import fetch_complete_race_data
from kyotei_predictor.tools.fetch.odds_fetcher import fetch_trifecta_odds
from kyotei_predictor.tools.common.venue_mapping import VENUE_MAPPING
from metaboatrace.models.stadium import StadiumTelCode
from datetime import datetime
import argparse
import sys
import atexit

RAW_DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), '..', 'data', 'raw')
RACE_FILE_PATTERN = re.compile(r"race_data_(\d{4}-\d{2}-\d{2})_([A-Z0-9]+)_R(\d{1,2})\.json")
CANCELED_FILE_PATTERN = re.compile(r"race_canceled_(\d{4}-\d{2}-\d{2})_([A-Z0-9]+)_R(\d{1,2})\.json")

# 1-12R
ALL_RACE_NOS = set(range(1, 13))

def collect_existing_races(raw_dir):
    files = os.listdir(raw_dir)
    existing = set()
    for fname in files:
        # race_data_ファイルをチェック
        m = RACE_FILE_PATTERN.match(fname)
        if m:
            date, venue, race_no = m.groups()
            existing.add((date, venue, int(race_no)))
        # race_canceled_ファイルもチェック（レース中止も「存在」として扱う）
        m_canceled = CANCELED_FILE_PATTERN.match(fname)
        if m_canceled:
            date, venue, race_no = m_canceled.groups()
            existing.add((date, venue, int(race_no)))
    return existing

def collect_missing_races(existing):
    # 日付・会場ごとに1-12Rのうち未取得を抽出
    missing = []
    by_date_venue = {}
    for date, venue, race_no in existing:
        by_date_venue.setdefault((date, venue), set()).add(race_no)
    for (date, venue), got_races in by_date_venue.items():
        missing_races = ALL_RACE_NOS - got_races
        for race_no in sorted(missing_races):
            missing.append((date, venue, race_no))
    return missing

def create_canceled_file(date_str, venue, race_no):
    """
    レース中止ファイルを作成
    """
    canceled_fname = f"race_canceled_{date_str}_{venue}_R{race_no}.json"
    canceled_fpath = os.path.join(RAW_DATA_DIR, canceled_fname)
    # 保存先ディレクトリを作成
    os.makedirs(os.path.dirname(canceled_fpath), exist_ok=True)
    canceled_data = {
        "status": "canceled",
        "race_info": {
            "date": date_str,
            "stadium": venue,
            "race_number": race_no,
            "title": f"{venue} 第{race_no}レース"
        },
        "canceled_at": datetime.now().isoformat(),
        "reason": "レース中止（再取得時検出）"
    }
    with open(canceled_fpath, 'w', encoding='utf-8') as f:
        json.dump(canceled_data, f, ensure_ascii=False, indent=2)
    print(f"  ✅ レース中止ファイル作成: {canceled_fname}")

def main():
    lockfile = 'retry_missing_races.lock'
    is_child = '--is-child' in sys.argv if '--is-child' in sys.argv else False
    if not is_child:
        if os.path.exists(lockfile):
            print(f"[警告] すでにロックファイル {lockfile} が存在します。多重起動はできません。", flush=True)
            print("このウィンドウで進捗を見たい場合は、他のバッチを停止してロックファイルを削除してから再実行してください。", flush=True)
            sys.exit(1)
        with open(lockfile, 'w') as f:
            f.write(f"pid={os.getpid()}\n")
            f.write(f"start={datetime.now().isoformat()}\n")
            f.write(f"cmd={' '.join(sys.argv)}\n")
        def remove_lockfile():
            if os.path.exists(lockfile):
                os.remove(lockfile)
        atexit.register(remove_lockfile)

    try:
        parser = argparse.ArgumentParser(description="欠損レース自動再取得バッチ（日付範囲指定対応）")
        parser.add_argument('--start-date', type=str, help='取得開始日 (YYYY-MM-DD)', default=None)
        parser.add_argument('--end-date', type=str, help='取得終了日 (YYYY-MM-DD)', default=None)
        args = parser.parse_args()
        
        start_date = None
        end_date = None
        if args.start_date:
            start_date = datetime.strptime(args.start_date, "%Y-%m-%d").date()
        if args.end_date:
            end_date = datetime.strptime(args.end_date, "%Y-%m-%d").date()

        print(f"[INFO] 欠損レース自動再取得バッチ開始")
        existing = collect_existing_races(RAW_DATA_DIR)
        missing = collect_missing_races(existing)
        # 日付範囲でフィルタ
        if start_date and end_date:
            missing = [m for m in missing if start_date <= datetime.strptime(m[0], "%Y-%m-%d").date() <= end_date]
        print(f"[INFO] 欠損レース数: {len(missing)}")
        for date, venue, race_no in missing:
            # venue(str)→StadiumTelCode変換
            stadium_enum = None
            for st, info in VENUE_MAPPING.items():
                if info['name'] == venue:
                    stadium_enum = st
                    break
            if stadium_enum is None:
                print(f"  ❌ 変換失敗: {venue} をStadiumTelCodeに変換できません")
                continue
            # date(str)→date型変換
            race_date = date
            if isinstance(race_date, str):
                try:
                    race_date = datetime.strptime(race_date, "%Y-%m-%d").date()
                except Exception as e:
                    print(f"  ❌ 日付変換失敗: {date} - {e}")
                    continue
            print(f"  [DEBUG] race_date type: {type(race_date)}, value: {race_date}")
            date_str = race_date.strftime('%Y-%m-%d')
            print(f"[RETRY] {date_str} {venue} R{race_no}")
            
            # レース中止ファイルの事前チェック
            canceled_fname = f"race_canceled_{date_str}_{venue}_R{race_no}.json"
            canceled_fpath = os.path.join(RAW_DATA_DIR, canceled_fname)
            if os.path.exists(canceled_fpath):
                print(f"  ⏭️ レース中止済み - スキップ: {canceled_fname}")
                continue
                
            try:
                # レースデータ取得
                race_data = fetch_complete_race_data(race_date, stadium_enum, race_no)
                if race_data:
                    race_fname = f"race_data_{date_str}_{venue}_R{race_no}.json"
                    race_fpath = os.path.join(RAW_DATA_DIR, race_fname)
                    with open(race_fpath, 'w', encoding='utf-8') as f:
                        json.dump(race_data, f, ensure_ascii=False, indent=2)
                    print(f"  ✅ race_data保存: {race_fname}")
                    
                    # レースデータが正常に取得できた場合のみオッズ取得
                    odds_data = fetch_trifecta_odds(race_date, stadium_enum, race_no)
                    if odds_data:
                        odds_fname = f"odds_data_{date_str}_{venue}_R{race_no}.json"
                        odds_fpath = os.path.join(RAW_DATA_DIR, odds_fname)
                        with open(odds_fpath, 'w', encoding='utf-8') as f:
                            json.dump(odds_data, f, ensure_ascii=False, indent=2)
                        print(f"  ✅ odds_data保存: {odds_fname}")
                else:
                    # レースデータが取得できない場合（レース中止の可能性）
                    print(f"  🚫 レースデータ取得失敗: {date_str} {venue} R{race_no}")
                    create_canceled_file(date_str, venue, race_no)
                    
            except Exception as e:
                error_msg = str(e)
                # レース中止エラーの検出
                if "RaceCanceled" in error_msg or "レース中止" in error_msg:
                    print(f"  🚫 レース中止検出: {date_str} {venue} R{race_no}")
                    create_canceled_file(date_str, venue, race_no)
                else:
                    print(f"  取得失敗: {date_str} {venue} R{race_no} - {error_msg}")
        print(f"[INFO] 欠損レース再取得バッチ完了")
    finally:
        if not is_child and os.path.exists(lockfile):
            os.remove(lockfile)

if __name__ == "__main__":
    main() 