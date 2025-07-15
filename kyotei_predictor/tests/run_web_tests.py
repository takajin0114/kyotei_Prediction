#!/usr/bin/env python3
"""
Web表示機能テスト実行スクリプト
簡単にテストを実行できるようにする
"""

import sys
import subprocess
import time
from pathlib import Path

# プロジェクトルートの設定
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.append(str(PROJECT_ROOT))

def run_web_tests():
    """Web表示機能のテストを実行"""
    print("=" * 60)
    print("Web表示機能 自動テスト実行")
    print("=" * 60)
    
    # テストファイルの存在確認
    test_file = PROJECT_ROOT / "kyotei_predictor" / "tests" / "test_web_display_simple.py"
    if not test_file.exists():
        print(f"エラー: テストファイルが見つかりません: {test_file}")
        return False
    
    print(f"テストファイル: {test_file}")
    print()
    
    # 必要なファイルの存在確認
    required_files = [
        PROJECT_ROOT / "kyotei_predictor" / "templates" / "predictions.html",
        PROJECT_ROOT / "kyotei_predictor" / "static" / "css" / "predictions.css",
        PROJECT_ROOT / "kyotei_predictor" / "static" / "js" / "predictions.js",
        PROJECT_ROOT / "kyotei_predictor" / "static" / "test_server.py"
    ]
    
    print("必要なファイルの確認:")
    for file_path in required_files:
        if file_path.exists():
            print(f"  ✅ {file_path.name}")
        else:
            print(f"  ❌ {file_path.name} (見つかりません)")
            return False
    
    print()
    
    # テストサーバーの起動確認
    print("テストサーバーの起動確認:")
    try:
        server_script = PROJECT_ROOT / "kyotei_predictor" / "static" / "test_server.py"
        server_process = subprocess.Popen(
            [sys.executable, str(server_script)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        # サーバー起動を待機
        time.sleep(3)
        
        # プロセスが生きているか確認
        if server_process.poll() is None:
            print("  ✅ テストサーバーが起動しました")
            server_process.terminate()
            server_process.wait()
        else:
            print("  ❌ テストサーバーの起動に失敗しました")
            return False
            
    except Exception as e:
        print(f"  ❌ テストサーバーの起動エラー: {e}")
        return False
    
    print()
    
    # pytestの実行
    print("pytestの実行:")
    try:
        result = subprocess.run(
            [
                sys.executable, "-m", "pytest", 
                str(test_file), 
                "-v", 
                "--tb=short"
            ],
            capture_output=True,
            text=True,
            timeout=60
        )
        
        print("実行結果:")
        print(result.stdout)
        
        if result.stderr:
            print("エラー出力:")
            print(result.stderr)
        
        if result.returncode == 0:
            print("✅ すべてのテストが成功しました！")
            return True
        else:
            print(f"❌ テストが失敗しました (終了コード: {result.returncode})")
            return False
            
    except subprocess.TimeoutExpired:
        print("❌ テストの実行がタイムアウトしました")
        return False
    except Exception as e:
        print(f"❌ テスト実行エラー: {e}")
        return False

def main():
    """メイン関数"""
    print("Web表示機能の自動テストを開始します...")
    print()
    
    success = run_web_tests()
    
    print()
    print("=" * 60)
    if success:
        print("🎉 Web表示機能の自動テストが完了しました！")
        print("✅ Phase 1実装は正常に動作しています")
    else:
        print("❌ Web表示機能の自動テストが失敗しました")
        print("🔧 問題を修正してから再実行してください")
    print("=" * 60)
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main()) 