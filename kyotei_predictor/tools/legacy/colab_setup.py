#!/usr/bin/env python3
"""
Google Colab用セットアップスクリプト

このスクリプトは、Google Colab環境でkyotei_Predictionプロジェクトを
実行するために必要な依存関係とファイル構造を設定します。
"""

import os
import sys
import subprocess
import json
from pathlib import Path

def install_requirements():
    """必要なパッケージをインストール"""
    print("📦 必要なパッケージをインストール中...")
    
    requirements = [
        "numpy",
        "pandas", 
        "matplotlib",
        "seaborn",
        "scikit-learn",
        "optuna",
        "stable-baselines3",
        "gymnasium",
        "torch",
        "flask",
        "flask-caching",
        "requests",
        "beautifulsoup4",
        "lxml",
        "pytest",
        "pytest-cov",
        "pytest-html"
    ]
    
    for package in requirements:
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])
            print(f"✅ {package} をインストールしました")
        except subprocess.CalledProcessError:
            print(f"❌ {package} のインストールに失敗しました")

def create_colab_directory_structure():
    """Colab用のディレクトリ構造を作成"""
    print("📁 Colab用ディレクトリ構造を作成中...")
    
    directories = [
        "kyotei_predictor",
        "kyotei_predictor/data",
        "kyotei_predictor/data/raw",
        "kyotei_predictor/data/processed", 
        "kyotei_predictor/data/sample",
        "kyotei_predictor/logs",
        "kyotei_predictor/outputs",
        "optuna_results",
        "optuna_studies",
        "optuna_models",
        "optuna_logs",
        "optuna_tensorboard"
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        print(f"✅ ディレクトリ作成: {directory}")

def create_sample_data():
    """サンプルデータを作成（テスト用）"""
    print("📊 サンプルデータを作成中...")
    
    # サンプルの最適化結果データ
    sample_optimization_result = {
        "optimization_time": "2025-01-27 03:44:13",
        "n_trials": 50,
        "best_trial": {
            "number": 23,
            "value": 8.45,
            "params": {
                "learning_rate": 0.0002,
                "batch_size": 32,
                "n_steps": 2048,
                "gamma": 0.99,
                "gae_lambda": 0.95,
                "n_epochs": 20,
                "clip_range": 0.2,
                "ent_coef": 0.01,
                "vf_coef": 0.5,
                "max_grad_norm": 0.5
            }
        },
        "all_trials": []
    }
    
    # 50個のサンプルトライアルを生成
    import numpy as np
    for i in range(50):
        trial = {
            "number": i,
            "value": np.random.normal(7.5, 1.0),  # 平均7.5、標準偏差1.0
            "params": {
                "learning_rate": np.random.uniform(0.0001, 0.001),
                "batch_size": np.random.choice([16, 32, 64, 128, 256]),
                "n_steps": np.random.choice([1024, 2048, 4096]),
                "gamma": np.random.uniform(0.95, 0.999),
                "gae_lambda": np.random.uniform(0.9, 0.99),
                "n_epochs": np.random.choice([10, 15, 20, 25]),
                "clip_range": np.random.uniform(0.1, 0.3),
                "ent_coef": np.random.uniform(0.005, 0.02),
                "vf_coef": np.random.uniform(0.3, 0.7),
                "max_grad_norm": np.random.uniform(0.3, 0.7)
            }
        }
        sample_optimization_result["all_trials"].append(trial)
    
    # ファイルに保存
    with open("graduated_reward_optimization_20250727_034413.json", "w", encoding="utf-8") as f:
        json.dump(sample_optimization_result, f, ensure_ascii=False, indent=2)
    
    print("✅ サンプル最適化結果データを作成しました")

def create_colab_notebook_template():
    """Colab用のノートブックテンプレートを作成"""
    print("📝 Colab用ノートブックテンプレートを作成中...")
    
    template = '''# Kyotei Prediction - Google Colab版

## セットアップ

```python
# 必要なパッケージをインストール
!pip install numpy pandas matplotlib seaborn scikit-learn optuna stable-baselines3 gymnasium torch flask flask-caching requests beautifulsoup4 lxml pytest pytest-cov pytest-html

# セットアップスクリプトを実行
!python colab_setup.py
```

## 分析スクリプトの実行

```python
# 分析スクリプトを実行
!python analysis_202401_results_colab.py
```

## ファイルのアップロード

分析に必要なJSONファイルをアップロードしてください：

```python
from google.colab import files
uploaded = files.upload()
```

## 結果のダウンロード

```python
from google.colab import files
files.download('analysis_202401_results_colab.png')
```
'''
    
    with open("colab_notebook_template.ipynb", "w", encoding="utf-8") as f:
        f.write(template)
    
    print("✅ Colab用ノートブックテンプレートを作成しました")

def main():
    """メイン処理"""
    print("🚀 Google Colab用セットアップを開始します")
    
    # 1. パッケージのインストール
    install_requirements()
    
    # 2. ディレクトリ構造の作成
    create_colab_directory_structure()
    
    # 3. サンプルデータの作成
    create_sample_data()
    
    # 4. ノートブックテンプレートの作成
    create_colab_notebook_template()
    
    print("\n✅ セットアップが完了しました！")
    print("\n📋 次のステップ:")
    print("1. analysis_202401_results_colab.py を実行")
    print("2. 必要に応じてJSONファイルをアップロード")
    print("3. 結果をダウンロード")

if __name__ == "__main__":
    main() 