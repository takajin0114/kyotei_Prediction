# 5年分データを数回に分けて取得する手順

## 概要

5年分（2021-01 ～ 2026-02）のレースデータを、複数回の実行に分けて取得するための仕組みです。

- **計画**は `scripts/fetch_5year_plan.json` で定義（対象月一覧）
- **取得済みかどうか**は `kyotei_predictor/data/raw/YYYY-MM/` に `race_data_*.json` が1件以上あるかで判定
- **上書きは行わない**ため、同じ期間を再実行しても欠けている分だけ取得され、重複しません
- 欠損レースは既存の `retry_missing_races` で補完できます

## 用意されているもの

| 対象 | 説明 |
|------|------|
| `scripts/fetch_5year_plan.json` | 取得対象月の一覧（2021-01 ～ 2026-02） |
| `kyotei_predictor/tools/batch/fetch_5year_chunked.py` | 進捗確認・チャンク取得の本体 |
| `scripts/run_fetch_5year_chunked.sh` | 上記のランチャー（Linux/macOS） |

## 基本的な流れ

1. **進捗確認**  
   どの月が取得済みか・次に取る月を確認する。

2. **「次の N ヶ月」または「指定期間」で取得**  
   未取得の先頭から N ヶ月分、または日付範囲を指定して取得する。既存ファイルはスキップされる。

3. **必要に応じて欠損補完**  
   取得後に `retry_missing_races` で欠損レースを補完する。

## コマンド例

### 進捗確認（どの月が取得済みか・次に取る範囲）

```bash
# シェルから
./scripts/run_fetch_5year_chunked.sh check

# または Python から
python -m kyotei_predictor.tools.batch.fetch_5year_chunked --check
```

- 取得済み月数・未取得月数が表示されます
- 未取得の先頭月と「次に取得する場合の例」（`--next 1` / `--next 3` / `--range`）が表示されます

### 全計画月の一覧と取得状況

```bash
./scripts/run_fetch_5year_chunked.sh list
# または
python -m kyotei_predictor.tools.batch.fetch_5year_chunked --list
```

### 未取得の「次の 1 ヶ月分」を取得

```bash
./scripts/run_fetch_5year_chunked.sh next 1
# または
python -m kyotei_predictor.tools.batch.fetch_5year_chunked --next 1
```

### 未取得の「次の 3 ヶ月分」を取得

```bash
./scripts/run_fetch_5year_chunked.sh next 3
python -m kyotei_predictor.tools.batch.fetch_5year_chunked --next 3
```

### 指定期間のみ取得（既存はスキップ）

```bash
./scripts/run_fetch_5year_chunked.sh range 2023-01-01 2023-12-31
# または
python -m kyotei_predictor.tools.batch.fetch_5year_chunked --range 2023-01-01 2023-12-31
```

### オプション（レート制限・並列数・進捗表示）

- 環境変数: `RATE_LIMIT`（デフォルト 1）、`RACE_WORKERS`（デフォルト 6）
- Python 直接実行時: `--rate-limit 1 --race-workers 6`、`--no-quiet` で進捗を通常表示

```bash
RATE_LIMIT=0.5 ./scripts/run_fetch_5year_chunked.sh next 1
python -m kyotei_predictor.tools.batch.fetch_5year_chunked --next 2 --rate-limit 0.5 --no-quiet
```

## 計画ファイルの編集

`scripts/fetch_5year_plan.json` の `months` を編集すると、対象月を変更できます。  
期間を延ばす場合は `start_date` / `end_date` と `months` の両方を整合させてください。

## 欠損レースの補完

取得後、特定期間で欠けているレースがある場合は、既存の retry スクリプトで補完できます。

```bash
python -m kyotei_predictor.tools.batch.retry_missing_races \
  --start-date 2023-01-01 --end-date 2023-12-31 \
  --output-data-dir kyotei_predictor/data/raw
```

詳細は [batch_usage.md](batch_usage.md) および `retry_missing_races.py` のヘルプを参照してください。
