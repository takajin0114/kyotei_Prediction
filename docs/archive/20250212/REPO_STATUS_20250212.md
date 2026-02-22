# リポジトリ現状サマリー

**確認日**: 2025-02-12  
**プロジェクト**: 競艇予測システム（Kyotei Prediction System）

---

## 1. リポジトリ構造

### 1.1 ワークスペースとプロジェクトルート

- **ワークスペースルート**: `c:\Users\takaj\Desktop\app\kyotei_Prediction`
- **実質的なプロジェクトルート**: `kyotei_Prediction/`（1階層下）
- ルート直下に `kyotei_Prediction` フォルダのみ存在する二重構造になっています。

### 1.2 プロジェクトルート直下の構成

| 種別 | パス | 説明 |
|------|------|------|
| 設定 | `optimization_config.ini` | 最適化モード・試行数・対象年月など |
| 依存関係 | `requirements.txt` | 統合依存関係（1ファイルに集約済み） |
| バッチ | `run_optimization_config.bat` | メイン最適化（推奨） |
| バッチ | `run_optimization_batch.bat` | シンプル最適化 |
| バッチ | `run_optimization_simple.bat` | 簡易実行 |
| バッチ | `cleanup_old_files.bat` | 古いファイル削除 |
| ドキュメント | `README.md` | プロジェクト概要（※文字化けの可能性あり） |
| ドキュメント | `BATCH_USAGE_GUIDE.md`, `OPTIMIZATION_SCRIPT_GUIDE.md`, `POWERSHELL_SCRIPT_README.md` | 実行手順・スクリプト説明 |
| ドキュメント | `docs/` | 詳細ドキュメント群 |
| コア | `kyotei_predictor/` | メインPythonパッケージ |
| テスト | `tests/` | 改善テスト・学習検証など（ルート階層） |
| 分析結果 | `analysis_results/` | 最適化・Top10分析のJSON（2025-08時点の出力） |

---

## 2. コアパッケージ `kyotei_predictor/` の構成

### 2.1 エントリポイント・Web

- **`app.py`** … Flask Webアプリケーション
- **`prediction_engine.py`** … 予測エンジン
- **`data_integration.py`**, **`errors.py`** … データ統合・エラー定義

### 2.2 主要ディレクトリ

