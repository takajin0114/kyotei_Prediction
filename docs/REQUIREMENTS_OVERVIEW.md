# 要件レベル整理（全体概要）

**最終更新**: 2025-02-12  
**目的**: プロジェクトの要件を「目的・業務・機能・非機能」で整理し、各ドキュメントへの案内を一元化する。

---

## 1. プロジェクト目的・スコープ

| 項目 | 内容 |
|------|------|
| **システム名** | 競艇予測システム（Kyotei Prediction） |
| **位置づけ** | 予想ツールとしての運用を目指す |
| **主な価値** | 機械学習（PPO＋Optuna）による3連単予測と購入方法提案を、自動化されたデータ取得・予測フローで提供する |

### 主要目標（CURRENT_STATUS_SUMMARY より）

- 深夜一括実行で前日データ取得・当日予測を自動化
- 全会場のレース予測を自動実行
- **3連単の予測確率を上位20組出力**
- **購入方法の提案機能を提供**（流し・ボックス・単勝買い等）
- 予測結果を JSON 形式で保存・Web 表示
- 運用負荷を最小化した完全自動化

### 対象ユーザー（現状）

- **プライマリ**: 競艇予測システムの利用者（現状は自分）
- **セカンダリ**: システム管理者・開発者（現状は自分）

---

## 2. 要件の階層と参照先

### 2.1 業務要件（何を実現するか）

| ID | 業務要件 | 状態 | 詳細ドキュメント |
|----|----------|------|------------------|
| B-001 | レース前データの取得・品質管理 | ✅ 完了 | [operations/data_acquisition.md](operations/data_acquisition.md) |
| B-002 | 3連単上位20組の予測確率出力 | ✅ 完了 | [CURRENT_STATUS_SUMMARY.md](CURRENT_STATUS_SUMMARY.md) |
| B-003 | 購入方法の提案（流し・ボックス等） | ✅ 完了 | [CURRENT_STATUS_SUMMARY.md](CURRENT_STATUS_SUMMARY.md) |
| B-004 | 予測結果の保存（JSON）・Web表示 | 🔄 一部完了 | [web_display/requirements.md](web_display/requirements.md) |
| B-005 | 深夜一括実行・運用監視 | 📋 計画中 | [operations/scheduled_maintenance.md](operations/scheduled_maintenance.md) |
| B-006 | 的中率向上・モデル改善 | 🔄 継続 | [trifecta_improvement_strategy.md](trifecta_improvement_strategy.md), [improvement_implementation_summary.md](improvement_implementation_summary.md) |

### 2.2 機能要件（領域別）

#### 予測・モデル

| ID | 機能要件 | 状態 | 備考 |
|----|----------|------|------|
| F-P01 | PPO による強化学習モデル | ✅ | kyotei_env, prediction_engine |
| F-P02 | Optuna ハイパーパラメータ最適化 | ✅ | 3段階モード（高速・中速・通常） |
| F-P03 | 3連単確率計算・上位20組 | ✅ | trifecta_probability, prediction_tool |
| F-P04 | 購入方法提案（8種類） | ✅ | prediction_tool |
| F-P05 | 会場・日付フィルタリング | ✅ | prediction_tool |

#### データ取得・品質

| ID | 機能要件 | 状態 | 備考 |
|----|----------|------|------|
| F-D01 | 全会場・日付のデータ取得バッチ | ✅ | batch_fetch_all_venues |
| F-D02 | 欠損再取得・レース中止処理 | ✅ | retry_missing_races 等 |
| F-D03 | データ品質チェック・レポート | ✅ | data_quality_checker |
| F-D04 | 定期メンテナンス・スケジュール | 📋 | scheduled_data_maintenance |

#### Web表示

| ID | 機能要件 | 状態 | 詳細 |
|----|----------|------|------|
| F-W01 | 予測結果一覧・集計サマリー | ✅ | [web_display/requirements.md](web_display/requirements.md) §2.1 |
| F-W02 | 会場・リスクフィルター | ✅ | 同上 |
| F-W03 | 3連単上位20組・購入提案表示 | ✅ | [web_display/complete.md](web_display/complete.md) |
| F-W04 | オッズ取得・比較表示 | ✅ | 同上 |
| F-W05 | システム状況ページ | 📋 要件済・実装一部 | [requirements/system_status_page.md](requirements/system_status_page.md) |
| F-W06 | 検索・ソート・エクスポート・グラフ等 | 📋 計画 | [requirements/ux_improvement.md](requirements/ux_improvement.md) |

#### 運用・保守

| ID | 機能要件 | 状態 | 備考 |
|----|----------|------|------|
| F-O01 | 最適化バッチ（設定ファイル駆動） | ✅ | optimization_config.ini, .bat |
| F-O02 | ログ・エラーログ出力 | ✅ | 各ツール |
| F-O03 | 深夜自動実行・アラート | 📋 | operations 参照 |

