#!/usr/bin/env python3
"""
データ可用性チェッカー

実際に着順情報が抽出できるレース数を確認
"""

import os
import json
import sys
import argparse
from typing import Dict, List, Any, Optional

def extract_actual_result(race_data: Dict[str, Any]) -> Optional[str]:
    """実際の結果を抽出"""
    try:
        # 実際の結果が含まれている場合
        if 'actual_result' in race_data:
            return race_data['actual_result']
        
        # race_recordsから実際の着順を抽出
        race_records = race_data.get('race_records', [])
        if not race_records:
            return None
        
        # arrival（着順）でソート（Noneを除外）
        valid_records = [r for r in race_records if r.get('arrival') is not None]
        if not valid_records:
            return None
            
        sorted_records = sorted(valid_records, key=lambda x: x.get('arrival', 999))
        
        # 上位3着の艇番号を取得
        top_3 = []
        for record in sorted_records:
            if record.get('arrival') is not None and record.get('arrival') <= 3:
                top_3.append(str(record['pit_number']))
        
        if len(top_3) >= 3:
            return '-'.join(top_3)
        return None
        
    except Exception as e:
        return None

def check_data_availability(data_dir: Optional[str] = None):
    """データ可用性チェック"""
    if data_dir is None:
        data_dir = os.environ.get('KYOTEI_RAW_DATA_DIR', os.path.join('kyotei_predictor', 'data', 'raw'))
    
    # レースデータファイル一覧
    race_files = []
    for root, _, files in os.walk(data_dir):
        for file in files:
            if file.startswith('race_data_') and file.endswith('.json'):
                race_files.append(os.path.join(root, file))
    
    print(f"総レースデータファイル数: {len(race_files)}")
    print("=" * 60)
    
    # 着順情報が抽出できるレース数を確認
    valid_races = 0
    invalid_races = 0
    error_details = []
    
    for i, race_file in enumerate(race_files):
        try:
            with open(race_file, 'r', encoding='utf-8') as f:
                race_data = json.load(f)
            
            actual_result = extract_actual_result(race_data)
            if actual_result:
                valid_races += 1
            else:
                invalid_races += 1
                error_details.append(os.path.basename(race_file))
                
        except Exception as e:
            invalid_races += 1
            error_details.append(f"{os.path.basename(race_file)}: {str(e)}")
        
        # 進捗表示
        if (i + 1) % 100 == 0:
            print(f"進捗: {i + 1}/{len(race_files)} レース処理済み")
    
    print("=" * 60)
    print(f"着順情報抽出可能: {valid_races} レース")
    print(f"着順情報抽出不可: {invalid_races} レース")
    if len(race_files) == 0:
        print("利用率: データファイルがありません")
        return
    print(f"利用率: {valid_races / len(race_files) * 100:.1f}%")
    
    if error_details:
        print(f"\n📋 抽出不可レース詳細（最初の10件）:")
        for detail in error_details[:10]:
            print(f"  - {detail}")
        if len(error_details) > 10:
            print(f"  ... 他 {len(error_details) - 10} 件")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="データ可用性チェッカー")
    parser.add_argument('--data-dir', type=str, default=None, help='チェック対象のレースデータディレクトリ')
    args = parser.parse_args()
    check_data_availability(args.data_dir)