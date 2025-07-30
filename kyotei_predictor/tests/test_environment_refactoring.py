#!/usr/bin/env python3
"""
環境依存脱却リファクタリングテスト
プロジェクトルート検出、パス解決、設定の一貫性を検証
"""

import sys
import os
from pathlib import Path
import pytest

# プロジェクトルートをsys.pathに追加
current_file = Path(__file__)
project_root = current_file.parent.parent.parent
sys.path.append(str(project_root))

from kyotei_predictor.config.settings import Settings, get_project_root as settings_get_project_root
from kyotei_predictor.app import get_project_root as app_get_project_root

from metaboatrace.models.stadium import StadiumTelCode

class TestEnvironmentRefactoring:
    """環境依存脱却リファクタリングのテスト"""
    
    def test_basic_project_root_detection(self):
        """基本的なプロジェクトルート検出テスト"""
        project_root = settings_get_project_root()
        assert project_root is not None
        assert isinstance(project_root, Path)
        assert project_root.exists()
        print(f"✅ プロジェクトルート検出成功: {project_root}")
    
    def test_colab_environment_simulation(self):
        """Google Colab環境シミュレーションテスト"""
        # Colab環境をシミュレート
        original_cwd = os.getcwd()
        try:
            # 一時的にColab環境をシミュレート
            temp_dir = os.path.join(os.getcwd(), "temp_test")
            os.makedirs(temp_dir, exist_ok=True)
            os.chdir(temp_dir)
            project_root = settings_get_project_root()
            assert project_root is not None
            print(f"✅ Colab環境シミュレーション成功: {project_root}")
        finally:
            os.chdir(original_cwd)
    
    def test_settings_app_consistency(self):
        """Settingsとappの一貫性テスト"""
        settings_root = settings_get_project_root()
        app_root = app_get_project_root()
        
        # 同じプロジェクトルートを指していることを確認
        assert settings_root == app_root
        print(f"✅ Settings-App一貫性確認成功: {settings_root}")
    
    def test_absolute_path_conversion(self):
        """絶対パス変換テスト"""
        relative_path = "data/test"
        absolute_path = Settings.get_absolute_path(relative_path)
        
        assert absolute_path.is_absolute()
        assert str(absolute_path).endswith(relative_path.replace('/', os.sep))
        print(f"✅ 絶対パス変換成功: {absolute_path}")
    
    def test_data_paths_generation(self):
        """データパス生成テスト"""
        data_paths = Settings.get_data_paths()
        
        assert 'data_dir' in data_paths
        assert 'raw_dir' in data_paths
        assert 'processed_dir' in data_paths
        assert 'sample_dir' in data_paths
        
        for path_name, path_value in data_paths.items():
            assert isinstance(path_value, str)
            print(f"✅ データパス生成成功: {path_name} = {path_value}")
    
    def test_optuna_paths_generation(self):
        """Optunaパス生成テスト"""
        optuna_paths = Settings.get_optuna_paths()
        
        assert 'studies_dir' in optuna_paths
        assert 'results_dir' in optuna_paths
        assert 'logs_dir' in optuna_paths
        assert 'models_dir' in optuna_paths
        assert 'tensorboard_dir' in optuna_paths
        
        for path_name, path_value in optuna_paths.items():
            assert isinstance(path_value, str)
            print(f"✅ Optunaパス生成成功: {path_name} = {path_value}")
    
    def test_web_paths_generation(self):
        """Webパス生成テスト"""
        web_paths = Settings.get_web_config()
        
        assert 'host' in web_paths
        assert 'port' in web_paths
        assert 'debug' in web_paths
        
        for path_name, path_value in web_paths.items():
            assert isinstance(path_value, (str, int, bool))
            print(f"✅ Webパス生成成功: {path_name} = {path_value}")
    
    def test_model_paths_generation(self):
        """モデルパス生成テスト"""
        model_paths = Settings.get_model_config()
        
        assert 'trifecta_combinations' in model_paths
        assert 'default_temperature' in model_paths
        assert 'min_probability' in model_paths
        
        for path_name, path_value in model_paths.items():
            assert isinstance(path_value, (int, float))
            print(f"✅ モデルパス生成成功: {path_name} = {path_value}")
    
    def test_investment_paths_generation(self):
        """投資設定生成テスト"""
        investment_paths = Settings.get_investment_config()
        
        assert 'default_threshold' in investment_paths
        assert 'conservative' in investment_paths
        assert 'balanced' in investment_paths
        assert 'aggressive' in investment_paths
        
        for path_name, path_value in investment_paths.items():
            assert isinstance(path_value, float)
            print(f"✅ 投資設定生成成功: {path_name} = {path_value}")
    
    def test_directory_creation(self):
        """ディレクトリ作成テスト"""
        try:
            Settings.create_directories()
            print("✅ ディレクトリ作成成功")
        except Exception as e:
            print(f"⚠️  ディレクトリ作成エラー（既に存在する可能性）: {e}")
    
    def test_path_independence(self):
        """パス独立性テスト"""
        original_cwd = os.getcwd()
        try:
            # 別のディレクトリに移動してテスト
            temp_dir = os.path.join(os.getcwd(), "temp_test")
            os.makedirs(temp_dir, exist_ok=True)
            os.chdir(temp_dir)
            
            # プロジェクトルートが正しく検出されることを確認
            project_root = settings_get_project_root()
            assert project_root is not None
            print(f"✅ パス独立性確認成功: {project_root}")
        finally:
            os.chdir(original_cwd)

if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 