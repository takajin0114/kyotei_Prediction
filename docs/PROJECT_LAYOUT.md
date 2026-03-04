# プロジェクト構成（レイアウト）

**更新**: 2025-02-12

---

## 1. ディレクトリ構造（プロジェクトルート = 内側の kyotei_Prediction/）

```
kyotei_Prediction/                    # プロジェクトルート（ここで python -m を実行）
├── optimization_config.ini           # 最適化の設定（モード・試行数・年月）
├── requirements.txt                  # 依存関係（UTF-8、1ファイルに統一）
├── README.md
├── docs/                             # ドキュメント一式
│   ├── README.md                     # 索引
│   ├── guides/                       # 実行ガイド（batch_usage, optimization_script, powershell）
│   ├── optimization/, operations/, requirements/, web_display/
│   └── *.md                          # 状況・レポート・要件など
├── scripts/                          # 実行用バッチ（.bat）一式
│   ├── run_optimization_config.bat   # メイン最適化（推奨）
│   ├── run_optimization_batch.bat
│   ├── run_optimization_simple.bat
│   ├── run_learning_prediction_cycle.bat
│   └── cleanup_old_files.bat
├── logs/                             # 実行ログ（バッチ・最適化の出力先）
├── outputs/                          # 予測結果 JSON 等
├── kyotei_predictor/                 # メイン Python パッケージ
└── tests/                            # ルート階層のテスト（improvement_tests 等）
```

---

## 2. エントリポイント・実行方法

| 用途 | コマンド／バッチ | 備考 |
|------|------------------|------|
| **学習（最適化）** | `scripts\run_optimization_config.bat` または `python -m kyotei_predictor.tools.optimization.optimize_graduated_reward ...` | プロジェクトルートで実行 |
| **予測** | `python -m kyotei_predictor.tools.prediction_tool --predict-date 2024-05-01 --data-dir kyotei_predictor/data/test_raw` | 同上 |
| **学習→予測一括** | `scripts\run_learning_prediction_cycle.bat` | test_raw で最小学習→予測 |
| **予測検証** | `python -m kyotei_predictor.tools.verify_predictions --prediction outputs/predictions_2024-05-01.json --data-dir kyotei_predictor/data/test_raw` | 的中率・回収率 |
| **Web** | `python -m kyotei_predictor.app` または `python kyotei_predictor/app.py` | Flask |

---

## 3. kyotei_predictor パッケージ内

| パス | 役割 |
|------|------|
| **app.py** | Flask Web アプリ |
| **prediction_engine.py** | 予測エンジン |
| **data_integration.py** | データ統合 |
| **errors.py** | Flask 用エラーハンドラ |
| **config/** | 設定（ImprovementConfigManager, improvement_config.json, optuna_config.json） |
| **utils/** | 共通（common, compression, logger, venue_mapping, exceptions） |
| **pipelines/** | 強化学習・前処理（kyotei_env, data_preprocessor, feature_analysis, trifecta_*） |
| **data/** | raw, test_raw, sample 等（race_data_* / odds_data_* のペアが学習に必要）。DB 化方針は [DATA_STORAGE_AND_DB.md](DATA_STORAGE_AND_DB.md) 参照。 |
| **results/** | 最適化結果 JSON |
| **static/, templates/** | Web 用 |
| **tools/** | 全ツール（予測・最適化・取得・分析・監視・legacy） |
| **tests/** | パッケージ内単体・統合テスト |

---

## 4. tools/ の整理

| サブディレクトリ／ファイル | 役割 |
|---------------------------|------|
| **prediction_tool.py** | 統合予測ツール（3連単上位20・購入提案） |
| **verify_predictions.py** | 予測結果の検証（的中率・回収率） |
| **optimization/optimize_graduated_reward.py** | 本流の学習・最適化 |
| **optimization/optimize_graduated_reward_202403.py** | 2024年3月版（参照用） |
| **fetch/** | レース・オッズ取得 |
| **batch/** | 一括取得・データ保守・学習スクリプト |
| **evaluation/** | モデル評価 |
| **analysis/** | 特徴量・報酬・オッズ・検証など |
| **monitoring/** | 的中率・最適化状況・パフォーマンス |
| **ai/optuna_optimizer.py** | Optuna 最適化（KyoteiOptunaOptimizer） |
| **optuna_optimizer.py** | ai の再エクスポート（後方互換） |
| **legacy/** | 旧最適化・Colab 等（参照用） |
| **viz/, continuous/, ensemble/** | 可視化・継続学習・アンサンブル |

---

## 5. ドキュメントの入口

- **概要・クイックスタート**: ルート `README.md`
- **ドキュメント索引**: `docs/README.md`
- **学習・予測の手順**: `docs/LEARNING_AND_PREDICTION_STATUS.md`
- **バッチの使い方**: `docs/guides/batch_usage.md`
- **要件整理**: `docs/REQUIREMENTS_OVERVIEW.md`
- **リポジトリ現状・整理履歴**: `docs/REPO_STATUS_20250212.md`, `docs/DEEP_CLEANUP_REPORT_20250212.md`, `docs/REFACTORING_REPORT_20250212.md`

---

## 6. ログの出力先

- **バッチ・最適化のログ**: ルートの `logs/`（optimization_*.log 等）
- **学習の詳細ログ**: `kyotei_predictor/logs/`（optimize_graduated_reward_*.log）
- **予測ツールのログ**: `kyotei_predictor/logs/`（prediction_tool_*.log）

## 7. 新規コードを置く場所

- **新しいツール**: `kyotei_predictor/tools/` 直下または適切なサブディレクトリ。実行は `python -m kyotei_predictor.tools.xxx` を推奨。
- **実行用バッチ**: `scripts/` に追加（先頭で `cd /d "%~dp0\.."` でルートに移動）。
- **設定の追加**: `config/` の JSON または `ImprovementConfigManager` の拡張。
- **パイプライン・モデル**: `pipelines/`。
- **ユーティリティ**: `utils/`。
- **テスト**: パッケージ内は `kyotei_predictor/tests/`、改善検証用はルート `tests/improvement_tests/`。
