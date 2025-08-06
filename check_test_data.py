#!/usr/bin/env python3
"""
test_rawディレクトリのデータファイル確認スクリプト
"""

import os
import glob
from pathlib import Path

def check_test_data():
    """test_rawディレクトリのデータファイルを確認"""
    data_dir = "kyotei_predictor/data/test_raw"
    
    print(f"=== test_rawディレクトリのデータ確認 ===")
    print(f"データディレクトリ: {data_dir}")
    
    if not os.path.exists(data_dir):
        print(f"❌ データディレクトリが存在しません: {data_dir}")
        return
    
    # レースデータファイルの確認
    race_files = glob.glob(os.path.join(data_dir, "race_data_*.json"))
    odds_files = glob.glob(os.path.join(data_dir, "odds_data_*.json"))
    
    print(f"\n📊 ファイル数:")
    print(f"  レースデータファイル: {len(race_files)}")
    print(f"  オッズデータファイル: {len(odds_files)}")
    
    if race_files:
        print(f"\n📁 レースデータファイル例:")
        for i, file in enumerate(race_files[:5]):
            print(f"  {i+1}. {os.path.basename(file)}")
        if len(race_files) > 5:
            print(f"  ... 他 {len(race_files) - 5} ファイル")
    
    if odds_files:
        print(f"\n📁 オッズデータファイル例:")
        for i, file in enumerate(odds_files[:5]):
            print(f"  {i+1}. {os.path.basename(file)}")
        if len(odds_files) > 5:
            print(f"  ... 他 {len(odds_files) - 5} ファイル")
    
    # ペアマッチングの確認
    print(f"\n🔍 ペアマッチング確認:")
    race_basenames = [os.path.basename(f) for f in race_files]
    odds_basenames = [os.path.basename(f) for f in odds_files]
    
    # レースファイル名からオッズファイル名を生成
    expected_odds_files = []
    for race_file in race_basenames:
        odds_file = race_file.replace("race_data_", "odds_data_")
        expected_odds_files.append(odds_file)
    
    # マッチするペアを確認
    matched_pairs = []
    for race_file in race_basenames:
        odds_file = race_file.replace("race_data_", "odds_data_")
        if odds_file in odds_basenames:
            matched_pairs.append((race_file, odds_file))
    
    print(f"  マッチするペア数: {len(matched_pairs)}")
    
    if matched_pairs:
        print(f"  ペア例:")
        for i, (race, odds) in enumerate(matched_pairs[:3]):
            print(f"    {i+1}. {race} ↔ {odds}")
        if len(matched_pairs) > 3:
            print(f"    ... 他 {len(matched_pairs) - 3} ペア")
    
    # データファイルの内容確認
    if matched_pairs:
        print(f"\n📋 データファイル内容確認:")
        sample_race_file = os.path.join(data_dir, matched_pairs[0][0])
        sample_odds_file = os.path.join(data_dir, matched_pairs[0][1])
        
        try:
            import json
            with open(sample_race_file, 'r', encoding='utf-8') as f:
                race_data = json.load(f)
            with open(sample_odds_file, 'r', encoding='utf-8') as f:
                odds_data = json.load(f)
            
            print(f"  レースデータ構造:")
            print(f"    - キー: {list(race_data.keys())}")
            print(f"    - race_entries: {len(race_data.get('race_entries', []))} エントリー")
            print(f"    - race_records: {len(race_data.get('race_records', []))} レコード")
            
            print(f"  オッズデータ構造:")
            print(f"    - odds_data: {len(odds_data.get('odds_data', []))} オッズ")
            
            # 有効なレースデータの確認
            valid_races = 0
            for record in race_data.get('race_records', []):
                if record.get('arrival') is not None:
                    valid_races += 1
            
            print(f"  有効なレースデータ: {valid_races}/{len(race_data.get('race_records', []))}")
            
            # arrivalデータの詳細確認
            if valid_races > 0:
                print(f"  arrivalデータ例:")
                for i, record in enumerate(race_data.get('race_records', [])[:3]):
                    if record.get('arrival') is not None:
                        print(f"    {i+1}. pit_number: {record['pit_number']}, arrival: {record['arrival']}")
            
            # 3連単の着順確認
            if valid_races >= 3:
                sorted_records = sorted([r for r in race_data.get('race_records', []) if r.get('arrival') is not None], 
                                      key=lambda x: x['arrival'])
                trifecta = tuple(r['pit_number'] for r in sorted_records[:3])
                print(f"  3連単着順: {trifecta}")
            
        except Exception as e:
            print(f"  データファイル読み込みエラー: {e}")
            import traceback
            traceback.print_exc()
    
    print(f"\n✅ 確認完了")

if __name__ == "__main__":
    check_test_data() 