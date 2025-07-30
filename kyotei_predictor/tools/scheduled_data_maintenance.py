#!/usr/bin/env python3
"""
スケジュールされたデータメンテナンススクリプト
"""

import os
import sys
import json
import logging
import schedule
import time
from datetime import datetime, timedelta
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

from kyotei_predictor.tools.batch.batch_fetch_all_venues import get_all_stadiums

class DataMaintenanceScheduler:
    """データメンテナンスのスケジューラー"""
    
    def __init__(self):
        """初期化"""
        self.project_root = PROJECT_ROOT
        self.log_dir = self.project_root / "kyotei_predictor" / "logs"
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # ログ設定
        log_file = self.log_dir / "data_maintenance.log"
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
        self.logger.info("DataMaintenanceScheduler初期化完了")
    
    def run_daily_maintenance(self):
        """日次メンテナンスを実行"""
        self.logger.info("日次メンテナンス開始")
        
        try:
            # データ取得
            self.fetch_missing_data()
            
            # データクリーンアップ
            self.cleanup_old_data()
            
            # レポート生成
            self.generate_maintenance_report()
            
            self.logger.info("日次メンテナンス完了")
            
        except Exception as e:
            self.logger.error(f"日次メンテナンスエラー: {e}")
    
    def fetch_missing_data(self):
        """不足データの取得"""
        self.logger.info("不足データ取得開始")
        
        try:
            # 昨日の日付
            yesterday = datetime.now() - timedelta(days=1)
            date_str = yesterday.strftime('%Y-%m-%d')
            
            # 全競艇場のデータを取得
            stadiums = get_all_stadiums()
            
            for stadium in stadiums:
                self.logger.info(f"{stadium.name}のデータを取得中...")
                
                # バッチ取得を実行
                self.run_batch_fetch(stadium.name, date_str)
                
        except Exception as e:
            self.logger.error(f"データ取得エラー: {e}")
    
    def run_batch_fetch(self, stadium: str, date: str):
        """バッチ取得を実行"""
        try:
            # バッチスクリプトを実行
            cmd = [
                sys.executable, '-m', 'kyotei_predictor.tools.batch.batch_fetch_all_venues',
                '--start-date', date,
                '--end-date', date,
                '--stadiums', stadium
            ]
            
            import subprocess
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                self.logger.info(f"{stadium}のデータ取得成功")
            else:
                self.logger.error(f"{stadium}のデータ取得失敗: {result.stderr}")
                
        except Exception as e:
            self.logger.error(f"バッチ実行エラー {stadium}: {e}")
    
    def cleanup_old_data(self):
        """古いデータのクリーンアップ"""
        self.logger.info("古いデータのクリーンアップ開始")
        
        try:
            # 30日以上古いデータを削除
            cutoff_date = datetime.now() - timedelta(days=30)
            
            data_dir = self.project_root / "kyotei_predictor" / "data" / "raw"
            
            if data_dir.exists():
                for file_path in data_dir.glob("*.json"):
                    if file_path.stat().st_mtime < cutoff_date.timestamp():
                        file_path.unlink()
                        self.logger.info(f"古いファイルを削除: {file_path.name}")
            
        except Exception as e:
            self.logger.error(f"クリーンアップエラー: {e}")
    
    def generate_maintenance_report(self):
        """メンテナンスレポートを生成"""
        self.logger.info("メンテナンスレポート生成開始")
        
        try:
            report = {
                'timestamp': datetime.now().isoformat(),
                'maintenance_type': 'daily',
                'data_fetch_status': 'completed',
                'cleanup_status': 'completed',
                'next_maintenance': (datetime.now() + timedelta(days=1)).isoformat()
            }
            
            report_dir = self.project_root / "outputs" / "maintenance_reports"
            report_dir.mkdir(parents=True, exist_ok=True)
            
            report_file = report_dir / f"maintenance_report_{datetime.now().strftime('%Y%m%d')}.json"
            
            with open(report_file, 'w') as f:
                json.dump(report, f, indent=2)
            
            self.logger.info(f"メンテナンスレポートを保存: {report_file}")
            
        except Exception as e:
            self.logger.error(f"レポート生成エラー: {e}")
    
    def schedule_maintenance(self):
        """メンテナンスをスケジュール"""
        # 毎日午前2時に実行
        schedule.every().day.at("02:00").do(self.run_daily_maintenance)
        
        self.logger.info("メンテナンスをスケジュール: 毎日午前2時")
    
    def run_scheduler(self):
        """スケジューラーを実行"""
        self.schedule_maintenance()
        
        self.logger.info("スケジューラー開始")
        
        while True:
            schedule.run_pending()
            time.sleep(60)  # 1分ごとにチェック

def main():
    """メイン関数"""
    scheduler = DataMaintenanceScheduler()
    
    if len(sys.argv) > 1 and sys.argv[1] == "--run-now":
        # 即座に実行
        scheduler.run_daily_maintenance()
    else:
        # スケジューラーとして実行
        scheduler.run_scheduler()

if __name__ == "__main__":
    main() 