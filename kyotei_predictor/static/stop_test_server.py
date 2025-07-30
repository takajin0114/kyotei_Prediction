#!/usr/bin/env python3
"""
テストサーバー停止スクリプト
"""

import os
import sys
import signal
import logging
from pathlib import Path
from typing import Optional, Dict

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

class TestServerStopper:
    """テストサーバー停止クラス"""
    
    def __init__(self):
        """初期化"""
        self.project_root = PROJECT_ROOT
        self.log_dir = self.project_root / "kyotei_predictor" / "logs"
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # ログ設定
        log_file = self.log_dir / "stop_test_server.log"
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
        self.logger.info("TestServerStopper初期化完了")
    
    def stop_test_server(self) -> bool:
        """
        テストサーバーを停止
        
        Returns:
            停止成功かどうか
        """
        try:
            self.logger.info("テストサーバー停止開始")
            
            # PIDファイルのパス
            pid_file = self.project_root / "kyotei_predictor" / "static" / "test_server.pid"
            
            if not pid_file.exists():
                self.logger.warning("PIDファイルが見つかりません")
                return False
            
            # PIDを読み込み
            try:
                with open(pid_file, 'r') as f:
                    pid = int(f.read().strip())
            except Exception as e:
                self.logger.error(f"PIDファイル読み込みエラー: {e}")
                return False
            
            # プロセスを停止
            try:
                os.kill(pid, signal.SIGTERM)
                self.logger.info(f"プロセス {pid} に停止シグナルを送信")
                
                # PIDファイルを削除
                pid_file.unlink()
                self.logger.info("PIDファイルを削除")
                
                return True
                
            except ProcessLookupError:
                self.logger.warning(f"プロセス {pid} は既に終了しています")
                pid_file.unlink()
                return True
            except Exception as e:
                self.logger.error(f"プロセス停止エラー: {e}")
                return False
                
        except Exception as e:
            self.logger.error(f"テストサーバー停止エラー: {e}")
            return False
    
    def check_server_status(self) -> Dict:
        """
        サーバーの状態をチェック
        
        Returns:
            サーバー状態
        """
        try:
            # PIDファイルのパス
            pid_file = self.project_root / "kyotei_predictor" / "static" / "test_server.pid"
            
            if not pid_file.exists():
                return {
                    'running': False,
                    'message': 'PIDファイルが存在しません'
                }
            
            # PIDを読み込み
            try:
                with open(pid_file, 'r') as f:
                    pid = int(f.read().strip())
            except Exception as e:
                return {
                    'running': False,
                    'message': f'PIDファイル読み込みエラー: {e}'
                }
            
            # プロセスの存在確認
            try:
                os.kill(pid, 0)  # シグナル0は存在確認のみ
                return {
                    'running': True,
                    'pid': pid,
                    'message': f'プロセス {pid} が実行中'
                }
            except ProcessLookupError:
                return {
                    'running': False,
                    'message': f'プロセス {pid} は存在しません'
                }
            except Exception as e:
                return {
                    'running': False,
                    'message': f'プロセス確認エラー: {e}'
                }
                
        except Exception as e:
            self.logger.error(f"サーバー状態チェックエラー: {e}")
            return {
                'running': False,
                'message': f'状態チェックエラー: {e}'
            }

def main():
    """メイン関数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='テストサーバー停止')
    parser.add_argument('--status', action='store_true', help='サーバー状態を確認')
    
    args = parser.parse_args()
    
    stopper = TestServerStopper()
    
    if args.status:
        # 状態確認
        status = stopper.check_server_status()
        print(f"=== サーバー状態 ===")
        print(f"実行中: {'はい' if status['running'] else 'いいえ'}")
        print(f"メッセージ: {status['message']}")
        
        if status['running']:
            print(f"PID: {status['pid']}")
    else:
        # サーバー停止
        print("テストサーバーを停止します...")
        
        if stopper.stop_test_server():
            print("テストサーバーを停止しました")
        else:
            print("テストサーバーの停止に失敗しました")

if __name__ == "__main__":
    main() 