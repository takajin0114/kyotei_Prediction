# プロジェクト構成（レイアウト）

**更新**: 2026-03

---

## 1. ディレクトリ構造（プロジェクトルート = kyotei_Prediction/）

```
kyotei_Prediction/                    # プロジェクトルート（ここで python -m を実行）
├── optimization_config.ini          # 最適化の設定（モード・試行数・年月）
├── requirements.txt                 # 依存関係（UTF-8、1ファイルに統一）
├── README.md
├── docs/                            # ドキュメント一式（入口: docs/README.md）
│   ├── README.md                    # 索引（推奨入口）
│   ├── ai_dev/                      # AI 共同開発（状態・タスク・チャット bootstrap）
│   ├── architecture/, strategy/, development/  # カテゴリ別ドキュメント
│   ├── guides/, optimization/, operations/, requirements/, web_display/, archive/
│   └── *.md                         # 状況・タスク・データ・要件など
├── experiments/                     # 実験トラッカー（ML 実験一覧・leaderboard・ログ）。docs/ai_dev/experiments は廃止
│   ├── README.md, experiment_index.md, leaderboard.md, open_questions.md
│   ├── templates/                   # 実験記録テンプレート
│   └── logs/                        # 個別実験ログ（YAML standard 推奨）
├── notebooks/                       # 分析・Colab 用ノートブック
│   ├── colab/                       # Colab 学習テンプレート（Drive 連携）
│   └── analysis/                   # 分析用ノートブック
├── scripts/                         # 実行用バッチ・ランチャー
│   ├── run_optimization_config.bat  # 最適化（推奨）
│   ├── run_learning_prediction_cycle.bat / .sh
│   ├── run_batch_fetch_1month.sh, run_fetch_5year_chunked.sh
│   └── README.md                    # 一覧・実行例
├── logs/                            # 実行ログ・比較結果 JSON（.gitignore。用途: logs/README.md）
├── outputs/                         # 予測結果 JSON・学習済みモデル（.gitignore）
├── kyotei_predictor/                # メイン Python パッケージ
│   ├── app.py, prediction_engine.py, data_integration.py, errors.py
│   ├── config/, utils/, pipelines/, data/, static/, templates/
│   ├── tools/                       # 予測・最適化・取得・分析・監視など
│   └── tests/                       # パッケージ内単体・統合テスト
└── tests/                           # ルート階層のテスト（improvement_tests 等）
```

**注意**: `kyotei_predictor/kyotei_predictor/` は冗長なネスト（中身は logs のみ）。使用していなければ削除してよい。`.gitignore` で除外推奨。

---

## 2. エントリポイント・実行方法

| 用途 | コマンド／バッチ | 備考 |
|------|------------------|------|
| **学習（最適化）** | `scripts\run_optimization_config.bat` または `python -m kyotei_predictor.tools.optimization.optimize_graduated_reward ...` | プロジェクトルートで実行。DB 利用は `--data-source db --date-from 2025-01-01 --date-to 2025-12-31` |
| **学習（直接訓練）** | `python -m kyotei_predictor.tools.batch.train_with_graduated_reward --data-source db --date-from 2025-01-01 --date-to 2025-12-31` | 同上 |
| **予測** | `python -m kyotei_predictor.tools.prediction_tool --predict-date 2024-05-01 --data-dir kyotei_predictor/data/test_raw` | 同上 |
| **学習→予測一括** | `scripts\run_learning_prediction_cycle.bat`（.sh） | test_raw で最小学習→予測 |
| **予測検証** | `python -m kyotei_predictor.tools.verify_predictions --prediction outputs/predictions_2024-05-01.json --data-dir kyotei_predictor/data/test_raw` | 的中率・回収率 |
| **Web** | `python -m kyotei_predictor.app` | Flask |
| **実行確認** | [docs/RUN_VERIFICATION.md](RUN_VERIFICATION.md) 参照 | venv・テスト・短い学習 |

