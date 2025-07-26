import os
import json
from collections import Counter

def check_valid_race_pairs(data_dir):
    race_files = [f for f in os.listdir(data_dir) if f.startswith('race_data_') and f.endswith('.json')]
    odds_files = [f for f in os.listdir(data_dir) if f.startswith('odds_data_') and f.endswith('.json')]
    race_set = set(f.replace('race_data_', '').replace('.json', '') for f in race_files)
    odds_set = set(f.replace('odds_data_', '').replace('.json', '') for f in odds_files)
    pairs = race_set & odds_set
    valid = 0
    invalid = 0
    missing = []
    for key in sorted(pairs):
        race_path = os.path.join(data_dir, f'race_data_{key}.json')
        try:
            with open(race_path, encoding='utf-8') as f:
                race = json.load(f)
            records = [r for r in race.get('race_records', []) if r.get('arrival') is not None]
            if len(records) >= 3:
                valid += 1
            else:
                invalid += 1
        except Exception as e:
            missing.append((race_path, str(e)))
    print(f"有効なレースペア数: {valid}")
    print(f"不完全なレースペア数: {invalid}")
    print(f"race_data/odds_dataペア総数: {len(pairs)}")
    if missing:
        print("読み込みエラー/欠損ファイル:")
        for path, err in missing:
            print(f"  {path}: {err}")
    # ペアが揃っていないファイルもリストアップ
    only_race = race_set - odds_set
    only_odds = odds_set - race_set
    if only_race:
        print("race_dataのみ存在:")
        for k in sorted(only_race):
            print(f"  race_data_{k}.json")
    if only_odds:
        print("odds_dataのみ存在:")
        for k in sorted(only_odds):
            print(f"  odds_data_{k}.json")

if __name__ == "__main__":
    check_valid_race_pairs("kyotei_predictor/data/raw/2024-06") 