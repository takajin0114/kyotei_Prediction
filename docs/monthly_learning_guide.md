# 1月ごとの学習実行ガイド

## 概要

このガイドでは、1月ごとに学習を実行する方法を説明します。年月フィルタ機能を使用することで、特定の月のデータのみを使用して学習を行うことができます。

## 機能

- **年月フィルタリング**: 指定した年月のデータのみを使用
- **コマンドライン引数対応**: `--year-month`オプションで年月を指定
- **バッチファイル対応**: `run_learning_pipeline.bat`で年月指定可能

## 使用方法

### 1. バッチファイルでの実行

#### 基本的な使用方法
```bash
# 2024年1月のデータで学習
.\run_learning_pipeline.bat --year-month 2024-01

# 2024年2月のデータで学習
.\run_learning_pipeline.bat --year-month 2024-02

# 2025年1月のデータで学習
.\run_learning_pipeline.bat --year-month 2025-01
```

#### オプション付きの実行
```bash
# テストモードで2024年3月のデータを使用
.\run_learning_pipeline.bat --test --year-month 2024-03

# 最小限モードで2024年4月のデータを使用
.\run_learning_pipeline.bat --minimal --year-month 2024-04

# Phase 2のみ実行、2024年5月のデータを使用
.\run_learning_pipeline.bat --phase 2 --year-month 2024-05
```

### 2. Pythonスクリプトでの直接実行

#### 最適化スクリプト
```bash
# 2024年1月のデータで最適化
python kyotei_predictor/tools/optimization/optimize_graduated_reward.py --year-month 2024-01 --minimal

# 2024年2月のデータで最適化（本番モード）
python kyotei_predictor/tools/optimization/optimize_graduated_reward.py --year-month 2024-02 --n-trials 50
```

## 利用可能なデータ期間

現在利用可能なデータ期間：
- **2024年1月** ～ **2025年7月**

### データディレクトリ構造
```
kyotei_predictor/data/raw/
├── 2024-01/
├── 2024-02/
├── ...
├── 2025-06/
└── 2025-07/
```

## 実行例

### 例1: 2024年1月のデータで学習
```bash
.\run_learning_pipeline.bat --year-month 2024-01 --minimal
```

実行結果：
```
実行設定:
- モード: minimal
- Phase: all
- データディレクトリ: kyotei_predictor\data\raw
- 年月フィルタ: 2024-01
- 学習ステップ数: 5000
- 評価エピソード数: 50
- 試行回数: 1
- クリーンアップ: true
```

### 例2: 2024年2月のデータで本格学習
```bash
.\run_learning_pipeline.bat --year-month 2024-02
```

実行結果：
```
実行設定:
- モード: production
- Phase: all
- データディレクトリ: kyotei_predictor\data\raw
- 年月フィルタ: 2024-02
- 学習ステップ数: 200000
- 評価エピソード数: 5000
- 試行回数: 50
- クリーンアップ: true
```

## 注意事項

1. **データの存在確認**: 指定した年月のデータが存在しない場合、エラーが発生します
2. **ファイル名形式**: データファイルは `race_data_YYYY-MM-DD_VENUE_RN.json` 形式である必要があります
3. **年月フォーマット**: `YYYY-MM` 形式で指定してください（例: `2024-01`）

## トラブルシューティング

### エラー: "No valid race-odds pairs found"
- 指定した年月のデータが存在しない可能性があります
- データディレクトリの構造を確認してください

### エラー: "Invalid year-month format"
- 年月の指定形式が正しくありません
- `YYYY-MM` 形式で指定してください（例: `2024-01`）

## 関連ファイル

- `kyotei_predictor/pipelines/kyotei_env.py`: 環境クラス（年月フィルタ機能）
- `kyotei_predictor/tools/optimization/optimize_graduated_reward.py`: 最適化スクリプト
- `run_learning_pipeline.bat`: 学習パイプライン実行スクリプト
- `tests/improvement_tests/simple_learning_verification.py`: 学習検証テスト 