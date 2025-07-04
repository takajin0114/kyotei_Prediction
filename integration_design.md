# 競艇予測Webアプリケーション - 統合設計書

**最終更新日: 2025-07-03**

---

## 本ドキュメントの役割
- システム全体の統合設計・アーキテクチャ・開発フローを記載
- 各機能の連携・開発方針・成功基準を明確化
- 詳細なアルゴリズム・Web要件・タスクは他設計書・NEXT_STEPS.md参照

## 関連ドキュメント
- [README.md](README.md)（全体概要・セットアップ・タスク入口）
- [NEXT_STEPS.md](NEXT_STEPS.md)（今後のタスク・優先度・進捗管理）
- [prediction_algorithm_design.md](prediction_algorithm_design.md)（予測アルゴリズム設計）
- [site_analysis.md](site_analysis.md)（データ取得元サイト分析）
- [web_app_requirements.md](web_app_requirements.md)（Webアプリ要件・UI設計）

---

# 以下、従来の設計書内容（現状維持・必要に応じて最新化）

## 📋 設計概要

### 目的
既存のデータ取得機能とWebアプリケーションの統合設計を策定し、効率的な実装を実現する

### 設計方針
1. **既存資産の最大活用**: `race_data_fetcher.py`, `data_display.py`をそのまま活用
2. **段階的実装**: MVP → 機能拡張の順序で実装
3. **疎結合設計**: 各コンポーネントの独立性を保持
4. **拡張性確保**: 将来的な機能追加に対応

## 🏗️ アーキテクチャ設計

### 1. 全体アーキテクチャ
```
┌─────────────────────────────────────────────────────────┐
│                    Frontend (Browser)                   │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────────────┐ │
│  │ index.html  │ │ style.css   │ │ app.js + Chart.js   │ │
│  └─────────────┘ └─────────────┘ └─────────────────────┘ │
└─────────────────────────────────────────────────────────┘
                              │ HTTP/AJAX
                              ▼
┌─────────────────────────────────────────────────────────┐
│                 Flask Web Application                   │
│  ┌─────────────────────────────────────────────────────┐ │
│  │                   app.py                            │ │
│  │  ┌─────────────┐ ┌─────────────┐ ┌───────────────┐  │ │
│  │  │ Routes      │ │ API Handler │ │ Prediction    │  │ │
│  │  │ Controller  │ │             │ │ Algorithm     │  │ │
│  │  └─────────────┘ └─────────────┘ └───────────────┘  │ │
│  └─────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────┐
│              Existing Data Layer (統合)                 │
│  ┌─────────────────┐ ┌─────────────────┐ ┌─────────────┐ │
│  │race_data_fetcher│ │ data_display    │ │ JSON Files  │ │
│  │.py              │ │ .py             │ │             │ │
│  └─────────────────┘ └─────────────────┘ └─────────────┘ │
└─────────────────────────────────────────────────────────┘
```

### 2. コンポーネント設計

#### 2.1 Flask Application (app.py)
```python
# app.py の構造設計
from flask import Flask, render_template, jsonify, request
from race_data_fetcher import fetch_complete_race_data
from data_display import display_race_data_tables
import json
import os
from datetime import datetime

class KyoteiPredictorApp:
    def __init__(self):
        self.app = Flask(__name__)
        self.setup_routes()
        self.load_sample_data()
    
    def setup_routes(self):
        """ルーティング設定"""
        self.app.route('/')(self.index)
        self.app.route('/api/race_data')(self.get_race_data)
        self.app.route('/api/predict', methods=['POST'])(self.predict)
        self.app.route('/api/save_prediction', methods=['POST'])(self.save_prediction)
        self.app.route('/api/predictions_history')(self.get_predictions_history)
    
    def load_sample_data(self):
        """サンプルデータの読み込み"""
        pass
    
    # 各エンドポイントの実装
    def index(self): pass
    def get_race_data(self): pass
    def predict(self): pass
    def save_prediction(self): pass
    def get_predictions_history(self): pass
```

