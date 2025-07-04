import os
import json
import requests
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
import time

def fetch_actual_race_schedule(venue_code, date_str):
    """実際のレーススケジュールを取得"""
    try:
        # 公式サイトのレース一覧ページを取得
        url = f"https://boatrace.jp/owpc/pc/race/racelist?jcd={venue_code}&hd={date_str}"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # レース一覧の存在確認
        race_list = soup.find('div', class_='raceList')
        if not race_list:
            return []
        
        # レース番号を抽出
        races = []
        race_items = race_list.find_all('div', class_='raceList_item')
        for item in race_items:
            race_link = item.find('a')
            if race_link:
                href = race_link.get('href', '')
                if href and 'rno=' in href:
                    try:
                        race_number = href.split('rno=')[1].split('&')[0]
                        races.append(int(race_number))
                    except (IndexError, ValueError):
                        continue
        
        return sorted(races)
    
    except Exception as e:
        print(f"エラー: {venue_code} {date_str} - {str(e)}")
        return []

def verify_race_data_integrity():
    """取得データの整合性を検証"""
    data_dir = 'data'
    
    # 取得されたファイルを分析
    race_files = [f for f in os.listdir(data_dir) if f.startswith('race_data_') and f.endswith('.json')]
    odds_files = [f for f in os.listdir(data_dir) if f.startswith('odds_data_') and f.endswith('.json')]
    
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
    
    # 会場コードマッピング
    venue_codes = {
        'KIRYU': '01',
        'TODA': '02',
        'EDOGAWA': '03'
    }
    
    print("=== データ整合性検証結果 ===\n")
    
    missing_races = []
    missing_odds = []
    extra_races = []
    
    for date in sorted(data_by_date_venue.keys()):
        print(f"📅 {date}")
        
        for venue in sorted(data_by_date_venue[date].keys()):
            venue_code = venue_codes.get(venue, '')
            if not venue_code:
                continue
                
            print(f"  🏟️ {venue}")
            
            # 実際のレーススケジュールを取得
            actual_races = fetch_actual_race_schedule(venue_code, date.replace('-', ''))
            time.sleep(1)  # レート制限対策
            
            # 取得されたデータ
            fetched_races = sorted(data_by_date_venue[date][venue]['races'])
            fetched_odds = sorted(data_by_date_venue[date][venue]['odds'])
            
            print(f"    実際のレース: {actual_races}")
            print(f"    取得レース: {fetched_races}")
            print(f"    取得オッズ: {fetched_odds}")
            
            # 不足しているレースをチェック
            missing_race_nums = [r for r in actual_races if r not in fetched_races]
            if missing_race_nums:
                missing_races.append((date, venue, missing_race_nums))
                print(f"    ❌ 不足レース: {missing_race_nums}")
            
            # 不足しているオッズをチェック
            missing_odds_nums = [r for r in fetched_races if r not in fetched_odds]
            if missing_odds_nums:
                missing_odds.append((date, venue, missing_odds_nums))
                print(f"    ❌ 不足オッズ: {missing_odds_nums}")
            
            # 余分なレースをチェック（実際には開催されていないのに取得されている）
            extra_race_nums = [r for r in fetched_races if r not in actual_races]
            if extra_race_nums:
                extra_races.append((date, venue, extra_race_nums))
                print(f"    ⚠️ 余分レース: {extra_race_nums}")
            
            print()
    
    # サマリー
    print("=== 検証サマリー ===")
    print(f"不足レース: {len(missing_races)}件")
    print(f"不足オッズ: {len(missing_odds)}件")
    print(f"余分レース: {len(extra_races)}件")
    
    if missing_races:
        print("\n詳細な不足レース:")
        for date, venue, races in missing_races:
            print(f"  {date} {venue}: {races}")
    
    if missing_odds:
        print("\n詳細な不足オッズ:")
        for date, venue, races in missing_odds:
            print(f"  {date} {venue}: {races}")
    
    if extra_races:
        print("\n詳細な余分レース:")
        for date, venue, races in extra_races:
            print(f"  {date} {venue}: {races}")

def check_data_quality():
    """データ品質の詳細チェック"""
    data_dir = 'data'
    
    print("\n=== データ品質チェック ===")
    
    # サンプルファイルで詳細チェック
    race_files = [f for f in os.listdir(data_dir) if f.startswith('race_data_') and f.endswith('.json')]
    
    if race_files:
        sample_file = race_files[0]
        with open(os.path.join(data_dir, sample_file), 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        print(f"サンプルファイル: {sample_file}")
        print(f"レース情報: {data.get('race_info', {})}")
        
        # レース結果の存在確認
        race_records = data.get('race_records', [])
        if race_records:
            print(f"レース結果: {len(race_records)}件")
            for record in race_records:
                if record.get('total_time') and record.get('arrival'):
                    print(f"  艇番{record['pit_number']}: {record['total_time']}秒, {record['arrival']}着")
        else:
            print("⚠️ レース結果が存在しません")

if __name__ == "__main__":
    verify_race_data_integrity()
    check_data_quality() 