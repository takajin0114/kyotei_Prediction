#!/usr/bin/env python3
"""
新しいレースデータ取得スクリプト

既存のrace_data_fetcher.pyを使用して、
異なる競艇場・レースのデータを取得し、
予測アルゴリズムの汎用性を検証する。
"""

import json
import os
from datetime import date
from race_data_fetcher import fetch_complete_race_data
from metaboatrace.models.stadium import StadiumTelCode

def fetch_multiple_races():
    """
    複数のレースデータを取得
    """
    print("🚤 複数レースデータ取得開始")
    print("=" * 50)
    
    # 取得対象のレース設定
    race_configs = [
        {
            'date': date(2024, 6, 15),
            'stadium': StadiumTelCode.KIRYU,  # 桐生
            'race_number': 2,
            'description': '桐生競艇場 第2レース'
        },
        {
            'date': date(2024, 6, 15), 
            'stadium': StadiumTelCode.TODA,   # 戸田
            'race_number': 1,
            'description': '戸田競艇場 第1レース'
        },
        {
            'date': date(2024, 6, 15),
            'stadium': StadiumTelCode.EDOGAWA, # 江戸川
            'race_number': 1, 
            'description': '江戸川競艇場 第1レース'
        }
    ]
    
    successful_fetches = []
    failed_fetches = []
    
    for i, config in enumerate(race_configs, 1):
        print(f"\n📊 {i}/{len(race_configs)}: {config['description']}")
        print(f"   日付: {config['date']}")
        print(f"   競艇場: {config['stadium'].name}")
        print(f"   レース: R{config['race_number']}")
        
        try:
            # データ取得実行
            race_data = fetch_complete_race_data(
                config['date'],
                config['stadium'], 
                config['race_number']
            )
            
            if race_data:
                # ファイル名生成
                filename = f"race_data_{config['date']}_{config['stadium'].name}_R{config['race_number']}.json"
                filepath = os.path.join(os.path.dirname(__file__), filename)
                
                # ファイル保存
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(race_data, f, ensure_ascii=False, indent=2)
                
                print(f"   ✅ 取得成功: {filename}")
                print(f"   📋 出走艇数: {len(race_data.get('race_entries', []))}艇")
                
                # レース情報の表示
                if 'race_info' in race_data:
                    info = race_data['race_info']
                    print(f"   🏁 レースタイトル: {info.get('title', 'N/A')}")
                    print(f"   ⏰ 締切時刻: {info.get('deadline_at', 'N/A')}")
                
                # 天候情報の表示
                if 'weather_condition' in race_data:
                    weather = race_data['weather_condition']
                    print(f"   🌤️ 天候: {weather.get('weather', 'N/A')}")
                    print(f"   💨 風速: {weather.get('wind_velocity', 'N/A')}m/s")
                
                successful_fetches.append({
                    'config': config,
                    'filename': filename,
                    'data': race_data
                })
                
            else:
                print(f"   ❌ 取得失敗: データが空です")
                failed_fetches.append(config)
                
        except Exception as e:
            print(f"   ❌ 取得エラー: {str(e)}")
            failed_fetches.append(config)
    
    # 結果サマリー
    print("\n" + "=" * 50)
    print("📊 取得結果サマリー")
    print(f"✅ 成功: {len(successful_fetches)}件")
    print(f"❌ 失敗: {len(failed_fetches)}件")
    
    if successful_fetches:
        print("\n✅ 取得成功したレース:")
        for fetch in successful_fetches:
            config = fetch['config']
            print(f"   - {config['description']} → {fetch['filename']}")
    
    if failed_fetches:
        print("\n❌ 取得失敗したレース:")
        for config in failed_fetches:
            print(f"   - {config['description']}")
    
    return successful_fetches

def analyze_race_data(race_data, description):
    """
    取得したレースデータの分析
    """
    print(f"\n🔍 {description} - データ分析")
    print("-" * 40)
    
    # 基本情報
    entries = race_data.get('race_entries', [])
    print(f"📋 出走艇数: {len(entries)}艇")
    
    # 選手級別分布
    rating_count = {}
    for entry in entries:
        rating = entry.get('racer', {}).get('current_rating', 'Unknown')
        rating_count[rating] = rating_count.get(rating, 0) + 1
    
    print("🏆 級別分布:")
    for rating in ['A1', 'A2', 'B1', 'B2']:
        count = rating_count.get(rating, 0)
        if count > 0:
            print(f"   {rating}級: {count}名")
    
    # 勝率分析
    all_rates = []
    local_rates = []
    for entry in entries:
        perf = entry.get('performance', {})
        all_rate = perf.get('rate_in_all_stadium')
        local_rate = perf.get('rate_in_event_going_stadium')
        
        if all_rate is not None:
            all_rates.append(all_rate)
        if local_rate is not None:
            local_rates.append(local_rate)
    
    if all_rates:
        print(f"📊 全国勝率: 最高{max(all_rates):.2f} 最低{min(all_rates):.2f} 平均{sum(all_rates)/len(all_rates):.2f}")
    if local_rates:
        print(f"📊 当地勝率: 最高{max(local_rates):.2f} 最低{min(local_rates):.2f} 平均{sum(local_rates)/len(local_rates):.2f}")
    
    # レース結果があるかチェック
    if 'race_records' in race_data and race_data['race_records']:
        print("🏁 レース結果: あり")
        records = race_data['race_records']
        winner = next((r for r in records if r.get('arrival') == 1), None)
        if winner:
            pit_num = winner.get('pit_number')
            winner_entry = next((e for e in entries if e.get('pit_number') == pit_num), None)
            if winner_entry:
                racer_name = winner_entry.get('racer', {}).get('name', 'Unknown')
                rating = winner_entry.get('racer', {}).get('current_rating', 'Unknown')
                print(f"🏆 1着: {pit_num}号艇 {racer_name} ({rating}級)")
    else:
        print("🏁 レース結果: なし（レース前データ）")

def main():
    """
    メイン実行関数
    """
    print("🚤 新しいレースデータ取得・分析ツール")
    print("=" * 50)
    
    # 複数レースデータの取得
    successful_fetches = fetch_multiple_races()
    
    # 取得したデータの分析
    if successful_fetches:
        print("\n" + "=" * 50)
        print("🔍 取得データの詳細分析")
        
        for fetch in successful_fetches:
            analyze_race_data(fetch['data'], fetch['config']['description'])
    
    print("\n✅ 処理完了")
    return successful_fetches

if __name__ == "__main__":
    main()