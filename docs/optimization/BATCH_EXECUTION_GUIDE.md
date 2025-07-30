# 最適化バッチ実行ガイド

## 📋 概要

このガイドでは、競艇予測モデルのハイパーパラメータ最適化バッチの実行方法について詳細に説明します。

## 🎯 最適化バッチの種類

### 1. 段階的報酬最適化（`optimize_graduated_reward.py`）
- **目的**: 段階的報酬設計モデルのハイパーパラメータ最適化
- **対象**: PPO（Proximal Policy Optimization）アルゴリズム
- **特徴**: 部分的中にも報酬を与える段階的報酬設計

### 2. AI最適化ツール（`optuna_optimizer.py`）
- **目的**: 競艇RLモデルの包括的なハイパーパラメータ最適化
- **対象**: 複数の強化学習アルゴリズム
- **特徴**: Optunaを使用した自動最適化

### 3. 学習バッチ（`train_with_graduated_reward.py`）
- **目的**: 最適化されたパラメータでの学習実行
- **対象**: 段階的報酬設計モデル
- **特徴**: チェックポイント保存と評価機能

## 🚀 実行方法

### 基本的な実行

```bash
# 段階的報酬最適化（本番モード）
python -m kyotei_predictor.tools.optimization.optimize_graduated_reward \
    --data-dir kyotei_predictor/data/raw/2024-03 \
    --n-trials 50 \
    --study-name graduated_reward_optimization_202403

# テストモードでの実行
python -m kyotei_predictor.tools.optimization.optimize_graduated_reward \
    --data-dir kyotei_predictor/data/raw/2024-03 \
    --n-trials 3 \
    --test-mode

# 既存スタディの継続
python -m kyotei_predictor.tools.optimization.optimize_graduated_reward \
    --data-dir kyotei_predictor/data/raw/2024-03 \
    --n-trials 20 \
    --resume-existing
```

### カスタムスクリプトでの実行

```bash
# 本番想定の最適化
python run_full_optimization.py

# テスト最適化
python test_optimization.py

# シンプルな最適化
python simple_optimization.py
```

### Pythonコードからの実行

```python
from kyotei_predictor.tools.optimization.optimize_graduated_reward import optimize_graduated_reward

# 本番想定の最適化
study = optimize_graduated_reward(
    n_trials=50,
    study_name="graduated_reward_optimization_202403_full",
    data_dir="kyotei_predictor/data/raw/2024-03",
    test_mode=False,
    resume_existing=False
)

print(f"最良スコア: {study.best_value:.4f}")
print(f"最良パラメータ: {study.best_params}")
```

## ⚙️ パラメータ設定

### 本番想定パラメータ

| パラメータ | 値 | 説明 |
|------------|----|------|
| `n_trials` | 50 | 最適化試行回数 |
| `total_timesteps` | 100,000 | 学習ステップ数 |
| `n_eval_episodes` | 2,000 | 評価エピソード数 |
| `test_mode` | False | 本番モード |
| `resume_existing` | False | 新規スタディ |

### テストモードパラメータ

| パラメータ | 値 | 説明 |
|------------|----|------|
| `n_trials` | 3-5 | 少ない試行回数 |
| `total_timesteps` | 10,000 | 短時間学習 |
| `n_eval_episodes` | 100 | 少ない評価回数 |
| `test_mode` | True | テストモード |

### ハイパーパラメータ探索範囲

| パラメータ | 範囲 | タイプ | 説明 |
|------------|------|--------|------|
| `learning_rate` | 1e-5 ~ 1e-2 | float (log) | 学習率 |
| `batch_size` | [32, 64, 128, 256] | categorical | バッチサイズ |
| `n_steps` | [1024, 2048, 4096] | categorical | ステップ数 |
| `gamma` | 0.9 ~ 0.999 | float | 割引率 |
| `gae_lambda` | 0.8 ~ 0.99 | float | GAE λ |
| `n_epochs` | 3 ~ 20 | int | エポック数 |
| `clip_range` | 0.1 ~ 0.4 | float | クリップ範囲 |
| `ent_coef` | 0.0 ~ 0.1 | float | エントロピー係数 |
| `vf_coef` | 0.1 ~ 1.0 | float | 価値関数係数 |
| `max_grad_norm` | 0.1 ~ 1.0 | float | 勾配クリッピング |

## 📊 実行状況監視

### プロセス確認

```bash
# Pythonプロセスの確認
Get-Process python | Select-Object Id, ProcessName, StartTime

# プロセス数の確認
Get-Process python | Measure-Object
```

### 進行状況確認

```bash
# スタディファイルの確認
ls optuna_studies/

# ログディレクトリの確認
ls optuna_logs/

# 結果ファイルの確認
ls optuna_results/
```

### リアルタイム監視

```python
import os
import time
from datetime import datetime

def monitor_optimization():
    """最適化の進行状況を監視"""
    while True:
        # プロセス確認
        import subprocess
        result = subprocess.run(['Get-Process', 'python'], capture_output=True, text=True)
        
        if 'python' in result.stdout:
            print(f"[{datetime.now()}] 最適化実行中...")
            
            # ログディレクトリ確認
            log_dirs = [d for d in os.listdir('optuna_logs') if d.startswith('trial_')]
            print(f"完了試行数: {len(log_dirs)}")
            
        else:
            print(f"[{datetime.now()}] 最適化完了")
            break
            
        time.sleep(60)  # 1分間隔で確認
```

