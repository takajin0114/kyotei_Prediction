#!/usr/bin/env python3
"""
テストサーバー
"""

import os
import sys
import json
import logging
import signal
import subprocess
from pathlib import Path
from typing import Dict, List, Optional

# プロジェクトルートを動的に取得
def get_project_root() -> Path:
    """プロジェクトルートを動的に検出"""
    current_file = Path(__file__)
    project_root = current_file.parent.parent.parent
    
    # Google Colab環境の検出
    if str(project_root).startswith('/content/'):
        return Path('/content/kyotei_Prediction')
    
    return project_root

PROJECT_ROOT = get_project_root()

# プロジェクトルートをパスに追加
sys.path.append(str(PROJECT_ROOT))

class TestServer:
    """テストサーバークラス"""
    
    def __init__(self):
        """初期化"""
        self.project_root = PROJECT_ROOT
        self.log_dir = self.project_root / "kyotei_predictor" / "logs"
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # ログ設定
        log_file = self.log_dir / "test_server.log"
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
        self.logger.info("TestServer初期化完了")
    
    def start_test_server(self, port: int = 5000) -> bool:
        """
        テストサーバーを開始
        
        Args:
            port: ポート番号
            
        Returns:
            開始成功かどうか
        """
        try:
            self.logger.info(f"テストサーバー開始: ポート {port}")
            
            # Flaskアプリケーションをインポート
            from kyotei_predictor.app import app
            
            # サーバー開始
            app.run(host='0.0.0.0', port=port, debug=True)
            
            return True
            
        except Exception as e:
            self.logger.error(f"テストサーバー開始エラー: {e}")
            return False
    
    def run_tests(self) -> Dict:
        """
        テストを実行
        
        Returns:
            テスト結果
        """
        try:
            self.logger.info("テスト実行開始")
            
            results = {
                'timestamp': datetime.now().isoformat(),
                'tests': [],
                'passed': 0,
                'failed': 0,
                'total': 0
            }
            
            # テストケース実行
            self.test_basic_functionality(results)
            self.test_api_endpoints(results)
            self.test_data_integration(results)
            
            # 結果集計
            results['total'] = len(results['tests'])
            results['passed'] = len([t for t in results['tests'] if t['status'] == 'passed'])
            results['failed'] = len([t for t in results['tests'] if t['status'] == 'failed'])
            
            self.logger.info(f"テスト実行完了: {results['passed']}/{results['total']} 成功")
            return results
            
        except Exception as e:
            self.logger.error(f"テスト実行エラー: {e}")
            return {
                'timestamp': datetime.now().isoformat(),
                'error': str(e),
                'tests': [],
                'passed': 0,
                'failed': 0,
                'total': 0
            }
    
    def test_basic_functionality(self, results: Dict):
        """基本機能テスト"""
        try:
            # テスト1: プロジェクト構造チェック
            test_name = "プロジェクト構造"
            try:
                required_dirs = [
                    'kyotei_predictor',
                    'kyotei_predictor/config',
                    'kyotei_predictor/data',
                    'kyotei_predictor/templates',
                    'kyotei_predictor/static'
                ]
                
                missing_dirs = []
                for dir_path in required_dirs:
                    full_path = self.project_root / dir_path
                    if not full_path.exists():
                        missing_dirs.append(dir_path)
                
                if not missing_dirs:
                    results['tests'].append({
                        'name': test_name,
                        'status': 'passed',
                        'message': "全ディレクトリが存在"
                    })
                else:
                    results['tests'].append({
                        'name': test_name,
                        'status': 'failed',
                        'message': f"不足ディレクトリ: {', '.join(missing_dirs)}"
                    })
            except Exception as e:
                results['tests'].append({
                    'name': test_name,
                    'status': 'failed',
                    'message': f"プロジェクト構造チェックエラー: {e}"
                })
            
            # テスト2: 設定ファイルチェック
            test_name = "設定ファイル"
            try:
                config_file = self.project_root / "kyotei_predictor" / "config" / "settings.py"
                if config_file.exists():
                    results['tests'].append({
                        'name': test_name,
                        'status': 'passed',
                        'message': "設定ファイルが存在"
                    })
                else:
                    results['tests'].append({
                        'name': test_name,
                        'status': 'failed',
                        'message': "設定ファイルが存在しない"
                    })
            except Exception as e:
                results['tests'].append({
                    'name': test_name,
                    'status': 'failed',
                    'message': f"設定ファイルチェックエラー: {e}"
                })
                
        except Exception as e:
            self.logger.error(f"基本機能テストエラー: {e}")
            results['tests'].append({
                'name': '基本機能テスト',
                'status': 'failed',
                'message': f"基本機能テストエラー: {e}"
            })
    
    def test_api_endpoints(self, results: Dict):
        """APIエンドポイントテスト"""
        try:
            from kyotei_predictor.app import app
            
            # Flaskアプリケーションのテスト
            with app.test_client() as client:
                # テスト1: ルートページ
                test_name = "ルートページ"
                try:
                    response = client.get('/')
                    if response.status_code == 200:
                        results['tests'].append({
                            'name': test_name,
                            'status': 'passed',
                            'message': "ルートページアクセス成功"
                        })
                    else:
                        results['tests'].append({
                            'name': test_name,
                            'status': 'failed',
                            'message': f"ルートページアクセス失敗: {response.status_code}"
                        })
                except Exception as e:
                    results['tests'].append({
                        'name': test_name,
                        'status': 'failed',
                        'message': f"ルートページテストエラー: {e}"
                    })
                
                # テスト2: APIエンドポイント
                test_name = "APIエンドポイント"
                try:
                    response = client.get('/api/races')
                    if response.status_code == 200:
                        data = response.get_json()
                        if data:
                            results['tests'].append({
                                'name': test_name,
                                'status': 'passed',
                                'message': "APIエンドポイント成功"
                            })
                        else:
                            results['tests'].append({
                                'name': test_name,
                                'status': 'failed',
                                'message': "APIレスポンスが空"
                            })
                    else:
                        results['tests'].append({
                            'name': test_name,
                            'status': 'failed',
                            'message': f"APIエンドポイント失敗: {response.status_code}"
                        })
                except Exception as e:
                    results['tests'].append({
                        'name': test_name,
                        'status': 'failed',
                        'message': f"APIエンドポイントテストエラー: {e}"
                    })
                    
        except Exception as e:
            self.logger.error(f"APIエンドポイントテストエラー: {e}")
            results['tests'].append({
                'name': 'APIエンドポイントテスト',
                'status': 'failed',
                'message': f"APIエンドポイントテストエラー: {e}"
            })
    
    def test_data_integration(self, results: Dict):
        """データ統合テスト"""
        try:
            from kyotei_predictor.data_integration import DataIntegration
            
            # DataIntegrationインスタンス作成
            data_integration = DataIntegration()
            
            # テスト1: データ取得
            test_name = "データ取得"
            try:
                data = data_integration.get_race_data()
                if data:
                    results['tests'].append({
                        'name': test_name,
                        'status': 'passed',
                        'message': "データ取得成功"
                    })
                else:
                    results['tests'].append({
                        'name': test_name,
                        'status': 'failed',
                        'message': "データ取得失敗"
                    })
            except Exception as e:
                results['tests'].append({
                    'name': test_name,
                    'status': 'failed',
                    'message': f"データ取得エラー: {e}"
                })
                
        except Exception as e:
            self.logger.error(f"データ統合テストエラー: {e}")
            results['tests'].append({
                'name': 'データ統合テスト',
                'status': 'failed',
                'message': f"データ統合テストエラー: {e}"
            })
    
    def save_test_report(self, results: Dict) -> Optional[Path]:
        """テストレポートを保存"""
        try:
            # 出力ディレクトリ
            output_dir = self.project_root / "outputs" / "test_reports"
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # ファイル名
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"test_server_{timestamp}.json"
            output_path = output_dir / filename
            
            # 保存
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"テストレポートを保存: {output_path}")
            return output_path
            
        except Exception as e:
            self.logger.error(f"テストレポート保存エラー: {e}")
            return None

def main():
    """メイン関数"""
    import argparse
    from datetime import datetime
    
    parser = argparse.ArgumentParser(description='テストサーバー')
    parser.add_argument('--port', type=int, default=5000, help='ポート番号')
    parser.add_argument('--test-only', action='store_true', help='テストのみ実行')
    
    args = parser.parse_args()
    
    server = TestServer()
    
    if args.test_only:
        # テストのみ実行
        results = server.run_tests()
        
        # 結果表示
        print(f"=== テスト結果 ===")
        print(f"実行時刻: {results['timestamp']}")
        print(f"総テスト数: {results['total']}")
        print(f"成功: {results['passed']}")
        print(f"失敗: {results['failed']}")
        
        if results['tests']:
            print(f"\n=== 詳細結果 ===")
            for test_result in results['tests']:
                status_icon = "✅" if test_result['status'] == 'passed' else "❌"
                print(f"{status_icon} {test_result['name']}: {test_result['message']}")
        
        # レポート保存
        output_path = server.save_test_report(results)
        if output_path:
            print(f"\nレポート保存: {output_path}")
    else:
        # サーバー開始
        print(f"テストサーバーを開始します: ポート {args.port}")
        server.start_test_server(args.port)

if __name__ == "__main__":
    main() 