import os
import json
from datetime import datetime

def check_batch_results():
    data_dir = 'data'
    
    # レースデータファイルを取得
    race_files = [f for f in os.listdir(data_dir) if f.startswith('race_data_') and f.endswith('.json')]
    odds_files = [f for f in os.listdir(data_dir) if f.startswith('odds_data_') and f.endswith('.json')]
    
    print(f"取得されたレースデータファイル数: {len(race_files)}")
    print(f"取得されたオッズデータファイル数: {len(odds_files)}")
    
    # 日付と会場を抽出
    dates = set()
    venues = set()
    
    for f in race_files:
        parts = f.replace('race_data_', '').replace('.json', '').split('_')
        if len(parts) >= 2:
            dates.add(parts[0])
            venues.add(parts[1])
    
    if dates:
        print(f"取得期間: {min(dates)} から {max(dates)}")
        print(f"取得会場: {sorted(venues)}")
        print(f"1日あたりの平均レース数: {len(race_files) // len(dates)}")
        
        # 各日付のレース数を確認
        daily_races = {}
        for f in race_files:
            parts = f.replace('race_data_', '').replace('.json', '').split('_')
            if len(parts) >= 2:
                date = parts[0]
                daily_races[date] = daily_races.get(date, 0) + 1
        
        print("\n日別レース数:")
        for date in sorted(daily_races.keys()):
            print(f"  {date}: {daily_races[date]}レース")
    
    # データの品質チェック
    print("\nデータ品質チェック:")
    sample_race_file = race_files[0] if race_files else None
    sample_odds_file = odds_files[0] if odds_files else None
    
    if sample_race_file:
        with open(os.path.join(data_dir, sample_race_file), 'r', encoding='utf-8') as f:
            race_data = json.load(f)
        print(f"レースデータ構造: {list(race_data.keys())}")
        print(f"出走者数: {len(race_data.get('race_entries', []))}")
    
    if sample_odds_file:
        with open(os.path.join(data_dir, sample_odds_file), 'r', encoding='utf-8') as f:
            odds_data = json.load(f)
        print(f"オッズデータ構造: {list(odds_data.keys())}")
        print(f"オッズ数: {odds_data.get('odds_count', 0)}")

if __name__ == "__main__":
    check_batch_results() 