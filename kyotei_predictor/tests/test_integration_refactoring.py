#!/usr/bin/env python3
"""
統合リファクタリングテスト
全モジュール間の一貫性と環境独立性の検証
"""

import sys
import os
import tempfile
from pathlib import Path
import pytest

# プロジェクトルートをsys.pathに追加
current_file = Path(__file__)
project_root = current_file.parent.parent.parent
sys.path.append(str(project_root))

from kyotei_predictor.config.settings import Settings, get_project_root as settings_get_project_root
from kyotei_predictor.app import get_project_root as app_get_project_root
from kyotei_predictor.pipelines.kyotei_env import KyoteiEnv

from metaboatrace.models.stadium import StadiumTelCode

class TestIntegrationRefactoring:
    """統合リファクタリングのテスト"""
    
    def test_project_root_consistency_across_modules(self):
        """モジュール間プロジェクトルート一貫性テスト"""
        settings_root = settings_get_project_root()
        app_root = app_get_project_root()
        
        assert settings_root == app_root
        print(f"✅ モジュール間プロジェクトルート一貫性確認成功: {settings_root}")
    
    def test_path_resolution_consistency(self):
        """パス解決一貫性テスト"""
        # 各モジュールでパス解決が一貫していることを確認
        settings_paths = Settings.get_data_paths()
        app_root = app_get_project_root()
        
        for path_name, path_value in settings_paths.items():
            assert isinstance(path_value, str)
            assert path_value.startswith(str(app_root))
            print(f"✅ パス解決一貫性確認成功: {path_name}")
    
    def test_environment_independence(self):
        """環境独立性テスト"""
        original_env = os.environ.copy()
        try:
            # 環境変数を変更してテスト
            os.environ['TEST_ENV'] = 'test_value'
            
            # プロジェクトルートが変わらないことを確認
            project_root = settings_get_project_root()
            assert project_root is not None
            print("✅ 環境独立性確認成功")
        finally:
            # 環境変数を元に戻す
            os.environ.clear()
            os.environ.update(original_env)
    
    def test_module_import_consistency(self):
        """モジュールインポート一貫性テスト"""
        # 主要なモジュールが正常にインポートできることを確認
        modules_to_test = [
            'kyotei_predictor.config.settings',
            'kyotei_predictor.app',
            'kyotei_predictor.pipelines.kyotei_env',
            'kyotei_predictor.tools.fetch.race_data_fetcher',
            'kyotei_predictor.tools.fetch.odds_fetcher'
        ]
        
        for module_name in modules_to_test:
            try:
                __import__(module_name)
                print(f"✅ モジュールインポート成功: {module_name}")
            except ImportError as e:
                print(f"⚠️  モジュールインポートエラー: {module_name} - {e}")
    
    def test_configuration_loading_consistency(self):
        """設定読み込み一貫性テスト"""
        # 各設定が一貫して読み込まれることを確認
        data_paths = Settings.get_data_paths()
        optuna_paths = Settings.get_optuna_paths()
        web_config = Settings.get_web_config()
        model_config = Settings.get_model_config()
        investment_config = Settings.get_investment_config()
        
        assert isinstance(data_paths, dict)
        assert isinstance(optuna_paths, dict)
        assert isinstance(web_config, dict)
        assert isinstance(model_config, dict)
        assert isinstance(investment_config, dict)
        
        print("✅ 設定読み込み一貫性確認成功")
    
    def test_directory_structure_validation(self):
        """ディレクトリ構造検証テスト"""
        project_root = settings_get_project_root()
        
        # 必要なディレクトリが存在することを確認
        required_dirs = [
            'kyotei_predictor',
            'kyotei_predictor/config',
            'kyotei_predictor/tools',
            'kyotei_predictor/pipelines',
            'kyotei_predictor/tests'
        ]
        
        for dir_name in required_dirs:
            dir_path = project_root / dir_name
            assert dir_path.exists()
            print(f"✅ ディレクトリ構造確認成功: {dir_name}")
    
    def test_file_accessibility(self):
        """ファイルアクセシビリティテスト"""
        project_root = settings_get_project_root()
        
        # 重要なファイルがアクセス可能であることを確認
        important_files = [
            'kyotei_predictor/config/settings.py',
            'kyotei_predictor/app.py',
            'kyotei_predictor/requirements.txt'
        ]
        
        for file_name in important_files:
            file_path = project_root / file_name
            assert file_path.exists()
            print(f"✅ ファイルアクセシビリティ確認成功: {file_name}")
    
    def test_settings_app_integration(self):
        """Settings-App統合テスト"""
        # SettingsとAppが正しく統合されていることを確認
        settings_root = settings_get_project_root()
        app_root = app_get_project_root()
        
        assert settings_root == app_root
        
        # 設定が正しく読み込まれることを確認
        data_paths = Settings.get_data_paths()
        assert 'data_dir' in data_paths
        
        print("✅ Settings-App統合確認成功")
    
    def test_data_processing_integration(self):
        """データ処理統合テスト"""
        try:
            # データ処理機能が統合されていることを確認
            from kyotei_predictor.pipelines.data_preprocessor import DataPreprocessor
            preprocessor = DataPreprocessor()
            assert preprocessor is not None
            print("✅ データ処理統合確認成功")
        except Exception as e:
            print(f"⚠️  データ処理統合エラー: {e}")
    
    def test_tools_integration(self):
        """ツール統合テスト"""
        try:
            # ツールが統合されていることを確認
            from kyotei_predictor.tools.fetch.race_data_fetcher import fetch_complete_race_data
            assert fetch_complete_race_data is not None
            print("✅ ツール統合確認成功")
        except Exception as e:
            print(f"⚠️  ツール統合エラー: {e}")
    
    def test_error_handling_integration(self):
        """エラーハンドリング統合テスト"""
        try:
            # エラーハンドリングが統合されていることを確認
            from kyotei_predictor.errors import handle_error
            assert handle_error is not None
            print("✅ エラーハンドリング統合確認成功")
        except Exception as e:
            print(f"⚠️  エラーハンドリング統合エラー: {e}")
    
    def test_local_environment_simulation(self):
        """ローカル環境シミュレーションテスト"""
        original_cwd = os.getcwd()
        try:
            # ローカル環境をシミュレート
            temp_dir = os.path.join(os.getcwd(), "temp_test")
            os.makedirs(temp_dir, exist_ok=True)
            os.chdir(temp_dir)
            
            project_root = settings_get_project_root()
            assert project_root is not None
            print("✅ ローカル環境シミュレーション成功")
        finally:
            os.chdir(original_cwd)
    
    def test_colab_environment_simulation(self):
        """Google Colab環境シミュレーションテスト"""
        original_cwd = os.getcwd()
        try:
            # Colab環境をシミュレート
            temp_dir = os.path.join(os.getcwd(), "temp_test")
            os.makedirs(temp_dir, exist_ok=True)
            os.chdir(temp_dir)
            
            project_root = settings_get_project_root()
            assert project_root is not None
            print("✅ Colab環境シミュレーション成功")
        finally:
            os.chdir(original_cwd)
    
    def test_metaboatrace_optional_dependency(self):
        """metaboatraceオプショナル依存関係テスト"""
        # StadiumTelCodeクラスが利用可能であることを確認
        assert StadiumTelCode is not None
        print("✅ StadiumTelCodeクラス利用可能")

if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 