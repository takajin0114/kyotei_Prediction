# 📚 競艇予測システム ドキュメント

## 📋 概要

このディレクトリには、競艇予測システムの詳細なドキュメントが含まれています。

## 🗂️ プロジェクト概要

- [README.md](../README.md) - プロジェクトの概要とクイックスタート
- **[PROJECT_LAYOUT.md](PROJECT_LAYOUT.md)** - **ディレクトリ構成・エントリポイント・新規コードの置き場所**
- **[LEARNING_AND_PREDICTION_STATUS.md](LEARNING_AND_PREDICTION_STATUS.md)** - **学習・予想を動かすための現状と手順**
- **[LEARNING_INPUT_OUTPUT.md](LEARNING_INPUT_OUTPUT.md)** - **学習のインプットとアウトプットの整理**
- **[ODDS_AND_STATE_DESIGN.md](ODDS_AND_STATE_DESIGN.md)** - **オッズの扱い（回収率専用）と状態定義の共通化**
- [LEARNING_PREDICTION_CYCLE_IMPROVEMENTS.md](LEARNING_PREDICTION_CYCLE_IMPROVEMENTS.md) - 学習→予測サイクル実施結果と改善点一覧
- **[guides/processing_flow.md](guides/processing_flow.md)** - **処理の流れ（Cursorで取得・保管 → Colabで学習 → Cursorで取得・予測）**
- [guides/batch_usage.md](guides/batch_usage.md) - バッチの使い方（scripts/）
- [guides/junction_setup.md](guides/junction_setup.md) - Windows Junction による日本語パス回避
- [guides/cursor_web_drive_upload.md](guides/cursor_web_drive_upload.md) - Cursor Web で取得したデータを Drive に保存する
- [guides/google_drive_colab_workflow.md](guides/google_drive_colab_workflow.md) - Google Drive保存とColab学習の手順
- [guides/optimization_script.md](guides/optimization_script.md) - 最適化スクリプト
- [guides/powershell.md](guides/powershell.md) - PowerShell メモ

## 🚀 最適化・学習

- [optimization/README.md](optimization/README.md) - 最適化の概要
- [optimization/FAST_MODE_IMPLEMENTATION_SUMMARY.md](optimization/FAST_MODE_IMPLEMENTATION_SUMMARY.md) - 3段階モード実装詳細
- [optimization/OPTIMIZATION_GUIDE.md](optimization/OPTIMIZATION_GUIDE.md) - 最適化の詳細ガイド
- [optimization/EXECUTION_EXAMPLES.md](optimization/EXECUTION_EXAMPLES.md) - 実行例とサンプル

## 📊 システム状況・進捗

- [CURRENT_STATUS_SUMMARY.md](CURRENT_STATUS_SUMMARY.md) - 現在の状況サマリー
- [REPO_STATUS_20250212.md](REPO_STATUS_20250212.md) - リポジトリ現状サマリー（2025-02-12）
- **[CURRENT_REPO_STATUS_20250212.md](CURRENT_REPO_STATUS_20250212.md)** - **現状整理（構成・機能・Git・実行入口・注意点）**
- [DEEP_CLEANUP_REPORT_20250212.md](DEEP_CLEANUP_REPORT_20250212.md) - ソース深堀り整理レポート（2025-02-12）
- [REFACTORING_REPORT_20250212.md](REFACTORING_REPORT_20250212.md) - リファクタリング・整理レポート（2025-02-12）
- [improvement_implementation_summary.md](improvement_implementation_summary.md) - 改善策の実装状況
- [test_results_summary.md](test_results_summary.md) - テスト結果の詳細
- [monthly_learning_guide.md](monthly_learning_guide.md) - 月次学習ガイド

- [RACE_DATA_ACQUISITION_AND_SOURCES.md](RACE_DATA_ACQUISITION_AND_SOURCES.md) - レースデータ取得処理・参照サイト・取得/必要データの洗い出し
- **[SITE_DATA_AND_FETCH_STATUS.md](SITE_DATA_AND_FETCH_STATUS.md)** - **サイトで取得できるデータ一覧と現状の取得状況（レース前予測前提）**

## 🔧 設定・運用

