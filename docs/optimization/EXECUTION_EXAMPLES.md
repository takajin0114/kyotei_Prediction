# 最適化実行例

## 概要

このドキュメントでは、様々な期間のデータを使用した最適化の実行例を示します。

## 目次

1. [基本的な実行例](#基本的な実行例)
2. [期間別実行例](#期間別実行例)
3. [設定別実行例](#設定別実行例)
4. [トラブルシューティング例](#トラブルシューティング例)

---

## 基本的な実行例

### 1. テスト実行（推奨開始点）

```bash
# 2024年3月データでのテスト実行
python run_optimization_generic.py \
    --data-dir kyotei_predictor/data/raw/2024-03 \
    --n-trials 3 \
    --test-mode
```

**期待される結果**:
- 実行時間: 数分
- スコア: 3-8程度
- 用途: 動作確認、パラメータ調整

### 2. 小規模実行

```bash
# 2024年3月データでの小規模実行
python run_optimization_generic.py \
    --data-dir kyotei_predictor/data/raw/2024-03 \
    --n-trials 10 \
    --test-mode
```

**期待される結果**:
- 実行時間: 10-15分
- スコア: 5-10程度
- 用途: パラメータ範囲の確認

### 3. 本格実行

```bash
# 2024年3月データでの本格実行
python run_optimization_generic.py \
    --data-dir kyotei_predictor/data/raw/2024-03 \
    --n-trials 50
```

**期待される結果**:
- 実行時間: 3-5時間
- スコア: 8-15程度
- 用途: 本格的な最適化

---

## 期間別実行例

### 2024年1月データ

```bash
# テスト実行
python run_optimization_generic.py \
    --data-dir kyotei_predictor/data/raw/2024-01 \
    --n-trials 5 \
    --test-mode \
    --study-name test_202401

# 本格実行
python run_optimization_generic.py \
    --data-dir kyotei_predictor/data/raw/2024-01 \
    --n-trials 30 \
    --study-name full_202401
```

### 2024年2月データ

```bash
# テスト実行
python run_optimization_generic.py \
    --data-dir kyotei_predictor/data/raw/2024-02 \
    --n-trials 5 \
    --test-mode \
    --study-name test_202402

# 本格実行
python run_optimization_generic.py \
    --data-dir kyotei_predictor/data/raw/2024-02 \
    --n-trials 30 \
    --study-name full_202402
```

### 2024年3月データ（完了済み）

```bash
# テスト実行（完了済み）
python run_optimization_generic.py \
    --data-dir kyotei_predictor/data/raw/2024-03 \
    --n-trials 3 \
    --test-mode \
    --study-name test_202403

# 本格実行（実行中）
python run_optimization_generic.py \
    --data-dir kyotei_predictor/data/raw/2024-03 \
    --n-trials 20 \
    --study-name full_202403
```

### 2024年4月データ

```bash
# テスト実行
python run_optimization_generic.py \
    --data-dir kyotei_predictor/data/raw/2024-04 \
    --n-trials 5 \
    --test-mode \
    --study-name test_202404

# 本格実行
python run_optimization_generic.py \
    --data-dir kyotei_predictor/data/raw/2024-04 \
    --n-trials 30 \
    --study-name full_202404
```

---

## 設定別実行例

### 高精度実行（長時間）

```bash
# より多くの試行回数で高精度実行
python run_optimization_generic.py \
    --data-dir kyotei_predictor/data/raw/2024-03 \
    --n-trials 100 \
    --study-name high_precision_202403
```

**特徴**:
- 試行回数: 100回
- 実行時間: 10-15時間
- 期待スコア: 10-20程度

### 高速実行（短時間）

```bash
# 最小限の試行回数で高速実行
python run_optimization_generic.py \
    --data-dir kyotei_predictor/data/raw/2024-03 \
    --n-trials 5 \
    --test-mode \
    --study-name quick_202403
```

**特徴**:
- 試行回数: 5回
- 実行時間: 10-15分
- 期待スコア: 3-8程度

### バランス実行（標準）

```bash
# バランスの取れた実行
python run_optimization_generic.py \
    --data-dir kyotei_predictor/data/raw/2024-03 \
    --n-trials 20 \
    --study-name balanced_202403
```

**特徴**:
- 試行回数: 20回
- 実行時間: 3-5時間
- 期待スコア: 8-15程度

---

## トラブルシューティング例

### 例1: データディレクトリが見つからない

**エラー**:
```
データディレクトリが存在しません: kyotei_predictor/data/raw/2024-03
```

**解決方法**:
```bash
# データディレクトリの存在確認
ls kyotei_predictor/data/raw/

# 正しいパスを指定
python run_optimization_generic.py --data-dir kyotei_predictor/data/raw/2024-03
```

### 例2: メモリ不足

**症状**: 実行中にメモリエラーが発生

**解決方法**:
```bash
# テストモードで実行
python run_optimization_generic.py \
    --data-dir kyotei_predictor/data/raw/2024-03 \
    --test-mode

# 試行回数を減らす
python run_optimization_generic.py \
    --data-dir kyotei_predictor/data/raw/2024-03 \
    --n-trials 5
```

### 例3: 実行時間が長すぎる

**解決方法**:
```bash
# テストモードで実行
python run_optimization_generic.py \
    --data-dir kyotei_predictor/data/raw/2024-03 \
    --test-mode

# 試行回数を減らす
python run_optimization_generic.py \
    --data-dir kyotei_predictor/data/raw/2024-03 \
    --n-trials 5
```

### 例4: スコアが低い

**原因**: データ不足、パラメータ範囲の問題

**解決方法**:
```bash
# より多くの試行回数で実行
python run_optimization_generic.py \
    --data-dir kyotei_predictor/data/raw/2024-03 \
    --n-trials 50

# 本格モードで実行
python run_optimization_generic.py \
    --data-dir kyotei_predictor/data/raw/2024-03 \
    --n-trials 30
```

---

## 実行結果の例

### テスト実行結果（2024年3月）

```json
{
  "optimization_time": "2025-07-29T11:45:21.983429",
  "study_name": "test_202403_optimization",
  "n_trials": 3,
  "best_trial": {
    "number": 2,
    "value": 6.1066,
    "params": {
      "learning_rate": 5.076e-05,
      "batch_size": 256,
      "n_steps": 1024,
      "gamma": 0.985,
      "gae_lambda": 0.878,
      "n_epochs": 4,
      "clip_range": 0.310,
      "ent_coef": 0.021,
      "vf_coef": 0.687,
      "max_grad_norm": 0.512
    }
  }
}
```

### 本格実行結果（予想）

```json
{
  "optimization_time": "2025-07-29T15:30:00.000000",
  "study_name": "full_202403_optimization",
  "n_trials": 20,
  "best_trial": {
    "number": 15,
    "value": 12.456,
    "params": {
      "learning_rate": 3.245e-04,
      "batch_size": 128,
      "n_steps": 2048,
      "gamma": 0.995,
      "gae_lambda": 0.920,
      "n_epochs": 8,
      "clip_range": 0.250,
      "ent_coef": 0.015,
      "vf_coef": 0.500,
      "max_grad_norm": 0.750
    }
  }
}
```

---

## ベストプラクティス

### 1. 段階的な実行

1. **テスト実行**: 動作確認
2. **小規模実行**: パラメータ確認
3. **本格実行**: 最適化

### 2. 結果の保存

```bash
# 結果ファイルのバックアップ
cp optuna_results/graduated_reward_optimization_*.json backup/

# 最良モデルの保存確認
ls optuna_models/graduated_reward_best/
```

### 3. 監視とログ

```bash
# 実行中の進捗確認
tail -f optuna_logs/trial_*/evaluations.npz

# エラーログの確認
ls outputs/logs/
```

---

**最終更新**: 2025-01-27  
**バージョン**: 1.0