#### 2.2 データ統合レイヤー
```python
# data_integration.py (新規作成)
class DataIntegration:
    """既存機能とWebアプリの統合を担当"""
    
    def __init__(self):
        self.sample_data_path = "complete_race_data_20240615_KIRYU_R1.json"
        self.predictions_path = "predictions.json"
    
    def get_race_data(self, source="sample"):
        """レースデータ取得の統一インターフェース"""
        if source == "sample":
            return self.load_sample_data()
        elif source == "live":
            return self.fetch_live_data()
    
    def load_sample_data(self):
        """既存サンプルデータの読み込み"""
        with open(self.sample_data_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def fetch_live_data(self):
        """ライブデータ取得（将来的な拡張）"""
        # race_data_fetcher.py を使用
        pass
```

#### 2.3 予測アルゴリズム
```python
# prediction_engine.py (新規作成)
class PredictionEngine:
    """予測アルゴリズムの実装"""
    
    def __init__(self):
        self.algorithms = {
            'basic': self.basic_prediction,
            'advanced': self.advanced_prediction
        }
    
    def basic_prediction(self, race_data):
        """基本予測アルゴリズム"""
        predictions = []
        for entry in race_data['race_entries']:
            score = (
                entry['performance']['rate_in_all_stadium'] * 0.6 +
                entry['performance']['rate_in_event_going_stadium'] * 0.4
            )
            predictions.append({
                'pit_number': entry['pit_number'],
                'racer_name': entry['racer']['name'],
                'prediction_score': round(score, 2),
                'rating': entry['racer']['current_rating']
            })
        
        # スコア順でソート
        predictions.sort(key=lambda x: x['prediction_score'], reverse=True)
        
        # 順位付け
        for i, pred in enumerate(predictions):
            pred['predicted_rank'] = i + 1
        
        return predictions
    
    def advanced_prediction(self, race_data):
        """高度予測アルゴリズム"""
        predictions = []
        weather = race_data.get('weather_condition', {})
        
        for entry in race_data['race_entries']:
            # 基本スコア
            base_score = (
                entry['performance']['rate_in_all_stadium'] * 0.4 +
                entry['performance']['rate_in_event_going_stadium'] * 0.3
            )
            
            # 機材スコア
            boat_score = entry['boat']['quinella_rate'] * 0.001
            motor_score = entry['motor']['quinella_rate'] * 0.001
            equipment_score = (boat_score + motor_score) * 0.2
            
            # 天候補正
            weather_factor = 1.0
            if weather.get('wind_velocity', 0) > 5:
                weather_factor = 0.95  # 強風時は減点
            
            total_score = (base_score + equipment_score) * weather_factor
            
            predictions.append({
                'pit_number': entry['pit_number'],
                'racer_name': entry['racer']['name'],
                'prediction_score': round(total_score, 2),
                'rating': entry['racer']['current_rating'],
                'base_score': round(base_score, 2),
                'equipment_score': round(equipment_score, 2),
                'weather_factor': weather_factor
            })
        
        # スコア順でソート・順位付け
        predictions.sort(key=lambda x: x['prediction_score'], reverse=True)
        for i, pred in enumerate(predictions):
            pred['predicted_rank'] = i + 1
        
        return predictions
```

## 🔌 API設計

### 1. エンドポイント詳細仕様

#### 1.1 GET `/` - メインページ
```python
@app.route('/')
def index():
    """メインページの表示"""
    return render_template('index.html')
```

#### 1.2 GET `/api/race_data` - レースデータ取得
```python
@app.route('/api/race_data')
def get_race_data():
    """レースデータの取得"""
    try:
        data_integration = DataIntegration()
        race_data = data_integration.get_race_data(source="sample")
        
        return jsonify({
            'status': 'success',
            'data': race_data,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500
```

#### 1.3 POST `/api/predict` - 予測実行
```python
@app.route('/api/predict', methods=['POST'])
def predict():
    """予測の実行"""
    try:
        request_data = request.get_json()
        algorithm = request_data.get('algorithm', 'basic')
        
        # データ取得
        data_integration = DataIntegration()
        race_data = data_integration.get_race_data()
        
        # 予測実行
        prediction_engine = PredictionEngine()
        predictions = prediction_engine.algorithms[algorithm](race_data)
        
        result = {
            'status': 'success',
            'predictions': predictions,
            'algorithm': algorithm,
            'timestamp': datetime.now().isoformat(),
            'race_info': race_data['race_info']
        }
        
        return jsonify(result)
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500
```

