"""
ContinuousLearningManagerのテスト

このテストスイートは、継続学習管理システムの基本機能を検証します。
"""

import pytest
import tempfile
import json
import os
from pathlib import Path
from datetime import datetime
from unittest.mock import patch, MagicMock

# テスト対象のモジュールをインポート
import sys
sys.path.append(str(Path(__file__).parent.parent.parent))

from tools.ai.continuous_learning_manager import ContinuousLearningManager


class TestContinuousLearningManager:
    """ContinuousLearningManagerのテストクラス"""
    
    @pytest.fixture
    def temp_dir(self):
        """一時ディレクトリの作成"""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield temp_dir
    
    @pytest.fixture
    def manager(self, temp_dir):
        """テスト用のマネージャーインスタンス"""
        model_dir = os.path.join(temp_dir, "models")
        history_file = os.path.join(temp_dir, "history.json")
        return ContinuousLearningManager(model_dir, history_file)
    
    def test_initialization(self, manager, temp_dir):
        """初期化のテスト"""
        assert manager.model_dir == Path(os.path.join(temp_dir, "models"))
        assert manager.history_file == Path(os.path.join(temp_dir, "history.json"))
        assert manager.performance_threshold == 0.01
        
        # ディレクトリが作成されていることを確認
        assert manager.model_dir.exists()
    
    def test_find_latest_model_no_files(self, manager):
        """モデルファイルが存在しない場合のテスト"""
        result = manager.find_latest_model()
        assert result is None
    
    def test_find_latest_model_with_files(self, manager, temp_dir):
        """モデルファイルが存在する場合のテスト"""
        # テスト用のモデルファイルを作成
        model_dir = manager.model_dir
        model_file1 = model_dir / "model1.zip"
        model_file2 = model_dir / "model2.zip"
        
        # ファイルを作成
        model_file1.touch()
        model_file2.touch()
        
        # 最新のファイルを取得
        result = manager.find_latest_model()
        assert result is not None
        assert result.name in ["model1.zip", "model2.zip"]
    
    def test_get_model_info(self, manager, temp_dir):
        """モデル情報取得のテスト"""
        # テスト用のモデルファイルを作成
        model_file = manager.model_dir / "test_model.zip"
        model_file.touch()
        
        info = manager.get_model_info(model_file)
        
        assert info['path'] == str(model_file)
        assert 'size' in info
        assert 'modified_time' in info
        assert 'created_time' in info
    
    def test_record_training_history(self, manager):
        """学習履歴記録のテスト"""
        model_path = "test_model.zip"
        performance_metrics = {
            'mean_reward': 0.5,
            'success_rate': 0.8,
            'loss': 0.1
        }
        
        # 履歴を記録
        result = manager.record_training_history(model_path, performance_metrics)
        assert result is True
        
        # 履歴ファイルが作成されていることを確認
        assert manager.history_file.exists()
        
        # 履歴の内容を確認
        with open(manager.history_file, 'r', encoding='utf-8') as f:
            history = json.load(f)
        
        assert len(history) == 1
        assert history[0]['model_path'] == model_path
        assert history[0]['performance'] == performance_metrics
        assert 'timestamp' in history[0]
        assert 'parent_model' in history[0]
        assert 'training_parameters' in history[0]
        assert 'data_version' in history[0]
    
    def test_should_continue_training_no_history(self, manager):
        """履歴が存在しない場合の継続学習判定テスト"""
        performance_metrics = {'mean_reward': 0.5}
        result = manager.should_continue_training(performance_metrics)
        assert result is True
    
    def test_should_continue_training_with_improvement(self, manager):
        """性能改善がある場合の継続学習判定テスト"""
        # 最初の履歴を記録
        initial_metrics = {'mean_reward': 0.3}
        manager.record_training_history("model1.zip", initial_metrics)
        
        # 改善された性能で判定
        improved_metrics = {'mean_reward': 0.5}  # 0.2の改善
        result = manager.should_continue_training(improved_metrics)
        assert result is True
    
    def test_should_continue_training_no_improvement(self, manager):
        """性能改善がない場合の継続学習判定テスト"""
        # 最初の履歴を記録
        initial_metrics = {'mean_reward': 0.5}
        manager.record_training_history("model1.zip", initial_metrics)
        
        # 改善されていない性能で判定
        same_metrics = {'mean_reward': 0.5}  # 改善なし
        result = manager.should_continue_training(same_metrics)
        assert result is False
    
    def test_get_training_lineage_empty(self, manager):
        """空の学習系譜取得テスト"""
        lineage = manager.get_training_lineage()
        assert lineage == []
    
    def test_get_training_lineage_with_history(self, manager):
        """履歴がある場合の学習系譜取得テスト"""
        # 履歴を記録
        metrics = {'mean_reward': 0.5}
        manager.record_training_history("model1.zip", metrics)
        
        lineage = manager.get_training_lineage()
        assert len(lineage) == 1
        assert lineage[0]['model_path'] == "model1.zip"
        assert lineage[0]['performance'] == metrics
    
    def test_get_training_parameters(self, manager):
        """学習パラメータ取得のテスト"""
        params = manager._get_training_parameters()
        
        expected_keys = [
            'learning_rate', 'n_steps', 'batch_size', 'n_epochs',
            'gamma', 'gae_lambda', 'clip_range', 'ent_coef',
            'vf_coef', 'max_grad_norm'
        ]
        
        for key in expected_keys:
            assert key in params
    
    def test_get_data_version(self, manager):
        """データバージョン取得のテスト"""
        version = manager._get_data_version()
        assert len(version) == 6  # YYYYMM形式
        assert version.isdigit()
    
    def test_error_handling_find_latest_model(self, manager):
        """モデル検索時のエラーハンドリングテスト"""
        # WindowsPathのglobメソッドは読み取り専用のため、別の方法でテスト
        with patch('pathlib.Path.glob', side_effect=Exception("Test error")):
            result = manager.find_latest_model()
            assert result is None
    
    def test_error_handling_record_history(self, manager):
        """履歴記録時のエラーハンドリングテスト"""
        with patch('builtins.open', side_effect=Exception("Test error")):
            result = manager.record_training_history("test.zip", {'mean_reward': 0.5})
            assert result is False


if __name__ == "__main__":
    # テストの実行
    pytest.main([__file__, "-v"]) 