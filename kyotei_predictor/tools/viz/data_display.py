#!/usr/bin/env python3
"""
競艇データ表示ツール - 取得データを見やすい表形式で表示
"""

import pandas as pd
import json
from datetime import datetime

def display_race_data_tables(json_file_path):
    """
    JSONファイルから競艇データを読み込んで表形式で表示
    
    Args:
        json_file_path (str): JSONファイルのパス
    """
    try:
        # JSONファイルを読み込み
        with open(json_file_path, 'r', encoding='utf-8') as f:
            race_data = json.load(f)
        
        print("🏁 競艇レースデータ 表形式表示")
        print("=" * 60)
        
        # 1. レース基本情報
        print(f"\n📋 レース情報")
        race_info_df = pd.DataFrame([{
            '日付': race_data['race_info']['date'],
            '競艇場': race_data['race_info']['stadium'],
            'レース番号': race_data['race_info']['race_number'],
            'タイトル': race_data['race_info']['title'],
            '締切時刻': race_data['race_info']['deadline_at'].replace('T', ' ').replace('+00:00', '') if race_data['race_info']['deadline_at'] else '-',
            '周回数': race_data['race_info']['number_of_laps']
        }])
        print(race_info_df.to_string(index=False))
        
        # 2. 出走表
        print(f"\n🚤 出走表")
        entry_data = []
        for entry in race_data['race_entries']:
            entry_data.append({
                '艇番': entry['pit_number'],
                '選手名': entry['racer']['name'],
                '登録番号': entry['racer']['registration_number'],
                '級別': entry['racer']['current_rating'],
                '全国勝率': entry['performance']['rate_in_all_stadium'],
                '当地勝率': entry['performance']['rate_in_event_going_stadium'],
                'ボート番号': entry['boat']['number'],
                'ボート2連率': f"{entry['boat']['quinella_rate']:.1f}%",
                'モーター番号': entry['motor']['number'],
                'モーター2連率': f"{entry['motor']['quinella_rate']:.1f}%"
            })
        
        entry_df = pd.DataFrame(entry_data)
        print(entry_df.to_string(index=False))
        
        # 3. レース結果（結果データがある場合のみ）
        if 'race_records' in race_data and race_data['race_records']:
            print(f"\n🏁 レース結果")
            result_data = []
            for record in race_data['race_records']:
                result_data.append({
                    '着順': record['arrival'],
                    '艇番': record['pit_number'],
                    'スタートコース': record['start_course'],
                    'スタートタイム': f"{record['start_time']:.2f}秒",
                    '総タイム': f"{record['total_time']:.1f}秒",
                    '決まり手': record['winning_trick'] if record['winning_trick'] else '-'
                })
            
            result_df = pd.DataFrame(result_data)
            result_df = result_df.sort_values('着順')
            print(result_df.to_string(index=False))
            
            # 4. 天候情報
            print(f"\n🌤️ 天候情報")
            weather_data = [{
                '天候': race_data['weather_condition']['weather'],
                '風速': f"{race_data['weather_condition']['wind_velocity']}m/s",
                '風向': f"{race_data['weather_condition']['wind_angle']}度",
                '気温': f"{race_data['weather_condition']['air_temperature']}℃",
                '水温': f"{race_data['weather_condition']['water_temperature']}℃",
                '波高': f"{race_data['weather_condition']['wavelength']}cm"
            }]
            
            weather_df = pd.DataFrame(weather_data)
            print(weather_df.to_string(index=False))
            
            # 5. 払戻情報
            if race_data['payoffs']:
                print(f"\n💰 払戻情報")
                payoff_data = []
                for payoff in race_data['payoffs']:
                    method_name = {
                        'TRIFECTA': '3連単',
                        'TRIO': '3連複',
                        'EXACTA': '2連単',
                        'QUINELLA': '2連複',
                        'WIN': '単勝',
                        'PLACE_SHOW': '複勝'
                    }.get(payoff['betting_method'], payoff['betting_method'])
                    
                    payoff_data.append({
                        '賭式': method_name,
                        '買い目': '-'.join(map(str, payoff['betting_numbers'])),
                        '払戻金': f"{payoff['amount']:,}円"
                    })
                
                payoff_df = pd.DataFrame(payoff_data)
                print(payoff_df.to_string(index=False))
            
            # 6. 統合分析表
            print(f"\n📊 出走表 vs 結果 分析表")
            analysis_data = []
            for entry in race_data['race_entries']:
                pit_number = entry['pit_number']
                
                # 対応する結果を検索
                result = next((r for r in race_data['race_records'] if r['pit_number'] == pit_number), None)
                
                analysis_data.append({
                    '艇番': pit_number,
                    '選手名': entry['racer']['name'],
                    '級別': entry['racer']['current_rating'],
                    '全国勝率': entry['performance']['rate_in_all_stadium'],
                    '当地勝率': entry['performance']['rate_in_event_going_stadium'],
                    'スタートタイム': f"{result['start_time']:.2f}秒" if result else '-',
                    '着順': result['arrival'] if result else '-',
                    '総タイム': f"{result['total_time']:.1f}秒" if result else '-',
                    '決まり手': result['winning_trick'] if result and result['winning_trick'] else '-'
                })
            
            analysis_df = pd.DataFrame(analysis_data)
            # 着順でソート
            if any(isinstance(x, int) for x in analysis_df['着順']):
                analysis_df['着順_sort'] = pd.to_numeric(analysis_df['着順'], errors='coerce')
                analysis_df = analysis_df.sort_values('着順_sort').drop('着順_sort', axis=1)
            
            print(analysis_df.to_string(index=False))
            
            # 7. 簡単な分析
            print(f"\n🎯 レース分析:")
            
            # 最高勝率選手
            max_rate_entry = max(race_data['race_entries'], key=lambda x: x['performance']['rate_in_all_stadium'])
            max_rate_result = next((r for r in race_data['race_records'] if r['pit_number'] == max_rate_entry['pit_number']), None)
            
            print(f"• 最高勝率: {max_rate_entry['racer']['name']}({max_rate_entry['pit_number']}号艇) 勝率{max_rate_entry['performance']['rate_in_all_stadium']} → {max_rate_result['arrival']}着")
            
            # 1着選手
            winner = next((r for r in race_data['race_records'] if r['arrival'] == 1), None)
            if winner:
                winner_entry = next((e for e in race_data['race_entries'] if e['pit_number'] == winner['pit_number']), None)
                print(f"• 1着: {winner_entry['racer']['name']}({winner['pit_number']}号艇) 勝率{winner_entry['performance']['rate_in_all_stadium']} ST{winner['start_time']:.2f}秒")
            
            # 最速スタート
            fastest_start = min(race_data['race_records'], key=lambda x: x['start_time'])
            fastest_entry = next((e for e in race_data['race_entries'] if e['pit_number'] == fastest_start['pit_number']), None)
            print(f"• 最速ST: {fastest_entry['racer']['name']}({fastest_start['pit_number']}号艇) {fastest_start['start_time']:.2f}秒 → {fastest_start['arrival']}着")
            
            # 配当
            if race_data['payoffs']:
                for payoff in race_data['payoffs']:
                    method_name = {
                        'TRIFECTA': '3連単',
                        'TRIO': '3連複',
                        'EXACTA': '2連単',
                        'QUINELLA': '2連複'
                    }.get(payoff['betting_method'], payoff['betting_method'])
                    numbers = '-'.join(map(str, payoff['betting_numbers']))
                    print(f"• 配当: {method_name} {numbers} → {payoff['amount']:,}円")
        
        else:
            print(f"\n⚠️ レース結果データがありません（レース前データのみ）")
        
        print(f"\n✅ データ表示完了")
        
    except Exception as e:
        print(f"❌ エラー: {e}")
        import traceback
        traceback.print_exc()

