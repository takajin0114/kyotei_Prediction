#!/usr/bin/env python3
"""
一括バッチ（run_data_maintenance.py）のスケジューラ用ラッパースクリプト

機能:
1. 前日分のデータ取得・欠損再取得・品質チェックを自動実行
2. 当日分のレース前データ取得・予測実行
3. 実行結果のログ管理・レポート生成
4. エラー時のアラート通知
5. 定期実行の履歴管理

使用方法:
    python -m kyotei_predictor.tools.scheduled_data_maintenance --run-now
    python -m kyotei_predictor.tools.scheduled_data_maintenance --schedule
    python -m kyotei_predictor.tools.scheduled_data_maintenance --test-run
    python -m kyotei_predictor.tools.scheduled_data_maintenance --prediction-only --predict-date 2024-07-12
"""

import os
import sys
import json
import argparse
import logging
import subprocess
import schedule
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# プロジェクトルートの設定
from kyotei_predictor.config.settings import Settings

PROJECT_ROOT = Settings.PROJECT_ROOT
LOGS_DIR = PROJECT_ROOT / Settings.LOGS_DIR.replace("/", os.sep)
OUTPUTS_DIR = PROJECT_ROOT / getattr(Settings, "ROOT_OUTPUTS_DIR", "outputs")

# 予想ツールのインポート
sys.path.append(str(PROJECT_ROOT))
from kyotei_predictor.tools.prediction_tool import PredictionTool

