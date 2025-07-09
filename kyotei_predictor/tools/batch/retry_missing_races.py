import os
import json
import re
from kyotei_predictor.tools.fetch.race_data_fetcher import fetch_complete_race_data
from kyotei_predictor.tools.fetch.odds_fetcher import fetch_trifecta_odds
from kyotei_predictor.tools.common.venue_mapping import VENUE_MAPPING
from metaboatrace.models.stadium import StadiumTelCode
from datetime import datetime

RAW_DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), '..', 'data', 'raw')
RACE_FILE_PATTERN = re.compile(r"race_data_(\d{4}-\d{2}-\d{2})_([A-Z0-9]+)_R(\d{1,2})\.json")

# 1-12R
ALL_RACE_NOS = set(range(1, 13))

def collect_existing_races(raw_dir):
    files = os.listdir(raw_dir)
    existing = set()
    for fname in files:
        m = RACE_FILE_PATTERN.match(fname)
        if m:
            date, venue, race_no = m.groups()
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

def main():
    print(f"[INFO] 欠損レース自動再取得バッチ開始")
    existing = collect_existing_races(RAW_DATA_DIR)
    missing = collect_missing_races(existing)
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
        try:
            race_data = fetch_complete_race_data(race_date, stadium_enum, race_no)
            if race_data:
                race_fname = f"race_data_{date_str}_{venue}_R{race_no}.json"
                race_fpath = os.path.join(RAW_DATA_DIR, race_fname)
                with open(race_fpath, 'w', encoding='utf-8') as f:
                    json.dump(race_data, f, ensure_ascii=False, indent=2)
                print(f"  ✅ race_data保存: {race_fname}")
            odds_data = fetch_trifecta_odds(race_date, stadium_enum, race_no)
            if odds_data:
                odds_fname = f"odds_data_{date_str}_{venue}_R{race_no}.json"
                odds_fpath = os.path.join(RAW_DATA_DIR, odds_fname)
                with open(odds_fpath, 'w', encoding='utf-8') as f:
                    json.dump(odds_data, f, ensure_ascii=False, indent=2)
                print(f"  ✅ odds_data保存: {odds_fname}")
        except Exception as e:
            print(f"  ❌ 取得失敗: {date_str} {venue} R{race_no} - {e}")
    print(f"[INFO] 欠損レース再取得バッチ完了")

if __name__ == "__main__":
    main() 