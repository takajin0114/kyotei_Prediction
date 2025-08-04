"""
TrainingHistoryVisualizerのテスト

このテストスイートは、学習履歴可視化システムの基本機能を検証します。
"""

import pytest
import tempfile
import json
import os
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

# テスト対象のモジュールをインポート
import sys
sys.path.append(str(Path(__file__).parent.parent.parent))

from tools.ai.training_history_visualizer import TrainingHistoryVisualizer


class TestTrainingHistoryVisualizer:
    """TrainingHistoryVisualizerのテストクラス"""
    
    @pytest.fixture
    def temp_dir(self):
        """一時ディレクトリの作成"""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield temp_dir
    
    @pytest.fixture
    def sample_history_data(self):
        """サンプル履歴データ"""
        return [
            {
                'model_path': 'model1.zip',
                'timestamp': '2025-01-01T10:00:00',
                'performance': {
                    'mean_reward': 0.3,
                    'success_rate': 0.6,
                    'loss': 0.5
                },
                'parent_model': None,
                'training_parameters': {'learning_rate': 3e-4},
                'data_version': '202501'
            },
            {
                'model_path': 'model2.zip',
                'timestamp': '2025-01-02T10:00:00',
                'performance': {
                    'mean_reward': 0.5,
                    'success_rate': 0.7,
                    'loss': 0.3
                },
                'parent_model': 'model1.zip',
                'training_parameters': {'learning_rate': 3e-4},
                'data_version': '202501'
            },
            {
                'model_path': 'model3.zip',
                'timestamp': '2025-01-03T10:00:00',
                'performance': {
                    'mean_reward': 0.7,
                    'success_rate': 0.8,
                    'loss': 0.2
                },
                'parent_model': 'model2.zip',
                'training_parameters': {'learning_rate': 3e-4},
                'data_version': '202501'
            }
        ]
    
    @pytest.fixture
    def visualizer(self, temp_dir):
        """テスト用のビジュアライザーインスタンス"""
        history_file = os.path.join(temp_dir, "history.json")
        return TrainingHistoryVisualizer(history_file)
    
    def test_initialization(self, visualizer, temp_dir):
        """初期化のテスト"""
        expected_path = Path(os.path.join(temp_dir, "history.json"))
        assert visualizer.history_file == expected_path
    
    def test_plot_performance_trend_no_file(self, visualizer):
        """履歴ファイルが存在しない場合のプロットテスト"""
        result = visualizer.plot_performance_trend()
        assert result is False
    
    def test_plot_performance_trend_empty_data(self, visualizer):
        """空の履歴データの場合のプロットテスト"""
        # 空の履歴ファイルを作成
        with open(visualizer.history_file, 'w', encoding='utf-8') as f:
            json.dump([], f)
        
        result = visualizer.plot_performance_trend()
        assert result is False
    
    def test_plot_performance_trend_with_data(self, visualizer, sample_history_data):
        """履歴データがある場合のプロットテスト"""
        # 履歴ファイルを作成
        with open(visualizer.history_file, 'w', encoding='utf-8') as f:
            json.dump(sample_history_data, f)
        
        # プロットをファイルに保存
        save_path = visualizer.history_file.parent / "performance_trend.png"
        result = visualizer.plot_performance_trend(str(save_path))
        
        assert result is True
        assert save_path.exists()
    
    def test_plot_training_lineage_no_file(self, visualizer):
        """履歴ファイルが存在しない場合の系譜表示テスト"""
        result = visualizer.plot_training_lineage()
        assert result is False
    
    def test_plot_training_lineage_with_data(self, visualizer, sample_history_data):
        """履歴データがある場合の系譜表示テスト"""
        # 履歴ファイルを作成
        with open(visualizer.history_file, 'w', encoding='utf-8') as f:
            json.dump(sample_history_data, f)
        
        result = visualizer.plot_training_lineage()
        assert result is True
    
    def test_generate_performance_report_no_file(self, visualizer):
        """履歴ファイルが存在しない場合のレポート生成テスト"""
        result = visualizer.generate_performance_report()
        assert result is None
    
    def test_generate_performance_report_with_data(self, visualizer, sample_history_data):
        """履歴データがある場合のレポート生成テスト"""
        # 履歴ファイルを作成
        with open(visualizer.history_file, 'w', encoding='utf-8') as f:
            json.dump(sample_history_data, f)
        
        report = visualizer.generate_performance_report()
        
        assert report is not None
        assert report['total_training_sessions'] == 3
        assert 'latest_performance' in report
        assert 'first_performance' in report
        assert 'improvement_rate' in report
        assert 'training_duration' in report
        assert 'best_performance' in report
        assert 'statistics' in report
        assert 'report_generated_at' in report
    
    def test_export_history_to_csv_no_file(self, visualizer):
        """履歴ファイルが存在しない場合のCSVエクスポートテスト"""
        result = visualizer.export_history_to_csv("test.csv")
        assert result is False
    
    def test_export_history_to_csv_with_data(self, visualizer, sample_history_data):
        """履歴データがある場合のCSVエクスポートテスト"""
        # 履歴ファイルを作成
        with open(visualizer.history_file, 'w', encoding='utf-8') as f:
            json.dump(sample_history_data, f)
        
        csv_path = visualizer.history_file.parent / "history.csv"
        result = visualizer.export_history_to_csv(str(csv_path))
        
        assert result is True
        assert csv_path.exists()
    
    def test_calculate_improvement_rate(self, visualizer):
        """改善率計算のテスト"""
        first = {'mean_reward': 0.3, 'success_rate': 0.6}
        latest = {'mean_reward': 0.6, 'success_rate': 0.8}
        
        improvements = visualizer._calculate_improvement_rate(first, latest)
        
        assert 'mean_reward' in improvements
        assert 'success_rate' in improvements
        assert improvements['mean_reward'] == 100.0  # (0.6-0.3)/0.3 * 100
        assert abs(improvements['success_rate'] - 33.33) < 0.1  # (0.8-0.6)/0.6 * 100
    
    def test_calculate_training_duration(self, visualizer, sample_history_data):
        """学習期間計算のテスト"""
        duration = visualizer._calculate_training_duration(sample_history_data)
        assert duration != "N/A"
        assert "days" in duration or "hours" in duration
    
    def test_find_best_performance(self, visualizer, sample_history_data):
        """最高性能検索のテスト"""
        best = visualizer._find_best_performance(sample_history_data)
        
        assert best['performance']['mean_reward'] == 0.7  # 最高値
        assert best['model_path'] == 'model3.zip'
        assert 'timestamp' in best
    
    def test_calculate_statistics(self, visualizer, sample_history_data):
        """統計情報計算のテスト"""
        stats = visualizer._calculate_statistics(sample_history_data)
        
        assert 'mean_reward' in stats
        assert 'success_rate' in stats
        
        # mean_rewardの統計
        reward_stats = stats['mean_reward']
        assert 'mean' in reward_stats
        assert 'max' in reward_stats
        assert 'min' in reward_stats
        assert 'std' in reward_stats
        
        assert reward_stats['max'] == 0.7
        assert reward_stats['min'] == 0.3
        assert abs(reward_stats['mean'] - 0.5) < 0.01  # (0.3+0.5+0.7)/3
    
    def test_error_handling_plot_performance_trend(self, visualizer):
        """プロット時のエラーハンドリングテスト"""
        with patch('matplotlib.pyplot.subplots', side_effect=Exception("Test error")):
            result = visualizer.plot_performance_trend()
            assert result is False
    
    def test_error_handling_generate_report(self, visualizer):
        """レポート生成時のエラーハンドリングテスト"""
        with patch('builtins.open', side_effect=Exception("Test error")):
            result = visualizer.generate_performance_report()
            assert result is None


if __name__ == "__main__":
    # テストの実行
    pytest.main([__file__, "-v"]) 