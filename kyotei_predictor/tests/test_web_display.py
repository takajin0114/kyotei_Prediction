#!/usr/bin/env python3
"""
Web表示テスト
"""

import os
import sys
import json
import logging
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

class WebDisplayTest:
    """Web表示テストクラス"""
    
    def __init__(self):
        """初期化"""
        self.project_root = PROJECT_ROOT
        self.log_dir = self.project_root / "kyotei_predictor" / "logs"
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # ログ設定
        log_file = self.log_dir / "web_display_test.log"
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
        self.logger.info("WebDisplayTest初期化完了")
    
    def test_web_display(self) -> Dict:
        """
        Web表示テストを実行
        
        Returns:
            テスト結果
        """
        try:
            self.logger.info("Web表示テスト開始")
            
            results = {
                'timestamp': datetime.now().isoformat(),
                'tests': [],
                'passed': 0,
                'failed': 0,
                'total': 0
            }
            
            # テストケース実行
            self.test_data_integration(results)
            self.test_api_endpoints(results)
            self.test_ui_components(results)
            
            # 結果集計
            results['total'] = len(results['tests'])
            results['passed'] = len([t for t in results['tests'] if t['status'] == 'passed'])
            results['failed'] = len([t for t in results['tests'] if t['status'] == 'failed'])
            
            self.logger.info(f"Web表示テスト完了: {results['passed']}/{results['total']} 成功")
            return results
            
        except Exception as e:
            self.logger.error(f"Web表示テストエラー: {e}")
            return {
                'timestamp': datetime.now().isoformat(),
                'error': str(e),
                'tests': [],
                'passed': 0,
                'failed': 0,
                'total': 0
            }
    
    def test_data_integration(self, results: Dict):
        """データ統合テスト"""
        try:
            from kyotei_predictor.data_integration import DataIntegration
            
            # DataIntegrationインスタンス作成
            data_integration = DataIntegration()
            
            # テスト1: サンプルデータ取得
            test_name = "サンプルデータ取得"
            try:
                sample_data = data_integration.get_race_data()
                if sample_data and 'races' in sample_data:
                    results['tests'].append({
                        'name': test_name,
                        'status': 'passed',
                        'message': f"サンプルデータ取得成功: {len(sample_data['races'])}レース"
                    })
                else:
                    results['tests'].append({
                        'name': test_name,
                        'status': 'failed',
                        'message': "サンプルデータが不正な形式"
                    })
            except Exception as e:
                results['tests'].append({
                    'name': test_name,
                    'status': 'failed',
                    'message': f"サンプルデータ取得エラー: {e}"
                })
            
            # テスト2: 利用可能会場取得
            test_name = "利用可能会場取得"
            try:
                stadiums = data_integration.get_available_stadiums()
                if stadiums and len(stadiums) > 0:
                    results['tests'].append({
                        'name': test_name,
                        'status': 'passed',
                        'message': f"利用可能会場取得成功: {len(stadiums)}会場"
                    })
                else:
                    results['tests'].append({
                        'name': test_name,
                        'status': 'failed',
                        'message': "利用可能会場が空"
                    })
            except Exception as e:
                results['tests'].append({
                    'name': test_name,
                    'status': 'failed',
                    'message': f"利用可能会場取得エラー: {e}"
                })
                
        except Exception as e:
            self.logger.error(f"データ統合テストエラー: {e}")
            results['tests'].append({
                'name': 'データ統合テスト',
                'status': 'failed',
                'message': f"データ統合テストエラー: {e}"
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
                        if data and 'races' in data:
                            results['tests'].append({
                                'name': test_name,
                                'status': 'passed',
                                'message': f"APIエンドポイント成功: {len(data['races'])}レース"
                            })
                        else:
                            results['tests'].append({
                                'name': test_name,
                                'status': 'failed',
                                'message': "APIレスポンスが不正な形式"
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
    
    def test_ui_components(self, results: Dict):
        """UIコンポーネントテスト"""
        try:
            # テスト1: テンプレートファイル存在チェック
            test_name = "テンプレートファイル"
            try:
                templates_dir = self.project_root / "kyotei_predictor" / "templates"
                required_templates = ['index.html', 'races.html', 'predictions.html']
                
                missing_templates = []
                for template in required_templates:
                    template_path = templates_dir / template
                    if not template_path.exists():
                        missing_templates.append(template)
                
                if not missing_templates:
                    results['tests'].append({
                        'name': test_name,
                        'status': 'passed',
                        'message': "全テンプレートファイルが存在"
                    })
                else:
                    results['tests'].append({
                        'name': test_name,
                        'status': 'failed',
                        'message': f"不足テンプレート: {', '.join(missing_templates)}"
                    })
            except Exception as e:
                results['tests'].append({
                    'name': test_name,
                    'status': 'failed',
                    'message': f"テンプレートファイルチェックエラー: {e}"
                })
            
            # テスト2: 静的ファイル存在チェック
            test_name = "静的ファイル"
            try:
                static_dir = self.project_root / "kyotei_predictor" / "static"
                required_static = ['css', 'js']
                
                missing_static = []
                for static_type in required_static:
                    static_path = static_dir / static_type
                    if not static_path.exists():
                        missing_static.append(static_type)
                
                if not missing_static:
                    results['tests'].append({
                        'name': test_name,
                        'status': 'passed',
                        'message': "全静的ファイルディレクトリが存在"
                    })
                else:
                    results['tests'].append({
                        'name': test_name,
                        'status': 'failed',
                        'message': f"不足静的ディレクトリ: {', '.join(missing_static)}"
                    })
            except Exception as e:
                results['tests'].append({
                    'name': test_name,
                    'status': 'failed',
                    'message': f"静的ファイルチェックエラー: {e}"
                })
                
        except Exception as e:
            self.logger.error(f"UIコンポーネントテストエラー: {e}")
            results['tests'].append({
                'name': 'UIコンポーネントテスト',
                'status': 'failed',
                'message': f"UIコンポーネントテストエラー: {e}"
            })
    
    def save_test_report(self, results: Dict) -> Optional[Path]:
        """テストレポートを保存"""
        try:
            # 出力ディレクトリ
            output_dir = self.project_root / "outputs" / "test_reports"
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # ファイル名
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"web_display_test_{timestamp}.json"
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
    from datetime import datetime
    
    test = WebDisplayTest()
    
    # テスト実行
    results = test.test_web_display()
    
    # 結果表示
    print(f"=== Web表示テスト結果 ===")
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
    output_path = test.save_test_report(results)
    if output_path:
        print(f"\nレポート保存: {output_path}")

if __name__ == "__main__":
    main() 