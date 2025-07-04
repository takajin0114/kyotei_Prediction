# data ディレクトリ README

**最終更新日: 2025-07-03**

---

## 本READMEの役割
- データディレクトリの構成・運用方針・命名規則を記載
- データフロー・バックアップ・一時ファイル運用・設計書へのリンクを明記
- ルートREADMEやNEXT_STEPS.mdへのリンクも記載

## 関連ドキュメント
- [../../README.md](../../README.md)（全体概要・セットアップ・タスク入口）
- [../../NEXT_STEPS.md](../../NEXT_STEPS.md)（今後のタスク・優先度・進捗管理）
- [../../integration_design.md](../../integration_design.md)（統合設計・アーキテクチャ）
- [../../site_analysis.md](../../site_analysis.md)（データ取得元サイト分析）

---

# data ディレクトリ構成

競艇データ管理用ディレクトリです。生データ・中間データ・成果物・一時ファイル等を用途別に整理します。

## 📁 サブディレクトリ

- `raw/` : 取得したままの生データ（JSON, CSV等）
- `processed/` : 前処理・特徴量エンジニアリング済みデータ
- `backup/` : バックアップ用データ（定期保存・世代管理）
- `temp/` : 一時ファイル・作業用データ

## 🚀 データフロー

1. **raw/** にデータ取得スクリプトで生データ保存
2. **processed/** で前処理・特徴量生成・AI学習用データ作成
3. **backup/** で定期的に重要データをバックアップ
4. **temp/** で一時的な中間生成物や作業ファイルを管理

## 🔧 命名規則

- `race_data_YYYY-MM-DD_VENUE_RN.json` : レースデータ
- `odds_data_YYYY-MM-DD_VENUE_RN.json` : オッズデータ
- `complete_race_data_YYYYMMDD_VENUE_RN.json` : 完全データ
- `entry_only_YYYYMMDD_VENUE_RN.json` : エントリーのみ

## 📦 バックアップ運用

- 重要な生データ・成果物は **backup/** に世代管理で保存
- 定期的に外部ストレージ等へ退避推奨

## 🧹 一時ファイル運用

- temp/配下は随時削除OK（作業終了後クリーンアップ）
- 大容量ファイル・一時的な変換データ等を格納

## 📝 備考

- データ容量増大に注意し、不要データは適宜整理
- processed/配下はAI学習・分析用の主データ
- backup/は事故・障害時の復旧用
- temp/は作業効率化・高速化用 