# 競艇予測システム ドキュメント索引

**このファイルが docs の唯一の入口です。** 目的に応じて下のセクションから該当ドキュメントを開いてください。

---

## 1. まず読むもの（ロール別）

| ロール | 1本目 | 2本目 |
|--------|--------|--------|
| **初回利用** | [../README.md](../README.md)（プロジェクト概要） | [guides/processing_flow.md](guides/processing_flow.md)（処理の流れ） |
| **実行確認** | [RUN_VERIFICATION.md](RUN_VERIFICATION.md)（venv・テスト・短い学習） | [LEARNING_AND_PREDICTION_STATUS.md](LEARNING_AND_PREDICTION_STATUS.md)（学習・予測の手順） |
| **データ取得** | [guides/batch_usage.md](guides/batch_usage.md) | [RACE_DATA_FETCH_OVERVIEW.md](RACE_DATA_FETCH_OVERVIEW.md) |
| **学習・最適化** | [LEARNING_AND_PREDICTION_STATUS.md](LEARNING_AND_PREDICTION_STATUS.md) | [optimization/README.md](optimization/README.md) |
| **構成把握** | [PROJECT_LAYOUT.md](PROJECT_LAYOUT.md) | [REQUIREMENTS_OVERVIEW.md](REQUIREMENTS_OVERVIEW.md) |

---

## 2. 構成・レイアウト

| ドキュメント | 内容 |
|--------------|------|
| [PROJECT_LAYOUT.md](PROJECT_LAYOUT.md) | ディレクトリ構成・エントリポイント・新規コードの置き場所 |
| [REQUIREMENTS_OVERVIEW.md](REQUIREMENTS_OVERVIEW.md) | 要件全体の整理（目的・業務/機能/非機能・ドキュメント対応表） |
| [ROADMAP_A_TO_B_BACKGROUND.md](ROADMAP_A_TO_B_BACKGROUND.md) | **方針・ロードマップ** — A案（現行）からB案（予測と買い目選定分離・ROI重視）へ移行する背景と判断 |
| [IMPLEMENTATION_TASK_LIST_A_TO_B.md](IMPLEMENTATION_TASK_LIST_A_TO_B.md) | **実装タスク一覧** — 直近／B案前準備／B案新規の3分類（[NEXT_TASKS_OVERVIEW](NEXT_TASKS_OVERVIEW.md) と併用） |

---

## 3. 学習・予測の手順

| ドキュメント | 内容 |
|--------------|------|
| [LEARNING_AND_PREDICTION_STATUS.md](LEARNING_AND_PREDICTION_STATUS.md) | 学習と予測を動かすための現状・手順・データ前提 |
| [LEARNING_INPUT_OUTPUT.md](LEARNING_INPUT_OUTPUT.md) | 学習のインプット・アウトプット（race_data/odds_data の必須項目など） |
| [LEARNING_PREDICTION_CYCLE_IMPROVEMENTS.md](LEARNING_PREDICTION_CYCLE_IMPROVEMENTS.md) | 学習→予測サイクルの改善点・verify_predictions の使い方 |
| [RUN_VERIFICATION.md](RUN_VERIFICATION.md) | 実行確認の手順（venv 作成・テスト・学習の短い実行） |

---

## 4. タスク・「次にやること」

**全体の一覧（優先度順）**: [NEXT_TASKS_OVERVIEW.md](NEXT_TASKS_OVERVIEW.md) — 即時・短期・中期のチェックリストと参照リンク。

**役割別の詳細**:

| ドキュメント | 役割 |
|--------------|------|
| [LEARNING_NEXT_STEPS.md](LEARNING_NEXT_STEPS.md) | **学習**の次にやること（評価・検証、ステップ数延長、Optuna、性能監視・運用） |
| [NEXT_STEPS.md](NEXT_STEPS.md) | **テスト・CI・リポジトリ**の次にやること（失敗テスト修正、カバレッジ、pytest-mock 等） |
| [PREDICTION_ACCURACY_IMPROVEMENT_TODO.md](PREDICTION_ACCURACY_IMPROVEMENT_TODO.md) | **精度向上**のフェーズ別タスク（測定・学習強化・モデル拡張・運用監視） |
| [monthly_reports/README.md](monthly_reports/README.md) | **月次レポート**（学習設定・使用データ・検証結果を 1 ファイルにまとめるテンプレート） |
| [STATE_VECTOR_REVIEW.md](STATE_VECTOR_REVIEW.md) | **特徴量・状態ベクトル見直し**（3.3.3 検討メモ：展示走・天候・同一定義） |

---

## 5. データ・保管・取得

| ドキュメント | 内容 |
|--------------|------|
| [DATA_STORAGE_AND_DB.md](DATA_STORAGE_AND_DB.md) | データ保管と DB 化（JSON→SQLite、スキーマ、各処理の file/db 対応一覧） |
| [RACE_DATA_FETCH_OVERVIEW.md](RACE_DATA_FETCH_OVERVIEW.md) | レースデータ取得処理の概要 |
| [RACE_DATA_ACQUISITION_AND_SOURCES.md](RACE_DATA_ACQUISITION_AND_SOURCES.md) | 取得処理・参照サイト・必要データの洗い出し |
| [SITE_DATA_AND_FETCH_STATUS.md](SITE_DATA_AND_FETCH_STATUS.md) | サイトで取得できるデータ一覧と取得状況 |
| [PRE_RACE_FETCH_VERIFICATION.md](PRE_RACE_FETCH_VERIFICATION.md) | レース前取得の検証 |

---

## 6. 最適化・学習の詳細