### 実行例（ROI・買い目選定）

- **従来どおり**: 上記コマンドのまま。`improvement_config.json` の `evaluation.optimize_for` は `hybrid`（従来スコア）がデフォルト。
- **ROI 重視で最適化**: `improvement_config.json` の `evaluation.optimize_for` を `roi` に変更してから `optimize_graduated_reward` を実行。
- **買い目選定を切り替え**: `improvement_config.json` の `betting.strategy` を `single` / `top_n` / `threshold` に変更。予測時に `--include-selected-bets` を付けると結果に `selected_bets` が含まれる。
  - 例: `python -m kyotei_predictor.tools.prediction_tool --predict-date 2024-05-01 --include-selected-bets`
- **検証で ROI を確認**: `verify_predictions` の出力に「ROI (bet on 1st prediction)」「Reference (if bet on actual)」が含まれる。結果を JSON で保存: `--output パス` または **`--save`** で `outputs/verification_YYYYMMDD_HHMMSS.json` に自動作成（A/B比較用推奨）。指標定義は [EVALUATION_METRICS_SPEC.md](EVALUATION_METRICS_SPEC.md) を参照。

詳細な方針は [ROI_AND_RESPONSIBILITY_SEPARATION.md](ROI_AND_RESPONSIBILITY_SEPARATION.md)、変更差分は [CHANGELOG_ROI_RESPONSIBILITY.md](CHANGELOG_ROI_RESPONSIBILITY.md) を参照。

---

## 3. kyotei_predictor パッケージ内

