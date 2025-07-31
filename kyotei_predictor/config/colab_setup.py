#!/usr/bin/env python3
"""
Google Colab用セットアップスクリプト
環境依存をなくし、Colab環境で強化学習を実行できるようにします
"""

import os
import sys
import subprocess
import json
from pathlib import Path
from datetime import datetime

def detect_colab_environment():
    """Colab環境かどうかを検出"""
    return 'COLAB_GPU' in os.environ or 'COLAB_TPU' in os.environ

def get_colab_project_root():
    """Colab環境でのプロジェクトルートを取得"""
    if detect_colab_environment():
        return Path('/content/kyotei_Prediction')
    else:
        return Path.cwd()

def install_requirements():
    """必要なパッケージをインストール"""
    print("必要なパッケージをインストール中...")
    
    requirements = [
        "psutil",
        "schedule",
        "optuna",
        "torch",
        "numpy",
        "pandas",
        "matplotlib",
        "seaborn",
        "tqdm"
    ]
    
    for package in requirements:
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])
            print(f"✓ {package} をインストールしました")
        except subprocess.CalledProcessError as e:
            print(f"✗ {package} のインストールに失敗: {e}")

def setup_directories(project_root):
    """必要なディレクトリを作成"""
    print("ディレクトリ構造をセットアップ中...")
    
    directories = [
        "optuna_models",
        "optuna_logs", 
        "optuna_results",
        "optuna_studies",
        "outputs",
        "archives",
        "data",
        "kyotei_predictor/tools/maintenance/configs"
    ]
    
    for directory in directories:
        dir_path = project_root / directory
        dir_path.mkdir(parents=True, exist_ok=True)
        print(f"✓ {directory} ディレクトリを作成しました")

def create_colab_configs(project_root):
    """Colab環境用の設定ファイルを作成"""
    print("Colab環境用の設定ファイルを作成中...")
    
    # メンテナンス設定
    maintenance_configs = {
        "cleanup_config.json": {
            "max_disk_usage_percent": 90,  # Colabでは容量制限が厳しい
            "targets": {
                "outputs/logs": {
                    "enabled": True,
                    "max_files": 5,
                    "max_size_mb": 50
                },
                "optuna_models/graduated_reward_checkpoints": {
                    "enabled": True,
                    "max_files": 3,
                    "max_size_mb": 200
                }
            }
        },
        "monitor_config.json": {
            "monitoring": {
                "check_interval": 300,  # 5分間隔
                "warning_threshold": 80,
                "critical_threshold": 90,
                "emergency_threshold": 95
            },
            "directories": {
                "optuna_models": {"max_size_gb": 2},
                "optuna_logs": {"max_size_gb": 1},
                "outputs": {"max_size_gb": 0.5}
            }
        },
        "scheduler_config.json": {
            "schedules": {
                "daily_cleanup": {
                    "enabled": True,
                    "time": "02:00",
                    "command": "python kyotei_predictor/tools/maintenance/auto_cleanup.py --project-root /content/kyotei_Prediction"
                },
                "disk_monitor": {
                    "enabled": True,
                    "interval_minutes": 30,
                    "command": "python kyotei_predictor/tools/maintenance/disk_monitor.py --project-root /content/kyotei_Prediction --status"
                }
            }
        }
    }
    
    configs_dir = project_root / "kyotei_predictor/tools/maintenance/configs"
    configs_dir.mkdir(parents=True, exist_ok=True)
    
    for config_name, config_data in maintenance_configs.items():
        config_path = configs_dir / config_name
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config_data, f, indent=2, ensure_ascii=False)
        print(f"✓ {config_name} を作成しました")

def create_colab_notebook_template():
    """Colab用のノートブックテンプレートを作成"""
    template = '''# Kyotei Prediction - Google Colab 環境

## セットアップ

```python
# リポジトリをクローン
!git clone https://github.com/your-username/kyotei_Prediction.git
%cd kyotei_Prediction

# セットアップスクリプトを実行
!python colab_setup.py
```

## 強化学習の実行

```python
# 統合最適化スクリプトを使用
!python kyotei_predictor/tools/optimization/unified_optimizer.py \\
    --type graduated_reward \\
    --project-root /content/kyotei_Prediction \\
    --n-trials 50 \\
    --timeout 1800
```

## メンテナンス

```python
# ディスク容量監視
!python kyotei_predictor/tools/maintenance/disk_monitor.py \\
    --project-root /content/kyotei_Prediction \\
    --status

# 自動クリーンアップ
!python kyotei_predictor/tools/maintenance/auto_cleanup.py \\
    --project-root /content/kyotei_Prediction \\
    --report-only
```

## 注意事項

- Colab環境ではディスク容量に制限があります
- 長時間の実行はセッションタイムアウトに注意してください
- 重要な結果はGoogle Driveに保存することを推奨します
'''
    
    with open('colab_notebook_template.md', 'w', encoding='utf-8') as f:
        f.write(template)
    print("✓ Colab用ノートブックテンプレートを作成しました")

def main():
    """メイン関数"""
    print("=== Google Colab 環境セットアップ ===")
    
    # 環境検出
    if detect_colab_environment():
        print("✓ Google Colab環境を検出しました")
    else:
        print("⚠ ローカル環境で実行中です")
    
    # プロジェクトルートを取得
    project_root = get_colab_project_root()
    print(f"プロジェクトルート: {project_root}")
    
    # パッケージインストール
    install_requirements()
    
    # ディレクトリセットアップ
    setup_directories(project_root)
    
    # 設定ファイル作成
    create_colab_configs(project_root)
    
    # ノートブックテンプレート作成
    create_colab_notebook_template()
    
    print("\n=== セットアップ完了 ===")
    print("Google Colab環境で強化学習を実行する準備が整いました！")
    print("\n使用方法:")
    print("1. リポジトリをクローン")
    print("2. このスクリプトを実行")
    print("3. 統合最適化スクリプトで強化学習を実行")

if __name__ == "__main__":
    main() 