"""
CurriculumLearningクラスのテスト
"""

import pytest
import tempfile
import os
import json
from pathlib import Path
from unittest.mock import patch, MagicMock

from kyotei_predictor.tools.ai.curriculum_learning import CurriculumLearning, CurriculumStage


class TestCurriculumLearning:
    """CurriculumLearningのテストクラス"""
    
    @pytest.fixture
    def temp_dir(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            yield temp_dir
    
    @pytest.fixture
    def curriculum_file(self, temp_dir):
        return os.path.join(temp_dir, "curriculum_config.json")
    
    @pytest.fixture
    def curriculum(self, curriculum_file):
        return CurriculumLearning(curriculum_file)
    
    def test_initialization(self, curriculum):
        """初期化テスト"""
        assert curriculum.stages == []
        assert curriculum.current_stage_index == 0
        assert curriculum.curriculum_history == []
    
    def test_create_default_curriculum(self, curriculum):
        """デフォルトカリキュラム作成テスト"""
        result = curriculum.create_default_curriculum()
        assert result is True
        assert len(curriculum.stages) == 4
        
        # 各段階の確認
        stage_names = [stage.name for stage in curriculum.stages]
        expected_names = ["基礎学習", "中級学習", "上級学習", "最適化学習"]
        assert stage_names == expected_names
        
        # 難易度レベルの確認
        difficulty_levels = [stage.difficulty_level for stage in curriculum.stages]
        expected_levels = [0.2, 0.5, 0.8, 1.0]
        assert difficulty_levels == expected_levels
    
    def test_get_current_stage_empty(self, curriculum):
        """空のカリキュラムでの現在段階取得テスト"""
        current_stage = curriculum.get_current_stage()
        assert current_stage is None
    
    def test_get_current_stage_with_stages(self, curriculum):
        """段階がある場合の現在段階取得テスト"""
        curriculum.create_default_curriculum()
        current_stage = curriculum.get_current_stage()
        assert current_stage is not None
        assert current_stage.name == "基礎学習"
    
    def test_get_next_stage(self, curriculum):
        """次の段階取得テスト"""
        curriculum.create_default_curriculum()
        next_stage = curriculum.get_next_stage()
        assert next_stage is not None
        assert next_stage.name == "中級学習"
    
    def test_get_next_stage_last(self, curriculum):
        """最後の段階での次の段階取得テスト"""
        curriculum.create_default_curriculum()
        curriculum.current_stage_index = 3  # 最後の段階
        next_stage = curriculum.get_next_stage()
        assert next_stage is None
    
    def test_get_stage_parameters(self, curriculum):
        """段階パラメータ取得テスト"""
        curriculum.create_default_curriculum()
        params = curriculum.get_stage_parameters()
        assert isinstance(params, dict)
        assert "learning_rate" in params
        assert "batch_size" in params
        assert "epochs" in params
    
    def test_check_completion_criteria_success(self, curriculum):
        """完了条件チェック成功テスト"""
        curriculum.create_default_curriculum()
        performance_metrics = {
            "accuracy": 0.75,
            "loss": 0.3,
            "epochs": 100
        }
        result = curriculum.check_completion_criteria(performance_metrics)
        assert result is True
    
    def test_check_completion_criteria_failure_accuracy(self, curriculum):
        """完了条件チェック失敗テスト（精度不足）"""
        curriculum.create_default_curriculum()
        performance_metrics = {
            "accuracy": 0.5,  # 基準値0.6未満
            "loss": 0.3,
            "epochs": 100
        }
        result = curriculum.check_completion_criteria(performance_metrics)
        assert result is False
    
    def test_check_completion_criteria_failure_loss(self, curriculum):
        """完了条件チェック失敗テスト（損失過大）"""
        curriculum.create_default_curriculum()
        performance_metrics = {
            "accuracy": 0.75,
            "loss": 0.6,  # 基準値0.5超過
            "epochs": 100
        }
        result = curriculum.check_completion_criteria(performance_metrics)
        assert result is False
    
    def test_check_completion_criteria_failure_epochs(self, curriculum):
        """完了条件チェック失敗テスト（エポック数不足）"""
        curriculum.create_default_curriculum()
        performance_metrics = {
            "accuracy": 0.75,
            "loss": 0.3,
            "epochs": 30  # 基準値50未満
        }
        result = curriculum.check_completion_criteria(performance_metrics)
        assert result is False
    
    def test_complete_current_stage_success(self, curriculum):
        """段階完了成功テスト"""
        curriculum.create_default_curriculum()
        performance_metrics = {
            "accuracy": 0.75,
            "loss": 0.3,
            "epochs": 100
        }
        result = curriculum.complete_current_stage(performance_metrics)
        assert result is True
        
        # 段階が完了としてマークされているか確認
        current_stage = curriculum.get_current_stage()
        assert current_stage.name == "中級学習"  # 次の段階に進んでいる
        assert curriculum.stages[0].is_completed is True
        assert curriculum.stages[0].completed_at is not None
    
    def test_complete_current_stage_failure(self, curriculum):
        """段階完了失敗テスト"""
        curriculum.create_default_curriculum()
        performance_metrics = {
            "accuracy": 0.5,  # 基準値未満
            "loss": 0.3,
            "epochs": 100
        }
        result = curriculum.complete_current_stage(performance_metrics)
        assert result is False
        
        # 段階が完了としてマークされていないか確認
        assert curriculum.stages[0].is_completed is False
    
    def test_is_curriculum_completed_false(self, curriculum):
        """カリキュラム完了チェック（未完了）"""
        curriculum.create_default_curriculum()
        result = curriculum.is_curriculum_completed()
        assert result is False
    
    def test_is_curriculum_completed_true(self, curriculum):
        """カリキュラム完了チェック（完了）"""
        curriculum.create_default_curriculum()
        curriculum.current_stage_index = 4  # 全段階完了
        result = curriculum.is_curriculum_completed()
        assert result is True
    
    def test_get_progress(self, curriculum):
        """進捗取得テスト"""
        curriculum.create_default_curriculum()
        progress = curriculum.get_progress()
        
        assert progress['total_stages'] == 4
        assert progress['completed_stages'] == 0
        assert progress['current_stage_index'] == 0
        assert progress['progress_percentage'] == 0.0
        assert progress['current_stage'] == "基礎学習"
        assert progress['is_completed'] is False
    
    def test_get_progress_partial_completion(self, curriculum):
        """部分完了時の進捗取得テスト"""
        curriculum.create_default_curriculum()
        
        # 最初の段階を完了
        curriculum.stages[0].is_completed = True
        curriculum.current_stage_index = 1
        
        progress = curriculum.get_progress()
        assert progress['completed_stages'] == 1
        assert progress['progress_percentage'] == 25.0
        assert progress['current_stage'] == "中級学習"
    
    def test_get_curriculum_summary(self, curriculum):
        """カリキュラム概要取得テスト"""
        curriculum.create_default_curriculum()
        summary = curriculum.get_curriculum_summary()
        
        assert 'progress' in summary
        assert 'stages' in summary
        assert 'history' in summary
        assert len(summary['stages']) == 4
    
    def test_reset_curriculum(self, curriculum):
        """カリキュラムリセットテスト"""
        curriculum.create_default_curriculum()
        
        # 一部の段階を完了状態にする
        curriculum.stages[0].is_completed = True
        curriculum.current_stage_index = 1
        
        result = curriculum.reset_curriculum()
        assert result is True
        
        # リセットされているか確認
        assert curriculum.current_stage_index == 0
        assert all(not stage.is_completed for stage in curriculum.stages)
        assert len(curriculum.curriculum_history) == 0
    
    def test_add_custom_stage(self, curriculum):
        """カスタム段階追加テスト"""
        curriculum.create_default_curriculum()
        initial_count = len(curriculum.stages)
        
        custom_stage = CurriculumStage(
            stage_id=5,
            name="カスタム段階",
            description="テスト用のカスタム段階",
            difficulty_level=0.9,
            parameters={"learning_rate": 0.00001},
            completion_criteria={"min_accuracy": 0.9}
        )
        
        result = curriculum.add_custom_stage(custom_stage)
        assert result is True
        assert len(curriculum.stages) == initial_count + 1
        assert curriculum.stages[-1].name == "カスタム段階"
    
    def test_get_adaptive_parameters(self, curriculum):
        """適応的パラメータ取得テスト"""
        curriculum.create_default_curriculum()
        
        base_parameters = {
            "learning_rate": 0.001,
            "batch_size": 32,
            "epochs": 100
        }
        
        adaptive_params = curriculum.get_adaptive_parameters(base_parameters)
        
        # パラメータが調整されているか確認
        assert adaptive_params['learning_rate'] < base_parameters['learning_rate']
        assert adaptive_params['batch_size'] > base_parameters['batch_size']
        assert adaptive_params['epochs'] > base_parameters['epochs']
    
    def test_get_adaptive_parameters_no_current_stage(self, curriculum):
        """現在段階がない場合の適応的パラメータ取得テスト"""
        base_parameters = {
            "learning_rate": 0.001,
            "batch_size": 32,
            "epochs": 100
        }
        
        adaptive_params = curriculum.get_adaptive_parameters(base_parameters)
        
        # 元のパラメータがそのまま返される
        assert adaptive_params == base_parameters
    
    def test_load_curriculum_file_not_found(self, curriculum):
        """カリキュラムファイルが存在しない場合の読み込みテスト"""
        # 新しいインスタンスを作成（ファイルが存在しない状態）
        with tempfile.TemporaryDirectory() as temp_dir:
            non_existent_file = os.path.join(temp_dir, "non_existent.json")
            curriculum = CurriculumLearning(non_existent_file)
            
            assert curriculum.stages == []
            assert curriculum.current_stage_index == 0
    
    def test_save_and_load_curriculum(self, curriculum):
        """カリキュラムの保存と読み込みテスト"""
        curriculum.create_default_curriculum()
        
        # 一部の段階を完了状態にする
        curriculum.stages[0].is_completed = True
        curriculum.current_stage_index = 1
        
        # 保存
        save_result = curriculum._save_curriculum()
        assert save_result is True
        
        # 新しいインスタンスで読み込み
        new_curriculum = CurriculumLearning(curriculum.curriculum_file)
        
        # 状態が正しく復元されているか確認
        assert len(new_curriculum.stages) == len(curriculum.stages)
        assert new_curriculum.current_stage_index == curriculum.current_stage_index
        assert new_curriculum.stages[0].is_completed == curriculum.stages[0].is_completed


class TestCurriculumStage:
    """CurriculumStageのテストクラス"""
    
    def test_curriculum_stage_creation(self):
        """CurriculumStage作成テスト"""
        stage = CurriculumStage(
            stage_id=1,
            name="テスト段階",
            description="テスト用の段階",
            difficulty_level=0.5,
            parameters={"learning_rate": 0.001},
            completion_criteria={"min_accuracy": 0.7}
        )
        
        assert stage.stage_id == 1
        assert stage.name == "テスト段階"
        assert stage.description == "テスト用の段階"
        assert stage.difficulty_level == 0.5
        assert stage.parameters == {"learning_rate": 0.001}
        assert stage.completion_criteria == {"min_accuracy": 0.7}
        assert stage.is_completed is False
        assert stage.completed_at is None
        assert stage.performance_metrics is None
    
    def test_curriculum_stage_with_optional_fields(self):
        """オプションフィールド付きCurriculumStage作成テスト"""
        stage = CurriculumStage(
            stage_id=1,
            name="テスト段階",
            description="テスト用の段階",
            difficulty_level=0.5,
            parameters={"learning_rate": 0.001},
            completion_criteria={"min_accuracy": 0.7},
            is_completed=True,
            completed_at="2024-01-01T00:00:00",
            performance_metrics={"accuracy": 0.8}
        )
        
        assert stage.is_completed is True
        assert stage.completed_at == "2024-01-01T00:00:00"
        assert stage.performance_metrics == {"accuracy": 0.8} 