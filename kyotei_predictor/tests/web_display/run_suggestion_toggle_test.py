#!/usr/bin/env python3
"""
提案比較テーブルの展開/折りたたみ機能テスト実行スクリプト
"""

import sys
import os
import subprocess
import time
from pathlib import Path

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

def check_server_running():
    """サーバーが起動しているかチェック"""
    try:
        import requests
        response = requests.get("http://localhost:51932/", timeout=5)
        return response.status_code == 200
    except:
        return False

def start_server():
    """Webサーバーを起動"""
    print("🌐 Webサーバーを起動中...")
    
    # サーバー起動コマンド
    cmd = [sys.executable, "-m", "kyotei_predictor.app"]
    
    # バックグラウンドでサーバーを起動
    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd=project_root
    )
    
    # サーバーが起動するまで待機
    for i in range(30):
        if check_server_running():
            print("✅ Webサーバーが起動しました")
            return process
        time.sleep(1)
        print(f"⏳ サーバー起動待機中... ({i+1}/30)")
    
    print("❌ Webサーバーの起動に失敗しました")
    process.terminate()
    return None

def run_tests():
    """テストを実行"""
    print("🧪 提案比較テーブルの展開/折りたたみ機能テストを実行中...")
    
    # テストファイルのパス
    test_file = project_root / "tests" / "web_display" / "test_suggestion_toggle.py"
    
    # pytestコマンドを実行
    cmd = [
        sys.executable, "-m", "pytest",
        str(test_file),
        "-v",
        "--tb=short"
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=project_root)
        
        print("\n" + "="*60)
        print("テスト実行結果:")
        print("="*60)
        
        if result.stdout:
            print(result.stdout)
        
        if result.stderr:
            print("エラー出力:")
            print(result.stderr)
        
        if result.returncode == 0:
            print("✅ すべてのテストが成功しました！")
        else:
            print("❌ 一部のテストが失敗しました")
        
        return result.returncode == 0
        
    except Exception as e:
        print(f"❌ テスト実行中にエラーが発生しました: {e}")
        return False

def main():
    """メイン関数"""
    print("🚀 提案比較テーブルの展開/折りたたみ機能テスト開始")
    print("="*60)
    
    # サーバーが起動しているかチェック
    if not check_server_running():
        print("⚠️  Webサーバーが起動していません")
        server_process = start_server()
        if not server_process:
            print("❌ テストを実行できません")
            return False
        
        # サーバー起動後、少し待機
        time.sleep(3)
    else:
        print("✅ Webサーバーは既に起動しています")
        server_process = None
    
    try:
        # テストを実行
        success = run_tests()
        
        if success:
            print("\n🎉 提案比較テーブルの展開/折りたたみ機能は正常に動作しています！")
        else:
            print("\n🔧 提案比較テーブルの展開/折りたたみ機能に問題があります")
        
        return success
        
    finally:
        # サーバープロセスを終了
        if server_process:
            print("\n🛑 Webサーバーを終了中...")
            server_process.terminate()
            server_process.wait()

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 