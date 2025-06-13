#!/usr/bin/env python3
"""
競艇予測Webアプリケーション - Flask メインアプリケーション
"""

from flask import Flask, render_template, jsonify, request
import json
import os
from datetime import datetime
import traceback

# データ統合レイヤーのインポート
from data_integration import DataIntegration
from prediction_engine import PredictionEngine

# Flaskアプリケーションの初期化
app = Flask(__name__)

# 設定
app.config['DEBUG'] = True
app.config['JSON_AS_ASCII'] = False  # 日本語文字化け防止

class KyoteiPredictorApp:
    """競艇予測アプリケーションのメインクラス"""
    
    def __init__(self, flask_app):
        self.app = flask_app
        self.data_integration = DataIntegration()  # データ統合レイヤーの初期化
        self.prediction_engine = PredictionEngine()  # 予測エンジンの初期化
        self.setup_routes()
        self.test_data_integration()
    
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
    
    def test_data_integration(self):
        """データ統合レイヤーのテスト"""
        try:
            print("🔧 データ統合レイヤーとの連携テスト開始")
            
            # サンプルデータ取得テスト
            race_data = self.data_integration.get_race_data(source="sample")
            
            print(f"✅ データ統合レイヤー連携成功")
            print(f"   レース: {race_data['race_info']['date']} {race_data['race_info']['stadium']} 第{race_data['race_info']['race_number']}レース")
            print(f"   出走艇数: {len(race_data['race_entries'])}艇")
            
            # 要約データ作成テスト
            entries_summary = self.data_integration.get_race_entries_summary(race_data)
            results_summary = self.data_integration.get_race_results_summary(race_data)
            weather_summary = self.data_integration.get_weather_summary(race_data)
            
            print(f"   要約データ: 出走表{len(entries_summary)}艇, 結果{len(results_summary) if results_summary else 0}艇, 天候{'あり' if weather_summary else 'なし'}")
            
            return True
            
        except Exception as e:
            print(f"❌ データ統合レイヤー連携エラー: {e}")
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
                            <p><strong>データ統合:</strong> 有効</p>
                        </div>
                    </div>
                </div>
                
                <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
            </body>
            </html>
            """
    
    def get_race_data(self):
        """レースデータの取得API（データ統合レイヤー使用）"""
        try:
            print("📊 レースデータ取得APIが呼び出されました")
            
            # データ統合レイヤーを使用してデータ取得
            race_data = self.data_integration.get_race_data(source="sample")
            
            # 要約データも作成
            entries_summary = self.data_integration.get_race_entries_summary(race_data)
            results_summary = self.data_integration.get_race_results_summary(race_data)
            weather_summary = self.data_integration.get_weather_summary(race_data)
            
            print(f"✅ データ取得成功: {race_data['race_info']['stadium']} 第{race_data['race_info']['race_number']}レース")
            
            # レスポンスデータの構築
            response_data = {
                'status': 'success',
                'data': race_data,
                'summary': {
                    'entries': entries_summary,
                    'results': results_summary,
                    'weather': weather_summary
                },
                'timestamp': datetime.now().isoformat(),
                'message': 'レースデータを正常に取得しました',
                'source': 'sample'
            }
            
            return jsonify(response_data)
            
        except Exception as e:
            print(f"❌ データ取得エラー: {e}")
            print(traceback.format_exc())
            return jsonify({
                'status': 'error',
                'message': f'データ取得中にエラーが発生しました: {str(e)}',
                'error_type': type(e).__name__
            }), 500
    
    def predict(self):
        """予測実行API（予測エンジン統合版）"""
        try:
            print("🎯 予測APIが呼び出されました")
            
            # リクエストデータの取得
            request_data = request.get_json()
            if not request_data:
                request_data = {}
            
            algorithm = request_data.get('algorithm', 'basic')
            print(f"   アルゴリズム: {algorithm}")
            
            # レースデータの取得
            race_data = self.data_integration.get_race_data('sample')
            if not race_data:
                raise ValueError("レースデータの取得に失敗しました")
            
            # 予測エンジンで予測実行
            prediction_result = self.prediction_engine.predict(race_data, algorithm)
            
            # レスポンスの構築
            response = {
                'status': 'success',
                'message': f'{algorithm}アルゴリズムによる予測を実行しました',
                'prediction_result': prediction_result,
                'timestamp': datetime.now().isoformat()
            }
            
            print(f"✅ 予測完了: {algorithm}アルゴリズム")
            print(f"   実行時間: {prediction_result['execution_time']}秒")
            print(f"   本命: {prediction_result['summary']['favorite']['racer_name']}")
            
            return jsonify(response)
            
        except Exception as e:
            print(f"❌ 予測エラー: {e}")
            print(traceback.format_exc())
            return jsonify({
                'status': 'error',
                'message': f'予測実行中にエラーが発生しました: {str(e)}',
                'error_type': type(e).__name__
            }), 500
    
    def save_prediction(self):
        """予想保存API（データ統合レイヤー使用）"""
        try:
            print("💾 予想保存APIが呼び出されました")
            
            prediction_data = request.get_json()
            if not prediction_data:
                raise ValueError("保存するデータがありません")
            
            # データ統合レイヤーを使用して保存
            save_result = self.data_integration.save_prediction_data(prediction_data)
            
            print(f"✅ 予想保存成功: ID={save_result['prediction_id']}")
            
            return jsonify({
                'status': 'success',
                'message': '予想を正常に保存しました',
                'prediction_id': save_result['prediction_id'],
                'saved_at': save_result['saved_at'],
                'timestamp': datetime.now().isoformat()
            })
            
        except Exception as e:
            print(f"❌ 保存エラー: {e}")
            return jsonify({
                'status': 'error',
                'message': f'予想保存中にエラーが発生しました: {str(e)}',
                'error_type': type(e).__name__
            }), 500
    
    def get_predictions_history(self):
        """予想履歴取得API（データ統合レイヤー使用）"""
        try:
            print("📚 予想履歴取得APIが呼び出されました")
            
            # データ統合レイヤーを使用して履歴取得
            history = self.data_integration.get_predictions_history()
            
            print(f"✅ 履歴取得成功: {len(history)}件")
            
            return jsonify({
                'status': 'success',
                'history': history,
                'count': len(history),
                'message': f'予想履歴を正常に取得しました（{len(history)}件）',
                'timestamp': datetime.now().isoformat()
            })
            
        except Exception as e:
            print(f"❌ 履歴取得エラー: {e}")
            return jsonify({
                'status': 'error',
                'message': f'履歴取得中にエラーが発生しました: {str(e)}',
                'error_type': type(e).__name__
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
    print(f"   データ統合レイヤー: 有効")
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