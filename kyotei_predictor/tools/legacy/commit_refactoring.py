#!/usr/bin/env python3
"""
リファクタリング作業（Phase 1-4）のファイルをGitに追加するスクリプト
"""

import subprocess
import sys
import os

def run_command(cmd):
    """コマンドを実行し、結果を返す"""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        return result.returncode == 0, result.stdout, result.stderr
    except Exception as e:
        return False, "", str(e)

def main():
    """メイン処理"""
    print("🔧 リファクタリング作業のファイルをGitに追加します...")
    
    # リファクタリングに関連するファイルのリスト
    files_to_add = [
        "REFACTORING_REPORT.md",
        "docs/API_SPECIFICATION.md",
        "docs/DEVELOPER_GUIDE.md",
        "docs/OPERATIONS_MANUAL.md",
        "kyotei_predictor/utils/cache.py",
        "kyotei_predictor/utils/memory.py",
        "kyotei_predictor/utils/parallel.py",
        "kyotei_predictor/utils/__init__.py",
        "kyotei_predictor/app.py",
        "kyotei_predictor/data_integration.py",
        "kyotei_predictor/tools/batch/retry_missing_races.py"
    ]
    
    files_to_remove = [
        "kyotei_predictor/tests/test_common.py",
        "kyotei_predictor/tools/common/README.md",
        "kyotei_predictor/tools/common/test_env.py",
        "kyotei_predictor/tools/common/venue_mapping.py"
    ]
    
    # ファイルを追加
    for file_path in files_to_add:
        if os.path.exists(file_path):
            success, stdout, stderr = run_command(f'git add "{file_path}"')
            if success:
                print(f"✅ {file_path} を追加しました")
            else:
                print(f"❌ {file_path} の追加に失敗: {stderr}")
        else:
            print(f"⚠️ {file_path} が見つかりません")
    
    # ファイルを削除
    for file_path in files_to_remove:
        if os.path.exists(file_path):
            success, stdout, stderr = run_command(f'git rm "{file_path}"')
            if success:
                print(f"✅ {file_path} を削除しました")
            else:
                print(f"❌ {file_path} の削除に失敗: {stderr}")
        else:
            print(f"⚠️ {file_path} は既に存在しません")
    
    print("\n📋 現在のGitの状態を確認します...")
    success, stdout, stderr = run_command("git status --porcelain")
    if success:
        print("変更されたファイル:")
        print(stdout)
    else:
        print(f"Git statusの取得に失敗: {stderr}")

if __name__ == "__main__":
    main()