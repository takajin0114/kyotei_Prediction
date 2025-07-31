# 最適化実行ガイド

## 概要

このガイドでは、競艇予測モデルのハイパーパラメータ最適化の実行方法について説明します。
**汎用的な月別データ対応システム**に対応しています。

## 目次

1. [概要](#概要)
2. [実行方法](#実行方法)
3. [設定オプション](#設定オプション)
4. [実行例](#実行例)
5. [結果の確認](#結果の確認)
6. [トラブルシューティング](#トラブルシューティング)

---

## 実行方法

### 1. 汎用最適化スクリプトの使用（推奨）

#### インタラクティブ実行
```bash
# 月とモードを選択して実行
python run_optimization_generic.py
```

#### 一括実行
```bash
# 設定された月を順次実行
python run_optimization_batch.py
```

#### コマンドライン直接実行
```bash
# テストモード（1月データ）
python -m kyotei_predictor.tools.optimization.optimize_graduated_reward_generic \
    --data-month 2024-01 --test-mode --n-trials 3

# 本番モード（1月データ）
python -m kyotei_predictor.tools.optimization.optimize_graduated_reward_generic \
    --data-month 2024-01 --n-trials 50
```

### 2. 月別データ対応

#### 利用可能な月
- `2024-01` - 1月データ
- `2024-02` - 2月データ（今後追加）
- `2024-03` - 3月データ（今後追加）

#### 新しい月の追加方法
1. **データディレクトリの準備**
   ```
   kyotei_predictor/data/raw/2024-02/
   ├── race_data_2024-02-01_BIWAKO_R1.json
   ├── odds_data_2024-02-01_BIWAKO_R1.json
   └── ...
   ```

2. **実行スクリプトの更新**
   ```python
   # run_optimization_generic.py
   months = [
       "2024-01",  # 1月
       "2024-02",  # 2月（新規追加）
   ]
   ```

### 3. Pythonスクリプトからの実行

```python
from kyotei_predictor.tools.optimization.optimize_graduated_reward_generic import optimize_graduated_reward_generic

study = optimize_graduated_reward_generic(
    data_month="2024-01",
    n_trials=20,
    test_mode=False
)
```

---

## 設定オプション

### 基本パラメータ

| パラメータ | デフォルト | 説明 |
|------------|------------|------|
| `data_month` | 必須 | データ月（例: "2024-01"） |
| `n_trials` | 10 | 最適化の試行回数 |
| `test_mode` | True | テストモード（短時間設定） |
| `study_name` | 自動生成 | Optunaスタディ名 |

### テストモード vs 本番モード

| 設定 | テストモード | 本番モード |
|------|-------------|------------|
| **総ステップ数** | 1,000 | 100,000 |
| **評価エピソード数** | 10 | 2,000 |
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

### 例1: 2024年1月データでのテスト実行
```bash
python -m kyotei_predictor.tools.optimization.optimize_graduated_reward_generic \
    --data-month 2024-01 \
    --test-mode \
    --n-trials 3 \
    --study-name test_202401
```

### 例2: 2024年1月データでの本番実行
```bash
python -m kyotei_predictor.tools.optimization.optimize_graduated_reward_generic \
    --data-month 2024-01 \
    --n-trials 50 \
    --study-name production_202401
```

### 例3: 複数月の一括実行
```bash
# run_optimization_batch.pyを編集して対象月を設定
python run_optimization_batch.py
```

---

## 結果の確認

### 出力ファイル

| ファイル種別 | 保存場所 | 説明 |
|-------------|----------|------|
| **最適化結果** | `optuna_results/` | JSON形式の詳細結果 |
| **最良モデル** | `optuna_models/graduated_reward_best_YYYYMM/` | 学習済みモデル |
| **評価結果** | `optuna_logs/trial_X/` | 詳細な評価データ |
| **スタディファイル** | `optuna_studies/` | Optunaのデータベース |

### 結果の読み込み

```python
import json

# 最新の結果を読み込み
with open('optuna_results/graduated_reward_optimization_202401_YYYYMMDD_HHMMSS.json', 'r') as f:
    results = json.load(f)

print(f"最良スコア: {results['best_trial']['value']}")
print(f"最良パラメータ: {results['best_trial']['params']}")
print(f"対象月: {results['data_month']}")
```

### 最良モデルの読み込み

```python
from stable_baselines3 import PPO

# 最良モデルを読み込み
model = PPO.load("optuna_models/graduated_reward_best_202401/best_model.zip")
```

---

## トラブルシューティング

### 1. データが見つからない場合

```
エラー: データペアが存在しません
```

**対処法:**
- データディレクトリの存在確認
- ファイル名の形式確認（race_data_YYYY-MM-DD_VENUE_RX.json）
- データディレクトリのパス確認

### 2. メモリ不足の場合

**対処法:**
- テストモードで実行
- データ量を制限（KyoteiEnvManagerの修正）
- バッチサイズを小さくする

### 3. 学習時間が長すぎる場合

**対処法:**
- テストモードを使用
- 試行回数を減らす
- 学習ステップ数を調整

### 4. 的中率が0%の場合

**想定される原因:**
- テストモードでの短時間学習
- 競艇予測の難しさ（理論的中率約0.83%）
- 学習が不十分

**対処法:**
- 本番モードで長時間学習
- より多くの試行回数
- ハイパーパラメータの調整

---

## ベストプラクティス

### 1. 実行順序
1. **テストモード**で動作確認
2. **小規模な試行**でパラメータ調整
3. **本番モード**で本格実行

### 2. データ管理
- 月別データの整理
- ファイル名の統一
- バックアップの作成

### 3. 結果管理
- 定期的な結果の確認
- 最良モデルの保存
- ログファイルの整理

### 4. パフォーマンス監視
- メモリ使用量の監視
- 実行時間の記録
- エラーログの確認

---

## 関連ドキュメント

- [GENERIC_OPTIMIZATION_GUIDE.md](GENERIC_OPTIMIZATION_GUIDE.md) - 汎用的な最適化ガイド
- [BATCH_EXECUTION_GUIDE.md](BATCH_EXECUTION_GUIDE.md) - バッチ実行ガイド
- [CURRENT_STATUS.md](CURRENT_STATUS.md) - 現在の状況
- [EXECUTION_EXAMPLES.md](EXECUTION_EXAMPLES.md) - 実行例