- [config_usage_guide.md](config_usage_guide.md) - 設定ファイルの使用方法
- [trifecta_improvement_strategy.md](trifecta_improvement_strategy.md) - 3連単的中率改善戦略
- **[PREDICTION_ACCURACY_IMPROVEMENT_TODO.md](PREDICTION_ACCURACY_IMPROVEMENT_TODO.md)** - **予測精度向上のやること整理**（優先度・フェーズ別）

## 🌐 Web表示・UI

- [web_display/README.md](web_display/README.md) - Web表示システムの概要
- [web_display/requirements.md](web_display/requirements.md) - Web表示の要件
- [web_display/plan.md](web_display/plan.md) - Web表示の実装計画
- [web_display/complete.md](web_display/complete.md) - Web表示の実装完了状況

## 📋 運用・保守

- [operations/README.md](operations/README.md) - 運用の概要
- [operations/data_acquisition.md](operations/data_acquisition.md) - データ取得の運用
- [operations/scheduled_maintenance.md](operations/scheduled_maintenance.md) - 定期メンテナンス

## 📋 要件・仕様（要件レベルはここから）

- **[REQUIREMENTS_OVERVIEW.md](REQUIREMENTS_OVERVIEW.md)** - **要件全体の整理**（目的・業務/機能/非機能・ドキュメント対応表）
- [requirements/README.md](requirements/README.md) - 要件ディレクトリの索引
- [requirements/system_status_page.md](requirements/system_status_page.md) - システム状況ページの要件
- [requirements/ux_improvement.md](requirements/ux_improvement.md) - UX改善の要件
- [web_display/requirements.md](web_display/requirements.md) - Web表示機能の要件定義書

---

## 🆕 最近の更新

### **2025年2月**
- **PROJECT_LAYOUT.md** - プロジェクト構成・エントリポイント・新規コードの置き場所
- **REFACTORING_REPORT_20250212.md** - リファクタリング（config パッケージ化、optuna_optimizer 整理、ドキュメント追加）
- **REQUIREMENTS_OVERVIEW.md** - 要件レベルで全体を整理（目的・業務/機能/非機能・ドキュメント対応表）
- **REPO_STATUS_20250212.md** - リポジトリ構成・現状サマリー
- **DEEP_CLEANUP_REPORT_20250212.md** - ソース深堀り整理（インポート統一・会場マッピング一元化・不足モジュール追加等）
- **docs/README.md** - 要件・進捗セクションの見直し、PROJECT_LAYOUT・REFACTORING へのリンク追加

### **2025年2月（構成整理）**
- **scripts/** - バッチを一本化。**docs/guides/** - 実行ガイドを集約
- **logs/** - ルートにログ用ディレクトリ。analysis_results 削除、冗長ドキュメント整理

### **2025年1月**
- **3段階モード**: 高速・中速・通常モードの完全実装
- 重複ファイル削除、requirements.txt 統合、ドキュメント整備

---

## 📖 ドキュメントの使用方法

### **初回利用者**
1. [README.md](../README.md) - プロジェクトの概要を確認
2. **[REQUIREMENTS_OVERVIEW.md](REQUIREMENTS_OVERVIEW.md)** - 要件レベルで何を実現するか・どの doc に書いてあるかを把握
3. [guides/batch_usage.md](guides/batch_usage.md) - バッチ（scripts/）の使い方
4. [PROJECT_LAYOUT.md](PROJECT_LAYOUT.md) - ディレクトリ構成を理解

### **最適化実行者**
1. [optimization/README.md](optimization/README.md) - 最適化の概要を確認
2. [optimization/FAST_MODE_IMPLEMENTATION_SUMMARY.md](optimization/FAST_MODE_IMPLEMENTATION_SUMMARY.md) - 3段階モードの詳細を理解
3. [optimization/EXECUTION_EXAMPLES.md](optimization/EXECUTION_EXAMPLES.md) - 実行例を参考に実行

### **システム管理者**
1. [CURRENT_STATUS_SUMMARY.md](CURRENT_STATUS_SUMMARY.md) - 現在の状況を把握
2. [operations/README.md](operations/README.md) - 運用方法を確認
3. [config_usage_guide.md](config_usage_guide.md) - 設定方法を学習

---

**最終更新**: 2025-02-12  
**バージョン**: 3.1  
**主要改善**: 要件レベル整理（REQUIREMENTS_OVERVIEW）、docs 索引・リンク整備、2025-02 整理レポート追加