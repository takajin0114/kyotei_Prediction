#!/usr/bin/env python3
"""
セクション折り畳み機能の自動テスト実行スクリプト
"""

import sys
import os
import subprocess
import time
from pathlib import Path

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

def install_requirements():
    """Seleniumの依存関係をインストール"""
    print("Seleniumの依存関係をインストール中...")
    requirements_file = Path(__file__).parent / "requirements.txt"
    
    try:
        subprocess.run([
            sys.executable, "-m", "pip", "install", "-r", str(requirements_file)
        ], check=True, capture_output=True, text=True)
        print("✓ 依存関係のインストール完了")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ 依存関係のインストールに失敗: {e}")
        print(f"エラー出力: {e.stderr}")
        return False

def check_web_server():
    """Webサーバーが起動しているかチェック"""
    print("Webサーバーの状態を確認中...")
    
    try:
        import requests
        response = requests.get("http://127.0.0.1:51932/predictions", timeout=5)
        if response.status_code == 200:
            print("✓ Webサーバーが起動しています")
            return True
        else:
            print(f"✗ Webサーバーの応答が異常: {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ Webサーバーに接続できません: {e}")
        print("Webサーバーを起動してください: python -m kyotei_predictor.app")
        return False

def run_tests():
    """テストを実行"""
    print("セクション折り畳みテストを実行中...")
    
    test_file = Path(__file__).parent / "test_collapsible_sections.py"
    
    try:
        result = subprocess.run([
            sys.executable, str(test_file)
        ], check=False, capture_output=False)
        
        if result.returncode == 0:
            print("✓ すべてのテストが成功しました")
            return True
        else:
            print(f"✗ テストが失敗しました (終了コード: {result.returncode})")
            return False
    except Exception as e:
        print(f"✗ テスト実行中にエラーが発生: {e}")
        return False

def main():
    """メイン実行関数"""
    print("=" * 60)
    print("セクション折り畳み機能 自動テスト")
    print("=" * 60)
    
    # 依存関係のインストール
    if not install_requirements():
        return False
    
    # Webサーバーの確認
    if not check_web_server():
        return False
    
    # テスト実行
    success = run_tests()
    
    print("=" * 60)
    if success:
        print("🎉 テスト完了: セクション折り畳み機能は正常に動作しています")
    else:
        print("❌ テスト失敗: セクション折り畳み機能に問題があります")
    print("=" * 60)
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 