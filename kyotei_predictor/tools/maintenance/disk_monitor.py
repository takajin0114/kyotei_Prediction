#!/usr/bin/env python3
"""
ディスク容量監視スクリプト
リアルタイムでディスク容量を監視し、警告を発行
"""

import os
import json
import time
import logging
import argparse
from datetime import datetime, timedelta
from pathlib import Path
import psutil
import threading
from collections import deque

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('disk_monitor.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class DiskMonitor:
    def __init__(self, config_path='configs/monitor_config.json', project_root=None):
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
        self.history = deque(maxlen=100)  # 履歴を保持
        self.alert_history = deque(maxlen=50)  # アラート履歴
        self.running = False
        
    def load_config(self, config_path):
        """設定ファイルを読み込み"""
        default_config = {
            "monitoring": {
                "check_interval": 60,  # 秒
                "warning_threshold": 70,  # %
                "critical_threshold": 85,  # %
                "emergency_threshold": 95  # %
            },
            "directories": {
                "optuna_models": {"max_size_gb": 5},
                "optuna_logs": {"max_size_gb": 2},
                "optuna_tensorboard": {"max_size_gb": 3},
                "outputs": {"max_size_gb": 1},
                "archives": {"max_size_gb": 10}
            },
            "notifications": {
                "enabled": True,
                "warning_interval": 3600,  # 秒
                "critical_interval": 1800   # 秒
            }
        }
        
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                return {**default_config, **json.load(f)}
        else:
            return default_config
    
    def get_disk_usage(self):
        """ディスク使用量を取得"""
        try:
            disk_usage = psutil.disk_usage(self.project_root)
            return {
                "total_gb": disk_usage.total / (1024**3),
                "used_gb": disk_usage.used / (1024**3),
                "free_gb": disk_usage.free / (1024**3),
                "usage_percent": (disk_usage.used / disk_usage.total) * 100
            }
        except Exception as e:
            logger.warning(f"ディスク使用量取得でエラーが発生: {e}")
            return {
                "total_gb": 0,
                "used_gb": 0,
                "free_gb": 0,
                "usage_percent": 0
            }
    
    def get_directory_sizes(self):
        """主要ディレクトリのサイズを取得"""
        sizes = {}
        for dir_name, settings in self.config["directories"].items():
            dir_path = self.project_root / dir_name
            if dir_path.exists():
                total_size = sum(f.stat().st_size for f in dir_path.rglob('*') if f.is_file())
                sizes[dir_name] = {
                    "size_gb": total_size / (1024**3),
                    "max_size_gb": settings.get("max_size_gb", 5),
                    "file_count": len(list(dir_path.rglob('*')))
                }
        return sizes
    
    def check_thresholds(self, usage_data):
        """閾値チェック"""
        alerts = []
        usage_percent = usage_data["usage_percent"]
        
        if usage_percent >= self.config["monitoring"]["emergency_threshold"]:
            alerts.append({
                "level": "EMERGENCY",
                "message": f"ディスク使用率が緊急レベルに達しました: {usage_percent:.1f}%",
                "timestamp": datetime.now().isoformat()
            })
        elif usage_percent >= self.config["monitoring"]["critical_threshold"]:
            alerts.append({
                "level": "CRITICAL",
                "message": f"ディスク使用率が危険レベルに達しました: {usage_percent:.1f}%",
                "timestamp": datetime.now().isoformat()
            })
        elif usage_percent >= self.config["monitoring"]["warning_threshold"]:
            alerts.append({
                "level": "WARNING",
                "message": f"ディスク使用率が警告レベルに達しました: {usage_percent:.1f}%",
                "timestamp": datetime.now().isoformat()
            })
        
        return alerts
    
    def check_directory_alerts(self, sizes):
        """ディレクトリサイズのアラートチェック"""
        alerts = []
        
        for dir_name, size_data in sizes.items():
            if size_data["size_gb"] > size_data["max_size_gb"]:
                alerts.append({
                    "level": "WARNING",
                    "message": f"{dir_name}のサイズが制限を超過: {size_data['size_gb']:.1f}GB > {size_data['max_size_gb']}GB",
                    "timestamp": datetime.now().isoformat()
                })
        
        return alerts
    
    def should_send_notification(self, alert_level):
        """通知を送信すべきかチェック"""
        if not self.config["notifications"]["enabled"]:
            return False
        
        # 最後の通知時刻をチェック
        if not self.alert_history:
            return True
        
        last_alert = self.alert_history[-1]
        time_diff = (datetime.now() - datetime.fromisoformat(last_alert["timestamp"])).total_seconds()
        
        if alert_level == "EMERGENCY":
            return True  # 緊急時は常に通知
        elif alert_level == "CRITICAL":
            return time_diff >= self.config["notifications"]["critical_interval"]
        elif alert_level == "WARNING":
            return time_diff >= self.config["notifications"]["warning_interval"]
        
        return False
    
    def send_notification(self, alert):
        """通知を送信"""
        if self.should_send_notification(alert["level"]):
            logger.warning(f"アラート: {alert['message']}")
            # ここでメールやDiscord通知を実装可能
            self.alert_history.append(alert)
    
    def generate_report(self):
        """監視レポートを生成"""
        usage_data = self.get_disk_usage()
        sizes = self.get_directory_sizes()
        
        report = {
            "timestamp": datetime.now().isoformat(),
            "disk_usage": usage_data,
            "directory_sizes": sizes,
            "alerts": list(self.alert_history)[-10:],  # 最新10個のアラート
            "history": list(self.history)[-20:]  # 最新20個の履歴
        }
        
        # レポートを保存
        try:
            report_path = self.project_root / "disk_monitor_report.json"
            with open(report_path, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.warning(f"レポート保存でエラーが発生: {e}")
            # レポートは返すが、保存は失敗
        
        return report
    
    def monitor_loop(self):
        """監視ループ"""
        while self.running:
            try:
                # ディスク使用量を取得
                usage_data = self.get_disk_usage()
                sizes = self.get_directory_sizes()
                
                # 履歴に追加
                self.history.append({
                    "timestamp": datetime.now().isoformat(),
                    "usage": usage_data,
                    "sizes": sizes
                })
                
                # アラートチェック
                disk_alerts = self.check_thresholds(usage_data)
                dir_alerts = self.check_directory_alerts(sizes)
                
                all_alerts = disk_alerts + dir_alerts
                
                # アラート処理
                for alert in all_alerts:
                    self.send_notification(alert)
                
                # ログ出力
                logger.info(f"ディスク使用率: {usage_data['usage_percent']:.1f}% "
                          f"({usage_data['used_gb']:.1f}GB / {usage_data['total_gb']:.1f}GB)")
                
                # 設定された間隔で待機
                time.sleep(self.config["monitoring"]["check_interval"])
                
            except Exception as e:
                logger.error(f"監視中にエラーが発生: {e}")
                time.sleep(10)  # エラー時は10秒待機
    
    def start_monitoring(self):
        """監視を開始"""
        logger.info("ディスク容量監視を開始")
        self.running = True
        self.monitor_loop()
    
    def stop_monitoring(self):
        """監視を停止"""
        logger.info("ディスク容量監視を停止")
        self.running = False
    
    def get_status(self):
        """現在のステータスを取得"""
        usage_data = self.get_disk_usage()
        sizes = self.get_directory_sizes()
        
        status = {
            "timestamp": datetime.now().isoformat(),
            "disk_usage": usage_data,
            "directory_sizes": sizes,
            "monitoring_active": self.running,
            "alert_count": len(self.alert_history)
        }
        
        return status

def main():
    parser = argparse.ArgumentParser(description='ディスク容量監視スクリプト')
    parser.add_argument('--config', default='monitor_config.json', help='設定ファイルパス')
    parser.add_argument('--project-root', help='プロジェクトルートパス')
    parser.add_argument('--status', action='store_true', help='現在のステータスを表示')
    parser.add_argument('--report', action='store_true', help='レポートを生成')
    parser.add_argument('--daemon', action='store_true', help='デーモンモードで実行')
    
    args = parser.parse_args()
    
    monitor = DiskMonitor(args.config, args.project_root)
    
    if args.status:
        status = monitor.get_status()
        print(json.dumps(status, indent=2, ensure_ascii=False))
    elif args.report:
        report = monitor.generate_report()
        print(json.dumps(report, indent=2, ensure_ascii=False))
    elif args.daemon:
        try:
            monitor.start_monitoring()
        except KeyboardInterrupt:
            monitor.stop_monitoring()
    else:
        # 1回だけ実行
        status = monitor.get_status()
        print(json.dumps(status, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main() 