class ScheduledDataMaintenance:
    """一括バッチのスケジューラ用ラッパー"""
    
    def __init__(self, log_level=logging.INFO):
        self.setup_logging(log_level)
        self.alert_config = self.load_alert_config()
        self.prediction_tool = PredictionTool(log_level)
        
    def setup_logging(self, log_level):
        """ログ設定"""
        log_file = LOGS_DIR / f"scheduled_maintenance_{datetime.now().strftime('%Y%m%d')}.log"
        log_file.parent.mkdir(exist_ok=True)
        
        from kyotei_predictor.utils.logger import get_logging_format, get_logging_datefmt
        logging.basicConfig(
            level=log_level,
            format=get_logging_format(),
            datefmt=get_logging_datefmt(),
            handlers=[
                logging.FileHandler(log_file, encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
    def load_alert_config(self) -> Dict:
        """アラート設定の読み込み"""
        config_file = PROJECT_ROOT / "kyotei_predictor" / "config" / "alert_config.json"
        
        if config_file.exists():
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                self.logger.warning(f"アラート設定の読み込みに失敗: {e}")
        
        # デフォルト設定
        return {
            'email_enabled': False,
            'smtp_server': 'smtp.gmail.com',
            'smtp_port': 587,
            'sender_email': '',
            'sender_password': '',
            'recipient_emails': [],
            'alert_threshold': 'warning'  # critical, warning, info
        }
    
    def get_yesterday_date(self) -> str:
        """前日の日付を取得"""
        yesterday = datetime.now() - timedelta(days=1)
        return yesterday.strftime('%Y-%m-%d')
    
    def get_today_date(self) -> str:
        """今日の日付を取得"""
        return datetime.now().strftime('%Y-%m-%d')
    
    def run_data_maintenance(self, start_date: str = None, end_date: str = None, 
                           stadiums: str = "ALL", test_mode: bool = False) -> Tuple[bool, str]:
        """データメンテナンスバッチを実行"""
        try:
            # 日付が指定されていない場合は前日
            if not start_date:
                start_date = self.get_yesterday_date()
            if not end_date:
                end_date = start_date
            
            self.logger.info(f"データメンテナンス開始: {start_date} ～ {end_date}, 会場: {stadiums}")
            
            # コマンド構築
            cmd = [
                sys.executable, "-m", "kyotei_predictor.tools.batch.run_data_maintenance",
                "--start-date", start_date,
                "--end-date", end_date,
                "--stadiums", stadiums
            ]
            
            if test_mode:
                # test_modeの場合は実際には実行せず、コマンドのみ表示
                self.logger.info("テストモード: 実際の実行は行いません")
                self.logger.info(f"実行予定コマンド: {' '.join(cmd)}")
                return True, "テストモード: コマンド確認のみ"
            
            # バッチ実行
            self.logger.info(f"実行コマンド: {' '.join(cmd)}")
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding='utf-8',
                cwd=PROJECT_ROOT
            )
            
            # 結果判定
            success = result.returncode == 0
            
            if success:
                self.logger.info("データメンテナンス完了")
                if result.stdout:
                    self.logger.info(f"出力: {result.stdout}")
            else:
                self.logger.error(f"データメンテナンス失敗: {result.stderr}")
                if result.stdout:
                    self.logger.info(f"出力: {result.stdout}")
            
            return success, (result.stdout or "") + (result.stderr or "")
            
        except Exception as e:
            error_msg = f"データメンテナンス実行エラー: {str(e)}"
            self.logger.error(error_msg)
            return False, error_msg
    
    def run_quality_check(self, date: str = None) -> Tuple[bool, str]:
        """品質チェックを実行"""
        try:
            if not date:
                date = self.get_yesterday_date()
            
            self.logger.info(f"品質チェック開始: {date}")
            
            # 品質チェックコマンド
            cmd = [
                sys.executable, "-m", "kyotei_predictor.tools.data_quality_checker",
                "--date", date
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding='utf-8',
                cwd=PROJECT_ROOT
            )
            
            success = result.returncode == 0
            
            if success:
                self.logger.info("品質チェック完了")
            else:
                self.logger.error(f"品質チェック失敗: {result.stderr}")
            
            return success, (result.stdout or "") + (result.stderr or "")
            
        except Exception as e:
            error_msg = f"品質チェック実行エラー: {str(e)}"
            self.logger.error(error_msg)
            return False, error_msg
    
    def run_prediction(self, predict_date: Optional[str] = None, venues: Optional[List[str]] = None) -> Tuple[bool, str]:
        """予測実行"""
        try:
            if not predict_date:
                predict_date = self.get_today_date()
            
            self.logger.info(f"予測実行開始: {predict_date}")
            
            # 予想ツールで予測実行
            result = self.prediction_tool.predict_races(predict_date, venues or [])
            
            if result:
                # 結果保存
                output_path = self.prediction_tool.save_prediction_result(result)
                
                if output_path:
                    self.logger.info(f"予測完了: {len(result['predictions'])}レース")
                    return True, f"予測完了: {len(result['predictions'])}レース, 出力: {output_path}"
                else:
                    self.logger.error("予測結果の保存に失敗")
                    return False, "予測結果の保存に失敗"
            else:
                self.logger.error("予測の実行に失敗")
                return False, "予測の実行に失敗"
            
        except Exception as e:
            error_msg = f"予測実行エラー: {str(e)}"
            self.logger.error(error_msg)
            return False, error_msg
    
    def run_daily_maintenance(self):
        """日次メンテナンスの実行（前日データ取得 + 当日予測）"""
        try:
            self.logger.info("=== 日次データメンテナンス開始 ===")
            
            start_time = datetime.now()
            yesterday = self.get_yesterday_date()
            today = self.get_today_date()
            
            # 1. 前日データメンテナンスバッチ実行
            maintenance_success, maintenance_output = self.run_data_maintenance(
                start_date=yesterday,
                end_date=yesterday
            )
            
            # 2. 前日品質チェック実行
            quality_success, quality_output = self.run_quality_check(yesterday)
            
            # 3. 当日予測実行
            prediction_success, prediction_output = self.run_prediction(today)
            
            # 4. 実行結果の記録
            execution_record = {
                'execution_time': start_time.isoformat(),
                'date_processed': yesterday,
                'prediction_date': today,
                'maintenance_success': maintenance_success,
                'quality_success': quality_success,
                'prediction_success': prediction_success,
                'total_success': maintenance_success and quality_success and prediction_success,
                'maintenance_output': maintenance_output[:1000],  # 最初の1000文字のみ
                'quality_output': quality_output[:1000],  # 最初の1000文字のみ
                'prediction_output': prediction_output[:1000],  # 最初の1000文字のみ
                'duration_minutes': (datetime.now() - start_time).total_seconds() / 60
            }
            
            self.record_execution_result(execution_record)
            
            # 5. アラート判定
            if not execution_record['total_success']:
                self.send_alert(self.create_alert_message(execution_record), "error")
            
            self.logger.info("=== 日次データメンテナンス完了 ===")
            
            return execution_record
            
        except Exception as e:
            error_msg = f"日次メンテナンス実行中にエラーが発生: {str(e)}"
            self.logger.error(error_msg)
            self.send_alert(error_msg, "error")
            return None
    
    def create_alert_message(self, execution_record: Dict) -> str:
        """アラートメッセージの作成"""
        date = execution_record['date_processed']
        prediction_date = execution_record.get('prediction_date', 'N/A')
        success = execution_record['total_success']
        duration = execution_record['duration_minutes']
        
        message = f"""
データメンテナンス・予測アラート

処理日: {date}
予測日: {prediction_date}
実行時刻: {execution_record['execution_time']}
実行時間: {duration:.1f}分
結果: {'成功' if success else '失敗'}

=== 詳細 ===
データメンテナンス: {'成功' if execution_record['maintenance_success'] else '失敗'}
品質チェック: {'成功' if execution_record['quality_success'] else '失敗'}
予測実行: {'成功' if execution_record['prediction_success'] else '失敗'}

=== 出力ログ ===
{execution_record['maintenance_output'][:500]}...
"""
        return message
    
    def send_alert(self, message: str, level: str):
        """アラートの送信"""
        if not self.alert_config.get('email_enabled', False):
            self.logger.info(f"アラート（{level}）: {message}")
            return
        
        try:
            # メール送信の実装（簡略化）
            self.logger.info(f"アラートメール送信（{level}）: {message[:100]}...")
            
            # 実際のメール送信処理はここに実装
            # smtp_server = self.alert_config['smtp_server']
            # smtp_port = self.alert_config['smtp_port']
            # sender_email = self.alert_config['sender_email']
            # sender_password = self.alert_config['sender_password']
            # recipient_emails = self.alert_config['recipient_emails']
            
        except Exception as e:
            self.logger.error(f"アラート送信エラー: {e}")
    
    def record_execution_result(self, execution_record: Dict):
        """実行結果の記録"""
        # 実行履歴ファイルに記録
        history_file = OUTPUTS_DIR / "scheduled_maintenance_history.json"
        
        try:
            if history_file.exists():
                with open(history_file, 'r', encoding='utf-8') as f:
                    history = json.load(f)
            else:
                history = []
            
            history.append(execution_record)
            
            # 最新30件のみ保持
            if len(history) > 30:
                history = history[-30:]
            
            with open(history_file, 'w', encoding='utf-8') as f:
                json.dump(history, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            self.logger.error(f"実行結果記録エラー: {e}")
    
    def schedule_daily_maintenance(self, time_str: str = "02:00"):
        """日次メンテナンスのスケジューリング"""
        self.logger.info(f"日次データメンテナンス・予測をスケジュール: {time_str}")
        
        schedule.every().day.at(time_str).do(self.run_daily_maintenance)
        
        self.logger.info("スケジューラー開始。Ctrl+Cで停止してください。")
        
        try:
            while True:
                schedule.run_pending()
                time.sleep(60)  # 1分ごとにチェック
        except KeyboardInterrupt:
            self.logger.info("スケジューラーを停止しました")
    
    def run_test(self):
        """テスト実行"""
        self.logger.info("=== テスト実行開始 ===")
        
        # テスト用に前日ではなく2日前のデータで実行
        test_date = (datetime.now() - timedelta(days=2)).strftime('%Y-%m-%d')
        
        maintenance_success, maintenance_output = self.run_data_maintenance(
            start_date=test_date,
            end_date=test_date,
            test_mode=True
        )
        
        quality_success, quality_output = self.run_quality_check(test_date)
        
        # 予測テスト（今日の日付で）
        prediction_success, prediction_output = self.run_prediction(self.get_today_date())
        
        print(f"\n=== テスト実行結果 ===")
        print(f"テスト日: {test_date}")
        print(f"データメンテナンス: {'成功' if maintenance_success else '失敗'}")
        print(f"品質チェック: {'成功' if quality_success else '失敗'}")
        print(f"予測実行: {'成功' if prediction_success else '失敗'}")
        
        if maintenance_output:
            print(f"\nメンテナンス出力: {maintenance_output[:200]}...")
        
        if quality_output:
            print(f"\n品質チェック出力: {quality_output[:200]}...")
        
        if prediction_output:
            print(f"\n予測出力: {prediction_output[:200]}...")
        
        self.logger.info("=== テスト実行完了 ===")

def main():
    parser = argparse.ArgumentParser(description='一括バッチのスケジューラ用ラッパー')
    parser.add_argument('--run-now', action='store_true', help='今すぐメンテナンスを実行')
    parser.add_argument('--schedule', action='store_true', help='スケジューラーを開始')
    parser.add_argument('--time', type=str, default='02:00', help='実行時刻 (HH:MM)')
    parser.add_argument('--test-run', action='store_true', help='テスト実行')
    parser.add_argument('--prediction-only', action='store_true', help='予測のみ実行')
    parser.add_argument('--predict-date', type=str, help='予測対象日 (YYYY-MM-DD)')
    parser.add_argument('--venues', type=str, help='対象会場 (カンマ区切り)')
    parser.add_argument('--start-date', type=str, help='開始日 (YYYY-MM-DD)')
    parser.add_argument('--end-date', type=str, help='終了日 (YYYY-MM-DD)')
    parser.add_argument('--stadiums', type=str, default='ALL', help='対象会場')
    parser.add_argument('--verbose', action='store_true', help='詳細ログ出力')
    
    args = parser.parse_args()
    
    # ログレベル設定
    log_level = logging.DEBUG if args.verbose else logging.INFO
    
    # ラッパー初期化
    wrapper = ScheduledDataMaintenance(log_level)
    
    if args.test_run:
        # テスト実行
        wrapper.run_test()
    elif args.prediction_only:
        # 予測のみ実行
        venues = None
        if args.venues:
            venues = [v.strip() for v in args.venues.split(',')]
        
        success, output = wrapper.run_prediction(args.predict_date or None, venues)
        print(f"予測実行結果: {'成功' if success else '失敗'}")
        if output:
            print(f"出力: {output[:500]}...")
    elif args.run_now:
        # 今すぐ実行
        if args.start_date and args.end_date:
            # 指定日付で実行
            success, output = wrapper.run_data_maintenance(
                start_date=args.start_date,
                end_date=args.end_date,
                stadiums=args.stadiums
            )
            print(f"実行結果: {'成功' if success else '失敗'}")
            if output:
                print(f"出力: {output[:500]}...")
        else:
            # 日次メンテナンス実行
            wrapper.run_daily_maintenance()
    elif args.schedule:
        # スケジューラー開始
        wrapper.schedule_daily_maintenance(args.time)
    else:
        # デフォルト: 日次メンテナンス実行
        wrapper.run_daily_maintenance()

if __name__ == "__main__":
    main() 