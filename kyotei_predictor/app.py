

import sys
from pathlib import Path
from datetime import timedelta

# プロジェクトルートとtoolsディレクトリをパスに追加
project_root = Path(__file__).parent
sys.path.append(str(project_root))
sys.path.append(str(project_root / "tools"))
sys.path.append(str(project_root / "tools" / "fetch"))
sys.path.append(str(project_root / "tools" / "viz"))

from flask import Flask, render_template, request, jsonify
from flask_caching import Cache
import json
import os
from kyotei_predictor.tools.fetch.race_data_fetcher import fetch_race_entry_data
from kyotei_predictor.tools.viz.html_display import generate_html_display as generate_race_html
from kyotei_predictor.errors import APIError, register_error_handlers

app = Flask(__name__, static_folder='static')
register_error_handlers(app)  # エラーハンドラーを登録

# キャッシュ設定
cache = Cache(config={
    'CACHE_TYPE': 'SimpleCache',
    'CACHE_DEFAULT_TIMEOUT': 300  # 5分
})
cache.init_app(app)

SAMPLE_DATA = Path('data/complete_race_data_20240615_KIRYU_R1.json')


@app.route('/')
def index():
    """メインページ"""
    return render_template('index.html')


@app.route('/predictions')
def predictions():
    """予測ページ"""
    return render_template('predictions.html')


@app.route('/outputs/<filename>')
def serve_output_file(filename):
    """outputsディレクトリのファイルを提供"""
    import os
    file_path = os.path.join('outputs', filename)
    if os.path.exists(file_path) and filename.endswith('.json'):
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read(), 200, {'Content-Type': 'application/json'}
    return "File not found", 404


@app.route('/kyotei_predictor/data/raw/<filename>')
def serve_raw_data_file(filename):
    """data/rawディレクトリのファイルを提供"""
    import os
    file_path = os.path.join('kyotei_predictor', 'data', 'raw', filename)
    if os.path.exists(file_path) and filename.endswith('.json'):
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read(), 200, {'Content-Type': 'application/json'}
    return "File not found", 404


@app.route('/api/race_data', methods=['GET'])
@cache.cached(timeout=300, query_string=True)  # 5分間キャッシュ
def get_race_data():
    if SAMPLE_DATA.exists():
        with open(SAMPLE_DATA) as f:
            return jsonify(json.load(f))
    return jsonify({"error": "Sample data not found"}), 404

@app.route('/api/predict', methods=['POST'])
@cache.cached(timeout=60)  # 1分間キャッシュ
def predict():
    data = request.get_json()
    # 簡易的な予測ロジック
    race_entries = data.get('race_entries', [])
    if not race_entries:
        return jsonify({"error": "No race data provided"}), 400

    # 簡易的な予測：勝率が最も高い選手を1着と予測
    predicted_winner = max(race_entries, key=lambda x: x.get('rate_in_all_stadium', 0))
    return jsonify({
        "predicted_winner": predicted_winner,
        "confidence": 0.75
    })

@app.route('/api/races', methods=['GET'])
@cache.cached(timeout=300)  # 5分間キャッシュ
def get_races():
    try:
        # サンプルデータからレース一覧を生成
        sample_files = list(Path('data').glob('complete_race_data_*.json'))
        if not sample_files:
            raise APIError('No race data available', status_code=404)
            
        races = []
        for file in sample_files:
            try:
                with open(file) as f:
                    data = json.load(f)
                    races.append({
                        'date': data['race_info']['date'],
                        'stadium': data['race_info']['stadium'],
                        'race_number': data['race_info']['race_number'],
                        'title': data['race_info']['title']
                    })
            except (json.JSONDecodeError, KeyError) as e:
                raise APIError(f'Invalid data format in {file.name}', status_code=500)
                
        return jsonify(races)
        
    except Exception as e:
        if not isinstance(e, APIError):
            raise APIError(str(e), status_code=500)
        raise

@app.route('/api/weather', methods=['GET'])
@cache.cached(timeout=300, query_string=True)  # 5分間キャッシュ（クエリパラメータ考慮）
def get_weather():
    try:
        # クエリパラメータから日付と競艇場を取得
        date = request.args.get('date')
        stadium = request.args.get('stadium')
        
        if not date or not stadium:
            raise APIError('date and stadium parameters are required', status_code=400)
        
        # 該当するデータファイルを検索
        file_path = Path(f'data/complete_race_data_{date}_{stadium}_R1.json')
        if not file_path.exists():
            raise APIError('Weather data not found', status_code=404)
        
        try:
            with open(file_path) as f:
                data = json.load(f)
                return jsonify(data['weather_condition'])
        except (json.JSONDecodeError, KeyError) as e:
            raise APIError('Invalid weather data format', status_code=500)
            
    except Exception as e:
        if not isinstance(e, APIError):
            raise APIError(str(e), status_code=500)
        raise

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=51932, debug=True)

