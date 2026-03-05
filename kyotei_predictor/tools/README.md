# tools ディレクトリ README

> **注記**: 詳細な設計・運用ルール・全体像は[../../docs/README.md](../../docs/README.md)・[../pipelines/README.md](../pipelines/README.md)・各設計書を参照してください。

## 参照フロー・索引
- プロジェクト構成・ツール配置: [../../docs/PROJECT_LAYOUT.md](../../docs/PROJECT_LAYOUT.md)
- データ取得・前処理・運用: [../../docs/operations/data_acquisition.md](../../docs/operations/data_acquisition.md)
- パイプライン全体: [../pipelines/README.md](../pipelines/README.md)

## 概要
- データ取得・バッチ処理・分析・可視化・共通処理などのツール群を集約
- サブディレクトリごとに用途別に整理
- 詳細な設計・運用ルールはdocs/配下に集約

## 主なサブディレクトリ・ツール
- `batch/` : データ取得・再取得・一括運用バッチ（batch_fetch_all_venues, fetch_5year_chunked, retry_missing_races）
- `analysis/` : 分析・可視化・統計ツール
- `fetch/` : データ取得用API・スクレイパ
- `optimization/` : **本流** Optuna 最適化（optimize_graduated_reward、file/db 対応）
- `ai/` : AI学習・評価（optuna_optimizer）。tools/optuna_optimizer.py は ai の再エクスポート
- `common/` : 共通処理・ユーティリティ（venue_mapping は utils.venue_mapping のラッパー）
- `viz/` : 可視化・グラフ生成

## 主要バッチ・ツールの使い方
- 各サブディレクトリのREADMEやdocstringを参照
- 例: データ取得一括バッチ
```bash
python -m kyotei_predictor.tools.batch.run_data_maintenance --start-date 2024-01-01 --end-date 2024-01-31 --stadiums ALL
```
- 例: 欠損データ再取得
```bash
python -m kyotei_predictor.tools.batch.retry_missing_races --input-dir kyotei_predictor/data/raw
```
- 例: データ取得状況サマリ
```bash
python -m kyotei_predictor.tools.batch.list_fetched_data_summary --input-dir kyotei_predictor/data/raw
```

## 運用方針
- 用途別にサブディレクトリで整理
- バッチ・分析・共通処理はtools/配下に集約
- 詳細な運用ルール・設計はdocs/配下に記載

---

# 以下、従来の内容（詳細な使い方・サンプル等）は現状維持 