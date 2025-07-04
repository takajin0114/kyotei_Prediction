import os
import json
from datetime import datetime

def verify_race_data_integrity():
    """取得データの整合性を検証（簡易版）"""
    data_dir = 'data'
    
    # 取得されたファイルを分析
    race_files = [f for f in os.listdir(data_dir) if f.startswith('race_data_') and f.endswith('.json')]
    odds_files = [f for f in os.listdir(data_dir) if f.startswith('odds_data_') and f.endswith('.json')]
    
    print(f"=== データ整合性検証結果 ===\n")
    print(f"取得されたレースデータファイル数: {len(race_files)}")
    print(f"取得されたオッズデータファイル数: {len(odds_files)}")
    
    # 日付と会場ごとに整理
    data_by_date_venue = {}
    
    for f in race_files:
        parts = f.replace('race_data_', '').replace('.json', '').split('_')
        if len(parts) >= 2:
            date = parts[0]
            venue = parts[1]
            race_num = int(parts[2].replace('R', ''))
            
            if date not in data_by_date_venue:
                data_by_date_venue[date] = {}
            if venue not in data_by_date_venue[date]:
                data_by_date_venue[date][venue] = {'races': [], 'odds': []}
            
            data_by_date_venue[date][venue]['races'].append(race_num)
    
    for f in odds_files:
        parts = f.replace('odds_data_', '').replace('.json', '').split('_')
        if len(parts) >= 2:
            date = parts[0]
            venue = parts[1]
            race_num = int(parts[2].replace('R', ''))
            
            if date in data_by_date_venue and venue in data_by_date_venue[date]:
                data_by_date_venue[date][venue]['odds'].append(race_num)
    
    print("\n=== 日別・会場別データ詳細 ===\n")
    
    missing_odds = []
    data_quality_issues = []
    
    for date in sorted(data_by_date_venue.keys()):
        print(f"📅 {date}")
        
        for venue in sorted(data_by_date_venue[date].keys()):
            fetched_races = sorted(data_by_date_venue[date][venue]['races'])
            fetched_odds = sorted(data_by_date_venue[date][venue]['odds'])
            
            print(f"  🏟️ {venue}")
            print(f"    レース: {fetched_races}")
            print(f"    オッズ: {fetched_odds}")
            
            # 不足しているオッズをチェック
            missing_odds_nums = [r for r in fetched_races if r not in fetched_odds]
            if missing_odds_nums:
                missing_odds.append((date, venue, missing_odds_nums))
                print(f"    ❌ 不足オッズ: {missing_odds_nums}")
            
            # レース番号の連続性チェック
            if len(fetched_races) > 1:
                expected_races = list(range(min(fetched_races), max(fetched_races) + 1))
                missing_race_nums = [r for r in expected_races if r not in fetched_races]
                if missing_race_nums:
                    data_quality_issues.append((date, venue, f"連続性の問題: {missing_race_nums}"))
                    print(f"    ⚠️ 連続性の問題: {missing_race_nums}")
            
            print()
    
    # サマリー
    print("=== 検証サマリー ===")
    print(f"不足オッズ: {len(missing_odds)}件")
    print(f"データ品質問題: {len(data_quality_issues)}件")
    
    if missing_odds:
        print("\n詳細な不足オッズ:")
        for date, venue, races in missing_odds:
            print(f"  {date} {venue}: {races}")
    
    if data_quality_issues:
        print("\nデータ品質問題:")
        for date, venue, issue in data_quality_issues:
            print(f"  {date} {venue}: {issue}")

def check_race_results():
    """レース結果の存在確認"""
    data_dir = 'data'
    
    print("\n=== レース結果確認 ===\n")
    
    race_files = [f for f in os.listdir(data_dir) if f.startswith('race_data_') and f.endswith('.json')]
    
    files_with_results = 0
    files_without_results = 0
    
    for i, filename in enumerate(race_files[:10]):  # 最初の10ファイルをチェック
        try:
            with open(os.path.join(data_dir, filename), 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            race_records = data.get('race_records', [])
            race_info = data.get('race_info', {})
            
            print(f"{i+1}. {filename}")
            print(f"   レース情報: {race_info.get('title', 'N/A')} - {race_info.get('date', 'N/A')}")
            
            if race_records and len(race_records) > 0:
                files_with_results += 1
                print(f"   ✅ レース結果: {len(race_records)}件")
                
                # 結果の詳細を表示
                for record in race_records:
                    if record.get('total_time') and record.get('arrival'):
                        print(f"      艇番{record['pit_number']}: {record['total_time']}秒, {record['arrival']}着")
            else:
                files_without_results += 1
                print(f"   ❌ レース結果なし")
            
            print()
            
        except Exception as e:
            print(f"{i+1}. {filename} - エラー: {str(e)}")
            print()
    
    print(f"結果あり: {files_with_results}件")
    print(f"結果なし: {files_without_results}件")

def check_odds_data_quality():
    """オッズデータの品質確認"""
    data_dir = 'data'
    
    print("\n=== オッズデータ品質確認 ===\n")
    
    odds_files = [f for f in os.listdir(data_dir) if f.startswith('odds_data_') and f.endswith('.json')]
    
    for i, filename in enumerate(odds_files[:5]):  # 最初の5ファイルをチェック
        try:
            with open(os.path.join(data_dir, filename), 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            print(f"{i+1}. {filename}")
            print(f"   オッズ数: {data.get('odds_count', 0)}")
            print(f"   レース日: {data.get('race_date', 'N/A')}")
            print(f"   会場: {data.get('stadium', 'N/A')}")
            print(f"   レース番号: {data.get('race_number', 'N/A')}")
            
            odds_data = data.get('odds_data', [])
            if odds_data:
                print(f"   サンプルオッズ: {odds_data[0] if odds_data else 'なし'}")
            
            print()
            
        except Exception as e:
            print(f"{i+1}. {filename} - エラー: {str(e)}")
            print()

if __name__ == "__main__":
    verify_race_data_integrity()
    check_race_results()
    check_odds_data_quality() 