#!/usr/bin/env python3
"""
性能監視システム
モデルの性能指標を追跡し、改善状況を監視する
"""

import os
import sys
import json
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime
from typing import Dict, Any, List, Optional
import logging

# プロジェクトルートをパスに追加
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

class PerformanceMonitor:
    """
    性能監視システム
    
    特徴:
    - 的中率、報酬、学習効率の追跡
    - 性能推移の可視化
    - 改善目標との比較
    - 自動レポート生成
    """
    
    def __init__(self, output_dir: str = "kyotei_predictor/monitoring"):
        self.output_dir = output_dir
        self.metrics = {}
        self.targets = {
            'hit_rate': 4.0,  # 的中率目標
            'reward_stability': 80.0,  # 報酬安定性目標
            'mean_reward': 30.0,  # 平均報酬目標
            'learning_efficiency': 25.0  # 学習効率目標
        }
        
        os.makedirs(output_dir, exist_ok=True)
    
    def track_metrics(self, model_path: str, eval_results: Dict[str, Any]) -> None:
        """
        性能指標の追跡
        
        Args:
            model_path: モデルパス
            eval_results: 評価結果
        """
        timestamp = datetime.now().isoformat()
        
        metrics = {
            'timestamp': timestamp,
            'model_path': model_path,
            'hit_rate': eval_results.get('hit_rate', 0),
            'mean_reward': eval_results.get('mean_reward', 0),
            'reward_stability': eval_results.get('positive_reward_rate', 0),
            'learning_efficiency': eval_results.get('learning_efficiency', 0),
            'std_reward': eval_results.get('std_reward', 0),
            'max_reward': eval_results.get('max_reward', 0),
            'min_reward': eval_results.get('min_reward', 0),
            'hit_type_analysis': eval_results.get('hit_type_analysis', {})
        }
        
        self.metrics[model_path] = metrics
        logging.info(f"Metrics tracked for {model_path}: {metrics}")
    
    def generate_report(self) -> Dict[str, Any]:
        """
        性能レポートの生成
        
        Returns:
            性能レポート
        """
        if not self.metrics:
            return {'message': 'No metrics available'}
        
        # 最新の性能指標
        latest_metrics = list(self.metrics.values())[-1]
        
        # 目標との比較
        performance_gaps = {}
        for metric, target in self.targets.items():
            current = latest_metrics.get(metric, 0)
            gap = target - current
            performance_gaps[metric] = {
                'current': current,
                'target': target,
                'gap': gap,
                'achievement_rate': (current / target * 100) if target > 0 else 0
            }
        
        # 性能推移
        timestamps = [m['timestamp'] for m in self.metrics.values()]
        hit_rates = [m['hit_rate'] for m in self.metrics.values()]
        mean_rewards = [m['mean_reward'] for m in self.metrics.values()]
        reward_stabilities = [m['reward_stability'] for m in self.metrics.values()]
        
        report = {
            'latest_metrics': latest_metrics,
            'performance_gaps': performance_gaps,
            'trends': {
                'timestamps': timestamps,
                'hit_rates': hit_rates,
                'mean_rewards': mean_rewards,
                'reward_stabilities': reward_stabilities
            },
            'summary': {
                'total_evaluations': len(self.metrics),
                'best_hit_rate': max(hit_rates) if hit_rates else 0,
                'best_mean_reward': max(mean_rewards) if mean_rewards else 0,
                'improvement_status': self._assess_improvement_status()
            }
        }
        
        return report
    
    def _assess_improvement_status(self) -> Dict[str, Any]:
        """
        改善状況の評価
        
        Returns:
            改善状況の評価結果
        """
        if len(self.metrics) < 2:
            return {'status': 'insufficient_data'}
        
        # 最新と過去の比較
        metrics_list = list(self.metrics.values())
        latest = metrics_list[-1]
        previous = metrics_list[-2]
        
        improvements = {}
        for metric in ['hit_rate', 'mean_reward', 'reward_stability']:
            current = latest.get(metric, 0)
            past = previous.get(metric, 0)
            improvement = current - past
            improvements[metric] = {
                'current': current,
                'previous': past,
                'improvement': improvement,
                'improvement_rate': (improvement / past * 100) if past != 0 else 0
            }
        
        # 全体的な改善状況
        positive_improvements = sum(1 for imp in improvements.values() if imp['improvement'] > 0)
        total_metrics = len(improvements)
        
        status = {
            'improvements': improvements,
            'positive_improvement_ratio': positive_improvements / total_metrics if total_metrics > 0 else 0,
            'overall_trend': 'improving' if positive_improvements > total_metrics / 2 else 'declining'
        }
        
        return status
    
    def save_metrics(self, filename: str = None) -> str:
        """
        メトリクスをファイルに保存
        
        Args:
            filename: ファイル名（Noneの場合は自動生成）
            
        Returns:
            保存されたファイルパス
        """
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"performance_metrics_{timestamp}.json"
        
        filepath = os.path.join(self.output_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.metrics, f, indent=2, ensure_ascii=False)
        
        logging.info(f"Metrics saved to {filepath}")
        return filepath
    
    def load_metrics(self, filepath: str) -> None:
        """
        メトリクスをファイルから読み込み
        
        Args:
            filepath: ファイルパス
        """
        with open(filepath, 'r', encoding='utf-8') as f:
            self.metrics = json.load(f)
        
        logging.info(f"Metrics loaded from {filepath}")
    
    def plot_performance_trends(self, save_path: str = None) -> None:
        """
        性能推移のプロット生成
        
        Args:
            save_path: 保存先パス
        """
        if not self.metrics:
            logging.warning("No metrics available for plotting")
            return
        
        metrics_list = list(self.metrics.values())
        timestamps = [m['timestamp'] for m in metrics_list]
        hit_rates = [m['hit_rate'] for m in metrics_list]
        mean_rewards = [m['mean_reward'] for m in metrics_list]
        reward_stabilities = [m['reward_stability'] for m in metrics_list]
        
        # プロット作成
        fig, axes = plt.subplots(2, 2, figsize=(15, 10))
        fig.suptitle('Performance Trends', fontsize=16)
        
        # 的中率の推移
        axes[0, 0].plot(range(len(hit_rates)), hit_rates, 'b-o')
        axes[0, 0].axhline(y=self.targets['hit_rate'], color='r', linestyle='--', label=f'Target: {self.targets["hit_rate"]}%')
        axes[0, 0].set_title('Hit Rate Trend')
        axes[0, 0].set_ylabel('Hit Rate (%)')
        axes[0, 0].legend()
        axes[0, 0].grid(True)
        
        # 平均報酬の推移
        axes[0, 1].plot(range(len(mean_rewards)), mean_rewards, 'g-o')
        axes[0, 1].axhline(y=self.targets['mean_reward'], color='r', linestyle='--', label=f'Target: {self.targets["mean_reward"]}')
        axes[0, 1].set_title('Mean Reward Trend')
        axes[0, 1].set_ylabel('Mean Reward')
        axes[0, 1].legend()
        axes[0, 1].grid(True)
        
        # 報酬安定性の推移
        axes[1, 0].plot(range(len(reward_stabilities)), reward_stabilities, 'm-o')
        axes[1, 0].axhline(y=self.targets['reward_stability'], color='r', linestyle='--', label=f'Target: {self.targets["reward_stability"]}%')
        axes[1, 0].set_title('Reward Stability Trend')
        axes[1, 0].set_ylabel('Reward Stability (%)')
        axes[1, 0].legend()
        axes[1, 0].grid(True)
        
        # 目標達成率
        achievement_rates = []
        for i, metrics in enumerate(metrics_list):
            hit_rate_achievement = (metrics['hit_rate'] / self.targets['hit_rate'] * 100) if self.targets['hit_rate'] > 0 else 0
            reward_achievement = (metrics['mean_reward'] / self.targets['mean_reward'] * 100) if self.targets['mean_reward'] > 0 else 0
            stability_achievement = (metrics['reward_stability'] / self.targets['reward_stability'] * 100) if self.targets['reward_stability'] > 0 else 0
            
            avg_achievement = (hit_rate_achievement + reward_achievement + stability_achievement) / 3
            achievement_rates.append(avg_achievement)
        
        axes[1, 1].plot(range(len(achievement_rates)), achievement_rates, 'c-o')
        axes[1, 1].axhline(y=100, color='r', linestyle='--', label='100% Achievement')
        axes[1, 1].set_title('Overall Achievement Rate')
        axes[1, 1].set_ylabel('Achievement Rate (%)')
        axes[1, 1].legend()
        axes[1, 1].grid(True)
        
        plt.tight_layout()
        
        if save_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            save_path = os.path.join(self.output_dir, f"performance_trends_{timestamp}.png")
        
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        logging.info(f"Performance trends plot saved to {save_path}")
    
    def generate_improvement_recommendations(self) -> List[str]:
        """
        改善推奨事項の生成
        
        Returns:
            改善推奨事項のリスト
        """
        if not self.metrics:
            return ["No metrics available for recommendations"]
        
        latest_metrics = list(self.metrics.values())[-1]
        recommendations = []
        
        # 的中率の改善推奨
        if latest_metrics['hit_rate'] < self.targets['hit_rate']:
            gap = self.targets['hit_rate'] - latest_metrics['hit_rate']
            recommendations.append(f"的中率改善が必要: 現在{latest_metrics['hit_rate']:.2f}% → 目標{self.targets['hit_rate']}% (差: {gap:.2f}%)")
        
        # 平均報酬の改善推奨
        if latest_metrics['mean_reward'] < self.targets['mean_reward']:
            gap = self.targets['mean_reward'] - latest_metrics['mean_reward']
            recommendations.append(f"平均報酬改善が必要: 現在{latest_metrics['mean_reward']:.2f} → 目標{self.targets['mean_reward']} (差: {gap:.2f})")
        
        # 報酬安定性の改善推奨
        if latest_metrics['reward_stability'] < self.targets['reward_stability']:
            gap = self.targets['reward_stability'] - latest_metrics['reward_stability']
            recommendations.append(f"報酬安定性改善が必要: 現在{latest_metrics['reward_stability']:.2f}% → 目標{self.targets['reward_stability']}% (差: {gap:.2f}%)")
        
        # 学習効率の改善推奨
        if latest_metrics.get('learning_efficiency', 0) < self.targets['learning_efficiency']:
            gap = self.targets['learning_efficiency'] - latest_metrics.get('learning_efficiency', 0)
            recommendations.append(f"学習効率改善が必要: 現在{latest_metrics.get('learning_efficiency', 0):.2f}倍 → 目標{self.targets['learning_efficiency']}倍 (差: {gap:.2f}倍)")
        
        if not recommendations:
            recommendations.append("すべての目標を達成しています！素晴らしい性能です。")
        
        return recommendations

