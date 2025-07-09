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

# ディレクトリ構成・運用ルール（2025-07-08時点）

- `raw/` : 取得したままの生データ（race_data_*.json, odds_data_*.json など）
- `processed/` : 前処理・特徴量エンジニアリング済みデータ
- `results/` : 予測・分析・評価結果
- `logs/` : ログファイル
- `backup/` : バックアップ用データ
- `temp/` : 一時ファイル
- `sample/` : サンプルデータ（今後はraw/またはresults/へ統合予定）

## 命名規則
- `race_data_YYYY-MM-DD_VENUE_RN.json` など。種別・日付・会場・レース番号で統一。

## 保存方針
- 生データは必ずraw/、前処理後はprocessed/、成果物はresults/、ログはlogs/へ保存。
- サンプルデータは一時的にsample/に置くが、将来的にはraw/resultsへ統合。
- 重要なデータはbackup/で世代管理。
- 一時ファイルはtemp/で作業終了後にクリーンアップ。

## 今後のTODO
- results/やlogs/ディレクトリの新設・運用開始
- sample/の廃止・統合（必要に応じてraw/resultsへ移動）
- 既存ファイルの命名規則統一・整理
- READMEの随時更新 