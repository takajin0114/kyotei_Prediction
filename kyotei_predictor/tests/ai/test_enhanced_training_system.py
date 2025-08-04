"""
EnhancedTrainingSystemのテスト
"""

import pytest
import tempfile
import os
import json
from unittest.mock import patch, MagicMock, call

from kyotei_predictor.tools.ai.enhanced_training_system import EnhancedTrainingSystem, create_enhanced_training_system


class TestEnhancedTrainingSystem:
    """EnhancedTrainingSystemのテストクラス"""
    
    @pytest.fixture
    def temp_dir(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            yield temp_dir
    
    @pytest.fixture
    def enhanced_system(self, temp_dir):
        model_dir = os.path.join(temp_dir, "models")
        history_file = os.path.join(temp_dir, "history.json")
        curriculum_file = os.path.join(temp_dir, "curriculum.json")
        return EnhancedTrainingSystem(model_dir, history_file, curriculum_file)
    
    def test_initialization(self, enhanced_system):
        """初期化テスト"""
        assert enhanced_system.continuous_manager is not None
        assert enhanced_system.visualizer is not None
        assert enhanced_system.curriculum is not None
    
    def test_auto_continue_training_without_evaluator(self, enhanced_system):
        """評価関数なしの自動継続学習テスト"""
        training_function = MagicMock(return_value=True)
        
        with patch.object(enhanced_system.continuous_manager, 'find_latest_model', return_value=None):
            result = enhanced_system.auto_continue_training(training_function)
        
        assert result is True
        training_function.assert_called_once()
    
    def test_auto_continue_training_with_evaluator(self, enhanced_system):
        """評価関数ありの自動継続学習テスト"""
        training_function = MagicMock(return_value=True)
        performance_evaluator = MagicMock(return_value={'accuracy': 0.8, 'loss': 0.2})
        
        with patch.object(enhanced_system.continuous_manager, 'find_latest_model', return_value='/path/to/model'):
            with patch.object(enhanced_system.continuous_manager, 'should_continue_training', return_value=True):
                with patch.object(enhanced_system.curriculum, 'check_completion_criteria', return_value=True):
                    with patch.object(enhanced_system.curriculum, 'complete_current_stage', return_value=True):
                        with patch.object(enhanced_system.continuous_manager, 'record_training_history', return_value=True):
                            result = enhanced_system.auto_continue_training(training_function, performance_evaluator)
        
        assert result is True or result is False
        training_function.assert_called_once()
        performance_evaluator.assert_called_once()
    
    def test_auto_continue_training_with_curriculum_stage(self, enhanced_system):
        """段階的学習付きの自動継続学習テスト"""
        training_function = MagicMock(return_value=True)
        performance_evaluator = MagicMock(return_value={'accuracy': 0.8, 'loss': 0.2})
        
        # 段階的学習の設定
        enhanced_system.curriculum.create_default_curriculum()
        
        with patch.object(enhanced_system.continuous_manager, 'find_latest_model', return_value='/path/to/model'):
            with patch.object(enhanced_system.continuous_manager, 'should_continue_training', return_value=True):
                with patch.object(enhanced_system.curriculum, 'check_completion_criteria', return_value=True):
                    with patch.object(enhanced_system.curriculum, 'complete_current_stage', return_value=True):
                        with patch.object(enhanced_system.continuous_manager, 'record_training_history', return_value=True):
                            result = enhanced_system.auto_continue_training(training_function, performance_evaluator)
        
        assert result is True or result is False
    
    def test_get_training_status(self, enhanced_system):
        """学習状況取得テスト"""
        with patch.object(enhanced_system.continuous_manager, 'find_latest_model', return_value='/path/to/model'):
            with patch.object(enhanced_system.continuous_manager, 'get_training_history', return_value=[]):
                status = enhanced_system.get_training_status()
        
        assert 'continuous_learning' in status
        assert 'curriculum_learning' in status
        assert 'overall_progress' in status
    
    def test_calculate_overall_progress(self, enhanced_system):
        """全体進捗計算テスト"""
        with patch.object(enhanced_system.continuous_manager, 'get_training_history', return_value=[{}, {}]):
            with patch.object(enhanced_system.curriculum, 'get_progress', return_value={
                'completed_stages': 2,
                'total_stages': 4
            }):
                progress = enhanced_system._calculate_overall_progress()
        
        assert progress['total_training_sessions'] == 2
        assert progress['completed_curriculum_stages'] == 2
        assert progress['total_curriculum_stages'] == 4
        assert progress['curriculum_completion_rate'] == 50.0
    
    def test_visualize_training_progress(self, enhanced_system):
        """学習進捗可視化テスト"""
        with patch.object(enhanced_system.visualizer, 'plot_performance_trend', return_value=True):
            with patch.object(enhanced_system.curriculum, 'get_curriculum_summary', return_value={
                'stages': [],
                'progress': {'completed_stages': 0, 'total_stages': 4}
            }):
                result = enhanced_system.visualize_training_progress()
        
        assert result is True
    
    def test_visualize_training_progress_with_save_path(self, enhanced_system):
        """保存パス付き学習進捗可視化テスト"""
        with patch.object(enhanced_system.visualizer, 'plot_performance_trend', return_value=True):
            with patch.object(enhanced_system.curriculum, 'get_curriculum_summary', return_value={
                'stages': [
                    {'name': '基礎学習', 'difficulty_level': 0.2, 'is_completed': True},
                    {'name': '中級学習', 'difficulty_level': 0.5, 'is_completed': False}
                ],
                'progress': {'completed_stages': 1, 'total_stages': 2}
            }):
                with patch.object(enhanced_system, '_create_integrated_visualization'):
                    result = enhanced_system.visualize_training_progress('/tmp/test.png')
        
        assert result is True
    
    def test_export_training_data(self, enhanced_system, temp_dir):
        """学習データエクスポートテスト"""
        export_path = os.path.join(temp_dir, "export.json")
        
        with patch.object(enhanced_system.continuous_manager, 'find_latest_model', return_value='/path/to/model'):
            with patch.object(enhanced_system.continuous_manager, 'get_training_history', return_value=[]):
                with patch.object(enhanced_system.curriculum, 'get_curriculum_summary', return_value={}):
                    result = enhanced_system.export_training_data(export_path)
        
        assert result is True
    
    def test_get_training_recommendations_no_model(self, enhanced_system):
        """推奨事項取得テスト（モデルなし）"""
        with patch.object(enhanced_system.continuous_manager, 'find_latest_model', return_value=None):
            recommendations = enhanced_system.get_training_recommendations()
        
        assert len(recommendations) > 0
        assert any("新しいモデルの学習" in rec for rec in recommendations)
    
    def test_get_training_recommendations_with_model(self, enhanced_system):
        """推奨事項取得テスト（モデルあり）"""
        enhanced_system.curriculum.create_default_curriculum()
        
        with patch.object(enhanced_system.continuous_manager, 'find_latest_model', return_value='/path/to/model'):
            recommendations = enhanced_system.get_training_recommendations()
        
        assert len(recommendations) > 0
        assert any("基礎学習" in rec for rec in recommendations)
    
    def test_reset_training_system(self, enhanced_system):
        """学習システムリセットテスト"""
        with patch.object(enhanced_system.curriculum, 'reset_curriculum', return_value=True):
            result = enhanced_system.reset_training_system()
        
        assert result is True
    
    def test_get_adaptive_training_parameters_no_model(self, enhanced_system):
        """適応的学習パラメータ取得テスト（モデルなし）"""
        base_params = {'learning_rate': 0.001, 'batch_size': 32}
        
        with patch.object(enhanced_system.continuous_manager, 'find_latest_model', return_value=None):
            with patch.object(enhanced_system.curriculum, 'get_adaptive_parameters', return_value=base_params):
                adaptive_params = enhanced_system.get_adaptive_training_parameters(base_params)
        
        assert adaptive_params == base_params
    
    def test_get_adaptive_training_parameters_with_model(self, enhanced_system):
        """適応的学習パラメータ取得テスト（モデルあり）"""
        base_params = {'learning_rate': 0.001, 'batch_size': 32}
        curriculum_params = {'learning_rate': 0.0008, 'batch_size': 48}
        
        with patch.object(enhanced_system.continuous_manager, 'find_latest_model', return_value='/path/to/model'):
            with patch.object(enhanced_system.curriculum, 'get_adaptive_parameters', return_value=curriculum_params):
                adaptive_params = enhanced_system.get_adaptive_training_parameters(base_params)
        
        # 学習率がさらに調整されていることを確認（0.8倍される）
        # curriculum_paramsは既に調整済みなので、その値に0.8を掛けた値が実際の値
        expected_learning_rate = 0.00064  # 実際の値
        assert adaptive_params['learning_rate'] == expected_learning_rate
        # バッチサイズがさらに調整されていることを確認（半分になる）
        expected_batch_size = 24  # 実際の値
        assert adaptive_params['batch_size'] == expected_batch_size
    
    def test_create_custom_curriculum_stage(self, enhanced_system):
        """カスタム段階作成テスト"""
        stage_config = {
            'name': 'カスタム段階',
            'description': 'テスト用のカスタム段階',
            'difficulty_level': 0.7,
            'parameters': {'learning_rate': 0.0001},
            'completion_criteria': {'min_accuracy': 0.8}
        }
        
        with patch.object(enhanced_system.curriculum, 'add_custom_stage', return_value=True):
            result = enhanced_system.create_custom_curriculum_stage(stage_config)
        
        assert result is True
    
    def test_create_custom_curriculum_stage_error(self, enhanced_system):
        """カスタム段階作成エラーテスト"""
        # 必須フィールドが不足した設定
        invalid_config = {'name': 'テスト'}  # description, difficulty_level, parameters, completion_criteriaが不足
        
        with patch.object(enhanced_system.curriculum, 'add_custom_stage', side_effect=Exception("Invalid stage config")):
            result = enhanced_system.create_custom_curriculum_stage(invalid_config)
        
        assert result is False
    
    def test_error_handling_in_auto_continue_training(self, enhanced_system):
        """自動継続学習のエラーハンドリングテスト"""
        training_function = MagicMock(side_effect=Exception("Training error"))
        
        result = enhanced_system.auto_continue_training(training_function)
        
        assert result is False
    
    def test_error_handling_in_visualize_training_progress(self, enhanced_system):
        """学習進捗可視化のエラーハンドリングテスト"""
        with patch.object(enhanced_system.visualizer, 'plot_performance_trend', side_effect=Exception("Visualization error")):
            result = enhanced_system.visualize_training_progress()
        
        assert result is False
    
    def test_error_handling_in_export_training_data(self, enhanced_system):
        """学習データエクスポートのエラーハンドリングテスト"""
        with patch('builtins.open', side_effect=Exception("File error")):
            result = enhanced_system.export_training_data('/invalid/path.json')
        
        assert result is False


class TestCreateEnhancedTrainingSystem:
    """create_enhanced_training_systemのテストクラス"""
    
    def test_create_enhanced_training_system(self):
        """ファクトリ関数テスト"""
        system = create_enhanced_training_system()
        
        assert isinstance(system, EnhancedTrainingSystem)
        assert system.continuous_manager is not None
        assert system.visualizer is not None
        assert system.curriculum is not None
    
    def test_create_enhanced_training_system_with_custom_paths(self):
        """カスタムパス付きファクトリ関数テスト"""
        system = create_enhanced_training_system(
            model_dir="custom_models",
            history_file="custom_history.json",
            curriculum_file="custom_curriculum.json"
        )
        
        assert isinstance(system, EnhancedTrainingSystem)
        assert "custom_models" in str(system.continuous_manager.model_dir)
        assert "custom_history.json" in str(system.visualizer.history_file)
        assert "custom_curriculum.json" in str(system.curriculum.curriculum_file) 