#### 1.4 POST `/api/save_prediction` - 予想保存
```python
@app.route('/api/save_prediction', methods=['POST'])
def save_prediction():
    """予想の保存"""
    try:
        prediction_data = request.get_json()
        
        # 既存履歴の読み込み
        predictions_file = 'predictions.json'
        if os.path.exists(predictions_file):
            with open(predictions_file, 'r', encoding='utf-8') as f:
                history = json.load(f)
        else:
            history = []
        
        # 新しい予想を追加
        prediction_data['id'] = len(history) + 1
        prediction_data['saved_at'] = datetime.now().isoformat()
        history.append(prediction_data)
        
        # ファイルに保存
        with open(predictions_file, 'w', encoding='utf-8') as f:
            json.dump(history, f, ensure_ascii=False, indent=2)
        
        return jsonify({
            'status': 'success',
            'message': '予想を保存しました',
            'prediction_id': prediction_data['id']
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500
```

#### 1.5 GET `/api/predictions_history` - 予想履歴取得
```python
@app.route('/api/predictions_history')
def get_predictions_history():
    """予想履歴の取得"""
    try:
        predictions_file = 'predictions.json'
        if os.path.exists(predictions_file):
            with open(predictions_file, 'r', encoding='utf-8') as f:
                history = json.load(f)
        else:
            history = []
        
        return jsonify({
            'status': 'success',
            'history': history,
            'count': len(history)
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500
```

## 🎨 フロントエンド設計

