#!/usr/bin/env python3
"""
全国24場・2012-01-01〜2024-07-02・1日12Rの全組み合わせで
race_data/odds_dataを自動取得するバッチスクリプト
"""
import os
import sys
import json
import time
from datetime import date, timedelta
from metaboatrace.models.stadium import StadiumTelCode
from tools.race_data_fetcher import fetch_complete_race_data
from tools.odds_fetcher import fetch_trifecta_odds

def daterange(start_date, end_date):
    for n in range((end_date - start_date).days + 1):
        yield start_date + timedelta(n)

def main():
    # 期間設定
    start_date = date(2012, 1, 1)
    end_date = date(2024, 7, 2)
    race_numbers = range(1, 13)  # 1日12R
    # 全国24場
    stadiums = list(StadiumTelCode)
    print(f"対象期間: {start_date}〜{end_date}、場: {len(stadiums)}場、1日12R")
    print(f"合計レース数（理論値）: {(end_date-start_date).days * len(stadiums) * 12}")

    data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')
    os.makedirs(data_dir, exist_ok=True)

    for stadium in stadiums:
        for single_date in daterange(start_date, end_date):
            ymd = single_date.strftime('%Y-%m-%d')
            for race_no in race_numbers:
                race_fname = f"race_data_{ymd}_{stadium.name}_R{race_no}.json"
                odds_fname = f"odds_data_{ymd}_{stadium.name}_R{race_no}.json"
                race_fpath = os.path.join(data_dir, race_fname)
                odds_fpath = os.path.join(data_dir, odds_fname)

                # 既存ファイルはスキップ
                if os.path.exists(race_fpath) and os.path.exists(odds_fpath):
                    continue

                print(f"\n=== {ymd} {stadium.name} R{race_no} ===")
                # race_data取得
                if not os.path.exists(race_fpath):
                    try:
                        race_data = fetch_complete_race_data(single_date, stadium, race_no)
                        if race_data:
                            with open(race_fpath, 'w', encoding='utf-8') as f:
                                json.dump(race_data, f, ensure_ascii=False, indent=2)
                            print(f"✅ race_data保存: {race_fname}")
                        else:
                            print(f"❌ race_data取得失敗: {race_fname}")
                    except Exception as e:
                        print(f"❌ race_data取得エラー: {e}")
                    time.sleep(3)  # レートリミット

                # odds_data取得
                if not os.path.exists(odds_fpath):
                    try:
                        odds_data = fetch_trifecta_odds(single_date, stadium, race_no)
                        if odds_data:
                            with open(odds_fpath, 'w', encoding='utf-8') as f:
                                json.dump(odds_data, f, ensure_ascii=False, indent=2)
                            print(f"✅ odds_data保存: {odds_fname}")
                        else:
                            print(f"❌ odds_data取得失敗: {odds_fname}")
                    except Exception as e:
                        print(f"❌ odds_data取得エラー: {e}")
                    time.sleep(3)  # レートリミット

if __name__ == "__main__":
    main() 