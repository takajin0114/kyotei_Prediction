"""
学習履歴可視化システム

このモジュールは、継続学習の履歴を可視化し、
学習の進捗を分析するための機能を提供します。
"""

import json
import matplotlib.pyplot as plt
import pandas as pd
from pathlib import Path
from typing import Dict, Any, List, Optional
import logging
from datetime import datetime

# ログ設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TrainingHistoryVisualizer:
    """学習履歴の可視化クラス"""
    
    def __init__(self, history_file: str = "training_history.json"):
        """
        初期化
        
        Args:
            history_file: 学習履歴ファイルのパス
        """
        self.history_file = Path(history_file)
        logger.info(f"TrainingHistoryVisualizer initialized: history_file={self.history_file}")
    
    def plot_performance_trend(self, save_path: Optional[str] = None) -> bool:
        """
        性能トレンドをプロット
        
        Args:
            save_path: 保存パス（指定された場合）
            
        Returns:
            プロット成功時True
        """
        try:
            if not self.history_file.exists():
                logger.warning("履歴ファイルが存在しません")
                return False
            
            with open(self.history_file, 'r', encoding='utf-8') as f:
                history = json.load(f)
            
            if not history:
                logger.warning("履歴データが空です")
                return False
            
            # データフレームに変換
            df = pd.DataFrame(history)
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            
            # 性能指標を抽出
            performance_data = []
            for _, row in df.iterrows():
                perf = row['performance']
                performance_data.append({
                    'timestamp': row['timestamp'],
                    'mean_reward': perf.get('mean_reward', 0),
                    'success_rate': perf.get('success_rate', 0),
                    'loss': perf.get('loss', 0)
                })
            
            perf_df = pd.DataFrame(performance_data)
            
            # プロット作成
            fig, axes = plt.subplots(2, 2, figsize=(15, 10))
            fig.suptitle('学習性能の推移', fontsize=16)
            
            # 平均報酬の推移
            axes[0, 0].plot(perf_df['timestamp'], perf_df['mean_reward'], 'b-o')
            axes[0, 0].set_title('平均報酬の推移')
            axes[0, 0].set_xlabel('日時')
            axes[0, 0].set_ylabel('平均報酬')
            axes[0, 0].tick_params(axis='x', rotation=45)
            axes[0, 0].grid(True)
            
            # 成功率の推移
            axes[0, 1].plot(perf_df['timestamp'], perf_df['success_rate'], 'g-o')
            axes[0, 1].set_title('成功率の推移')
            axes[0, 1].set_xlabel('日時')
            axes[0, 1].set_ylabel('成功率')
            axes[0, 1].tick_params(axis='x', rotation=45)
            axes[0, 1].grid(True)
            
            # 損失の推移
            axes[1, 0].plot(perf_df['timestamp'], perf_df['loss'], 'r-o')
            axes[1, 0].set_title('損失の推移')
            axes[1, 0].set_xlabel('日時')
            axes[1, 0].set_ylabel('損失')
            axes[1, 0].tick_params(axis='x', rotation=45)
            axes[1, 0].grid(True)
            
            # 学習回数の推移
            axes[1, 1].plot(range(len(perf_df)), perf_df['mean_reward'], 'm-o')
            axes[1, 1].set_title('学習回数 vs 平均報酬')
            axes[1, 1].set_xlabel('学習回数')
            axes[1, 1].set_ylabel('平均報酬')
            axes[1, 1].grid(True)
            
            plt.tight_layout()
            
            if save_path:
                plt.savefig(save_path, dpi=300, bbox_inches='tight')
                logger.info(f"プロットを保存: {save_path}")
            else:
                plt.show()
            
            return True
            
        except Exception as e:
            logger.error(f"性能トレンドプロット中にエラーが発生: {e}")
            return False
    
    def plot_training_lineage(self) -> bool:
        """
        学習系譜を表示
        
        Returns:
            表示成功時True
        """
        try:
            if not self.history_file.exists():
                logger.warning("履歴ファイルが存在しません")
                return False
            
            with open(self.history_file, 'r', encoding='utf-8') as f:
                history = json.load(f)
            
            if not history:
                logger.warning("履歴データが空です")
                return False
            
            print("=== 学習系譜 ===")
            for i, entry in enumerate(history):
                print(f"モデル {i+1}: {entry['model_path']}")
                print(f"  親モデル: {entry.get('parent_model', '新規')}")
                print(f"  性能: {entry['performance']}")
                print(f"  学習日時: {entry['timestamp']}")
                print(f"  データバージョン: {entry.get('data_version', 'N/A')}")
                print("---")
            
            return True
            
        except Exception as e:
            logger.error(f"学習系譜表示中にエラーが発生: {e}")
            return False
    
    def generate_performance_report(self) -> Optional[Dict[str, Any]]:
        """
        性能レポートを生成
        
        Returns:
            性能レポートの辞書、失敗時はNone
        """
        try:
            if not self.history_file.exists():
                logger.warning("履歴ファイルが存在しません")
                return None
            
            with open(self.history_file, 'r', encoding='utf-8') as f:
                history = json.load(f)
            
            if not history:
                logger.warning("履歴データが空です")
                return None
            
            latest = history[-1]
            first = history[0]
            
            # 性能指標を計算
            latest_perf = latest['performance']
            first_perf = first['performance']
            
            # 改善率を計算
            improvement_rate = self._calculate_improvement_rate(first_perf, latest_perf)
            
            # 学習期間を計算
            training_duration = self._calculate_training_duration(history)
            
            # 最高性能を検索
            best_performance = self._find_best_performance(history)
            
            # 統計情報を計算
            stats = self._calculate_statistics(history)
            
            report = {
                'total_training_sessions': len(history),
                'latest_performance': latest_perf,
                'first_performance': first_perf,
                'improvement_rate': improvement_rate,
                'training_duration': training_duration,
                'best_performance': best_performance,
                'statistics': stats,
                'report_generated_at': datetime.now().isoformat()
            }
            
            logger.info(f"性能レポートを生成: {len(history)}セッション")
            return report
            
        except Exception as e:
            logger.error(f"性能レポート生成中にエラーが発生: {e}")
            return None
    
    def export_history_to_csv(self, output_path: str) -> bool:
        """
        履歴をCSVファイルにエクスポート
        
        Args:
            output_path: 出力ファイルパス
            
        Returns:
            エクスポート成功時True
        """
        try:
            if not self.history_file.exists():
                logger.warning("履歴ファイルが存在しません")
                return False
            
            with open(self.history_file, 'r', encoding='utf-8') as f:
                history = json.load(f)
            
            if not history:
                logger.warning("履歴データが空です")
                return False
            
            # データフレームに変換
            df = pd.DataFrame(history)
            
            # 性能指標を展開
            performance_df = pd.json_normalize(df['performance'])
            df = pd.concat([df.drop('performance', axis=1), performance_df], axis=1)
            
            # CSVに保存
            df.to_csv(output_path, index=False, encoding='utf-8')
            logger.info(f"履歴をCSVにエクスポート: {output_path}")
            
            return True
            
        except Exception as e:
            logger.error(f"CSVエクスポート中にエラーが発生: {e}")
            return False
    
    def _calculate_improvement_rate(self, first: Dict[str, Any], latest: Dict[str, Any]) -> Dict[str, float]:
        """改善率を計算"""
        improvements = {}
        
        for metric in ['mean_reward', 'success_rate']:
            first_val = first.get(metric, 0)
            latest_val = latest.get(metric, 0)
            
            if first_val == 0:
                improvements[metric] = 0.0
            else:
                improvements[metric] = ((latest_val - first_val) / abs(first_val)) * 100
        
        return improvements
    
    def _calculate_training_duration(self, history: List[Dict[str, Any]]) -> str:
        """学習期間を計算"""
        if len(history) < 2:
            return "N/A"
        
        first_time = pd.to_datetime(history[0]['timestamp'])
        last_time = pd.to_datetime(history[-1]['timestamp'])
        duration = last_time - first_time
        
        return str(duration)
    
    def _find_best_performance(self, history: List[Dict[str, Any]]) -> Dict[str, Any]:
        """最高性能を検索"""
        best_entry = max(history, key=lambda x: x['performance'].get('mean_reward', 0))
        return {
            'performance': best_entry['performance'],
            'model_path': best_entry['model_path'],
            'timestamp': best_entry['timestamp']
        }
    
    def _calculate_statistics(self, history: List[Dict[str, Any]]) -> Dict[str, Any]:
        """統計情報を計算"""
        rewards = [entry['performance'].get('mean_reward', 0) for entry in history]
        success_rates = [entry['performance'].get('success_rate', 0) for entry in history]
        
        return {
            'mean_reward': {
                'mean': sum(rewards) / len(rewards) if rewards else 0,
                'max': max(rewards) if rewards else 0,
                'min': min(rewards) if rewards else 0,
                'std': pd.Series(rewards).std() if len(rewards) > 1 else 0
            },
            'success_rate': {
                'mean': sum(success_rates) / len(success_rates) if success_rates else 0,
                'max': max(success_rates) if success_rates else 0,
                'min': min(success_rates) if success_rates else 0,
                'std': pd.Series(success_rates).std() if len(success_rates) > 1 else 0
            }
        } 