### 1. HTMLテンプレート構造
```html
<!-- templates/index.html -->
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>競艇予測ツール</title>
    <!-- Bootstrap 5 CSS -->
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <!-- Font Awesome -->
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <!-- Custom CSS -->
    <link href="{{ url_for('static', filename='css/style.css') }}" rel="stylesheet">
</head>
<body>
    <!-- ナビゲーション -->
    <nav class="navbar navbar-expand-lg navbar-dark bg-primary">
        <div class="container">
            <a class="navbar-brand" href="#">
                <i class="fas fa-ship"></i> 競艇予測ツール
            </a>
        </div>
    </nav>

    <!-- メインコンテンツ -->
    <div class="container mt-4">
        <!-- タブナビゲーション -->
        <ul class="nav nav-tabs" id="mainTabs" role="tablist">
            <li class="nav-item" role="presentation">
                <button class="nav-link active" id="data-tab" data-bs-toggle="tab" data-bs-target="#data-content">
                    <i class="fas fa-table"></i> データ表示
                </button>
            </li>
            <li class="nav-item" role="presentation">
                <button class="nav-link" id="predict-tab" data-bs-toggle="tab" data-bs-target="#predict-content">
                    <i class="fas fa-chart-line"></i> 予測
                </button>
            </li>
            <li class="nav-item" role="presentation">
                <button class="nav-link" id="history-tab" data-bs-toggle="tab" data-bs-target="#history-content">
                    <i class="fas fa-history"></i> 履歴
                </button>
            </li>
            <li class="nav-item" role="presentation">
                <button class="nav-link" id="analysis-tab" data-bs-toggle="tab" data-bs-target="#analysis-content">
                    <i class="fas fa-chart-bar"></i> 分析
                </button>
            </li>
        </ul>

        <!-- タブコンテンツ -->
        <div class="tab-content" id="mainTabContent">
            <!-- データ表示タブ -->
            <div class="tab-pane fade show active" id="data-content">
                <div class="row mt-3">
                    <div class="col-12">
                        <div class="card">
                            <div class="card-header">
                                <h5><i class="fas fa-info-circle"></i> レース情報</h5>
                            </div>
                            <div class="card-body" id="race-info">
                                <!-- レース基本情報 -->
                            </div>
                        </div>
                    </div>
                </div>
                <div class="row mt-3">
                    <div class="col-12">
                        <div class="card">
                            <div class="card-header">
                                <h5><i class="fas fa-users"></i> 出走表</h5>
                            </div>
                            <div class="card-body">
                                <div class="table-responsive" id="race-entries-table">
                                    <!-- 出走表テーブル -->
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
                <div class="row mt-3">
                    <div class="col-md-6">
                        <div class="card">
                            <div class="card-header">
                                <h5><i class="fas fa-cloud-sun"></i> 天候情報</h5>
                            </div>
                            <div class="card-body" id="weather-info">
                                <!-- 天候情報 -->
                            </div>
                        </div>
                    </div>
                    <div class="col-md-6">
                        <div class="card">
                            <div class="card-header">
                                <h5><i class="fas fa-trophy"></i> レース結果</h5>
                            </div>
                            <div class="card-body" id="race-results">
                                <!-- レース結果 -->
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- 予測タブ -->
            <div class="tab-pane fade" id="predict-content">
                <div class="row mt-3">
                    <div class="col-md-4">
                        <div class="card">
                            <div class="card-header">
                                <h5><i class="fas fa-cogs"></i> 予測設定</h5>
                            </div>
                            <div class="card-body">
                                <div class="mb-3">
                                    <label for="algorithm-select" class="form-label">アルゴリズム</label>
                                    <select class="form-select" id="algorithm-select">
                                        <option value="basic">基本予測</option>
                                        <option value="advanced">高度予測</option>
                                    </select>
                                </div>
                                <button class="btn btn-primary w-100" id="execute-prediction">
                                    <i class="fas fa-play"></i> 予測実行
                                </button>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-8">
                        <div class="card">
                            <div class="card-header">
                                <h5><i class="fas fa-list-ol"></i> 予測結果</h5>
                            </div>
                            <div class="card-body">
                                <div id="prediction-results">
                                    <!-- 予測結果 -->
                                </div>
                                <div class="mt-3">
                                    <button class="btn btn-success" id="save-prediction" style="display: none;">
                                        <i class="fas fa-save"></i> 予想を保存
                                    </button>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- 履歴タブ -->
            <div class="tab-pane fade" id="history-content">
                <div class="row mt-3">
                    <div class="col-12">
                        <div class="card">
                            <div class="card-header">
                                <h5><i class="fas fa-history"></i> 予想履歴</h5>
                            </div>
                            <div class="card-body" id="predictions-history">
                                <!-- 予想履歴 -->
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- 分析タブ -->
            <div class="tab-pane fade" id="analysis-content">
                <div class="row mt-3">
                    <div class="col-md-6">
                        <div class="card">
                            <div class="card-header">
                                <h5><i class="fas fa-chart-bar"></i> 勝率比較</h5>
                            </div>
                            <div class="card-body">
                                <canvas id="win-rate-chart"></canvas>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-6">
                        <div class="card">
                            <div class="card-header">
                                <h5><i class="fas fa-chart-line"></i> 機材成績</h5>
                            </div>
                            <div class="card-body">
                                <canvas id="equipment-chart"></canvas>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <!-- Bootstrap 5 JS -->
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    <!-- Chart.js -->
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <!-- Custom JS -->
    <script src="{{ url_for('static', filename='js/app.js') }}"></script>
</body>
</html>
```

