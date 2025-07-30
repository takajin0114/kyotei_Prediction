#!/usr/bin/env python3
"""
大容量ファイルをGitから削除するスクリプト
"""
import os
import subprocess
import sys

def run_command(command):
    """コマンドを実行し、結果を返す"""
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        return result.returncode == 0, result.stdout, result.stderr
    except Exception as e:
        return False, "", str(e)

def main():
    print("大容量ファイルのクリーンアップを開始します...")
    
    # 大容量ディレクトリのリスト
    large_dirs = [
        "optuna_models",
        "optuna_logs", 
        "optuna_studies",
        "optuna_studies_backup",
        "optuna_tensorboard",
        "optuna_results",
        "archives",
        "outputs",
        "ppo_tensorboard",
        "simple_test_tensorboard"
    ]
    
    # 各ディレクトリをGitから削除
    for dir_name in large_dirs:
        if os.path.exists(dir_name):
            print(f"削除中: {dir_name}")
            success, stdout, stderr = run_command(f'git rm -r --cached "{dir_name}"')
            if success:
                print(f"✓ {dir_name} を削除しました")
            else:
                print(f"✗ {dir_name} の削除に失敗: {stderr}")
        else:
            print(f"ディレクトリが存在しません: {dir_name}")
    
    # .gitignoreの更新をコミット
    print("\n.gitignoreの更新をコミットします...")
    success, stdout, stderr = run_command('git add .gitignore')
    if success:
        print("✓ .gitignoreをステージングしました")
    else:
        print(f"✗ .gitignoreのステージングに失敗: {stderr}")
    
    # 現在の状況を確認
    print("\n現在のGit状況:")
    success, stdout, stderr = run_command('git status --porcelain')
    if success:
        print(stdout)
    else:
        print(f"Git状況の確認に失敗: {stderr}")
    
    print("\nクリーンアップが完了しました。")
    print("次のコマンドでコミットしてください:")
    print("git commit -m 'Remove large files and update .gitignore'")

if __name__ == "__main__":
    main()