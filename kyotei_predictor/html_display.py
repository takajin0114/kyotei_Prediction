#!/usr/bin/env python3
"""
競艇データHTML表示ツール - 取得データをHTML表形式で表示
"""

import pandas as pd
import json
from datetime import datetime

def generate_html_display(json_file_path, output_html_path=None):
    """
    JSONファイルから競艇データを読み込んでHTML表形式で表示
    
    Args:
        json_file_path (str): JSONファイルのパス
        output_html_path (str): 出力HTMLファイルのパス（Noneの場合は表示のみ）
    
    Returns:
        str: 生成されたHTML
    """
    try:
        # JSONファイルを読み込み
        with open(json_file_path, 'r', encoding='utf-8') as f:
            race_data = json.load(f)
        
        # HTMLの開始
        html_content = """
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>競艇レースデータ</title>
    <style>
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 20px; background-color: #f5f5f5; }
        .container { max-width: 1200px; margin: 0 auto; background-color: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        h1 { color: #2c3e50; text-align: center; border-bottom: 3px solid #3498db; padding-bottom: 10px; }
        h2 { color: #34495e; margin-top: 30px; margin-bottom: 15px; }
        table { width: 100%; border-collapse: collapse; margin-bottom: 20px; }
        th, td { border: 1px solid #ddd; padding: 8px; text-align: center; }
        th { background-color: #3498db; color: white; font-weight: bold; }
        tr:nth-child(even) { background-color: #f2f2f2; }
        tr:hover { background-color: #e8f4fd; }
        .race-info { background-color: #ecf0f1; padding: 15px; border-radius: 5px; margin-bottom: 20px; }
        .analysis { background-color: #e8f5e8; padding: 15px; border-radius: 5px; margin-top: 20px; }
        .highlight { background-color: #fff3cd; font-weight: bold; }
        .winner { background-color: #d4edda; font-weight: bold; }
        .a-class { background-color: #ffeaa7; }
        .b-class { background-color: #fab1a0; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🏁 競艇レースデータ</h1>
"""
        
        # レース基本情報
        race_info = race_data['race_info']
        html_content += f"""
        <div class="race-info">
            <h2>📋 レース情報</h2>
            <p><strong>日付:</strong> {race_info['date']}</p>
            <p><strong>競艇場:</strong> {race_info['stadium']}</p>
            <p><strong>レース番号:</strong> 第{race_info['race_number']}レース</p>
            <p><strong>タイトル:</strong> {race_info['title']}</p>
            <p><strong>締切時刻:</strong> {race_info['deadline_at'].replace('T', ' ').replace('+00:00', '') if race_info['deadline_at'] else '-'}</p>
            <p><strong>周回数:</strong> {race_info['number_of_laps']}周</p>
        </div>
"""
        
        # 出走表
        html_content += """
        <h2>🚤 出走表</h2>
        <table>
            <tr>
                <th>艇番</th>
                <th>選手名</th>
                <th>登録番号</th>
                <th>級別</th>
                <th>全国勝率</th>
                <th>当地勝率</th>
                <th>ボート番号</th>
                <th>ボート2連率</th>
                <th>モーター番号</th>
                <th>モーター2連率</th>
            </tr>
"""
        
        for entry in race_data['race_entries']:
            rating = entry['racer']['current_rating']
            row_class = 'a-class' if rating in ['A1', 'A2'] else 'b-class'
            
            html_content += f"""
            <tr class="{row_class}">
                <td><strong>{entry['pit_number']}</strong></td>
                <td>{entry['racer']['name']}</td>
                <td>{entry['racer']['registration_number']}</td>
                <td><strong>{rating}</strong></td>
                <td>{entry['performance']['rate_in_all_stadium']}</td>
                <td>{entry['performance']['rate_in_event_going_stadium']}</td>
                <td>{entry['boat']['number']}</td>
                <td>{entry['boat']['quinella_rate']:.1f}%</td>
                <td>{entry['motor']['number']}</td>
                <td>{entry['motor']['quinella_rate']:.1f}%</td>
            </tr>
"""
        
        html_content += "</table>"
        
        # レース結果（ある場合のみ）
        if 'race_records' in race_data and race_data['race_records']:
            html_content += """
        <h2>🏁 レース結果</h2>
        <table>
            <tr>
                <th>着順</th>
                <th>艇番</th>
                <th>スタートコース</th>
                <th>スタートタイム</th>
                <th>総タイム</th>
                <th>決まり手</th>
            </tr>
"""
            
            # 着順でソート
            sorted_records = sorted(race_data['race_records'], key=lambda x: x['arrival'])
            
            for record in sorted_records:
                row_class = 'winner' if record['arrival'] == 1 else ''
                
                html_content += f"""
            <tr class="{row_class}">
                <td><strong>{record['arrival']}</strong></td>
                <td><strong>{record['pit_number']}</strong></td>
                <td>{record['start_course']}</td>
                <td>{record['start_time']:.2f}秒</td>
                <td>{record['total_time']:.1f}秒</td>
                <td>{record['winning_trick'] if record['winning_trick'] else '-'}</td>
            </tr>
"""
            
            html_content += "</table>"
            
            # 天候情報
            weather = race_data['weather_condition']
            html_content += f"""
        <h2>🌤️ 天候情報</h2>
        <table>
            <tr>
                <th>天候</th>
                <th>風速</th>
                <th>風向</th>
                <th>気温</th>
                <th>水温</th>
                <th>波高</th>
            </tr>
            <tr>
                <td>{weather['weather']}</td>
                <td>{weather['wind_velocity']}m/s</td>
                <td>{weather['wind_angle']}度</td>
                <td>{weather['air_temperature']}℃</td>
                <td>{weather['water_temperature']}℃</td>
                <td>{weather['wavelength']}cm</td>
            </tr>
        </table>
"""
            
            # 払戻情報
            if race_data['payoffs']:
                html_content += """
        <h2>💰 払戻情報</h2>
        <table>
            <tr>
                <th>賭式</th>
                <th>買い目</th>
                <th>払戻金</th>
            </tr>
"""
                
                for payoff in race_data['payoffs']:
                    method_name = {
                        'TRIFECTA': '3連単',
                        'TRIO': '3連複',
                        'EXACTA': '2連単',
                        'QUINELLA': '2連複',
                        'WIN': '単勝',
                        'PLACE_SHOW': '複勝'
                    }.get(payoff['betting_method'], payoff['betting_method'])
                    
                    html_content += f"""
            <tr class="highlight">
                <td><strong>{method_name}</strong></td>
                <td><strong>{'-'.join(map(str, payoff['betting_numbers']))}</strong></td>
                <td><strong>{payoff['amount']:,}円</strong></td>
            </tr>
"""
                
                html_content += "</table>"
            
            # 分析
            html_content += '<div class="analysis">'
            html_content += '<h2>🎯 レース分析</h2>'
            
            # 最高勝率選手
            max_rate_entry = max(race_data['race_entries'], key=lambda x: x['performance']['rate_in_all_stadium'])
            max_rate_result = next((r for r in race_data['race_records'] if r['pit_number'] == max_rate_entry['pit_number']), None)
            
            html_content += f"<p><strong>最高勝率:</strong> {max_rate_entry['racer']['name']}({max_rate_entry['pit_number']}号艇) 勝率{max_rate_entry['performance']['rate_in_all_stadium']} → {max_rate_result['arrival']}着</p>"
            
            # 1着選手
            winner = next((r for r in race_data['race_records'] if r['arrival'] == 1), None)
            if winner:
                winner_entry = next((e for e in race_data['race_entries'] if e['pit_number'] == winner['pit_number']), None)
                html_content += f"<p><strong>1着:</strong> {winner_entry['racer']['name']}({winner['pit_number']}号艇) 勝率{winner_entry['performance']['rate_in_all_stadium']} ST{winner['start_time']:.2f}秒</p>"
            
            # 最速スタート
            fastest_start = min(race_data['race_records'], key=lambda x: x['start_time'])
            fastest_entry = next((e for e in race_data['race_entries'] if e['pit_number'] == fastest_start['pit_number']), None)
            html_content += f"<p><strong>最速ST:</strong> {fastest_entry['racer']['name']}({fastest_start['pit_number']}号艇) {fastest_start['start_time']:.2f}秒 → {fastest_start['arrival']}着</p>"
            
            html_content += '</div>'
        
        else:
            html_content += '<div class="analysis">'
            html_content += '<h2>🎯 予想ポイント</h2>'
            
            # 最高勝率選手
            max_rate_entry = max(race_data['race_entries'], key=lambda x: x['performance']['rate_in_all_stadium'])
            html_content += f"<p><strong>最高勝率:</strong> {max_rate_entry['racer']['name']}({max_rate_entry['pit_number']}号艇) {max_rate_entry['performance']['rate_in_all_stadium']}</p>"
            
            # A級選手
            a_class_entries = [e for e in race_data['race_entries'] if e['racer']['current_rating'] in ['A1', 'A2']]
            if a_class_entries:
                html_content += f"<p><strong>A級選手:</strong> {len(a_class_entries)}名</p>"
                html_content += "<ul>"
                for entry in a_class_entries:
                    html_content += f"<li>{entry['racer']['name']}({entry['pit_number']}号艇) {entry['racer']['current_rating']} 勝率{entry['performance']['rate_in_all_stadium']}</li>"
                html_content += "</ul>"
            
            html_content += '</div>'
        
        # HTMLの終了
        html_content += """
    </div>
</body>
</html>
"""
        
        # ファイルに保存
        if output_html_path:
            with open(output_html_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            print(f"✅ HTMLファイルを保存しました: {output_html_path}")
        
        return html_content
        
    except Exception as e:
        print(f"❌ エラー: {e}")
        import traceback
        traceback.print_exc()
        return None

def main():
    """メイン実行関数"""
    import sys
    
    if len(sys.argv) > 1:
        json_file = sys.argv[1]
    else:
        json_file = "complete_race_data_20240615_KIRYU_R1.json"
    
    output_html = json_file.replace('.json', '.html')
    
    print(f"📊 データファイル: {json_file}")
    print(f"📄 出力HTMLファイル: {output_html}")
    
    generate_html_display(json_file, output_html)

if __name__ == "__main__":
    main()