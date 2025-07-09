import os
import re
import collections
from datetime import datetime
import csv

RAW_DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'raw')
RACE_FILE_PATTERN = re.compile(r"race_data_(\d{4}-\d{2}-\d{2})_([A-Z0-9]+)_R(\d{1,2})\.json")


def collect_race_files(raw_dir):
    files = os.listdir(raw_dir)
    print(f"[DEBUG] ファイル数: {len(files)}")
    race_info = []
    unmatched = []
    for fname in files:
        m = RACE_FILE_PATTERN.match(fname)
        if m:
            date, venue, race_no = m.groups()
            race_info.append((date, venue, int(race_no)))
        else:
            unmatched.append(fname)
    print(f"[DEBUG] マッチしたファイル数: {len(race_info)}")
    if unmatched:
        print(f"[DEBUG] マッチしなかったファイル例: {unmatched[:5]}")
        race_data_unmatched = [f for f in unmatched if f.startswith('race_data_')]
        if race_data_unmatched:
            print(f"[DEBUG] race_data_で始まるマッチしなかったファイル例: {race_data_unmatched[:5]}")
    return race_info


def build_report(race_info):
    # date -> venue -> set(race_no)
    report = collections.defaultdict(lambda: collections.defaultdict(set))
    for date, venue, race_no in race_info:
        report[date][venue].add(race_no)
    return report


def print_report(report):
    print("\n=== データ取得進捗レポート ===\n")
    all_dates = sorted(report.keys())
    for date in all_dates:
        print(f"日付: {date}")
        for venue in sorted(report[date].keys()):
            races = sorted(report[date][venue])
            print(f"  会場: {venue} 取得レース: {len(races)}/12  -> {races}")
        print()
    # 欠損レースの抽出
    print("--- 欠損レース一覧 ---")
    for date in all_dates:
        for venue in sorted(report[date].keys()):
            got = set(report[date][venue])
            missing = [r for r in range(1, 13) if r not in got]
            if missing:
                print(f"{date} {venue}: 欠損レース {missing}")
    print("\n--- 集計完了 ---\n")


def save_report_csv(report, csv_path):
    with open(csv_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['date', 'venue', 'race_no'])
        for date in sorted(report.keys()):
            for venue in sorted(report[date].keys()):
                for race_no in sorted(report[date][venue]):
                    writer.writerow([date, venue, race_no])


def main():
    if not os.path.exists(RAW_DATA_DIR):
        print(f"データディレクトリが存在しません: {RAW_DATA_DIR}")
        return
    race_info = collect_race_files(RAW_DATA_DIR)
    if not race_info:
        print("race_data_*.json ファイルが見つかりません。")
        return
    print(f"[INFO] 検出ファイル数: {len(race_info)}")
    report = build_report(race_info)
    print_report(report)
    # CSV出力
    csv_path = os.path.join(RAW_DATA_DIR, 'race_data_coverage_report.csv')
    save_report_csv(report, csv_path)
    print(f"[INFO] 進捗レポートCSVを出力: {csv_path}")

if __name__ == "__main__":
    main() 