#!/usr/bin/env python3
"""
自動クリーンアップスクリプト
定期的なファイル整理とディスク容量監視を実行
"""

import os
import shutil
import glob
import logging
import json
import time
from datetime import datetime, timedelta
from pathlib import Path
import psutil
import argparse

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('auto_cleanup.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class AutoCleanup:
    def __init__(self, config_path='configs/cleanup_config.json', project_root=None):
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
        
    def load_config(self, config_path):
        """設定ファイルを読み込み"""
        default_config = {
            "max_disk_usage_percent": 80,
            "cleanup_schedules": {
                "daily": {
                    "enabled": True,
                    "time": "02:00",
                    "retention_days": 7
                },
                "weekly": {
                    "enabled": True,
                    "day": "sunday",
                    "time": "03:00",
                    "retention_days": 30
                }
            },
            "targets": {
                "outputs/logs": {
                    "enabled": True,
                    "max_files": 10,
                    "max_size_mb": 100
                },
                "optuna_models/graduated_reward_checkpoints": {
                    "enabled": True,
                    "max_files": 5,
                    "max_size_mb": 500
                },
                "archives/optimization": {
                    "enabled": True,
                    "max_files": 20,
                    "max_size_mb": 1000
                }
            }
        }
        
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                return {**default_config, **json.load(f)}
        else:
            return default_config
    
    def check_disk_usage(self):
        """ディスク容量をチェック"""
        try:
            disk_usage = psutil.disk_usage(self.project_root)
            usage_percent = (disk_usage.used / disk_usage.total) * 100
            
            logger.info(f"ディスク使用率: {usage_percent:.1f}% ({disk_usage.used / (1024**3):.1f}GB / {disk_usage.total / (1024**3):.1f}GB)")
            
            if usage_percent > self.config["max_disk_usage_percent"]:
                logger.warning(f"ディスク使用率が{self.config['max_disk_usage_percent']}%を超過しています")
                return True
            return False
        except Exception as e:
            logger.warning(f"ディスク容量チェックでエラーが発生: {e}")
            return False
    
    def cleanup_logs(self, target_path, max_files=10, max_size_mb=100):
        """ログファイルのクリーンアップ"""
        target_dir = self.project_root / target_path
        if not target_dir.exists():
            return
        
        # ファイルサイズをチェック
        total_size = sum(f.stat().st_size for f in target_dir.iterdir() if f.is_file())
        total_size_mb = total_size / (1024 * 1024)
        
        if total_size_mb > max_size_mb:
            logger.info(f"{target_path}: サイズ超過 ({total_size_mb:.1f}MB > {max_size_mb}MB)")
            
            # 古いファイルを削除
            files = sorted(target_dir.iterdir(), key=lambda x: x.stat().st_mtime)
            for file in files[:-max_files]:
                try:
                    file.unlink()
                    logger.info(f"削除: {file}")
                except Exception as e:
                    logger.error(f"削除失敗: {file} - {e}")
    
    def cleanup_checkpoints(self, target_path, max_files=5, max_size_mb=500):
        """チェックポイントファイルのクリーンアップ"""
        target_dir = self.project_root / target_path
        if not target_dir.exists():
            return
        
        # ファイルサイズをチェック
        total_size = sum(f.stat().st_size for f in target_dir.iterdir() if f.is_file())
        total_size_mb = total_size / (1024 * 1024)
        
        if total_size_mb > max_size_mb:
            logger.info(f"{target_path}: サイズ超過 ({total_size_mb:.1f}MB > {max_size_mb}MB)")
            
            # 最新のファイルを保持
            files = sorted(target_dir.iterdir(), key=lambda x: x.stat().st_mtime, reverse=True)
            for file in files[max_files:]:
                try:
                    file.unlink()
                    logger.info(f"削除: {file}")
                except Exception as e:
                    logger.error(f"削除失敗: {file} - {e}")
    
    def cleanup_archives(self, target_path, max_files=20, max_size_mb=1000):
        """アーカイブファイルのクリーンアップ"""
        target_dir = self.project_root / target_path
        if not target_dir.exists():
            return
        
        # ファイルサイズをチェック
        total_size = sum(f.stat().st_size for f in target_dir.rglob('*') if f.is_file())
        total_size_mb = total_size / (1024 * 1024)
        
        if total_size_mb > max_size_mb:
            logger.info(f"{target_path}: サイズ超過 ({total_size_mb:.1f}MB > {max_size_mb}MB)")
            
            # 古いファイルを削除
            files = []
            for file in target_dir.rglob('*'):
                if file.is_file():
                    files.append((file, file.stat().st_mtime))
            
            files.sort(key=lambda x: x[1])
            for file, _ in files[:-max_files]:
                try:
                    file.unlink()
                    logger.info(f"削除: {file}")
                except Exception as e:
                    logger.error(f"削除失敗: {file} - {e}")
    
    def cleanup_trial_directories(self):
        """古いtrialディレクトリのクリーンアップ"""
        # optuna_models内のtrialディレクトリ
        optuna_models_dir = self.project_root / "optuna_models"
        if optuna_models_dir.exists():
            trial_dirs = [d for d in optuna_models_dir.iterdir() if d.is_dir() and d.name.startswith('trial_')]
            if len(trial_dirs) > 10:  # 最新10個以外を削除
                trial_dirs.sort(key=lambda x: x.stat().st_mtime, reverse=True)
                for trial_dir in trial_dirs[10:]:
                    try:
                        shutil.rmtree(trial_dir)
                        logger.info(f"削除: {trial_dir}")
                    except Exception as e:
                        logger.error(f"削除失敗: {trial_dir} - {e}")
        
        # optuna_logs内のtrialディレクトリ
        optuna_logs_dir = self.project_root / "optuna_logs"
        if optuna_logs_dir.exists():
            trial_dirs = [d for d in optuna_logs_dir.iterdir() if d.is_dir() and d.name.startswith('trial_')]
            if len(trial_dirs) > 10:  # 最新10個以外を削除
                trial_dirs.sort(key=lambda x: x.stat().st_mtime, reverse=True)
                for trial_dir in trial_dirs[10:]:
                    try:
                        shutil.rmtree(trial_dir)
                        logger.info(f"削除: {trial_dir}")
                    except Exception as e:
                        logger.error(f"削除失敗: {trial_dir} - {e}")
    
    def cleanup_temp_files(self):
        """一時ファイルのクリーンアップ"""
        temp_patterns = [
            "**/__pycache__",
            "**/.pytest_cache",
            "**/*.tmp",
            "**/*.temp",
            "**/*.log.bak"
        ]
        
        for pattern in temp_patterns:
            for file_path in self.project_root.glob(pattern):
                try:
                    if file_path.is_file():
                        file_path.unlink()
                        logger.info(f"削除: {file_path}")
                    elif file_path.is_dir():
                        shutil.rmtree(file_path)
                        logger.info(f"削除: {file_path}")
                except Exception as e:
                    logger.error(f"削除失敗: {file_path} - {e}")
    
    def run_cleanup(self):
        """クリーンアップを実行"""
        logger.info("自動クリーンアップを開始")
        
        # ディスク容量チェック
        if self.check_disk_usage():
            logger.warning("ディスク容量が不足しています。緊急クリーンアップを実行します。")
        
        # 各ターゲットのクリーンアップ
        for target, settings in self.config["targets"].items():
            if not settings["enabled"]:
                continue
                
            logger.info(f"クリーンアップ実行: {target}")
            
            if "logs" in target:
                self.cleanup_logs(
                    target,
                    settings.get("max_files", 10),
                    settings.get("max_size_mb", 100)
                )
            elif "checkpoints" in target:
                self.cleanup_checkpoints(
                    target,
                    settings.get("max_files", 5),
                    settings.get("max_size_mb", 500)
                )
            elif "archives" in target:
                self.cleanup_archives(
                    target,
                    settings.get("max_files", 20),
                    settings.get("max_size_mb", 1000)
                )
        
        # trialディレクトリのクリーンアップ
        self.cleanup_trial_directories()
        
        # 一時ファイルのクリーンアップ
        self.cleanup_temp_files()
        
        logger.info("自動クリーンアップ完了")
    
    def generate_report(self):
        """クリーンアップレポートを生成"""
        report = {
            "timestamp": datetime.now().isoformat(),
            "disk_usage": {
                "total_gb": psutil.disk_usage(self.project_root).total / (1024**3),
                "used_gb": psutil.disk_usage(self.project_root).used / (1024**3),
                "free_gb": psutil.disk_usage(self.project_root).free / (1024**3),
                "usage_percent": (psutil.disk_usage(self.project_root).used / psutil.disk_usage(self.project_root).total) * 100
            },
            "directories": {}
        }
        
        # 主要ディレクトリのサイズをチェック
        key_dirs = [
            "optuna_models", "optuna_logs", "optuna_tensorboard",
            "outputs", "archives", "kyotei_predictor"
        ]
        
        for dir_name in key_dirs:
            dir_path = self.project_root / dir_name
            if dir_path.exists():
                total_size = sum(f.stat().st_size for f in dir_path.rglob('*') if f.is_file())
                report["directories"][dir_name] = {
                    "size_mb": total_size / (1024 * 1024),
                    "file_count": len(list(dir_path.rglob('*')))
                }
        
        # レポートを保存
        try:
            report_path = self.project_root / "cleanup_report.json"
            with open(report_path, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            
            logger.info(f"レポート生成完了: {report_path}")
        except Exception as e:
            logger.warning(f"レポート保存でエラーが発生: {e}")
            # レポートは返すが、保存は失敗
        return report

def main():
    parser = argparse.ArgumentParser(description='自動クリーンアップスクリプト')
    parser.add_argument('--config', default='cleanup_config.json', help='設定ファイルパス')
    parser.add_argument('--project-root', help='プロジェクトルートパス')
    parser.add_argument('--report-only', action='store_true', help='レポートのみ生成')
    parser.add_argument('--dry-run', action='store_true', help='実際の削除は行わない')
    
    args = parser.parse_args()
    
    cleanup = AutoCleanup(args.config, args.project_root)
    
    if args.report_only:
        report = cleanup.generate_report()
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        cleanup.run_cleanup()
        cleanup.generate_report()

if __name__ == "__main__":
    main() 