def create_performance_monitor(output_dir: str = "kyotei_predictor/monitoring") -> PerformanceMonitor:
    """
    性能監視システムを作成
    
    Args:
        output_dir: 出力ディレクトリ
        
    Returns:
        性能監視システム
    """
    return PerformanceMonitor(output_dir)

if __name__ == "__main__":
    # テスト実行
    logging.basicConfig(level=logging.INFO)
    
    # 性能監視システムを作成
    monitor = create_performance_monitor()
    
    # サンプルメトリクスを追加
    sample_metrics = {
        'hit_rate': 1.70,
        'mean_reward': 4.83,
        'positive_reward_rate': 52.5,
        'learning_efficiency': 16.2,
        'std_reward': 15.2,
        'max_reward': 25.0,
        'min_reward': -100.0,
        'hit_type_analysis': {
            'win': 0.017,
            'first_second': 0.135,
            'first_only': 0.848
        }
    }
    
    # メトリクスを追跡
    monitor.track_metrics("sample_model_1", sample_metrics)
    
    # レポート生成
    report = monitor.generate_report()
    print("Performance Report:")
    print(json.dumps(report, indent=2, ensure_ascii=False))
    
    # 改善推奨事項
    recommendations = monitor.generate_improvement_recommendations()
    print("\nImprovement Recommendations:")
    for rec in recommendations:
        print(f"- {rec}")
    
    # メトリクス保存
    monitor.save_metrics()
    
    print(f"\nPerformance monitoring system initialized in {monitor.output_dir}") 