def display_entry_only(json_file_path):
    """
    出走表のみを表示（レース前用）
    
    Args:
        json_file_path (str): JSONファイルのパス
    """
    try:
        with open(json_file_path, 'r', encoding='utf-8') as f:
            race_data = json.load(f)
        
        print("🚤 出走表データ")
        print("=" * 40)
        
        # レース情報
        print(f"📋 {race_data['race_info']['date']} {race_data['race_info']['stadium']} 第{race_data['race_info']['race_number']}レース")
        print(f"   {race_data['race_info']['title']} 締切: {race_data['race_info']['deadline_at']}")
        
        # 出走表
        entry_data = []
        for entry in race_data['race_entries']:
            entry_data.append({
                '艇番': entry['pit_number'],
                '選手名': entry['racer']['name'],
                '級別': entry['racer']['current_rating'],
                '全国勝率': entry['performance']['rate_in_all_stadium'],
                '当地勝率': entry['performance']['rate_in_event_going_stadium'],
                'ボート': entry['boat']['number'],
                'モーター': entry['motor']['number']
            })
        
        entry_df = pd.DataFrame(entry_data)
        print(f"\n{entry_df.to_string(index=False)}")
        
        # 予想ポイント
        print(f"\n🎯 予想ポイント:")
        max_rate_entry = max(race_data['race_entries'], key=lambda x: x['performance']['rate_in_all_stadium'])
        print(f"• 最高勝率: {max_rate_entry['racer']['name']}({max_rate_entry['pit_number']}号艇) {max_rate_entry['performance']['rate_in_all_stadium']}")
        
        a_class_entries = [e for e in race_data['race_entries'] if e['racer']['current_rating'] in ['A1', 'A2']]
        if a_class_entries:
            print(f"• A級選手: {len(a_class_entries)}名")
            for entry in a_class_entries:
                print(f"  - {entry['racer']['name']}({entry['pit_number']}号艇) {entry['racer']['current_rating']} 勝率{entry['performance']['rate_in_all_stadium']}")
        
    except Exception as e:
        print(f"❌ エラー: {e}")

def main():
    """メイン実行関数"""
    import sys
    
    if len(sys.argv) > 1:
        json_file = sys.argv[1]
    else:
        # デフォルトファイル
        json_file = "complete_race_data_20240615_KIRYU_R1.json"
    
    print(f"📊 データファイル: {json_file}")
    display_race_data_tables(json_file)

if __name__ == "__main__":
    main()