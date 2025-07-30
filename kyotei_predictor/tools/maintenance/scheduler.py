#!/usr/bin/env python3
"""
定期実行スケジューラ
自動クリーンアップとディスク監視を定期実行
"""

import os
import time
import json
import logging
import argparse
import subprocess
import schedule
from datetime import datetime, timedelta
from pathlib import Path
import threading

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scheduler.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class MaintenanceScheduler:
    def __init__(self, config_path='configs/scheduler_config.json', project_root=None):
        self.config = self.load_config(config_path)
        # プロジェクトルートを動的に決定
        if project_root:
            self.project_root = Path(project_root)
        else:
            # スクリプトの場所から相対的に決定
            script_path = Path(__file__)
            # Colab環境では/content/kyotei_Predictionのような構造になる可能性
            if '/content/' in str(script_path):
                # Colab環境の場合
                self.project_root = Path('/content/kyotei_Prediction')
            else:
                # ローカル環境の場合
                self.project_root = script_path.parent.parent.parent
        self.running = False
        
    def load_config(self, config_path):
        """設定ファイルを読み込み"""
        default_config = {
            "schedules": {
                "daily_cleanup": {
                    "enabled": True,
                    "time": "02:00",
                    "command": "python kyotei_predictor/tools/maintenance/auto_cleanup.py"
                },
                "weekly_cleanup": {
                    "enabled": True,
                    "day": "sunday",
                    "time": "03:00",
                    "command": "python kyotei_predictor/tools/maintenance/auto_cleanup.py --config cleanup_config.json"
                },
                "disk_monitor": {
                    "enabled": True,
                    "interval_minutes": 30,
                    "command": "python kyotei_predictor/tools/maintenance/disk_monitor.py --status"
                }
            },
            "monitoring": {
                "enabled": True,
                "check_interval": 60
            }
        }
        
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                return {**default_config, **json.load(f)}
        else:
            return default_config
    
    def run_command(self, command, description=""):
        """コマンドを実行"""
        try:
            logger.info(f"実行開始: {description} - {command}")
            
            # プロジェクトルートでコマンドを実行
            result = subprocess.run(
                command,
                shell=True,
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=300  # 5分でタイムアウト
            )
            
            if result.returncode == 0:
                logger.info(f"実行成功: {description}")
                if result.stdout:
                    logger.debug(f"出力: {result.stdout}")
            else:
                logger.error(f"実行失敗: {description} - {result.stderr}")
                
        except subprocess.TimeoutExpired:
            logger.error(f"実行タイムアウト: {description}")
        except Exception as e:
            logger.error(f"実行エラー: {description} - {e}")
    
    def daily_cleanup_job(self):
        """日次クリーンアップジョブ"""
        if self.config["schedules"]["daily_cleanup"]["enabled"]:
            command = self.config["schedules"]["daily_cleanup"]["command"]
            self.run_command(command, "日次クリーンアップ")
    
    def weekly_cleanup_job(self):
        """週次クリーンアップジョブ"""
        if self.config["schedules"]["weekly_cleanup"]["enabled"]:
            command = self.config["schedules"]["weekly_cleanup"]["command"]
            self.run_command(command, "週次クリーンアップ")
    
    def disk_monitor_job(self):
        """ディスク監視ジョブ"""
        if self.config["schedules"]["disk_monitor"]["enabled"]:
            command = self.config["schedules"]["disk_monitor"]["command"]
            self.run_command(command, "ディスク監視")
    
    def emergency_cleanup_job(self):
        """緊急クリーンアップジョブ"""
        logger.warning("緊急クリーンアップを実行")
        command = "python kyotei_predictor/tools/maintenance/auto_cleanup.py --config cleanup_config.json"
        self.run_command(command, "緊急クリーンアップ")
    
    def setup_schedules(self):
        """スケジュールを設定"""
        # 日次クリーンアップ
        if self.config["schedules"]["daily_cleanup"]["enabled"]:
            schedule.every().day.at(self.config["schedules"]["daily_cleanup"]["time"]).do(self.daily_cleanup_job)
            logger.info(f"日次クリーンアップをスケジュール: {self.config['schedules']['daily_cleanup']['time']}")
        
        # 週次クリーンアップ
        if self.config["schedules"]["weekly_cleanup"]["enabled"]:
            day = self.config["schedules"]["weekly_cleanup"]["day"]
            time_str = self.config["schedules"]["weekly_cleanup"]["time"]
            
            if day == "sunday":
                schedule.every().sunday.at(time_str).do(self.weekly_cleanup_job)
            elif day == "monday":
                schedule.every().monday.at(time_str).do(self.weekly_cleanup_job)
            elif day == "tuesday":
                schedule.every().tuesday.at(time_str).do(self.weekly_cleanup_job)
            elif day == "wednesday":
                schedule.every().wednesday.at(time_str).do(self.weekly_cleanup_job)
            elif day == "thursday":
                schedule.every().thursday.at(time_str).do(self.weekly_cleanup_job)
            elif day == "friday":
                schedule.every().friday.at(time_str).do(self.weekly_cleanup_job)
            elif day == "saturday":
                schedule.every().saturday.at(time_str).do(self.weekly_cleanup_job)
            
            logger.info(f"週次クリーンアップをスケジュール: {day} {time_str}")
        
        # ディスク監視（定期実行）
        if self.config["schedules"]["disk_monitor"]["enabled"]:
            interval = self.config["schedules"]["disk_monitor"]["interval_minutes"]
            schedule.every(interval).minutes.do(self.disk_monitor_job)
            logger.info(f"ディスク監視をスケジュール: {interval}分間隔")
    
    def check_disk_usage(self):
        """ディスク使用量をチェック"""
        try:
            import psutil
            disk_usage = psutil.disk_usage(self.project_root)
            usage_percent = (disk_usage.used / disk_usage.total) * 100
            
            if usage_percent > 90:  # 90%を超過した場合
                logger.warning(f"ディスク使用率が90%を超過: {usage_percent:.1f}%")
                self.emergency_cleanup_job()
            elif usage_percent > 80:  # 80%を超過した場合
                logger.warning(f"ディスク使用率が80%を超過: {usage_percent:.1f}%")
                
        except ImportError:
            logger.warning("psutilがインストールされていません")
        except Exception as e:
            logger.warning(f"ディスク使用量チェックエラー: {e}")
            # Colab環境などではディスク容量チェックができない場合がある
    
    def run_scheduler(self):
        """スケジューラを実行"""
        logger.info("メンテナンススケジューラを開始")
        self.running = True
        
        # スケジュールを設定
        self.setup_schedules()
        
        # 初回実行
        logger.info("初回実行を開始")
        self.disk_monitor_job()
        
        # スケジュールループ
        while self.running:
            try:
                # スケジュールされたジョブを実行
                schedule.run_pending()
                
                # ディスク使用量をチェック
                if self.config["monitoring"]["enabled"]:
                    self.check_disk_usage()
                
                # 設定された間隔で待機
                time.sleep(self.config["monitoring"]["check_interval"])
                
            except KeyboardInterrupt:
                logger.info("スケジューラを停止")
                self.running = False
                break
            except Exception as e:
                logger.error(f"スケジューラエラー: {e}")
                time.sleep(10)
    
    def stop_scheduler(self):
        """スケジューラを停止"""
        logger.info("メンテナンススケジューラを停止")
        self.running = False
    
    def get_status(self):
        """スケジューラのステータスを取得"""
        status = {
            "timestamp": datetime.now().isoformat(),
            "running": self.running,
            "schedules": self.config["schedules"],
            "next_run": schedule.next_run()
        }
        return status

def main():
    parser = argparse.ArgumentParser(description='メンテナンススケジューラ')
    parser.add_argument('--config', default='scheduler_config.json', help='設定ファイルパス')
    parser.add_argument('--project-root', help='プロジェクトルートパス')
    parser.add_argument('--status', action='store_true', help='現在のステータスを表示')
    parser.add_argument('--run-now', action='store_true', help='即座にクリーンアップを実行')
    parser.add_argument('--daemon', action='store_true', help='デーモンモードで実行')
    
    args = parser.parse_args()
    
    scheduler = MaintenanceScheduler(args.config, args.project_root)
    
    if args.status:
        status = scheduler.get_status()
        print(json.dumps(status, indent=2, ensure_ascii=False))
    elif args.run_now:
        scheduler.daily_cleanup_job()
    elif args.daemon:
        try:
            scheduler.run_scheduler()
        except KeyboardInterrupt:
            scheduler.stop_scheduler()
    else:
        # 1回だけ実行
        status = scheduler.get_status()
        print(json.dumps(status, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main() 