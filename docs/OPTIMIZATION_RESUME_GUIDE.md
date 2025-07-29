# 最適化継続機能ガイド

## 概要

このガイドでは、中断された最適化を継続実行する方法について説明します。

## 機能

### 既存スタディ継続機能

`--resume-existing` オプションを使用することで、中断された最適化を継続実行できます。

## 使用方法

### 基本的な使用方法

```bash
# 既存スタディを継続して最適化を実行
python -m kyotei_predictor.tools.optimization.optimize_graduated_reward \
  --data-dir kyotei_predictor/data/raw/2024-03 \
  --study-name opt_202403 \
  --n-trials 50 \
  --resume-existing
```

### パラメータ説明

- `--resume-existing`: 既存スタディを継続するフラグ
- `--study-name`: 継続するスタディ名（例: `opt_202403`）
- `--n-trials`: 新たに実行する試行数
- `--data-dir`: 使用するデータディレクトリ

## 動作仕様

### 既存スタディファイルの検索

1. `optuna_studies/` ディレクトリ内の該当スタディ名のファイルを検索
2. 最新の `.db` ファイルを自動選択
3. 既存の試行数を表示

### 継続実行

- 既存の試行結果を保持
- 新たに指定された試行数を追加実行
- 合計試行数 = 既存試行数 + 新規試行数

## 使用例

### 3月データの最適化継続

```bash
# 3月データで50試行の最適化を継続実行
python -m kyotei_predictor.tools.optimization.optimize_graduated_reward \
  --data-dir kyotei_predictor/data/raw/2024-03 \
  --study-name opt_202403 \
  --n-trials 50 \
  --resume-existing
```

### 新規スタディの作成

```bash
# 新規スタディを作成して最適化を実行
python -m kyotei_predictor.tools.optimization.optimize_graduated_reward \
  --data-dir kyotei_predictor/data/raw/2024-04 \
  --study-name opt_202404 \
  --n-trials 50
```

## 注意事項

- 既存スタディファイルが存在しない場合は新規作成されます
- 既存の試行結果は保持されます
- 同じスタディ名で複数のファイルが存在する場合は最新のファイルが使用されます

## トラブルシューティング

### よくある問題

1. **スタディファイルが見つからない**
   - `optuna_studies/` ディレクトリを確認
   - スタディ名が正しいか確認

2. **権限エラー**
   - ファイルの読み書き権限を確認
   - 管理者権限で実行を試行

3. **データディレクトリエラー**
   - 指定したデータディレクトリが存在するか確認
   - パスが正しいか確認