#!/usr/bin/env python3
"""
リファクタリングテスト実行スクリプト
"""

import sys
import os
import subprocess
from pathlib import Path
import pytest

def run_test_suite(test_file, description):
    """テストスイートを実行"""
    print(f"\n{'='*60}")
    print(f"実行中: {description}")
    print(f"テストファイル: {test_file}")
    print(f"{'='*60}")
    
    try:
        # pytestでテストを実行
        result = subprocess.run([
            sys.executable, "-m", "pytest", 
            str(test_file), 
            "-v", 
            "--tb=short"
        ], capture_output=True, text=True, cwd=Path(__file__).parent.parent.parent)
        
        print("標準出力:")
        print(result.stdout)
        
        if result.stderr:
            print("エラー出力:")
            print(result.stderr)
        
        print(f"終了コード: {result.returncode}")
        
        if result.returncode == 0:
            print("✅ テスト成功")
        else:
            print("❌ テスト失敗")
        
        return result.returncode == 0
        
    except Exception as e:
        print(f"❌ テスト実行エラー: {e}")
        return False

def main():
    """メイン実行関数"""
    print("リファクタリングテストスイート実行開始")
    print(f"Python実行パス: {sys.executable}")
    print(f"現在のディレクトリ: {os.getcwd()}")
    
    # テストファイルのリスト
    test_files = [
        ("kyotei_predictor/tests/test_environment_refactoring.py", "環境依存脱却リファクタリングテスト"),
        ("kyotei_predictor/tests/test_rl_refactoring.py", "強化学習リファクタリングテスト"),
        ("kyotei_predictor/tests/test_web_refactoring.py", "Webアプリケーションリファクタリングテスト"),
        ("kyotei_predictor/tests/test_integration_refactoring.py", "統合リファクタリングテスト")
    ]
    
    # 各テストスイートを実行
    results = []
    for test_file, description in test_files:
        success = run_test_suite(test_file, description)
        results.append((description, success))
    
    # 結果サマリー
    print(f"\n{'='*60}")
    print("テスト実行結果サマリー")
    print(f"{'='*60}")
    
    total_tests = len(results)
    passed_tests = sum(1 for _, success in results if success)
    failed_tests = total_tests - passed_tests
    
    for description, success in results:
        status = "✅ 成功" if success else "❌ 失敗"
        print(f"{description}: {status}")
    
    print(f"\n総テストスイート数: {total_tests}")
    print(f"成功: {passed_tests}")
    print(f"失敗: {failed_tests}")
    
    if failed_tests == 0:
        print("\n🎉 すべてのテストが成功しました！")
        return 0
    else:
        print(f"\n⚠️  {failed_tests}個のテストスイートが失敗しました。")
        return 1

def run_quick_test():
    """クイックテスト実行"""
    print("クイックテスト実行中...")
    
    # 基本的な機能テストのみ実行
    quick_tests = [
        ("kyotei_predictor/tests/test_environment_refactoring.py::TestEnvironmentRefactoring::test_get_project_root_basic", "基本プロジェクトルート検出"),
        ("kyotei_predictor/tests/test_environment_refactoring.py::TestEnvironmentRefactoring::test_settings_project_root_consistency", "設定一貫性"),
        ("kyotei_predictor/tests/test_web_refactoring.py::TestWebAppRefactoring::test_app_initialization", "Webアプリ初期化"),
        ("kyotei_predictor/tests/test_integration_refactoring.py::TestIntegrationRefactoring::test_project_root_consistency_across_modules", "モジュール間一貫性")
    ]
    
    results = []
    for test_path, description in quick_tests:
        print(f"\n実行中: {description}")
        try:
            result = subprocess.run([
                sys.executable, "-m", "pytest", 
                test_path, 
                "-v", 
                "--tb=short"
            ], capture_output=True, text=True, cwd=Path(__file__).parent.parent.parent)
            
            success = result.returncode == 0
            results.append((description, success))
            
            if success:
                print("✅ 成功")
            else:
                print("❌ 失敗")
                print(result.stdout)
                if result.stderr:
                    print(result.stderr)
                    
        except Exception as e:
            print(f"❌ エラー: {e}")
            results.append((description, False))
    
    # 結果表示
    print(f"\n{'='*40}")
    print("クイックテスト結果")
    print(f"{'='*40}")
    
    for description, success in results:
        status = "✅ 成功" if success else "❌ 失敗"
        print(f"{description}: {status}")
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    print(f"\n成功: {passed}/{total}")
    
    if passed == total:
        print("🎉 クイックテスト成功！")
        return 0
    else:
        print("⚠️ クイックテスト失敗")
        return 1

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="リファクタリングテスト実行スクリプト")
    parser.add_argument("--quick", action="store_true", help="クイックテストのみ実行")
    
    args = parser.parse_args()
    
    if args.quick:
        exit_code = run_quick_test()
    else:
        exit_code = main()
    
    sys.exit(exit_code) 