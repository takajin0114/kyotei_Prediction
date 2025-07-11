# kyotei_Prediction プロジェクト ドキュメント

このディレクトリには、kyotei_Predictionプロジェクトの各種ドキュメントが含まれています。

## 📁 ドキュメント構成

### 🔄 運用・ステータス・TODO
- **[README.md](README.md)** - このファイル（ドキュメント構成の説明）
- **[CURRENT_STATUS_SUMMARY.md](CURRENT_STATUS_SUMMARY.md)** - プロジェクト全体の現在の状況サマリー
- **[NEXT_STEPS.md](NEXT_STEPS.md)** - 次のステップと優先タスク
- **[IMMEDIATE_ACTION_PLAN.md](IMMEDIATE_ACTION_PLAN.md)** - 直近の具体的な行動計画
- **[BATCH_SYSTEM_CURRENT_STATUS.md](BATCH_SYSTEM_CURRENT_STATUS.md)** - バッチシステムの現在の状況と実行状況
- **[SCHEDULED_MAINTENANCE_GUIDE.md](SCHEDULED_MAINTENANCE_GUIDE.md)** - 一括バッチスケジューラ化運用ガイド
- **[PREDICTION_TOOL_ROADMAP.md](PREDICTION_TOOL_ROADMAP.md)** - 予想ツール運用ロードマップ

### 🏗️ 設計・開発
- **[DEVELOPMENT_ROADMAP.md](DEVELOPMENT_ROADMAP.md)** - 開発ロードマップとフェーズ別計画
- **[PHASE2_DETAILED_TASKS.md](PHASE2_DETAILED_TASKS.md)** - フェーズ2の詳細タスク
- **[integration_design.md](integration_design.md)** - システム統合設計
- **[prediction_algorithm_design.md](prediction_algorithm_design.md)** - 予測アルゴリズム設計
- **[web_app_requirements.md](web_app_requirements.md)** - Webアプリケーション要件

### 📊 分析・改善
- **[data_acquisition.md](data_acquisition.md)** - データ取得システムの仕様と運用
- **[site_analysis.md](site_analysis.md)** - サイト分析とデータ構造

## 📋 ドキュメント更新ガイドライン

### 新規ドキュメント作成時
1. **適切なカテゴリに分類**：上記の3つのカテゴリのいずれかに分類
2. **命名規則**：`UPPER_CASE_WITH_UNDERSCORES.md` または `lower_case_with_underscores.md`
3. **README.md更新**：新規ドキュメントを適切なカテゴリに追加

### ドキュメント削除時
1. **README.md更新**：削除されたドキュメントをリストから削除
2. **関連性確認**：他のドキュメントからの参照がないか確認

### 定期的な整理
- **月次レビュー**：古いドキュメントや重複の確認
- **アーカイブ**：完了したプロジェクトや古い計画は適切にアーカイブ
- **最新性維持**：現在の状況を反映したドキュメントの更新

## 🔍 ドキュメント検索

### 運用関連
- 現在の状況確認 → `CURRENT_STATUS_SUMMARY.md`
- 次のタスク確認 → `NEXT_STEPS.md`
- 直近の行動計画 → `IMMEDIATE_ACTION_PLAN.md`
- バッチ実行状況 → `BATCH_SYSTEM_CURRENT_STATUS.md`
- スケジューラ化運用 → `SCHEDULED_MAINTENANCE_GUIDE.md`
- 予想ツール運用 → `PREDICTION_TOOL_ROADMAP.md`

### 開発関連
- 全体計画確認 → `DEVELOPMENT_ROADMAP.md`
- 詳細タスク確認 → `PHASE2_DETAILED_TASKS.md`
- システム設計確認 → `integration_design.md`

### 分析関連
- データ取得仕様 → `data_acquisition.md`
- サイト構造確認 → `site_analysis.md`

## 📝 運用方針（2025-07-11更新）

- **一括バッチ（run_data_maintenance.py）のスケジューラ化を推奨**
  - データ取得・欠損再取得・品質チェックを一括で自動実行
  - 品質チェック単体のスケジューラ化は行わず、バッチ完了後に自動実行される形を推奨
- **予想ツールとしての運用を目指す**
  - 深夜一括実行で前日データ取得・当日予測を自動化
  - **3連単の予測確率を上位20組出力**
  - **購入方法の提案機能を提供**
  - 予測結果をJSON形式で保存・Web表示
- スケジューラ設定例や運用手順は [SCHEDULED_MAINTENANCE_GUIDE.md](SCHEDULED_MAINTENANCE_GUIDE.md) を参照
- 予想ツールの詳細は [PREDICTION_TOOL_ROADMAP.md](PREDICTION_TOOL_ROADMAP.md) を参照
- 直近の具体的な行動計画は [IMMEDIATE_ACTION_PLAN.md](IMMEDIATE_ACTION_PLAN.md) を参照

## 📝 更新履歴

- **2025-07-11**: 直近の具体的な行動計画追加、予想ツール運用ロードマップ追加、スケジューラ化運用ガイド追加
- **2025-01-XX**: ドキュメント整理完了、不要ファイル削除
- **2025-01-XX**: カテゴリ別整理、README.md更新
- **2025-01-XX**: バッチシステム関連ドキュメント追加 