### 2. JavaScript設計
```javascript
// static/js/app.js
class KyoteiApp {
    constructor() {
        this.raceData = null;
        this.currentPrediction = null;
        this.charts = {};
        this.init();
    }

    async init() {
        console.log('競艇予測アプリを初期化中...');
        await this.loadRaceData();
        this.setupEventListeners();
        this.displayRaceData();
    }

    async loadRaceData() {
        try {
            const response = await fetch('/api/race_data');
            const result = await response.json();
            
            if (result.status === 'success') {
                this.raceData = result.data;
                console.log('レースデータ読み込み完了:', this.raceData);
            } else {
                throw new Error(result.message);
            }
        } catch (error) {
            console.error('データ読み込みエラー:', error);
            this.showError('データの読み込みに失敗しました');
        }
    }

    setupEventListeners() {
        // 予測実行ボタン
        document.getElementById('execute-prediction').addEventListener('click', () => {
            this.executePrediction();
        });

        // 予想保存ボタン
        document.getElementById('save-prediction').addEventListener('click', () => {
            this.savePrediction();
        });

        // タブ切り替え時の処理
        document.querySelectorAll('[data-bs-toggle="tab"]').forEach(tab => {
            tab.addEventListener('shown.bs.tab', (event) => {
                const targetId = event.target.getAttribute('data-bs-target');
                if (targetId === '#history-content') {
                    this.loadPredictionsHistory();
                } else if (targetId === '#analysis-content') {
                    this.renderCharts();
                }
            });
        });
    }

    displayRaceData() {
        if (!this.raceData) return;

        // レース基本情報
        this.displayRaceInfo();
        
        // 出走表
        this.displayRaceEntries();
        
        // 天候情報
        this.displayWeatherInfo();
        
        // レース結果（ある場合）
        if (this.raceData.race_records) {
            this.displayRaceResults();
        }
    }

    displayRaceInfo() {
        const raceInfo = this.raceData.race_info;
        const html = `
            <div class="row">
                <div class="col-md-3">
                    <strong>開催日:</strong><br>
                    ${raceInfo.date}
                </div>
                <div class="col-md-3">
                    <strong>競艇場:</strong><br>
                    ${raceInfo.stadium}
                </div>
                <div class="col-md-3">
                    <strong>レース:</strong><br>
                    第${raceInfo.race_number}レース
                </div>
                <div class="col-md-3">
                    <strong>タイトル:</strong><br>
                    ${raceInfo.title}
                </div>
            </div>
        `;
        document.getElementById('race-info').innerHTML = html;
    }

    displayRaceEntries() {
        const entries = this.raceData.race_entries;
        let html = `
            <table class="table table-striped table-hover">
                <thead class="table-primary">
                    <tr>
                        <th>艇番</th>
                        <th>選手名</th>
                        <th>級別</th>
                        <th>全国勝率</th>
                        <th>当地勝率</th>
                        <th>ボート</th>
                        <th>モーター</th>
                    </tr>
                </thead>
                <tbody>
        `;

        entries.forEach(entry => {
            const ratingClass = entry.racer.current_rating === 'A1' || entry.racer.current_rating === 'A2' ? 'table-warning' : '';
            html += `
                <tr class="${ratingClass}">
                    <td><strong>${entry.pit_number}</strong></td>
                    <td>${entry.racer.name}</td>
                    <td><span class="badge bg-secondary">${entry.racer.current_rating}</span></td>
                    <td>${entry.performance.rate_in_all_stadium}</td>
                    <td>${entry.performance.rate_in_event_going_stadium}</td>
                    <td>${entry.boat.number} (${entry.boat.quinella_rate.toFixed(1)}%)</td>
                    <td>${entry.motor.number} (${entry.motor.quinella_rate.toFixed(1)}%)</td>
                </tr>
            `;
        });

        html += '</tbody></table>';
        document.getElementById('race-entries-table').innerHTML = html;
    }

    displayWeatherInfo() {
        if (!this.raceData.weather_condition) return;

        const weather = this.raceData.weather_condition;
        const html = `
            <div class="row">
                <div class="col-6">
                    <strong>天候:</strong> ${weather.weather}<br>
                    <strong>風速:</strong> ${weather.wind_velocity}m/s<br>
                    <strong>風向:</strong> ${weather.wind_angle}度
                </div>
                <div class="col-6">
                    <strong>気温:</strong> ${weather.air_temperature}℃<br>
                    <strong>水温:</strong> ${weather.water_temperature}℃<br>
                    <strong>波高:</strong> ${weather.wavelength}cm
                </div>
            </div>
        `;
        document.getElementById('weather-info').innerHTML = html;
    }

    displayRaceResults() {
        const results = this.raceData.race_records;
        let html = `
            <table class="table table-sm">
                <thead>
                    <tr>
                        <th>着順</th>
                        <th>艇番</th>
                        <th>ST</th>
                        <th>タイム</th>
                    </tr>
                </thead>
                <tbody>
        `;

        results.sort((a, b) => a.arrival - b.arrival).forEach(result => {
            const rowClass = result.arrival === 1 ? 'table-success' : '';
            html += `
                <tr class="${rowClass}">
                    <td><strong>${result.arrival}</strong></td>
                    <td>${result.pit_number}</td>
                    <td>${result.start_time.toFixed(2)}</td>
                    <td>${result.total_time.toFixed(1)}</td>
                </tr>
            `;
        });

        html += '</tbody></table>';
        document.getElementById('race-results').innerHTML = html;
    }

    async executePrediction() {
        try {
            const algorithm = document.getElementById('algorithm-select').value;
            
            // ローディング表示
            document.getElementById('prediction-results').innerHTML = `
                <div class="text-center">
                    <div class="spinner-border" role="status">
                        <span class="visually-hidden">予測中...</span>
                    </div>
                    <p class="mt-2">予測を実行中...</p>
                </div>
            `;

            const response = await fetch('/api/predict', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ algorithm: algorithm })
            });

            const result = await response.json();

            if (result.status === 'success') {
                this.currentPrediction = result;
                this.displayPredictionResults(result);
                document.getElementById('save-prediction').style.display = 'block';
            } else {
                throw new Error(result.message);
            }
        } catch (error) {
            console.error('予測エラー:', error);
            this.showError('予測の実行に失敗しました');
        }
    }

    displayPredictionResults(result) {
        const predictions = result.predictions;
        let html = `
            <div class="mb-3">
                <span class="badge bg-info">アルゴリズム: ${result.algorithm}</span>
                <span class="badge bg-secondary">実行時刻: ${new Date(result.timestamp).toLocaleString()}</span>
            </div>
            <table class="table table-striped">
                <thead class="table-primary">
                    <tr>
                        <th>予想順位</th>
                        <th>艇番</th>
                        <th>選手名</th>
                        <th>級別</th>
                        <th>予測スコア</th>
                    </tr>
                </thead>
                <tbody>
        `;

        predictions.forEach((pred, index) => {
            const rankClass = index < 3 ? 'table-warning' : '';
            html += `
                <tr class="${rankClass}">
                    <td><strong>${pred.predicted_rank}</strong></td>
                    <td>${pred.pit_number}</td>
                    <td>${pred.racer_name}</td>
                    <td><span class="badge bg-secondary">${pred.rating}</span></td>
                    <td>${pred.prediction_score}</td>
                </tr>
            `;
        });

        html += '</tbody></table>';
        document.getElementById('prediction-results').innerHTML = html;
    }

    async savePrediction() {
        if (!this.currentPrediction) return;

        try {
            const memo = prompt('メモを入力してください（任意）:');
            
            const saveData = {
                ...this.currentPrediction,
                memo: memo || '',
                race_info: this.raceData.race_info
            };

            const response = await fetch('/api/save_prediction', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(saveData)
            });

            const result = await response.json();

            if (result.status === 'success') {
                alert('予想を保存しました！');
                document.getElementById('save-prediction').style.display = 'none';
            } else {
                throw new Error(result.message);
            }
        } catch (error) {
            console.error('保存エラー:', error);
            this.showError('予想の保存に失敗しました');
        }
    }

    async loadPredictionsHistory() {
        try {
            const response = await fetch('/api/predictions_history');
            const result = await response.json();

            if (result.status === 'success') {
                this.displayPredictionsHistory(result.history);
            } else {
                throw new Error(result.message);
            }
        } catch (error) {
            console.error('履歴読み込みエラー:', error);
            this.showError('履歴の読み込みに失敗しました');
        }
    }

    displayPredictionsHistory(history) {
        if (history.length === 0) {
            document.getElementById('predictions-history').innerHTML = `
                <div class="text-center text-muted">
                    <i class="fas fa-inbox fa-3x mb-3"></i>
                    <p>まだ予想履歴がありません</p>
                </div>
            `;
            return;
        }

        let html = '';
        history.reverse().forEach(prediction => {
            html += `
                <div class="card mb-3">
                    <div class="card-header">
                        <div class="row">
                            <div class="col-md-6">
                                <strong>${prediction.race_info.date} ${prediction.race_info.stadium} 第${prediction.race_info.race_number}レース</strong>
                            </div>
                            <div class="col-md-6 text-end">
                                <small class="text-muted">${new Date(prediction.saved_at).toLocaleString()}</small>
                            </div>
                        </div>
                    </div>
                    <div class="card-body">
                        <div class="row">
                            <div class="col-md-8">
                                <strong>予想:</strong> 
                                ${prediction.predictions.slice(0, 3).map(p => `${p.predicted_rank}位: ${p.pit_number}号艇 ${p.racer_name}`).join(', ')}
                            </div>
                            <div class="col-md-4">
                                <span class="badge bg-info">${prediction.algorithm}</span>
                            </div>
                        </div>
                        ${prediction.memo ? `<div class="mt-2"><strong>メモ:</strong> ${prediction.memo}</div>` : ''}
                    </div>
                </div>
            `;
        });

        document.getElementById('predictions-history').innerHTML = html;
    }

    renderCharts() {
        if (!this.raceData) return;

        // 勝率比較チャート
        this.renderWinRateChart();
        
        // 機材成績チャート
        this.renderEquipmentChart();
    }

    renderWinRateChart() {
        const ctx = document.getElementById('win-rate-chart').getContext('2d');
        
        if (this.charts.winRate) {
            this.charts.winRate.destroy();
        }

        const entries = this.raceData.race_entries;
        const labels = entries.map(e => `${e.pit_number}号艇\n${e.racer.name}`);
        const allStadiumRates = entries.map(e => e.performance.rate_in_all_stadium);
        const localRates = entries.map(e => e.performance.rate_in_event_going_stadium);

        this.charts.winRate = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [
                    {
                        label: '全国勝率',
                        data: allStadiumRates,
                        backgroundColor: 'rgba(52, 152, 219, 0.8)',
                        borderColor: 'rgba(52, 152, 219, 1)',
                        borderWidth: 1
                    },
                    {
                        label: '当地勝率',
                        data: localRates,
                        backgroundColor: 'rgba(46, 204, 113, 0.8)',
                        borderColor: 'rgba(46, 204, 113, 1)',
                        borderWidth: 1
                    }
                ]
            },
            options: {
                responsive: true,
                scales: {
                    y: {
                        beginAtZero: true,
                        max: 8
                    }
                }
            }
        });
    }

    renderEquipmentChart() {
        const ctx = document.getElementById('equipment-chart').getContext('2d');
        
        if (this.charts.equipment) {
            this.charts.equipment.destroy();
        }

        const entries = this.raceData.race_entries;
        const labels = entries.map(e => `${e.pit_number}号艇`);
        const boatRates = entries.map(e => e.boat.quinella_rate);
        const motorRates = entries.map(e => e.motor.quinella_rate);

        this.charts.equipment = new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [
                    {
                        label: 'ボート2連率',
                        data: boatRates,
                        borderColor: 'rgba(231, 76, 60, 1)',
                        backgroundColor: 'rgba(231, 76, 60, 0.1)',
                        tension: 0.4
                    },
                    {
                        label: 'モーター2連率',
                        data: motorRates,
                        borderColor: 'rgba(155, 89, 182, 1)',
                        backgroundColor: 'rgba(155, 89, 182, 0.1)',
                        tension: 0.4
                    }
                ]
            },
            options: {
                responsive: true,
                scales: {
                    y: {
                        beginAtZero: true,
                        max: 60
                    }
                }
            }
        });
    }

    showError(message) {
        alert(`エラー: ${message}`);
    }
}

// アプリケーション初期化
document.addEventListener('DOMContentLoaded', () => {
    new KyoteiApp();
});
```

