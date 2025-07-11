# docs ディレクトリ README

**最終更新日**: 2025-07-11  
**バージョン**: 1.5

---

## 📚 ドキュメント全体の使い方・参照ガイド

- 本ディレクトリは、競艇予測システムの設計・運用・API仕様・開発計画など横断的な内容を集約
- ルート[README.md](../README.md)・[../kyotei_predictor/pipelines/README.md](../kyotei_predictor/pipelines/README.md)と連携し、全体像・参照フロー・索引を明記
- 各ディレクトリREADMEは用途・使い方・参照先中心、詳細設計・運用ルールはdocs/配下に集約

---

## 🧭 参照フロー・索引
- [../README.md](../README.md)（全体概要・セットアップ・索引）
- [integration_design.md](integration_design.md)（システム全体設計・運用ルール）
- [data_acquisition.md](data_acquisition.md)（データ取得運用・手順）
- [BATCH_SYSTEM_CURRENT_STATUS.md](BATCH_SYSTEM_CURRENT_STATUS.md)（バッチシステム現状・最新修正）
- [CURRENT_STATUS_SUMMARY.md](CURRENT_STATUS_SUMMARY.md)（現在状況サマリー・最新）
- [../kyotei_predictor/data/README.md](../kyotei_predictor/data/README.md)（データ保存・命名規則）
- [DEVELOPMENT_ROADMAP.md](DEVELOPMENT_ROADMAP.md)（長期計画・課題・進行中タスク）
- [../kyotei_predictor/tools/README.md](../kyotei_predictor/tools/README.md)（ツール運用・バッチ・分析）
- [../kyotei_predictor/pipelines/README.md](../kyotei_predictor/pipelines/README.md)（パイプライン運用・分析）

---

## 📁 ドキュメント構成・索引

### 設計・運用ドキュメント
- [integration_design.md](integration_design.md) - システム統合設計・運用ルール
- [prediction_algorithm_design.md](prediction_algorithm_design.md) - 予測アルゴリズム設計
- [web_app_requirements.md](web_app_requirements.md) - Webアプリ要件定義
- [site_analysis.md](site_analysis.md) - サイト分析・データ取得設計
- [data_acquisition.md](data_acquisition.md) - データ取得運用・手順
- [BATCH_SYSTEM_CURRENT_STATUS.md](BATCH_SYSTEM_CURRENT_STATUS.md) - バッチシステム現状・最新修正
- [CURRENT_STATUS_SUMMARY.md](CURRENT_STATUS_SUMMARY.md) - 現在状況サマリー（最新）
- [TRIFECTA_IMPROVEMENT_PLAN.md](TRIFECTA_IMPROVEMENT_PLAN.md) - 3連単確率計算改善計画・結果
- [EQUIPMENT_ENHANCEMENT_PLAN.md](EQUIPMENT_ENHANCEMENT_PLAN.md) - 機材重視ロジック強化計画・結果
- [GRADUATED_REWARD_IMPLEMENTATION.md](GRADUATED_REWARD_IMPLEMENTATION.md) - 段階的報酬設計・実装
- [EV_THRESHOLD_OPTIMIZATION.md](EV_THRESHOLD_OPTIMIZATION.md) - 期待値閾値最適化
- [LEARNING_DEBUGGING_PLAN.md](LEARNING_DEBUGGING_PLAN.md) - 学習デバッグ計画
- [LEARNING_DEBUGGING_RESULTS.md](LEARNING_DEBUGGING_RESULTS.md) - 学習デバッグ結果
- [WEB_APP_ENHANCEMENT_PLAN.md](WEB_APP_ENHANCEMENT_PLAN.md) - Webアプリ拡張計画
- [DEVELOPMENT_ROADMAP.md](DEVELOPMENT_ROADMAP.md) - 開発ロードマップ・今後の計画
- [NEXT_STEPS.md](NEXT_STEPS.md) - 直近のTODO・優先度・進捗

### その他
- [../API_SPECIFICATION.md](../API_SPECIFICATION.md) - API仕様書
- [../PROJECT_STRUCTURE.md](../PROJECT_STRUCTURE.md) - プロジェクト構造詳細
- [../REFACTORING_PLAN.md](../REFACTORING_PLAN.md) - リファクタリング計画
- [../REFACTORING_COMPLETE_REPORT.md](../REFACTORING_COMPLETE_REPORT.md) - リファクタリング完了報告
- [../PHASE3_COMPLETE_REPORT.md](../PHASE3_COMPLETE_REPORT.md) - フェーズ完了報告

---

## 📝 整理・集約方針
- 設計・運用・API仕様など横断的な内容はdocs/配下に集約
- 各ディレクトリREADMEは用途・使い方・参照先中心に簡潔化
- 進行中タスク・今後の計画はREADMEまたはDEVELOPMENT_ROADMAP.mdに一本化
- 古い/重複するドキュメントは随時統合・削除

---

# 以下、従来の内容（進行中タスク・運用ルール等）は現状維持・必要に応じて最新化 