| ディレクトリ | 役割 |
|-------------|------|
| **config/** | 設定（config.json, improvement_config, optuna_config, ImprovementConfigManager） |
| **utils/** | 共通ユーティリティ（common, config, logger, venue_mapping, exceptions） |
| **pipelines/** | データ処理・強化学習（kyotei_env, data_preprocessor, feature_analysis, trifecta_*, feature_enhancer, db_integration） |
| **data/** | データ格納（sample, test_raw にサンプル・テスト用JSONあり） |
| **results/** | 予測・最適化結果（graduated_reward最適化のJSONなど） |
| **static/** | CSS/JS、test_server.py, stop_test_server.py |
| **templates/** | index.html, predictions.html, system_status.html |
| **tools/** | バッチ・分析・予測・最適化・監視など全ツール |
| **tests/** | 単体・統合・Web表示・AI・データテスト |

### 2.3 ツール (`tools/`) の整理

- **batch/** … 全会場取得、データ保守、欠損再取得、月別整理、学習スクリプトなど
- **optimization/** … `optimize_graduated_reward.py`（本流）、202403版
- **evaluation/** … モデル評価
- **analysis/** … 特徴量・報酬設計・3連単・投資価値・オッズ・データ検証など多数
- **prediction_tool.py** … **統合予測ツール**（3連単予測・購入方法提案）※`tools/` 直下
- **monitoring/** … 的中率・最適化状況・パフォーマンス監視
- **fetch/** … オッズ・レースデータ取得
- **ai/** … Optuna最適化・RLサンプル
- **viz/** … 可視化・HTML表示
- **common/** … 会場マッピング・環境テスト
- **legacy/** … 旧最適化・Colab連携など（参照用）
- **continuous/** … 継続学習
- **ensemble/** … アンサンブル
- 直下: `data_quality_checker.py`, `scheduled_data_maintenance.py`, `data_acquisition_report.py`, `optuna_optimizer.py`

---

## 3. ドキュメント (`docs/`) の整理

- **CURRENT_STATUS_SUMMARY.md** … 全体の状況（2025-01-27 更新、内容は有効）
- **REPOSITORY_ORGANIZATION_GUIDE.md** … 整理方針・3段階モード・保守方針
- **README.md** … ドキュメントの索引
- **config_usage_guide.md**, **monthly_learning_guide.md**, **improvement_implementation_summary.md**
- **optimization/** … 最適化ガイド・実行例・高速モード実装まとめ
- **operations/** … データ取得・定期保守
- **requirements/** … システム状況ページ・UX改善要件
- **web_display/** … Web表示の計画・要件・完了メモ
- **trifecta_improvement_strategy.md**, **test_results_summary.md**
- **WORK_COMPLETION_SUMMARY_20250127.md**

---

## 4. 依存関係（requirements.txt）

- **コア**: numpy, pandas, pyarrow
- **ML/RL**: torch, stable-baselines3, gymnasium, optuna, mlflow
- **可視化**: matplotlib, seaborn, scipy, tensorboard
- **Web**: Flask, Flask-Caching, requests
- **データ**: metaboatrace.scrapers, python-dateutil
- **ユーティリティ**: tqdm, rich
- **テスト**: pytest, pytest-cov, pytest-html  
（Selenium系はコメントアウト）

---

## 5. 注意点・整理提案

### 5.1 構造

- **二重ルート**: ワークスペースが `kyotei_Prediction`、実プロジェクトがその中の `kyotei_Prediction/`。運用時は「プロジェクトルート = `kyotei_Prediction/`」と意識するとよいです。
- **予測ツールの場所**: ドキュメントでは「tools/prediction/prediction_tool.py」とある場合がありますが、実体は **`tools/prediction_tool.py`** です。

### 5.2 .gitignore

- `*.bat`, `*.ps1` が除外されているため、リポジトリにバッチ・PowerShellスクリプトは含まれません。意図的であれば問題ありませんが、配布用にバッチを残す場合は除外ルールの見直しが必要です。

### 5.3 README.md のエンコーディング

- ルートの `README.md` が UTF-16 BOM 等で保存されている可能性があり、一部環境で文字化けします。UTF-8（BOMなし）での保存を推奨します。

### 5.4 テストの二系統

- **`tests/`（プロジェクトルート直下）** … 改善テスト・学習検証・設定テスト（improvement_tests）
- **`kyotei_predictor/tests/`** … 本パッケージの単体・統合・Web・AI・データテスト

両方とも有効な構成です。どのテストをいつ実行するかは README や BATCH_USAGE_GUIDE に書いておくと分かりやすいです。

### 5.5 分析結果

- `analysis_results/` に 2025-08 付きの最適化・Top10 分析 JSON が保存されています。必要に応じて `data/results` や `kyotei_predictor/results` と役割を揃えると、後から探しやすくなります。

---

## 6. 現状のまとめ（一言）

- **競艇の3連単予測と購入方法提案**を、PPO＋Optuna最適化で行うシステム。
- **データ取得〜品質チェック〜最適化〜予測〜結果保存**まで一通り実装済み。
- **Web表示**はテンプレート・静的ファイルあり。静的HTML/JSでの表示拡張は計画・要件レベル。
- **バッチ**は `.bat` で最適化・クリーンアップを実行可能。データ取得・保守は `kyotei_predictor/tools/batch/` のスクリプトとバッチで実行。
- ドキュメントは `docs/` とルートの README 群で整理済み。日付の古い「現状サマリー」は `docs/CURRENT_STATUS_SUMMARY.md`、本確認結果は **`docs/REPO_STATUS_20250212.md`** に記載。

---

**作成日**: 2025-02-12
