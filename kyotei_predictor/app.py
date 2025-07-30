#!/usr/bin/env python3
"""
競艇予測Webアプリケーション
"""

import sys
from pathlib import Path
from datetime import timedelta

# プロジェクトルートを動的に取得
def get_project_root() -> Path:
    """プロジェクトルートを動的に検出"""
    current_file = Path(__file__)
    # app.pyはkyotei_predictorディレクトリ内にあるため、2階層上がる
    project_root = current_file.parent.parent
    
    # Google Colab環境の検出
    if str(project_root).startswith('/content/'):
        return Path('/content/kyotei_Prediction')
    
    return project_root

PROJECT_ROOT = get_project_root()

# プロジェクトルートとtoolsディレクトリをパスに追加
sys.path.append(str(PROJECT_ROOT))
sys.path.append(str(PROJECT_ROOT / "tools"))
sys.path.append(str(PROJECT_ROOT / "tools" / "fetch"))
sys.path.append(str(PROJECT_ROOT / "tools" / "viz"))

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

SAMPLE_DATA = PROJECT_ROOT / 'data' / 'complete_race_data_20240615_KIRYU_R1.json'


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


@app.route('/api/race-data')
@cache.cached(timeout=300)
def get_race_data():
    """レースデータを取得"""
    try:
        # サンプルデータを使用
        if SAMPLE_DATA.exists():
            with open(SAMPLE_DATA, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return jsonify(data)
        else:
            return jsonify({'error': 'サンプルデータが見つかりません'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/predict', methods=['POST'])
def predict():
    """予測を実行"""
    try:
        data = request.get_json()
        race_id = data.get('race_id')
        
        if not race_id:
            return jsonify({'error': 'race_idが必要です'}), 400
        
        # ここで予測ロジックを実装
        # 現在はサンプルデータを返す
        prediction = {
            'race_id': race_id,
            'predictions': [
                {'combination': '1-2-3', 'probability': 0.15},
                {'combination': '2-1-3', 'probability': 0.12},
                {'combination': '3-1-2', 'probability': 0.10}
            ]
        }
        
        return jsonify(prediction)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/races', methods=['GET'])
@cache.cached(timeout=300)  # 5分間キャッシュ
def get_races():
    try:
        # サンプルデータからレース一覧を生成
        sample_files = list(PROJECT_ROOT.glob('data/complete_race_data_*.json'))
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
        file_path = PROJECT_ROOT / f'data/complete_race_data_{date}_{stadium}_R1.json'
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
    app.run(debug=True, host='0.0.0.0', port=5000)