| ドキュメント | 内容 |
|--------------|------|
| [optimization/README.md](optimization/README.md) | 最適化の概要・クイックスタート |
| [optimization/OPTIMIZATION_GUIDE.md](optimization/OPTIMIZATION_GUIDE.md) | 最適化の詳細ガイド |
| [optimization/FAST_MODE_IMPLEMENTATION_SUMMARY.md](optimization/FAST_MODE_IMPLEMENTATION_SUMMARY.md) | 3段階モード（高速・中・通常）の実装詳細 |
| [optimization/EXECUTION_EXAMPLES.md](optimization/EXECUTION_EXAMPLES.md) | 実行例・サンプル |
| [trifecta_improvement_strategy.md](trifecta_improvement_strategy.md) | 3連単的中率向上の戦略（報酬設計・学習時間・アンサンブル） |
| [improvement_implementation_summary.md](improvement_implementation_summary.md) | 改善策の実装状況（Phase1〜4） |
| [monthly_learning_guide.md](monthly_learning_guide.md) | 月次学習ガイド |

---

## 7. 設計・設定

| ドキュメント | 内容 |
|--------------|------|
| [ROADMAP_A_TO_B_BACKGROUND.md](ROADMAP_A_TO_B_BACKGROUND.md) | A案→B案移行の背景・現状構成・今やること／やらないこと・次のフェーズ |
| [IMPLEMENTATION_TASK_LIST_A_TO_B.md](IMPLEMENTATION_TASK_LIST_A_TO_B.md) | **実装タスク一覧** — 直近／B案前準備／B案で新規の3分類・優先度・完了条件 |
| [ROI_AND_RESPONSIBILITY_SEPARATION.md](ROI_AND_RESPONSIBILITY_SEPARATION.md) | 予測と買い目選定の責務分離・ROI 重視の技術方針 |
| [EVALUATION_METRICS_SPEC.md](EVALUATION_METRICS_SPEC.md) | 評価・検証の指標定義（共通キー・最適化結果JSON仕様・A/B比較用） |
| [ODDS_AND_STATE_DESIGN.md](ODDS_AND_STATE_DESIGN.md) | オッズの扱い（回収率専用）と状態定義の共通化 |
| [config_usage_guide.md](config_usage_guide.md) | 設定ファイルの使用方法（config.json, improvement_config 等） |

---

## 8. 運用・ガイド

| ドキュメント | 内容 |
|--------------|------|
| [guides/README.md](guides/README.md) | ガイド一覧 |
| [guides/processing_flow.md](guides/processing_flow.md) | 処理の流れ（取得→保管→学習→予測） |
| [guides/batch_usage.md](guides/batch_usage.md) | バッチ（scripts/）の使い方 |
| [guides/fetch_5year_chunked.md](guides/fetch_5year_chunked.md) | 5年分データを分けて取得する手順 |
| [guides/colab_learning_prep.md](guides/colab_learning_prep.md) | Colab で学習する準備 |
| [guides/google_drive_colab_workflow.md](guides/google_drive_colab_workflow.md) | Google Drive 保存と Colab 学習の手順 |
| [guides/cursor_web_drive_upload.md](guides/cursor_web_drive_upload.md) | Cursor Web で取得したデータを Drive に保存 |
| [guides/optimization_script.md](guides/optimization_script.md) | 最適化スクリプトの設定・実行 |
| [guides/powershell.md](guides/powershell.md) | PowerShell メモ |
| [guides/junction_setup.md](guides/junction_setup.md) | Windows Junction（日本語パス回避） |
| [guides/git_staging_safety.md](guides/git_staging_safety.md) | LFS 環境での安全なステージング |
| [operations/README.md](operations/README.md) | 運用の概要 |
| [operations/data_acquisition.md](operations/data_acquisition.md) | データ取得の運用 |
| [operations/scheduled_maintenance.md](operations/scheduled_maintenance.md) | 定期メンテナンス |

---

## 9. 状況・テスト・要件

| ドキュメント | 内容 |
|--------------|------|
| [CURRENT_STATUS_SUMMARY.md](CURRENT_STATUS_SUMMARY.md) | 現在の状況サマリー |
| [test_results_summary.md](test_results_summary.md) | テスト結果の詳細 |
| [requirements/README.md](requirements/README.md) | 要件ディレクトリの索引 |
| [requirements/system_status_page.md](requirements/system_status_page.md) | システム状況ページの要件 |
| [requirements/ux_improvement.md](requirements/ux_improvement.md) | UX 改善の要件 |

---

## 10. Web 表示

| ドキュメント | 内容 |
|--------------|------|
| [web_display/README.md](web_display/README.md) | Web 表示システムの概要 |
| [web_display/requirements.md](web_display/requirements.md) | Web 表示の要件 |
| [web_display/plan.md](web_display/plan.md) | 実装計画 |
| [web_display/complete.md](web_display/complete.md) | 実装完了状況 |

---

## 11. アーカイブ

| ディレクトリ | 内容 |
|--------------|------|
| [archive/20250212/](archive/20250212/) | 2025-02-12 整理レポート（REPO_STATUS, REFACTORING_REPORT, DEEP_CLEANUP 等） |

---

## ドキュメント整理方針（メモ）

- **索引**: 本 README.md を唯一の入口とし、上記セクションで目的別にリンクする。
- **「次にやること」**: 学習用＝LEARNING_NEXT_STEPS、テスト/CI用＝NEXT_STEPS、精度向上フェーズ別＝PREDICTION_ACCURACY_IMPROVEMENT_TODO。役割が違うため 3 本で運用。
- **データまわり**: 保管・DB＝DATA_STORAGE_AND_DB、取得概要＝RACE_DATA_FETCH_OVERVIEW を中心に、他は必要に応じて参照。
- **新規ドキュメント**: 追加時は本 README の該当セクションに 1 行で追記する。

**最終更新**: 2026-03
