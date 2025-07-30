#!/usr/bin/env python3
"""
リファクタリング基本機能テスト
"""

import sys
import os
from pathlib import Path

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent
sys.path.append(str(project_root))

def test_project_root_detection():
    """プロジェクトルート検出のテスト"""
    print("=== プロジェクトルート検出テスト ===")
    
    try:
        from kyotei_predictor.config.settings import get_project_root, Settings
        
        # プロジェクトルートを取得
        project_root = get_project_root()
        print(f"プロジェクトルート: {project_root}")
        
        # プロジェクトルートが存在することを確認
        assert project_root.exists(), "プロジェクトルートが存在しません"
        assert project_root.is_dir(), "プロジェクトルートがディレクトリではありません"
        
        # 必要なファイルが存在することを確認
        required_files = ["kyotei_predictor", "README.md", "requirements.txt"]
        for file_name in required_files:
            file_path = project_root / file_name
            assert file_path.exists(), f"必要なファイルが存在しません: {file_name}"
        
        print("✅ プロジェクトルート検出テスト成功")
        return True
        
    except Exception as e:
        print(f"❌ プロジェクトルート検出テスト失敗: {e}")
        return False

def test_settings_consistency():
    """設定一貫性のテスト"""
    print("\n=== 設定一貫性テスト ===")
    
    try:
        from kyotei_predictor.config.settings import get_project_root, Settings
        
        # 異なる方法でプロジェクトルートを取得
        direct_root = get_project_root()
        settings_root = Settings.get_project_root_path()
        
        print(f"直接取得: {direct_root}")
        print(f"Settings取得: {settings_root}")
        
        # 両方が一致することを確認
        assert direct_root == settings_root, "プロジェクトルートが一致しません"
        
        print("✅ 設定一貫性テスト成功")
        return True
        
    except Exception as e:
        print(f"❌ 設定一貫性テスト失敗: {e}")
        return False

def test_path_resolution():
    """パス解決のテスト"""
    print("\n=== パス解決テスト ===")
    
    try:
        from kyotei_predictor.config.settings import Settings
        
        # データパスを取得
        data_paths = Settings.get_data_paths()
        print("データパス:")
        for key, path in data_paths.items():
            print(f"  {key}: {path}")
            assert Path(path).is_absolute(), f"絶対パスではありません: {path}"
        
        # Optunaパスを取得
        optuna_paths = Settings.get_optuna_paths()
        print("Optunaパス:")
        for key, path in optuna_paths.items():
            print(f"  {key}: {path}")
            assert Path(path).is_absolute(), f"絶対パスではありません: {path}"
        
        print("✅ パス解決テスト成功")
        return True
        
    except Exception as e:
        print(f"❌ パス解決テスト失敗: {e}")
        return False

def test_configuration_loading():
    """設定読み込みのテスト"""
    print("\n=== 設定読み込みテスト ===")
    
    try:
        from kyotei_predictor.config.settings import Settings
        
        # Web設定を取得
        web_config = Settings.get_web_config()
        print("Web設定:")
        for key, value in web_config.items():
            print(f"  {key}: {value}")
        
        # モデル設定を取得
        model_config = Settings.get_model_config()
        print("モデル設定:")
        for key, value in model_config.items():
            print(f"  {key}: {value}")
        
        # 投資設定を取得
        investment_config = Settings.get_investment_config()
        print("投資設定:")
        for key, value in investment_config.items():
            print(f"  {key}: {value}")
        
        print("✅ 設定読み込みテスト成功")
        return True
        
    except Exception as e:
        print(f"❌ 設定読み込みテスト失敗: {e}")
        return False

def test_environment_independence():
    """環境独立性のテスト"""
    print("\n=== 環境独立性テスト ===")
    
    try:
        from kyotei_predictor.config.settings import get_project_root
        
        original_cwd = os.getcwd()
        
        # 一時的にディレクトリを変更
        import tempfile
        temp_dir = tempfile.mkdtemp()
        os.chdir(temp_dir)
        
        try:
            # 異なるディレクトリからでもプロジェクトルートが取得できることを確認
            project_root = get_project_root()
            print(f"異なるディレクトリからのプロジェクトルート: {project_root}")
            
            assert project_root.exists(), "プロジェクトルートが存在しません"
            assert (project_root / "kyotei_predictor").exists(), "kyotei_predictorディレクトリが存在しません"
            
            print("✅ 環境独立性テスト成功")
            return True
            
        finally:
            # 元のディレクトリに戻す
            os.chdir(original_cwd)
            import shutil
            shutil.rmtree(temp_dir, ignore_errors=True)
        
    except Exception as e:
        print(f"❌ 環境独立性テスト失敗: {e}")
        return False

def test_web_app_initialization():
    """Webアプリ初期化のテスト"""
    print("\n=== Webアプリ初期化テスト ===")
    
    try:
        from kyotei_predictor.app import app, get_project_root
        
        # Flaskアプリケーションが正常に初期化されることを確認
        assert app is not None, "Flaskアプリケーションが初期化されていません"
        print(f"Flaskアプリケーション名: {app.name}")
        
        # プロジェクトルートが一致することを確認
        app_root = get_project_root()
        from kyotei_predictor.config.settings import get_project_root as settings_get_root
        settings_root = settings_get_root()
        
        assert app_root == settings_root, "プロジェクトルートが一致しません"
        
        print("✅ Webアプリ初期化テスト成功")
        return True
        
    except Exception as e:
        print(f"❌ Webアプリ初期化テスト失敗: {e}")
        return False

def main():
    """メイン実行関数"""
    print("リファクタリング基本機能テスト開始")
    print("=" * 50)
    
    tests = [
        ("プロジェクトルート検出", test_project_root_detection),
        ("設定一貫性", test_settings_consistency),
        ("パス解決", test_path_resolution),
        ("設定読み込み", test_configuration_loading),
        ("環境独立性", test_environment_independence),
        ("Webアプリ初期化", test_web_app_initialization)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            success = test_func()
            results.append((test_name, success))
        except Exception as e:
            print(f"❌ {test_name}で予期しないエラー: {e}")
            results.append((test_name, False))
    
    # 結果サマリー
    print("\n" + "=" * 50)
    print("テスト結果サマリー")
    print("=" * 50)
    
    total_tests = len(results)
    passed_tests = sum(1 for _, success in results if success)
    failed_tests = total_tests - passed_tests
    
    for test_name, success in results:
        status = "✅ 成功" if success else "❌ 失敗"
        print(f"{test_name}: {status}")
    
    print(f"\n総テスト数: {total_tests}")
    print(f"成功: {passed_tests}")
    print(f"失敗: {failed_tests}")
    
    if failed_tests == 0:
        print("\n🎉 すべてのテストが成功しました！")
        return 0
    else:
        print(f"\n⚠️  {failed_tests}個のテストが失敗しました。")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code) 