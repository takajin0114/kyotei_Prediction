# リポジトリ現状整理

**整理日**: 2025-02-12  
**ブランチ**: feature/pre-race-before-information

---

## 1. プロジェクト概要

**競艇予測システム（Kyotei Prediction System）**

- **目的**: 競艇の3連単を PPO + Optuna で予測し、オッズ比較・回収率・購入方法提案まで行う予想ツールとして運用する。
- **技術スタック**: Python 3.8+, PyTorch, Stable-Baselines3, Optuna, Flask, Pandas/NumPy, metaboatrace.scrapers

---

## 2. ディレクトリ構成（現状）

```
kyotei_Prediction/                    # プロジェクトルート（ここで python -m 実行）
├── optimization_config.ini           # 最適化の設定（MODE, TRIALS, YEAR_MONTH）
├── requirements.txt                 # 依存関係（1ファイル・UTF-8）
├── README.md                        # プロジェクト概要（※文字化けの可能性あり）
├── docs/                            # ドキュメント一式
│   ├── README.md                    # ドキュメント索引
│   ├── guides/                      # 実行ガイド（batch_usage, optimization_script, powershell）
│   ├── optimization/, operations/, requirements/, web_display/
│   └── 各種 .md                     # 状況・レポート・要件・TODO
├── scripts/                         # 実行用 .bat 一式
│   ├── run_optimization_config.bat  # メイン最適化（推奨）
│   ├── run_optimization_batch.bat
│   ├── run_optimization_simple.bat
│   ├── run_learning_prediction_cycle.bat
│   ├── cleanup_old_files.bat
│   └── verify_pre_race_fetch.py    # レース前情報取得確認
├── logs/                            # 実行ログ（.gitkeep のみコミット）
├── outputs/                         # 予測結果 JSON（predictions_*.json）
├── kyotei_predictor/                # メイン Python パッケージ
└── tests/                           # ルート階層テスト（improvement_tests 等）
```

---

## 3. コアパッケージ `kyotei_predictor/` の要点

| 種別 | パス | 役割 |
|------|------|------|
| Web | `app.py` | Flask アプリ（予測一覧・システム状況） |
| 予測 | `prediction_engine.py` | 予測エンジン |
| データ | `data_integration.py` | データ統合 |
| 設定 | `config/` | settings, improvement_config, optuna_config, ImprovementConfigManager |
| 共通 | `utils/` | common, config, logger, venue_mapping, exceptions |
| パイプライン | `pipelines/` | kyotei_env, data_preprocessor, feature_analysis, trifecta_*, feature_enhancer, db_integration |
| データ格納 | `data/` | sample, test_raw（学習・予測用 JSON） |
| 結果 | `results/` | 最適化結果 JSON 等 |
| フロント | `static/`, `templates/` | CSS/JS, predictions.html, system_status.html |
| ツール | `tools/` | 予測・最適化・取得・分析・監視・legacy |
| テスト | `tests/` | 単体・統合・Web・AI・データ |

**主なツール（tools/）**

- **prediction_tool.py** … 統合予測（3連単上位20・購入提案）※直下
- **verify_predictions.py** … 予測結果の検証（的中率・回収率）
- **optimization/optimize_graduated_reward.py** … 本流の学習・最適化
- **fetch/** … レースデータ・オッズ取得（race_data_fetcher, odds_fetcher）
- **batch/** … 全会場取得・データ保守・欠損再取得・学習スクリプト
- **evaluation/**, **analysis/**, **monitoring/** … 評価・分析・監視
- **ai/optuna_optimizer.py** … Optuna 最適化
- **legacy/** … 旧最適化・Colab 等（参照用）

※ `errors.py` は PROJECT_LAYOUT に記載ありだが、現リポジトリには存在しない（削除済みまたは別名の可能性）。

---

## 4. 実装済み機能の状態

| 機能 | 状態 | 備考 |
|------|------|------|
| データ取得（全会場・前日） | ✅ 済 | batch_fetch_all_venues, scheduled_data_maintenance |
| 当日予測一括（取得→予測→保存） | ✅ 済 | prediction_tool 統合フロー |
| 3連単上位20組・オッズ比較・回収率・購入提案 | ✅ 済 | 8種類の提案・リスクレベル |
| 予測結果 JSON 保存・Web 表示 | ✅ 済 | outputs/, Flask, predictions.html |
| 深夜スケジューラ・失敗時アラート | 🔲 これから | タスクスケジューラ／運用ルールの明文化 |
| レース前情報（出走表・直前情報）取得確認 | 🔄 進行中 | verify_pre_race_fetch.py, PRE_RACE_FETCH_VERIFICATION.md |
| 予測精度向上（ベースライン計測・検証定期化） | 📋 計画 | PREDICTION_ACCURACY_IMPROVEMENT_TODO.md |

---

## 5. Git 状態（2025-02-12 時点）

- **ブランチ**: feature/pre-race-before-information
- **origin/main との差分**: 2コミット先行（`feature/pre-race-before-information`）
- **主な変更**: docs 追加/更新、`fetch_pre_race_data`・`fetch_before_information` 追加、`state_vector.py` 新設、最適化成果物（db/json/tensorboard）の整理
- **作業ツリー**: クリーン（未コミット差分なし）

---

## 6. 実行の入口（よく使うもの）

| 用途 | コマンド／バッチ |
|------|------------------|
| 最適化（学習） | `scripts\run_optimization_config.bat` |
| 学習→予測一括 | `scripts\run_learning_prediction_cycle.bat` |
| 予測のみ | `python -m kyotei_predictor.tools.prediction_tool --predict-date 2024-05-01 --data-dir kyotei_predictor/data/test_raw` |
| 予測検証 | `python -m kyotei_predictor.tools.verify_predictions --prediction outputs/predictions_2024-05-01.json --data-dir kyotei_predictor/data/test_raw` |
| Web | `python -m kyotei_predictor.app` |
| レース前情報確認 | `python scripts/verify_pre_race_fetch.py`（Windows では `py` でも可） |

※ いずれもプロジェクトルート（kyotei_Prediction/）で実行。

---

## 7. ドキュメントの入口

- **全体索引**: docs/README.md
- **構成・エントリポイント**: docs/PROJECT_LAYOUT.md
- **学習・予測の手順**: docs/LEARNING_AND_PREDICTION_STATUS.md
- **現状サマリー（目標とやること）**: docs/CURRENT_STATUS_SUMMARY.md
- **バッチの使い方**: docs/guides/batch_usage.md
- **要件整理**: docs/REQUIREMENTS_OVERVIEW.md
- **予測精度向上 TODO**: docs/PREDICTION_ACCURACY_IMPROVEMENT_TODO.md
- **レース前取得確認**: docs/PRE_RACE_FETCH_VERIFICATION.md
- **本整理**: docs/CURRENT_REPO_STATUS_20250212.md

---

## 8. 注意点・推奨アクション

1. **README.md 文字化け**: ルート README が UTF-16 BOM 等の可能性。UTF-8（BOM なし）推奨。
2. **REPO_STATUS_20250212.md**: バッチが「ルート直下」と書かれているが、現在は **scripts/** に集約済み（DIRECTORY_RESTRUCTURE_20250212 実施済み）。
3. **outputs/**: 予測 JSON の取り扱い（`.gitignore` で無視するか、サンプルのみ管理するか）を方針化するとよい。
4. **次の優先**: 深夜自動実行の開始、運用ルールの明文化、予測精度のベースライン計測（PREDICTION_ACCURACY_IMPROVEMENT_TODO フェーズ A）。

---

**作成**: 2025-02-12（リポジトリ確認に基づく現状整理）
