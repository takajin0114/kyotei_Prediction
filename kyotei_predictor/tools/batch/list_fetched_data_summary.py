import os
import re
from collections import defaultdict

RAW_DIR = os.path.join(os.path.dirname(__file__), '../../data/raw')

race_pattern = re.compile(r'race_data_(\d{4}-\d{2}-\d{2})_([A-Z0-9]+)_R\d+\.json')
odds_pattern = re.compile(r'odds_data_(\d{4}-\d{2}-\d{2})_([A-Z0-9]+)_R\d+\.json')

def collect_summary(pattern):
    summary = defaultdict(set)
    for fname in os.listdir(RAW_DIR):
        m = pattern.match(fname)
        if m:
            day, stadium = m.groups()
            summary[stadium].add(day)
    return summary

def print_summary(summary, label):
    print(f'--- {label} ---')
    for stadium in sorted(summary):
        days = sorted(summary[stadium])
        if days:
            print(f'{stadium}: {days[0]} ～ {days[-1]} ({len(days)}日分)')
        else:
            print(f'{stadium}: データなし')

if __name__ == '__main__':
    print('取得済みデータ一覧（期間・会場ごと）')
    race_summary = collect_summary(race_pattern)
    odds_summary = collect_summary(odds_pattern)
    print_summary(race_summary, 'レースデータ')
    print_summary(odds_summary, 'オッズデータ') 