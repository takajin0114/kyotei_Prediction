#!/usr/bin/env python3
"""
最適化プロセスの進行状況をリアルタイムで監視するスクリプト
"""

import os
import time
import subprocess
from datetime import datetime

def safe_read_file(filepath, max_lines=5):
    """安全にファイルを読み込む（エンコーディングエラー対応）"""
    try:
        if not os.path.exists(filepath):
            return None, 0
        
        # 複数のエンコーディングを試行
        encodings = ['utf-8', 'shift_jis', 'cp932', 'latin-1']
        content = None
        
        for encoding in encodings:
            try:
                with open(filepath, 'r', encoding=encoding) as f:
                    content = f.read()
                break
            except UnicodeDecodeError:
                continue
        
        if content is None:
            return None, 0
        
        lines = content.split('\n')
        return lines, len(lines)
        
    except Exception as e:
        return None, 0

def check_optimization_completion():
    """最適化完了をチェック"""
    # 1. プロセスが終了しているかチェック
    result = subprocess.run(['tasklist', '/FI', 'IMAGENAME eq python.exe'], 
                          capture_output=True, text=True, shell=True)
    process_running = 'python.exe' in result.stdout
    
    # 2. 結果ファイルの更新をチェック
    optuna_results_dir = "./optuna_results"
    if os.path.exists(optuna_results_dir):
        files = os.listdir(optuna_results_dir)
        json_files = [f for f in files if f.endswith('.json')]
        if json_files:
            latest_file = max(json_files, key=lambda x: os.path.getctime(os.path.join(optuna_results_dir, x)))
            latest_file_path = os.path.join(optuna_results_dir, latest_file)
            file_time = os.path.getctime(latest_file_path)
            current_time = time.time()
            
            # 最新ファイルが5分以内に作成されていて、プロセスが終了している場合
            if not process_running and (current_time - file_time) < 300:
                return True, latest_file
    
    return False, None

def monitor_optimization():
    """最適化プロセスの進行状況を監視"""
    print("🔍 最適化プロセス監視を開始します...")
    print("=" * 60)
    
    # 初期状態を記録
    initial_file_count = 0
    optuna_results_dir = "./optuna_results"
    if os.path.exists(optuna_results_dir):
        files = os.listdir(optuna_results_dir)
        json_files = [f for f in files if f.endswith('.json')]
        initial_file_count = len(json_files)
    
    while True:
        try:
            # 最適化完了チェック
            is_completed, latest_file = check_optimization_completion()
            
            # 1. プロセス状況の確認
            print(f"\n📊 [{datetime.now().strftime('%H:%M:%S')}] プロセス状況:")
            result = subprocess.run(['tasklist', '/FI', 'IMAGENAME eq python.exe'], 
                                  capture_output=True, text=True, shell=True)
            if 'python.exe' in result.stdout:
                print("✅ Pythonプロセス実行中")
            else:
                print("❌ Pythonプロセスが見つかりません")
            
            # 2. ログファイルの確認
            print(f"\n📝 [{datetime.now().strftime('%H:%M:%S')}] ログファイル状況:")
            
            # stdoutログの確認
            lines, line_count = safe_read_file('optimize_batch_stdout.txt')
            if lines is not None:
                print(f"📄 stdout: {line_count}行")
                if lines and lines[-1].strip():
                    latest_line = lines[-1][:80]
                    print(f"   最新: {latest_line}...")
                else:
                    print("   最新: 空")
            else:
                print("❌ stdoutログファイルが見つかりません")
            
            # stderrログの確認
            lines, line_count = safe_read_file('optimize_batch_stderr.txt')
            if lines is not None:
                print(f"📄 stderr: {line_count}行")
                if lines and lines[-1].strip():
                    latest_line = lines[-1][:80]
                    print(f"   最新: {latest_line}...")
                else:
                    print("   最新: 空")
            else:
                print("❌ stderrログファイルが見つかりません")
            
            # 3. 結果ファイルの確認
            print(f"\n📁 [{datetime.now().strftime('%H:%M:%S')}] 結果ファイル状況:")
            if os.path.exists(optuna_results_dir):
                files = os.listdir(optuna_results_dir)
                json_files = [f for f in files if f.endswith('.json')]
                current_file_count = len(json_files)
                print(f"📂 結果ファイル数: {current_file_count}")
                
                # ファイル数が増加したかチェック
                if current_file_count > initial_file_count:
                    print(f"   🆕 新規ファイル作成検知: {current_file_count - initial_file_count}個増加")
                
                if json_files:
                    latest_file = max(json_files, key=lambda x: os.path.getctime(os.path.join(optuna_results_dir, x)))
                    print(f"   最新ファイル: {latest_file}")
            else:
                print("❌ 結果ディレクトリが見つかりません")
            
            # 4. メモリ使用量の確認
            print(f"\n💾 [{datetime.now().strftime('%H:%M:%S')}] メモリ使用量:")
            try:
                result = subprocess.run(['tasklist', '/FI', 'IMAGENAME eq python.exe', '/FO', 'CSV'], 
                                      capture_output=True, text=True, shell=True)
                if 'python.exe' in result.stdout:
                    lines = result.stdout.strip().split('\n')
                    for line in lines[1:]:  # ヘッダーをスキップ
                        if 'python.exe' in line:
                            parts = line.split(',')
                            if len(parts) >= 5:
                                memory = parts[4].strip('"')
                                print(f"   メモリ使用量: {memory}")
            except Exception as e:
                print(f"   メモリ情報取得エラー: {e}")
            
            # 5. 最適化完了の検知
            if is_completed:
                print(f"\n🎉 最適化完了を検知しました！")
                print(f"   完了時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                print(f"   最新結果ファイル: {latest_file}")
                print("\n" + "=" * 60)
                print("✅ 最適化が正常に完了しました！")
                break
            
            print("\n" + "=" * 60)
            print("🔄 30秒後に再確認します... (Ctrl+Cで終了)")
            
            time.sleep(30)
            
        except KeyboardInterrupt:
            print("\n\n🛑 監視を終了します")
            break
        except Exception as e:
            print(f"\n❌ エラーが発生しました: {e}")
            time.sleep(5)

if __name__ == "__main__":
    monitor_optimization() 