## 📁 出力ファイル構造

### 結果ファイル

```
optuna_results/
├── graduated_reward_optimization_YYYYMMDD_HHMMSS.json
├── graduated_reward_optimization_YYYYMMDD_HHMMSS.json
└── README.md
```

### モデルファイル

```
optuna_models/
├── graduated_reward_best/
│   └── best_model.zip
├── graduated_reward_checkpoints/
│   ├── graduated_reward_model_XXXXX_steps.zip
│   └── graduated_reward_model_XXXXX_steps.zip
└── trial_X/
    ├── best_model.zip
    └── checkpoint_XXXXX_steps.zip
```

### ログファイル

```
optuna_logs/
├── graduated_reward/
│   └── evaluations.npz
└── trial_X/
    └── evaluations.npz
```

### スタディファイル

```
optuna_studies/
├── graduated_reward_optimization_YYYYMMDD_HHMMSS.db
├── graduated_reward_optimization_YYYYMMDD_HHMMSS.db
└── ...
```

## 🔍 結果分析

### 結果ファイルの読み込み

```python
import json
import numpy as np

# 最新の結果ファイルを読み込み
result_files = sorted([f for f in os.listdir('optuna_results') if f.endswith('.json')])
latest_file = result_files[-1]

with open(f'optuna_results/{latest_file}', 'r') as f:
    results = json.load(f)

print(f"最良スコア: {results['best_trial']['value']:.4f}")
print(f"最良パラメータ:")
for key, value in results['best_trial']['params'].items():
    print(f"  {key}: {value}")
```

### 評価結果の分析

```python
# 評価結果の読み込み
eval_data = np.load('optuna_logs/trial_X/evaluations.npz')
rewards = eval_data['rewards']
hit_rates = eval_data['hit_rates']

print(f"平均報酬: {np.mean(rewards):.4f}")
print(f"的中率: {np.mean(hit_rates)*100:.2f}%")
```

## 🛠️ トラブルシューティング

### よくある問題と解決方法

#### 1. プロセスが中断される
```bash
# プロセス確認
Get-Process python

# 強制終了
Stop-Process -Name python -Force

# 再実行
python run_full_optimization.py
```

#### 2. メモリ不足
```python
# バッチサイズを小さくする
batch_size = 32  # 256から32に変更

# ステップ数を減らす
n_steps = 1024  # 4096から1024に変更
```

#### 3. データ不足エラー
```python
# データペア数の確認
from kyotei_predictor.pipelines.kyotei_env import KyoteiEnvManager
env = KyoteiEnvManager(data_dir="kyotei_predictor/data/raw/2024-03")
print(f"データペア数: {len(env.pairs)}")
```

#### 4. 最適化が収束しない
```python
# 試行回数を増やす
n_trials = 100  # 50から100に増加

# パラメータ範囲を調整
learning_rate_range = (1e-4, 1e-3)  # 範囲を狭める
```

## 📈 実行例

### 2024年3月データでの本番最適化

```bash
# 実行開始
python run_full_optimization.py

# 実行状況確認
Get-Process python | Select-Object Id, ProcessName, StartTime

# 結果確認
ls optuna_results/
```

### 実行結果例

```
=== 2024年3月データでの本番想定最適化開始 ===
実行開始時刻: 2025-07-29 22:51:24
1. モジュールインポート...
   ✓ 最適化モジュールインポート成功
2. 環境確認...
   ✓ データペア数: 4221
3. 最適化パラメータ:
   試行回数: 50
   データディレクトリ: kyotei_predictor/data/raw/2024-03
   スタディ名: graduated_reward_optimization_202403_full
   テストモード: False
   既存スタディ継続: False
4. 最適化実行開始...

=== 最適化完了 ===
実行時間: 8.5時間
最良の試行: 23
最良のスコア: 12.4567
総試行数: 50

最良のパラメータ:
  learning_rate: 0.0005208350022906673
  batch_size: 32
  n_steps: 2048
  gamma: 0.9625736219052181
  gae_lambda: 0.848147099172992
  n_epochs: 13
  clip_range: 0.15048207902754762
  ent_coef: 0.029866380770793177
  vf_coef: 0.5881261629810149
  max_grad_norm: 0.8501367302468871
```

## 🔗 関連ドキュメント

- [最適化ガイド](OPTIMIZATION_GUIDE.md) - 詳細な最適化手法
- [実行例](EXECUTION_EXAMPLES.md) - 具体的な実行例
- [現在の状況サマリー](../CURRENT_STATUS_SUMMARY.md) - プロジェクト全体の状況
- [運用マニュアル](../OPERATIONS_MANUAL.md) - 運用に関するガイド

## 📝 更新履歴

- **2025-07-29**: バッチ実行ガイドの作成
- **2025-07-29**: 本番想定パラメータの定義
- **2025-07-29**: トラブルシューティングの追加
- **2025-07-29**: 実行例の追加

---

**最終更新**: 2025-07-29  
**バージョン**: 1.0