#!/usr/bin/env python3
import os
import json
import glob

data_dir = "kyotei_predictor/data/test_raw"
race_files = glob.glob(os.path.join(data_dir, "race_data_*.json"))
odds_files = glob.glob(os.path.join(data_dir, "odds_data_*.json"))

print(f"レースファイル数: {len(race_files)}")
print(f"オッズファイル数: {len(odds_files)}")

if race_files:
    sample_file = race_files[0]
    with open(sample_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    valid_records = [r for r in data.get('race_records', []) if r.get('arrival') is not None]
    print(f"有効なレースレコード: {len(valid_records)}/{len(data.get('race_records', []))}")
    
    if valid_records:
        sorted_records = sorted(valid_records, key=lambda x: x['arrival'])
        trifecta = tuple(r['pit_number'] for r in sorted_records[:3])
        print(f"3連単着順: {trifecta}")
        print("✅ データは正常です")
    else:
        print("❌ 有効なレースデータがありません") 