### 2.3 非機能要件

| 分類 | 要件 | 参照 |
|------|------|------|
| **パフォーマンス** | ページ読み込み3秒以内、予測実行後リアルタイム反映 | [web_display/requirements.md](web_display/requirements.md) §1.4.1 |
| **可用性** | 稼働率99%以上、保守時間外24時間稼働 | 同上 §1.4.2 |
| **セキュリティ** | 現時点では認証不要、読み取り専用 | 同上 §1.4.3 |
| **ブラウザ** | Chrome 90+, Firefox 88+, Safari 14+, Edge 90+、レスポンシブ | 同上 §1.4.4 |
| **運用** | データ更新と予測連動、ログ管理、定期バックアップ | 同上 §5 |
| **保守** | 月1回定期点検、バージョン管理、自動/手動テスト | 同上 §5.2 |

---

## 3. 要件ドキュメント一覧（docs 内）

### 3.1 要件専用

| ドキュメント | 役割 | ステータス |
|--------------|------|------------|
| [requirements/README.md](requirements/README.md) | 要件ディレクトリの索引 | 概要・管理状況 |
| [requirements/system_status_page.md](requirements/system_status_page.md) | システム状況ページの要件・UI設計 | 要件定義済、実装一部 |
| [requirements/ux_improvement.md](requirements/ux_improvement.md) | Phase 4 UX改善・拡張（検索・ソート・エクスポート・グラフ等） | 要件定義済、未実装 |
| [web_display/requirements.md](web_display/requirements.md) | Web表示機能の要件定義書（基本・ユースケース・非機能・技術） | 基本要件定義完了 |

### 3.2 方針・計画・実装状況（要件と対応）

| ドキュメント | 役割 |
|--------------|------|
| [CURRENT_STATUS_SUMMARY.md](CURRENT_STATUS_SUMMARY.md) | 全体の目標・完了/進行中/計画の対応 |
| [trifecta_improvement_strategy.md](trifecta_improvement_strategy.md) | 3連単的中率向上の評価・改善方針・段階的計画 |
| [improvement_implementation_summary.md](improvement_implementation_summary.md) | 報酬設計・学習時間・アンサンブル等の実装サマリー |
| [web_display/plan.md](web_display/plan.md) | Web表示の実装タスク・Phase 分割 |
| [web_display/complete.md](web_display/complete.md) | Web表示の実装完了状況・テスト |

### 3.3 運用・技術（要件実現の手段）

| ドキュメント | 役割 |
|--------------|------|
| [operations/README.md](operations/README.md) | 運用ガイドの索引 |
| [operations/data_acquisition.md](operations/data_acquisition.md) | データ取得バッチの運用 |
| [operations/scheduled_maintenance.md](operations/scheduled_maintenance.md) | 定期メンテナンス・スケジュール |
| [optimization/README.md](optimization/README.md) | 最適化の概要 |
| [optimization/OPTIMIZATION_GUIDE.md](optimization/OPTIMIZATION_GUIDE.md) | 最適化の詳細 |
| [config_usage_guide.md](config_usage_guide.md) | 設定ファイルの使い方 |

### 3.4 リポジトリ・コード整理

| ドキュメント | 役割 |
|--------------|------|
| [README.md](../README.md) | プロジェクト概要・クイックスタート |
| [REPO_STATUS_20250212.md](REPO_STATUS_20250212.md) | リポジトリ構成・現状サマリー |
| [DEEP_CLEANUP_REPORT_20250212.md](DEEP_CLEANUP_REPORT_20250212.md) | ソース深堀り整理・修正内容 |
| [DIRECTORY_RESTRUCTURE_20250212.md](DIRECTORY_RESTRUCTURE_20250212.md) | リポジトリ整理方針・構成再編の記録 |

---

## 4. 用語・状態の凡例

| 状態 | 意味 |
|------|------|
| ✅ 完了 | 要件を満たす実装が完了し運用可能 |
| 🔄 一部完了 / 継続 | 一部実装済み、または継続的に改善中 |
| 📋 計画中 / 要件済 | 要件は定義済みだが未実装、または計画段階 |

---

## 5. 今後の要件追加時の記載場所

- **新機能の要件定義**: [requirements/](requirements/) に新規 md を追加し、[requirements/README.md](requirements/README.md) の一覧に追記する。
- **既存機能の拡張**: 該当する要件ドキュメント（例: web_display/requirements.md, requirements/ux_improvement.md）を更新し、本 OVERVIEW の表で ID と状態を更新する。
- **目的・目標の変更**: 本 OVERVIEW の「1. プロジェクト目的・スコープ」と [CURRENT_STATUS_SUMMARY.md](CURRENT_STATUS_SUMMARY.md) の「主要目標」を整合させる。

---

**作成日**: 2025-02-12
