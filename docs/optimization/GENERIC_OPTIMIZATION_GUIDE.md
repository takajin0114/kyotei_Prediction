# 汎用的な段階的報酬最適化ガイド

## 概要

このガイドでは、月別データに対応した汎用的な段階的報酬最適化の使用方法を説明します。

## ファイル構成

### 1. 汎用的な最適化モジュール
- `kyotei_predictor/tools/optimization/optimize_graduated_reward_generic.py`
  - 月別データに対応した汎用的な最適化モジュール
  - コマンドライン引数で月を指定可能

### 2. 実行スクリプト
- `run_optimization_generic.py`
  - インタラクティブな実行スクリプト
  - 月とモードを選択して実行

- `run_optimization_batch.py`
  - 複数月の一括実行スクリプト
  - 設定した月を順次実行

## 使用方法

### 方法1: バッチファイル実行（推奨）

#### PowerShellでの実行
```powershell
# 本番実行（自動版）
.\run_optimization_production_with_cleanup_auto.bat 2024-02

# 本番実行（手動確認版）
.\run_optimization_production_with_cleanup.bat 2024-02

# シンプル版（30試行）
.\run_optimization_production_simple.bat 2024-02
```

#### コマンドプロンプトでの実行
```cmd
# 本番実行（自動版）
run_optimization_production_with_cleanup_auto.bat 2024-02

# 本番実行（手動確認版）
run_optimization_production_with_cleanup.bat 2024-02
```

### 方法2: インタラクティブ実行

```bash
python run_optimization_generic.py
```

実行すると以下の選択肢が表示されます：

1. **月の選択**
   - 1. 2024-01
   - 2. 2024-02（今後追加）
   - 3. 2024-03（今後追加）

2. **モードの選択**
   - 1. テストモード（短時間、3試行）
   - 2. 本番モード（長時間、50試行）

### 方法3: 一括実行

```bash
python run_optimization_batch.py
```

設定された月を順次実行します。

### 方法4: コマンドライン直接実行

```bash
# テストモード（1月データ）
python -m kyotei_predictor.tools.optimization.optimize_graduated_reward_generic --data-month 2024-01 --test-mode --n-trials 3

# 本番モード（1月データ）
python -m kyotei_predictor.tools.optimization.optimize_graduated_reward_generic --data-month 2024-01 --n-trials 50

# 本番モード（2月データ）
python -m kyotei_predictor.tools.optimization.optimize_graduated_reward_generic --data-month 2024-02 --n-trials 50
```

## 新しい月のデータを追加する方法

### 1. データディレクトリの準備

```
kyotei_predictor/data/raw/2024-02/
├── race_data_2024-02-01_BIWAKO_R1.json
├── odds_data_2024-02-01_BIWAKO_R1.json
├── race_data_2024-02-01_BIWAKO_R2.json
├── odds_data_2024-02-01_BIWAKO_R2.json
└── ...
```

### 2. 実行スクリプトの更新

`run_optimization_generic.py`の`months`リストに追加：

```python
months = [
    "2024-01",  # 1月
    "2024-02",  # 2月（新規追加）
    "2024-03",  # 3月（今後追加）
]
```

`run_optimization_batch.py`の`target_months`リストに追加：

```python
target_months = [
    "2024-01",  # 1月
    "2024-02",  # 2月（新規追加）
    # "2024-03",  # 3月（コメントアウトで無効化）
]
```

## 出力ファイル

### 1. 最適化結果
- `optuna_results/graduated_reward_optimization_202401_YYYYMMDD_HHMMSS.json`
  - 最適化の詳細結果
  - ハイパーパラメータとスコア

### 2. 最良モデル
- `optuna_models/graduated_reward_best_202401/best_model.zip`
  - 最良の学習済みモデル

### 3. 評価結果
- `optuna_logs/trial_X/evaluations.npz`
  - 詳細な評価結果

## トラブルシューティング

### 1. PowerShell実行ポリシーエラー

```
このシステムではスクリプトの実行が無効になっているため...
```

**対処法:**
```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
.\run_optimization_production_with_cleanup_auto.bat 2024-02
```

### 2. バッチファイルが見つからない

```
用語 'run_optimization_production_with_cleanup_auto.bat' は認識されません
```

**対処法:**
```powershell
.\run_optimization_production_with_cleanup_auto.bat 2024-02
```

### 3. データが見つからない場合

```
エラー: データペアが存在しません
```

**対処法:**
- データディレクトリの存在確認
- ファイル名の形式確認（race_data_YYYY-MM-DD_VENUE_RX.json）

### 4. メモリ不足の場合

**対処法:**
- テストモードで実行
- データ量を制限（KyoteiEnvManagerの修正）

### 5. 学習時間が長すぎる場合

**対処法:**
- テストモードを使用
- 試行回数を減らす
- 学習ステップ数を調整

## 今後の拡張

### 1. 新しい月の追加
- データディレクトリの準備
- 実行スクリプトの更新

### 2. ハイパーパラメータの調整
- `objective`関数内のパラメータ範囲を調整

### 3. 評価指標の追加
- `evaluate_model`関数に新しい指標を追加

## 注意事項

1. **データ形式**: 必ず`race_data_`と`odds_data_`のペアで配置
2. **ファイル名**: 日付と会場名を含む形式に統一
3. **メモリ使用量**: 大量データの場合はテストモードから開始
4. **実行時間**: 本番モードは数時間かかる場合があります
5. **PowerShell実行**: `.\\`プレフィックスを使用してバッチファイルを実行 