| パス | 役割 |
|------|------|
| **app.py** | Flask Web アプリ |
| **prediction_engine.py** | 予測エンジン |
| **data_integration.py** | データ統合 |
| **errors.py** | Flask 用エラーハンドラ |
| **config/** | 設定（config.json, improvement_config.json, optuna_config.json）。settings.py でパス一元管理。 |
| **utils/** | 共通（logger, compression, venue_mapping, exceptions）。ログは config の datefmt で日時分秒統一。 |
| **pipelines/** | 強化学習・前処理（kyotei_env, state_vector, trifecta_*） |
| **data/** | raw, sample 等。race_data_* / odds_data_* のペアが学習に必要。DB は [DATA_STORAGE_AND_DB.md](DATA_STORAGE_AND_DB.md) 参照。 |
| **results/** | 最適化結果 JSON |
| **static/, templates/** | Web 用 |
| **tools/** | 全ツール（予測・最適化・取得・分析・監視・batch）。**legacy は削除済み。** |
| **tests/** | パッケージ内単体・統合テスト |

---

## 4. tools/ の整理

| サブディレクトリ／ファイル | 役割 |
|---------------------------|------|
| **prediction_tool.py** | 統合予測ツール（3連単上位20・購入提案） |
| **verify_predictions.py** | 予測結果の検証（的中率・回収率） |
| **optimization/optimize_graduated_reward.py** | 本流の学習・最適化（file/db 対応） |
| **batch/** | 一括取得・データ保守・train_with_graduated_reward（file/db 対応） |
| **fetch/** | レース・オッズ取得 |
| **evaluation/** | モデル評価（metrics: 指標分離、evaluate_graduated_reward_model） |
| **betting/** | 買い目選定（strategy: single / top_n / threshold / ev） |
| **analysis/** | 特徴量・報酬・オッズ・検証など |
| **monitoring/** | 的中率・最適化状況・パフォーマンス |
| **storage/** | import_raw_to_db, delete_raw_after_import 等 |
| **ai/** | Optuna 最適化（KyoteiOptunaOptimizer）。tools/optuna_optimizer.py は再エクスポート。 |
| **viz/, continuous/, ensemble/** | 可視化・継続学習・アンサンブル |

---

## 5. ドキュメントの入口

- **ドキュメント索引**: [README.md](README.md)（目的別リンク一覧）
- **概要・クイックスタート**: ルート `README.md`
- **学習・予測の手順**: [LEARNING_AND_PREDICTION_STATUS.md](LEARNING_AND_PREDICTION_STATUS.md)
- **実行確認**: [RUN_VERIFICATION.md](RUN_VERIFICATION.md)
- **学習の次にやること**: [LEARNING_NEXT_STEPS.md](LEARNING_NEXT_STEPS.md)
- **バッチの使い方**: [guides/batch_usage.md](guides/batch_usage.md)
- **要件整理**: [REQUIREMENTS_OVERVIEW.md](REQUIREMENTS_OVERVIEW.md)
- **整理履歴（アーカイブ）**: [archive/20250212/](archive/20250212/)

---

## 6. ログの出力先

- **ルートの logs/** : バッチ取得（batch_fetch_*.log）、最適化・学習の tee 出力（optimize_*.log, train_*.log）、比較結果 JSON（rolling_validation_*.json 等）など。用途・Git 運用は [logs/README.md](../logs/README.md) を参照。
- **experiments/logs/** : 個別 ML 実験の記録（Markdown + YAML front matter）。実験トラッカー用。
- **kyotei_predictor/logs/** : 学習の詳細ログ、予測ツール、データ品質・スケジュール保守など
- 日時形式は `config.json` の `logging.datefmt` で統一（`utils/logger.py` 経由）
- **生成物の整理・cleanup**: [REPOSITORY_HYGIENE_AND_CLEANUP.md](REPOSITORY_HYGIENE_AND_CLEANUP.md) を参照

---

## 7. 新規コードを置く場所

- **新しいツール**: `kyotei_predictor/tools/` 直下または適切なサブディレクトリ。実行は `python -m kyotei_predictor.tools.xxx` を推奨。
- **実行用バッチ**: `scripts/` に追加（先頭でルートに移動）。
- **設定の追加**: `config/` の JSON または既存設定の拡張。
- **パイプライン・モデル**: `pipelines/`。
- **ユーティリティ**: `utils/`。
- **テスト**: パッケージ内は `kyotei_predictor/tests/`、改善検証用はルート `tests/improvement_tests/`。

---

## 8. リポジトリ構成の見直し（方針・実施内容）

### 実施した見直し（2026-03）

| 項目 | 内容 |
|------|------|
| **ドキュメント索引** | `docs/README.md` を主要な入口に整理。カテゴリ別（architecture / strategy / development / ai_dev / guides）の索引を追加。 |
| **実験トラッカー** | `experiments/` をリポジトリルートに配置。`docs/ai_dev/experiments/` は廃止。テンプレートは `experiments/templates/`、個別ログは `experiments/logs/`。 |
| **notebooks** | ルート直下に `notebooks/` を追加。Colab テンプレートは `notebooks/colab/`、分析用は `notebooks/analysis/`。 |
| **logs** | ルートの `logs/` は実行時生成物の出力先（.gitignore）。用途・保存方針は `logs/README.md` で明記。 |
| **「次にやること」** | 学習＝LEARNING_NEXT_STEPS、テスト/CI＝NEXT_STEPS、精度向上＝PREDICTION_ACCURACY_IMPROVEMENT_TODO と役割を分離。 |
| **PROJECT_LAYOUT** | 現状の構成・エントリに合わせて更新。legacy 削除済みを明記。DB・日付範囲の実行例を追加。 |
| **ネスト kyotei_predictor** | `kyotei_predictor/kyotei_predictor/` は冗長（中身は logs のみ）。`.gitignore` で除外。削除してよい。 |

### 方針

- **新規ドキュメント**: 追加時は `docs/README.md` の該当セクションに 1 行で追記する。
- **新規ツール**: `kyotei_predictor/tools/` の適切なサブディレクトリに置き、`python -m kyotei_predictor.tools.xxx` で実行する。
- **設定**: ルートの `optimization_config.ini` と `kyotei_predictor/config/*.json` を併用。パスは `config/settings.py` で一元管理。
