"""
的中率監視システム

的中率の自動監視、アラート機能、傾向分析を提供します。
"""

import os
import json
import logging
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Tuple
from enum import Enum
import numpy as np

from kyotei_predictor.utils.compression import DataCompressor

logger = logging.getLogger(__name__)


class AlertType(Enum):
    """アラートタイプ"""
    WARNING = "warning"
    DANGER = "danger"
    SUCCESS = "success"


@dataclass
class HitRateAlert:
    """的中率アラート"""
    alert_type: AlertType
    message: str
    hit_rate: float
    threshold: float
    timestamp: str
    venue: Optional[str] = None
    race_number: Optional[int] = None


class HitRateMonitor:
    """的中率監視システム"""
    
    def __init__(self, config_file: str = "monitoring/hit_rate_config.json"):
        """
        Args:
            config_file: 設定ファイルパス
        """
        self.config_file = config_file
        self.compressor = DataCompressor()
        self.performance_history: List[Dict] = []
        
        # デフォルト閾値
        self.warning_threshold = 15.0
        self.danger_threshold = 10.0
        self.success_threshold = 20.0
        
        # 設定を読み込み
        self._load_config()
    
    def _load_config(self) -> None:
        """設定を読み込み"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    self.warning_threshold = config.get('warning_threshold', 15.0)
                    self.danger_threshold = config.get('danger_threshold', 10.0)
                    self.success_threshold = config.get('success_threshold', 20.0)
                    logger.info("的中率監視設定を読み込みました")
        except Exception as e:
            logger.warning(f"設定読み込みエラー: {e}")
    
    def _save_config(self) -> None:
        """設定を保存"""
        try:
            config = {
                'warning_threshold': self.warning_threshold,
                'danger_threshold': self.danger_threshold,
                'success_threshold': self.success_threshold,
                'updated_at': datetime.now().isoformat()
            }
            
            os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            logger.error(f"設定保存エラー: {e}")
    
    def monitor_hit_rate(self, hit_rate: float, venue: Optional[str] = None, 
                        race_number: Optional[int] = None) -> Optional[HitRateAlert]:
        """
        的中率を監視
        
        Args:
            hit_rate: 的中率（%）
            venue: 会場名
            race_number: レース番号
            
        Returns:
            アラート（閾値を超えた場合）、それ以外はNone
        """
        timestamp = datetime.now().isoformat()
        
        # パフォーマンス履歴に記録
        performance_record = {
            'hit_rate': hit_rate,
            'venue': venue,
            'race_number': race_number,
            'timestamp': timestamp
        }
        self.performance_history.append(performance_record)
        
        # アラート判定
        alert = None
        
        if hit_rate <= self.danger_threshold:
            alert = HitRateAlert(
                alert_type=AlertType.DANGER,
                message=f"的中率が危険レベルです: {hit_rate:.2f}%",
                hit_rate=hit_rate,
                threshold=self.danger_threshold,
                timestamp=timestamp,
                venue=venue,
                race_number=race_number
            )
        elif hit_rate <= self.warning_threshold:
            alert = HitRateAlert(
                alert_type=AlertType.WARNING,
                message=f"的中率が警告レベルです: {hit_rate:.2f}%",
                hit_rate=hit_rate,
                threshold=self.warning_threshold,
                timestamp=timestamp,
                venue=venue,
                race_number=race_number
            )
        elif hit_rate >= self.success_threshold:
            alert = HitRateAlert(
                alert_type=AlertType.SUCCESS,
                message=f"的中率が成功レベルです: {hit_rate:.2f}%",
                hit_rate=hit_rate,
                threshold=self.success_threshold,
                timestamp=timestamp,
                venue=venue,
                race_number=race_number
            )
        
        # 履歴を保存
        self._save_performance_history()
        
        # アラートを保存
        if alert:
            self._save_alert(alert)
        
        return alert
    
    def analyze_trend(self, days: int = 7) -> Dict[str, float]:
        """
        的中率の傾向を分析
        
        Args:
            days: 分析期間（日数）
            
        Returns:
            傾向分析結果
        """
        if not self.performance_history:
            return {}
        
        # 指定期間のデータを抽出
        cutoff_date = datetime.now() - timedelta(days=days)
        recent_data = [
            record for record in self.performance_history
            if datetime.fromisoformat(record['timestamp']) >= cutoff_date
        ]
        
        if not recent_data:
            return {}
        
        hit_rates = [record['hit_rate'] for record in recent_data]
        
        # 統計計算
        mean_rate = np.mean(hit_rates)
        std_rate = np.std(hit_rates)
        min_rate = np.min(hit_rates)
        max_rate = np.max(hit_rates)
        
        # 傾向計算（線形回帰）
        timestamps = [datetime.fromisoformat(record['timestamp']) for record in recent_data]
        days_since_start = [(ts - timestamps[0]).days for ts in timestamps]
        
        if len(days_since_start) > 1:
            trend_slope = np.polyfit(days_since_start, hit_rates, 1)[0]
        else:
            trend_slope = 0.0
        
        return {
            'mean_rate': mean_rate,
            'std_rate': std_rate,
            'min_rate': min_rate,
            'max_rate': max_rate,
            'trend_slope': trend_slope,
            'data_points': len(recent_data),
            'period_days': days
        }
    
    def should_retrain(self, current_hit_rate: float, min_improvement: float = 2.0) -> bool:
        """
        再学習が必要かどうかを判定
        
        Args:
            current_hit_rate: 現在の的中率
            min_improvement: 最小改善率
            
        Returns:
            再学習が必要な場合True
        """
        trend = self.analyze_trend(days=7)
        
        if not trend:
            return False
        
        # 傾向が悪化している場合
        if trend['trend_slope'] < -1.0:
            return True
        
        # 現在の的中率が警告レベル以下の場合
        if current_hit_rate <= self.warning_threshold:
            return True
        
        # 平均的中率が大幅に低下している場合
        if trend['mean_rate'] < (current_hit_rate - min_improvement):
            return True
        
        return False
    
    def _save_performance_history(self) -> None:
        """パフォーマンス履歴を保存"""
        try:
            # 履歴ファイルのディレクトリを作成
            history_dir = "monitoring"
            os.makedirs(history_dir, exist_ok=True)
            history_file = os.path.join(history_dir, "performance_history.json")
            
            # 履歴データを辞書形式で保存
            history_data = {
                'performance_history': self.performance_history,
                'timestamp': datetime.now().isoformat(),
                'total_entries': len(self.performance_history)
            }
            self.compressor.save_compressed_json(history_data, history_file)
            
        except Exception as e:
            logger.error(f"履歴保存エラー: {e}")
    
    def _save_alert(self, alert: HitRateAlert) -> None:
        """アラートを保存"""
        try:
            alert_dir = "alerts"
            os.makedirs(alert_dir, exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            alert_file = os.path.join(alert_dir, f"hit_rate_alert_{timestamp}.json")
            
            alert_data = asdict(alert)
            alert_data['alert_type'] = alert.alert_type.value
            
            self.compressor.save_compressed_json(alert_data, alert_file)
            logger.info(f"アラート保存: {alert_file}")
            
        except Exception as e:
            logger.error(f"アラート保存エラー: {e}")
    
    def get_performance_summary(self) -> Dict[str, any]:
        """パフォーマンスサマリーを取得"""
        if not self.performance_history:
            return {}
        
        hit_rates = [record['hit_rate'] for record in self.performance_history]
        
        return {
            'total_races': len(self.performance_history),
            'average_hit_rate': np.mean(hit_rates),
            'best_hit_rate': np.max(hit_rates),
            'worst_hit_rate': np.min(hit_rates),
            'recent_trend': self.analyze_trend(days=7),
            'last_updated': datetime.now().isoformat()
        }


def create_hit_rate_monitor(config_file: str = "monitoring/hit_rate_config.json") -> HitRateMonitor:
    """的中率監視システムを作成（便利関数）"""
    return HitRateMonitor(config_file) 