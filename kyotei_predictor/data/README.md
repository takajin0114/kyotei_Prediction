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

# ディレクトリ構成（現状と今後の方針）

- `raw/` : 取得したままの生データ（JSON, CSV等）
- `processed/` : 前処理・特徴量エンジニアリング済みデータ
- `results/` : 予測・分析・評価などの成果物（新設予定）
- `logs/` : データ取得・処理・学習等のログファイル（新設予定）
- `backup/` : バックアップ用データ（定期保存・世代管理）
- `temp/` : 一時ファイル・作業用データ
- `sample/` : サンプルデータ（今後はraw/またはresults/へ統合・廃止予定）

---

# 運用ルール・命名規則

- データ種別・日付・会場・レース番号等でファイル命名
  - 例: `race_data_YYYY-MM-DD_VENUE_RN.json`, `odds_data_YYYY-MM-DD_VENUE_RN.json`, `complete_race_data_YYYYMMDD_VENUE_RN.json`
- 生データは必ず`raw/`に保存し、前処理後は`processed/`へ
- 予測・分析・評価結果は`results/`へ（今後新設）
- ログファイルは`logs/`へ（今後新設）
- サンプルデータは`sample/`に一時的に置くが、将来的にはraw/resultsへ統合
- 重要なデータは`backup/`で世代管理
- 一時ファイルは`temp/`で作業終了後にクリーンアップ

---

# 今後のTODO
- `results/`・`logs/`ディレクトリの新設と運用開始
- `sample/`の廃止・統合（必要に応じてraw/resultsへ移動）
- 既存ファイルの命名規則統一・整理
- READMEの随時更新 