### 3. CSS設計
```css
/* static/css/style.css */

/* カスタムスタイル */
:root {
    --primary-color: #3498db;
    --secondary-color: #2c3e50;
    --success-color: #27ae60;
    --warning-color: #f39c12;
    --danger-color: #e74c3c;
}

body {
    background-color: #f8f9fa;
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
}

.navbar-brand {
    font-weight: bold;
}

.card {
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    border: none;
    margin-bottom: 1rem;
}

.card-header {
    background-color: var(--primary-color);
    color: white;
    font-weight: bold;
}

.table-responsive {
    border-radius: 0.375rem;
}

.table th {
    border-top: none;
    font-weight: 600;
}

.nav-tabs .nav-link {
    color: var(--secondary-color);
    border: none;
    border-bottom: 3px solid transparent;
}

.nav-tabs .nav-link.active {
    background-color: transparent;
    border-bottom-color: var(--primary-color);
    color: var(--primary-color);
    font-weight: bold;
}

.nav-tabs .nav-link:hover {
    border-bottom-color: var(--primary-color);
    color: var(--primary-color);
}

/* 級別による色分け */
.table-warning {
    background-color: rgba(255, 193, 7, 0.1) !important;
}

/* 予測結果のスタイル */
.prediction-rank-1 {
    background-color: rgba(255, 215, 0, 0.3);
}

.prediction-rank-2 {
    background-color: rgba(192, 192, 192, 0.3);
}

.prediction-rank-3 {
    background-color: rgba(205, 127, 50, 0.3);
}

/* レスポンシブ対応 */
@media (max-width: 768px) {
    .container {
        padding-left: 10px;
        padding-right: 10px;
    }
    
    .card-body {
        padding: 1rem 0.5rem;
    }
    
    .table-responsive {
        font-size: 0.875rem;
    }
    
    .nav-tabs .nav-link {
        padding: 0.5rem 0.75rem;
        font-size: 0.875rem;
    }
}

/* ローディングアニメーション */
.spinner-border {
    color: var(--primary-color);
}

/* チャートコンテナ */
canvas {
    max-height: 400px;
}

/* エラーメッセージ */
.alert-custom {
    border-radius: 0.5rem;
    border: none;
}

/* ボタンスタイル */
.btn-primary {
    background-color: var(--primary-color);
    border-color: var(--primary-color);
}

.btn-primary:hover {
    background-color: #2980b9;
    border-color: #2980b9;
}

/* バッジスタイル */
.badge {
    font-size: 0.75em;
}

/* 履歴カードのスタイル */
.predictions-history .card {
    transition: transform 0.2s;
}

.predictions-history .card:hover {
    transform: translateY(-2px);
}
```

