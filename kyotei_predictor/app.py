#!/usr/bin/env python3
"""
競艇予測Webアプリケーション - Flask メインアプリケーション
"""

from flask import Flask, render_template, jsonify, request
import json
import os
from datetime import datetime
import traceback

# Flaskアプリケーションの初期化
app = Flask(__name__)

# 設定
app.config['DEBUG'] = True
app.config['JSON_AS_ASCII'] = False  # 日本語文字化け防止

class KyoteiPredictorApp:
    """競艇予測アプリケーションのメインクラス"""
    
    def __init__(self, flask_app):
        self.app = flask_app
        self.sample_data_path = "complete_race_data_20240615_KIRYU_R1.json"
        self.setup_routes()
        self.load_sample_data()
    
    def setup_routes(self):
        """ルーティングの設定"""
        self.app.route('/')(self.index)
        self.app.route('/api/race_data')(self.get_race_data)
        self.app.route('/api/predict', methods=['POST'])(self.predict)
        self.app.route('/api/save_prediction', methods=['POST'])(self.save_prediction)
        self.app.route('/api/predictions_history')(self.get_predictions_history)
        
        # エラーハンドラー
        self.app.errorhandler(404)(self.not_found)
        self.app.errorhandler(500)(self.internal_error)
    
    def load_sample_data(self):
        """サンプルデータの読み込み確認"""
        try:
            if os.path.exists(self.sample_data_path):
                with open(self.sample_data_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                print(f"✅ サンプルデータ読み込み成功: {self.sample_data_path}")
                print(f"   レース: {data['race_info']['date']} {data['race_info']['stadium']} 第{data['race_info']['race_number']}レース")
                print(f"   出走艇数: {len(data['race_entries'])}艇")
                return True
            else:
                print(f"❌ サンプルデータが見つかりません: {self.sample_data_path}")
                return False
        except Exception as e:
            print(f"❌ サンプルデータ読み込みエラー: {e}")
            return False
    
    def index(self):
        """メインページの表示"""
        try:
            print("📄 メインページにアクセスされました")
            return render_template('index.html')
        except Exception as e:
            print(f"❌ メインページエラー: {e}")
            # テンプレートが見つからない場合の簡易HTML
            return f"""
            <!DOCTYPE html>
            <html lang="ja">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>競艇予測ツール</title>
                <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
            </head>
            <body>
                <nav class="navbar navbar-expand-lg navbar-dark bg-primary">
                    <div class="container">
                        <a class="navbar-brand" href="#">
                            🚤 競艇予測ツール
                        </a>
                    </div>
                </nav>
                
                <div class="container mt-4">
                    <div class="alert alert-info">
                        <h4>🚧 開発中</h4>
                        <p>Flask アプリケーションが正常に起動しました！</p>
                        <p>現在、テンプレートファイルの実装中です。</p>
                        <hr>
                        <p><strong>API テスト:</strong></p>
                        <ul>
                            <li><a href="/api/race_data" target="_blank">レースデータ取得 API</a></li>
                        </ul>
                    </div>
                    
                    <div class="card">
                        <div class="card-header">
                            <h5>🔧 システム状況</h5>
                        </div>
                        <div class="card-body">
                            <p><strong>Flask:</strong> 正常動作中</p>
                            <p><strong>ポート:</strong> 12000</p>
                            <p><strong>デバッグモード:</strong> 有効</p>
                            <p><strong>サンプルデータ:</strong> {self.sample_data_path}</p>
                        </div>
                    </div>
                </div>
                
                <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
            </body>
            </html>
            """
    
    def get_race_data(self):
        """レースデータの取得API"""
        try:
            print("📊 レースデータ取得APIが呼び出されました")
            
            # サンプルデータの読み込み
            if not os.path.exists(self.sample_data_path):
                raise FileNotFoundError(f"サンプルデータが見つかりません: {self.sample_data_path}")
            
            with open(self.sample_data_path, 'r', encoding='utf-8') as f:
                race_data = json.load(f)
            
            print(f"✅ データ取得成功: {race_data['race_info']['stadium']} 第{race_data['race_info']['race_number']}レース")
            
            return jsonify({
                'status': 'success',
                'data': race_data,
                'timestamp': datetime.now().isoformat(),
                'message': 'レースデータを正常に取得しました'
            })
            
        except FileNotFoundError as e:
            print(f"❌ ファイルエラー: {e}")
            return jsonify({
                'status': 'error',
                'message': f'データファイルが見つかりません: {str(e)}',
                'error_type': 'FileNotFoundError'
            }), 404
            
        except json.JSONDecodeError as e:
            print(f"❌ JSONエラー: {e}")
            return jsonify({
                'status': 'error',
                'message': f'データファイルの形式が正しくありません: {str(e)}',
                'error_type': 'JSONDecodeError'
            }), 400
            
        except Exception as e:
            print(f"❌ 予期しないエラー: {e}")
            print(traceback.format_exc())
            return jsonify({
                'status': 'error',
                'message': f'データ取得中にエラーが発生しました: {str(e)}',
                'error_type': 'UnexpectedError'
            }), 500
    
    def predict(self):
        """予測実行API（基本実装）"""
        try:
            print("🎯 予測APIが呼び出されました")
            
            # リクエストデータの取得
            request_data = request.get_json()
            if not request_data:
                request_data = {}
            
            algorithm = request_data.get('algorithm', 'basic')
            print(f"   アルゴリズム: {algorithm}")
            
            # 現在は基本的なレスポンスを返す（後でprediction_engine.pyと統合）
            return jsonify({
                'status': 'success',
                'message': f'{algorithm}予測を実行しました（実装中）',
                'algorithm': algorithm,
                'timestamp': datetime.now().isoformat(),
                'predictions': [
                    {
                        'pit_number': 1,
                        'racer_name': 'テスト選手1',
                        'prediction_score': 4.5,
                        'predicted_rank': 1
                    },
                    {
                        'pit_number': 2,
                        'racer_name': 'テスト選手2',
                        'prediction_score': 4.2,
                        'predicted_rank': 2
                    }
                ]
            })
            
        except Exception as e:
            print(f"❌ 予測エラー: {e}")
            return jsonify({
                'status': 'error',
                'message': f'予測実行中にエラーが発生しました: {str(e)}',
                'error_type': 'PredictionError'
            }), 500
    
    def save_prediction(self):
        """予想保存API（基本実装）"""
        try:
            print("💾 予想保存APIが呼び出されました")
            
            prediction_data = request.get_json()
            if not prediction_data:
                raise ValueError("保存するデータがありません")
            
            # 現在は基本的なレスポンスを返す（後で実装）
            return jsonify({
                'status': 'success',
                'message': '予想を保存しました（実装中）',
                'prediction_id': 1,
                'timestamp': datetime.now().isoformat()
            })
            
        except Exception as e:
            print(f"❌ 保存エラー: {e}")
            return jsonify({
                'status': 'error',
                'message': f'予想保存中にエラーが発生しました: {str(e)}',
                'error_type': 'SaveError'
            }), 500
    
    def get_predictions_history(self):
        """予想履歴取得API（基本実装）"""
        try:
            print("📚 予想履歴取得APIが呼び出されました")
            
            # 現在は基本的なレスポンスを返す（後で実装）
            return jsonify({
                'status': 'success',
                'history': [],
                'count': 0,
                'message': '履歴機能は実装中です',
                'timestamp': datetime.now().isoformat()
            })
            
        except Exception as e:
            print(f"❌ 履歴取得エラー: {e}")
            return jsonify({
                'status': 'error',
                'message': f'履歴取得中にエラーが発生しました: {str(e)}',
                'error_type': 'HistoryError'
            }), 500
    
    def not_found(self, error):
        """404エラーハンドラー"""
        return jsonify({
            'status': 'error',
            'message': 'ページが見つかりません',
            'error_type': 'NotFound'
        }), 404
    
    def internal_error(self, error):
        """500エラーハンドラー"""
        return jsonify({
            'status': 'error',
            'message': 'サーバー内部エラーが発生しました',
            'error_type': 'InternalServerError'
        }), 500

def main():
    """メイン実行関数"""
    print("🚤 競艇予測Webアプリケーション起動中...")
    print("=" * 50)
    
    # アプリケーションの初期化
    kyotei_app = KyoteiPredictorApp(app)
    
    print("🔧 設定情報:")
    print(f"   ポート: 12000")
    print(f"   デバッグモード: {app.config['DEBUG']}")
    print(f"   サンプルデータ: {kyotei_app.sample_data_path}")
    print()
    
    print("🌐 アクセス情報:")
    print(f"   メインページ: http://localhost:12000")
    print(f"   レースデータAPI: http://localhost:12000/api/race_data")
    print(f"   予測API: http://localhost:12000/api/predict")
    print()
    
    print("📋 利用可能なエンドポイント:")
    print("   GET  /                        - メインページ")
    print("   GET  /api/race_data           - レースデータ取得")
    print("   POST /api/predict             - 予測実行")
    print("   POST /api/save_prediction     - 予想保存")
    print("   GET  /api/predictions_history - 予想履歴取得")
    print()
    
    print("🚀 サーバー起動中...")
    print("   Ctrl+C で停止")
    print("=" * 50)
    
    try:
        # Flaskアプリケーションの起動
        app.run(
            host='0.0.0.0',  # 外部からのアクセスを許可
            port=12000,      # ポート12000で起動
            debug=True,      # デバッグモード有効
            use_reloader=False  # リローダーを無効化（重複起動防止）
        )
    except KeyboardInterrupt:
        print("\n🛑 サーバーを停止しました")
    except Exception as e:
        print(f"\n❌ サーバー起動エラー: {e}")
        print(traceback.format_exc())

if __name__ == '__main__':
    main()