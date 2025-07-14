# tools/batch ディレクトリ README

> **注記**: 詳細な設計・運用ルール・全体像は[../../../docs/README.md](../../../docs/README.md)・[../../README.md](../../README.md)・[../../pipelines/README.md](../../pipelines/README.md)を参照

## 概要
- データ取得・再取得・一括運用・学習バッチなどを集約
- 各スクリプトの詳細はdocstring・親README・docs/配下を参照

## 主なバッチスクリプト
- `run_data_maintenance.py` : データ取得・欠損集計・再取得・品質チェック一括バッチ
- `batch_fetch_all_venues.py` : 全会場データ取得バッチ
- `retry_missing_races.py` : 欠損データ再取得
- `list_fetched_data_summary.py` : 取得状況サマリ
- `fetch_missing_months.py` : 月単位の欠損データ取得
- `train_with_graduated_reward.py` : 段階的報酬学習バッチ
- `train_extended_graduated_reward.py` : 拡張報酬学習バッチ

## 使い方・コマンド例
- 一括データ取得・品質管理
```bash
python -m kyotei_predictor.tools.batch.run_data_maintenance --start-date 2024-01-01 --end-date 2024-01-31 --stadiums ALL
```
- 欠損データ再取得
```bash
python -m kyotei_predictor.tools.batch.retry_missing_races --input-dir kyotei_predictor/data/raw
```
- 取得状況サマリ
```bash
python -m kyotei_predictor.tools.batch.list_fetched_data_summary --input-dir kyotei_predictor/data/raw
```

## 参照先
- [../../README.md](../../README.md) - ツール全体像
- [../../../docs/data_acquisition.md](../../../docs/data_acquisition.md) - データ取得運用・手順
- [../../../docs/integration_design.md](../../../docs/integration_design.md) - システム統合設計

---

# 以下、従来の内容（詳細な使い方・サンプル等）は現状維持 