# 最適化実行ガイド

## 概要

このガイドでは、競艇予測モデルのハイパーパラメータ最適化の実行方法について説明します。

## 目次

1. [概要](#概要)
2. [実行方法](#実行方法)
3. [設定オプション](#設定オプション)
4. [実行例](#実行例)
5. [結果の確認](#結果の確認)
6. [トラブルシューティング](#トラブルシューティング)

---

## 実行方法

### 1. 直接スクリプト実行（推奨）

```bash
# 基本的な実行（2024年1月データ）
python kyotei_predictor/tools/optimization/optimize_graduated_reward.py --n-trials 10 --year-month 2024-01

# テストモードでの実行
python kyotei_predictor/tools/optimization/optimize_graduated_reward.py --test-mode --n-trials 3

# 試行回数を指定
python kyotei_predictor/tools/optimization/optimize_graduated_reward.py --n-trials 50 --year-month 2024-03

# 最小限モードでの実行
python kyotei_predictor/tools/optimization/optimize_graduated_reward.py --minimal --n-trials 1
```

### 2. モジュール実行（代替方法）

```bash
# 標準的な実行
python -m kyotei_predictor.tools.optimization.optimize_graduated_reward \
    --n-trials 20 \
    --year-month 2024-01 \
    --test-mode
```

### 3. Pythonスクリプトからの実行

```python
from kyotei_predictor.tools.optimization.optimize_graduated_reward import optimize_graduated_reward

study = optimize_graduated_reward(
    n_trials=20,
    study_name="my_optimization",
    data_dir="kyotei_predictor/data/raw/2024-03",
    test_mode=False
)
```

---

## 設定オプション

### 基本パラメータ

| パラメータ | デフォルト | 説明 |
|------------|------------|------|
| `year_month` | 必須 | 対象年月（例：2024-01） |
| `n_trials` | 20 | 最適化の試行回数 |
| `test_mode` | False | テストモード（短時間設定） |
| `minimal` | False | 最小限モード（最短時間設定） |
| `study_name` | 自動生成 | Optunaスタディ名 |

### テストモード vs 通常モード

| 設定 | テストモード | 通常モード |
|------|-------------|------------|
| **総ステップ数** | 10,000 | 100,000 |
| **評価エピソード数** | 100 | 2,000 |
| **実行時間** | 数分 | 数時間 |
| **精度** | 低 | 高 |

### ハイパーパラメータ範囲

| パラメータ | 範囲 | 説明 |
|------------|------|------|
| `learning_rate` | 1e-5 ~ 1e-2 | 学習率（対数スケール） |
| `batch_size` | [32, 64, 128, 256] | バッチサイズ |
| `n_steps` | [1024, 2048, 4096] | 1エポックあたりのステップ数 |
| `gamma` | 0.9 ~ 0.999 | 割引率 |
| `gae_lambda` | 0.8 ~ 0.99 | GAEのλパラメータ |
| `n_epochs` | 3 ~ 20 | 1エポックあたりの更新回数 |
| `clip_range` | 0.1 ~ 0.4 | PPOのクリップ範囲 |
| `ent_coef` | 0.0 ~ 0.1 | エントロピー係数 |
| `vf_coef` | 0.1 ~ 1.0 | 価値関数の係数 |
| `max_grad_norm` | 0.1 ~ 1.0 | 勾配クリッピングの閾値 |

---

## 実行例

### 例1: 2024年3月データでのテスト実行

```bash
python kyotei_predictor/tools/optimization/optimize_graduated_reward.py \
    --year-month 2024-03 \
    --n-trials 5 \
    --test-mode
```

### 例2: 2024年1月データでの本格最適化

```bash
python kyotei_predictor/tools/optimization/optimize_graduated_reward.py \
    --year-month 2024-01 \
    --n-trials 50
```

### 例3: 特定の期間での最適化

```bash
python kyotei_predictor/tools/optimization/optimize_graduated_reward.py \
    --year-month 2024-02 \
    --n-trials 30
```

---

## 結果の確認

### 1. 最適化結果ファイル

結果は以下の場所に保存されます：

```
optuna_results/
├── graduated_reward_optimization_YYYYMMDD_HHMMSS.json
└── README.md
```

### 2. 最良モデル

```
optuna_models/
├── graduated_reward_best/
│   └── best_model.zip
└── trial_X/
    ├── best_model.zip
    └── checkpoint_X.zip
```

### 3. ログファイル

```
optuna_logs/
└── trial_X/
    └── evaluations.npz
```

### 4. 結果の読み込み

```python
import json

# 結果ファイルの読み込み
with open('optuna_results/graduated_reward_optimization_YYYYMMDD_HHMMSS.json', 'r') as f:
    results = json.load(f)

# 最良パラメータの取得
best_params = results['best_trial']['params']
best_score = results['best_trial']['value']

print(f"最良スコア: {best_score}")
print(f"最良パラメータ: {best_params}")
```

---

## トラブルシューティング

### よくある問題と解決方法

#### 1. データディレクトリが見つからない

**エラー**: `データディレクトリが存在しません`

**解決方法**:
```bash
# データディレクトリの存在確認
ls kyotei_predictor/data/raw/

# 正しいパスを指定
python kyotei_predictor/tools/optimization/optimize_graduated_reward.py --year-month 2024-03
```

#### 2. メモリ不足

**症状**: 実行中にメモリエラーが発生

**解決方法**:
- バッチサイズを小さくする
- テストモードを使用する
- 試行回数を減らす

#### 3. 実行時間が長すぎる

**解決方法**:
```bash
# テストモードで実行
python kyotei_predictor/tools/optimization/optimize_graduated_reward.py --year-month 2024-03 --test-mode

# 最小限モードで実行
python kyotei_predictor/tools/optimization/optimize_graduated_reward.py --year-month 2024-03 --minimal

# 試行回数を減らす
python kyotei_predictor/tools/optimization/optimize_graduated_reward.py --year-month 2024-03 --n-trials 5
```

#### 4. スコアが低い

**原因**: データ不足、パラメータ範囲の問題

**解決方法**:
- より多くのデータを使用
- パラメータ範囲を調整
- より多くの試行回数で実行

---

## ベストプラクティス

### 1. 実行前の確認

- [ ] データディレクトリの存在確認
- [ ] 十分なディスク容量の確認
- [ ] メモリ使用量の確認

### 2. 段階的な実行

1. **テスト実行**: 短時間で動作確認
2. **小規模実行**: 少数の試行でパラメータ確認
3. **本格実行**: 十分な試行回数で最適化

### 3. 結果の保存

- 最適化結果のJSONファイルをバックアップ
- 最良モデルの保存確認
- ログファイルの整理

### 4. 監視とログ

- 実行中の進捗確認
- エラーログの確認
- リソース使用量の監視

---

## 関連ドキュメント

- [要件レベル整理](../REQUIREMENTS_OVERVIEW.md) - 最適化機能の位置づけと要件の全体像
- [全体状況サマリー](../CURRENT_STATUS_SUMMARY.md) - 現在の実装状況・運用状況
- [運用ガイド索引](../operations/README.md) - 定期運用・保守手順の入口

---

**最終更新**: 2025-01-27  
**バージョン**: 1.0