## 📁 ファイル構成

### 実装後のディレクトリ構成
```
kyotei_predictor/
├── app.py                              # Flask メインアプリケーション
├── data_integration.py                 # データ統合レイヤー
├── prediction_engine.py                # 予測アルゴリズム
├── requirements.txt                    # 依存関係
├── predictions.json                    # 予想履歴（実行時生成）
├── templates/
│   └── index.html                     # HTMLテンプレート
├── static/
│   ├── css/
│   │   └── style.css                  # カスタムスタイル
│   └── js/
│       └── app.js                     # JavaScript機能
├── race_data_fetcher.py               # 既存: データ取得機能
├── data_display.py                    # 既存: 表示機能
├── html_display.py                    # 既存: HTML表示
├── complete_race_data_20240615_KIRYU_R1.json  # 既存: サンプルデータ
└── test_data_fetch.py                 # 既存: テストスクリプト
```

## 🔄 実装順序

### Day 2: Flask Webアプリケーション実装
1. **app.py** - 基本構造とルーティング
2. **data_integration.py** - データ統合レイヤー
3. **prediction_engine.py** - 予測アルゴリズム
4. **基本動作確認** - メインページ表示とAPI動作

### Day 3: フロントエンド実装
1. **templates/index.html** - HTMLテンプレート
2. **static/css/style.css** - スタイルシート
3. **static/js/app.js** - JavaScript機能
4. **統合テスト** - フロントエンド・バックエンド連携

