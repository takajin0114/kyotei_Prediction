# 最適化実行例

## 概要

このドキュメントでは、汎用的な月別データ対応システムを使用した最適化の実行例を示します。

## 目次

1. [基本的な実行例](#基本的な実行例)
2. [月別実行例](#月別実行例)
3. [設定別実行例](#設定別実行例)
4. [トラブルシューティング例](#トラブルシューティング例)

---

## 基本的な実行例

### 1. インタラクティブ実行（推奨開始点）

```bash
# 月とモードを選択して実行
python run_optimization_generic.py
```

**実行フロー**:
1. 対象月の選択（2024-01, 2024-02, 2024-03）
2. 実行モードの選択（テスト/本番）
3. 試行回数の入力
4. 自動実行

**期待される結果**:
- テストモード: 数分で完了
- 本番モード: 数時間で完了

### 2. 一括実行

```bash
# 設定された月を順次実行
python run_optimization_batch.py
```

**設定例**:
```python
# run_optimization_batch.py
target_months = [
    "2024-01",  # 1月
    # "2024-02",  # 2月（コメントアウトで無効化）
    # "2024-03",  # 3月（コメントアウトで無効化）
]
```

### 3. コマンドライン直接実行

```bash
# テストモード（1月データ）
python -m kyotei_predictor.tools.optimization.optimize_graduated_reward_generic \
    --data-month 2024-01 \
    --test-mode \
    --n-trials 3 \
    --study-name test_202401

# 本番モード（1月データ）
python -m kyotei_predictor.tools.optimization.optimize_graduated_reward_generic \
    --data-month 2024-01 \
    --n-trials 50 \
    --study-name production_202401
```

---

## 月別実行例

### 2024年1月データ

#### テスト実行
```bash
python -m kyotei_predictor.tools.optimization.optimize_graduated_reward_generic \
    --data-month 2024-01 \
    --test-mode \
    --n-trials 3 \
    --study-name test_202401
```

**期待される結果**:
- 実行時間: 数分
- 的中率: 0%（想定通り）
- 平均報酬: 0.5-1.0程度
- 用途: 動作確認

#### 本番実行
```bash
python -m kyotei_predictor.tools.optimization.optimize_graduated_reward_generic \
    --data-month 2024-01 \
    --n-trials 50 \
    --study-name production_202401
```

**期待される結果**:
- 実行時間: 数時間
- 的中率: 0-2%（理論的中率約0.83%）
- 平均報酬: 1.0-3.0程度
- 用途: 本格的な最適化

### 2024年2月データ（今後追加予定）

#### テスト実行
```bash
python -m kyotei_predictor.tools.optimization.optimize_graduated_reward_generic \
    --data-month 2024-02 \
    --test-mode \
    --n-trials 3 \
    --study-name test_202402
```

#### 本番実行
```bash
python -m kyotei_predictor.tools.optimization.optimize_graduated_reward_generic \
    --data-month 2024-02 \
    --n-trials 50 \
    --study-name production_202402
```

### 2024年3月データ（今後追加予定）

#### テスト実行
```bash
python -m kyotei_predictor.tools.optimization.optimize_graduated_reward_generic \
    --data-month 2024-03 \
    --test-mode \
    --n-trials 3 \
    --study-name test_202403
```

#### 本番実行
```bash
python -m kyotei_predictor.tools.optimization.optimize_graduated_reward_generic \
    --data-month 2024-03 \
    --n-trials 50 \
    --study-name production_202403
```

---

## 設定別実行例

### 1. 最小限のテスト実行

```bash
# 最短時間での動作確認
python -m kyotei_predictor.tools.optimization.optimize_graduated_reward_generic \
    --data-month 2024-01 \
    --test-mode \
    --n-trials 1 \
    --study-name minimal_test
```

**設定**:
- 総ステップ数: 1,000
- 評価エピソード数: 10
- 試行回数: 1
- 実行時間: 1-2分

### 2. 中規模テスト実行

```bash
# パラメータ調整用
python -m kyotei_predictor.tools.optimization.optimize_graduated_reward_generic \
    --data-month 2024-01 \
    --test-mode \
    --n-trials 5 \
    --study-name medium_test
```

**設定**:
- 総ステップ数: 1,000
- 評価エピソード数: 10
- 試行回数: 5
- 実行時間: 5-10分

### 3. 本番規模実行

```bash
# 本格的な最適化
python -m kyotei_predictor.tools.optimization.optimize_graduated_reward_generic \
    --data-month 2024-01 \
    --n-trials 50 \
    --study-name full_production
```

**設定**:
- 総ステップ数: 100,000
- 評価エピソード数: 2,000
- 試行回数: 50
- 実行時間: 3-5時間

---

## トラブルシューティング例

### 1. データが見つからない場合

**エラー例**:
```
エラー: データペアが存在しません
```

**対処法**:
```bash
# データディレクトリの確認
ls kyotei_predictor/data/raw/2024-01/

# ファイル名の確認
ls kyotei_predictor/data/raw/2024-01/ | head -10

# 正しい月を指定
python -m kyotei_predictor.tools.optimization.optimize_graduated_reward_generic \
    --data-month 2024-01 \
    --test-mode \
    --n-trials 1
```

### 2. メモリ不足の場合

**症状**: 実行中にメモリエラーが発生

**対処法**:
```bash
# テストモードで実行
python -m kyotei_predictor.tools.optimization.optimize_graduated_reward_generic \
    --data-month 2024-01 \
    --test-mode \
    --n-trials 1

# 試行回数を減らす
python -m kyotei_predictor.tools.optimization.optimize_graduated_reward_generic \
    --data-month 2024-01 \
    --test-mode \
    --n-trials 1
```

### 3. 的中率が0%の場合

**症状**: テスト実行で的中率が0%

**想定される原因**:
- テストモードでの短時間学習
- 競艇予測の難しさ（理論的中率約0.83%）
- 学習が不十分

**対処法**:
```bash
# 本番モードで長時間学習
python -m kyotei_predictor.tools.optimization.optimize_graduated_reward_generic \
    --data-month 2024-01 \
    --n-trials 50

# より多くの試行回数
python -m kyotei_predictor.tools.optimization.optimize_graduated_reward_generic \
    --data-month 2024-01 \
    --n-trials 100
```

### 4. 実行時間が長すぎる場合

**対処法**:
```bash
# テストモードを使用
python -m kyotei_predictor.tools.optimization.optimize_graduated_reward_generic \
    --data-month 2024-01 \
    --test-mode \
    --n-trials 3

# 試行回数を減らす
python -m kyotei_predictor.tools.optimization.optimize_graduated_reward_generic \
    --data-month 2024-01 \
    --test-mode \
    --n-trials 1
```

---

## 結果確認例

### 1. 最適化結果の確認

```python
import json

# 結果ファイルの読み込み
with open('optuna_results/graduated_reward_optimization_202401_20250730_231835.json', 'r') as f:
    results = json.load(f)

print(f"対象月: {results['data_month']}")
print(f"最良スコア: {results['best_trial']['value']}")
print(f"最良パラメータ: {results['best_trial']['params']}")
print(f"総試行数: {len(results['trials'])}")
```

### 2. 最良モデルの読み込み

```python
from stable_baselines3 import PPO

# 最良モデルを読み込み
model = PPO.load("optuna_models/graduated_reward_best_202401/best_model.zip")

# モデル情報の確認
print(f"学習ステップ数: {model.num_timesteps}")
print(f"ポリシー: {model.policy}")
```

### 3. 評価結果の確認

```python
import numpy as np

# 評価結果の読み込み
evaluations = np.load('optuna_logs/trial_0/evaluations.npz')

print(f"的中率: {evaluations['hit_rate']}")
print(f"平均報酬: {evaluations['mean_reward']}")
print(f"報酬の標準偏差: {evaluations['reward_std']}")
```

---

## ベストプラクティス

### 1. 実行順序
1. **最小限テスト**: 動作確認
2. **中規模テスト**: パラメータ調整
3. **本番実行**: 本格的な最適化

### 2. 結果管理
- 定期的な結果の確認
- 最良モデルの保存
- ログファイルの整理

### 3. パフォーマンス監視
- メモリ使用量の監視
- 実行時間の記録
- エラーログの確認

---

**最終更新**: 2025-07-30  
**バージョン**: 2.0（汎用システム対応）