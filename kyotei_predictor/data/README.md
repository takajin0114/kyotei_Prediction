# data ディレクトリ README

> **注記**: 詳細な設計・運用ルールはdocs/配下に集約しています。全体像・詳細は[../../README.md](../../README.md)・[../../docs/README.md](../../docs/README.md)・各設計書を参照してください。

## 概要
- データディレクトリの構成・運用方針・命名規則の概要を記載
- 詳細な運用ルール・欠損管理・品質チェックは[../../docs/operations/data_acquisition.md](../../docs/operations/data_acquisition.md)等を参照

## 主なディレクトリ
- `raw/` : 取得したままの生データ
- `processed/` : 前処理・特徴量エンジニアリング済みデータ
- `results/` : 予測・分析・評価結果
- `logs/` : ログファイル
- `backup/` : バックアップ用データ
- `temp/` : 一時ファイル
- `sample/` : サンプルデータ

## 参照先
- [../../README.md](../../README.md) - プロジェクト全体概要
- [../../docs/README.md](../../docs/README.md) - ドキュメント全体ガイド
- [../../docs/operations/data_acquisition.md](../../docs/operations/data_acquisition.md) - データ取得運用・手順
- [../../docs/PROJECT_LAYOUT.md](../../docs/PROJECT_LAYOUT.md) - プロジェクト構成

---

# 以下、従来の内容（構成・命名規則等）は現状維持 