### Day 4: データ統合・機能実装
1. **既存機能統合** - race_data_fetcher.pyとの連携
2. **予測機能実装** - アルゴリズムの実装と最適化
3. **履歴管理** - 予想保存・履歴表示機能
4. **エラーハンドリング** - 例外処理の実装

### Day 5: テスト・最適化
1. **動作確認** - 全機能のテスト
2. **レスポンシブ対応** - モバイル・タブレット対応
3. **パフォーマンス最適化** - 読み込み速度の改善
4. **ドキュメント更新** - README.mdの更新

## ✅ 成功基準

### 技術的成功基準
1. ✅ **Flask起動**: `python app.py` でエラーなく起動
2. ✅ **ページ表示**: `http://localhost:12000` でメインページ表示
3. ✅ **API動作**: 全5つのエンドポイントが正常動作
4. ✅ **データ表示**: 既存JSONデータが表形式で表示
5. ✅ **予測実行**: 基本・高度予測が実行可能
6. ✅ **履歴管理**: 予想保存・履歴表示が動作

### ユーザビリティ成功基準
1. ✅ **直感的操作**: タブ切り替えで機能にアクセス可能
2. ✅ **レスポンシブ**: PC・タブレット・スマホで適切表示
3. ✅ **エラー処理**: 適切なエラーメッセージ表示
4. ✅ **パフォーマンス**: 3秒以内でページ読み込み完了

---

**作成日**: 2025-06-13  
**バージョン**: 1.0  
**ステータス**: Day 1 統合設計完了