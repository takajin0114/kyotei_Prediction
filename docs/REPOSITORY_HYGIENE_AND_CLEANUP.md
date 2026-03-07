# リポジトリの生成物・一時ファイル整理と cleanup 方針

学習・予測・検証・比較実験で増える一時ファイル・成果物を整理し、今後の運用で散らからないようにするためのルールと棚卸しをまとめる。

---

## 1. 現状の生成物の種類

### 1.1 棚卸し一覧（path | category | keep/delete/ignore/archive | reason）

| path | category | 方針 | reason |
|------|----------|------|--------|
| **ルート直下** | | | |
| logs/ | 実験ログ・比較結果JSON | **ignore** | バッチログ・rolling/AB比較結果。Git 管理しない。.gitkeep のみ追跡可 |
| outputs/ | 予測JSON・学習済みモデル | **ignore** | 予測結果・baseline B モデル。容量大・環境依存のため Git 管理しない |
| optuna_logs/ | 最適化ログ | **ignore** | Optuna 試行ごとのログ。.gitignore 済み |
| optuna_models/ | 最適化成果物（モデル） | **ignore** | trial 別モデル・best_model。.gitignore 済み |
| optuna_studies/ | Optuna DB | **ignore** | 最適化 study の SQLite。.gitignore 済み |
| optuna_results/ | 最適化結果JSON | **ignore** | 最適化サマリ JSON。.gitignore 済み |
| optuna_tensorboard/ | TensorBoard ログ | **ignore** | .gitignore 済み |
| optuna_studies_backup_*/ | バックアップ | **ignore** | .gitignore 済み |
| archives/ | アーカイブ | **ignore** | .gitignore 済み。長期保管用 |
| final_results/ | 手動成果物 | **ignore** | .gitignore 済み |
| **kyotei_predictor 配下** | | | |
| kyotei_predictor/data/raw/ | 生データ | **ignore** | レースJSON 等。.gitignore 済み |
| kyotei_predictor/data/backup/ | バックアップ | **ignore** | .gitignore 済み |
| kyotei_predictor/data/temp/ | 一時 | **ignore** | .gitignore 済み |
| kyotei_predictor/data/processed/ | 前処理済み | **ignore** | .gitignore 済み |
| kyotei_predictor/outputs/ | 予測・モデル（パッケージ内） | **ignore** | .gitignore 済み。ルート outputs/ と役割が重複する場合はルートを優先 |
| kyotei_predictor/logs/ | パッケージ内ログ | **ignore** | .gitignore 済み（kyotei_predictor/logs/*.log） |
| kyotei_predictor/results/ | 結果JSON | **ignore** | .gitignore 済み（kyotei_predictor/results/*.json） |
| kyotei_predictor/optuna_* | 同上（ルートと同様） | **ignore** | .gitignore 済み |
| **ソース・ドキュメント** | | | |
| kyotei_predictor/**/*.py | ソースコード | **keep** | Git 管理 |
| docs/*.md | ドキュメント | **keep** | Git 管理 |
| scripts/*.bat, *.sh, *.py, *.ps1 | 実行スクリプト | **keep** | Git 管理（*.bat 等は .gitignore で例外指定済み） |
| tests/ | テスト | **keep** | Git 管理 |
| **キャッシュ・IDE** | | | |
| __pycache__/ | Python キャッシュ | **ignore** | .gitignore 済み |
| .pytest_cache/ | pytest キャッシュ | **ignore** | .gitignore 済み |
| .mypy_cache/ | mypy キャッシュ | **ignore** | .gitignore 済み |
| .ipynb_checkpoints/ | Jupyter チェックポイント | **ignore** | .gitignore 済み |
| .vscode/, .idea/ | IDE 設定 | **ignore** | .gitignore 済み |
| **Notebook** | | | |
| *.ipynb（ルートの Colab 用） | 補助ファイル | **keep** | テンプレートは Git 管理可。実行結果は含めない |
| **その他** | | | |
| batch_fetch_all_venues.lock | ロックファイル | **ignore** | .gitignore 済み |
| *.log, *.tmp, *.temp | 一時ファイル | **ignore** | .gitignore 済み |

### 1.2 生成物の主な出力先まとめ

| 種類 | 主な出力先 | 説明 |
|------|------------|------|
| バッチ・取得ログ | logs/batch_fetch_*.log, logs/fetch_*.log | データ取得のログ |
| 比較・検証結果 | logs/ab_test_*.json, logs/rolling_validation_*.json, logs/ev_threshold_*.json | A/B 比較・rolling validation・EV 閾値比較 |
| 検証テキスト | logs/verification_*.txt, logs/baseline_verification_*.txt | verify_predictions のテキスト出力 |
| 手動メモ | logs/*.md（after_*.md, comparison_*.md 等） | 実験メモ（必要なら docs に移す） |
| 予測 JSON | outputs/predictions_*.json | 日別・戦略別予測結果 |
| 学習済みモデル | outputs/*.joblib, outputs/*.joblib.meta.json | baseline B 等。rolling 用は outputs/rolling_* |
| Optuna | optuna_logs/, optuna_models/, optuna_studies/, optuna_results/ | 最適化のログ・モデル・DB・結果 |
| 学習詳細ログ | kyotei_predictor/logs/, outputs/logs/ | 一部スクリプトが参照 |

---

## 2. Keep / Ignore / Archive / Delete 方針

### 2.1 keep（Git 管理・残す）

- **ソースコード**: kyotei_predictor/**/*.py, scripts/*.py, *.sh, *.bat, *.ps1（scripts 配下）
- **ドキュメント**: docs/**/*.md（archive は参照用に残すか運用から外す）
- **設定・テンプレート**: サンプル設定、Colab 用 .ipynb テンプレート、fetch_5year_plan.json 等
- **テスト**: tests/ 配下
- **ディレクトリ維持用**: logs/.gitkeep 等（中身は ignore）

### 2.2 ignore（Git 管理しない・ローカルで運用）

- **logs/** 配下の .log, .json, .txt, .md（.gitkeep 以外）
- **outputs/** 配下すべて（予測 JSON、.joblib、.meta.json）
- **optuna_logs/, optuna_models/, optuna_studies/, optuna_results/, optuna_tensorboard/**
- **kyotei_predictor/data/raw/, backup/, temp/, processed/**
- **kyotei_predictor/outputs/, logs/*.log, results/*.json**
- **__pycache__/, .pytest_cache/, .mypy_cache/, .ipynb_checkpoints/**
- **archives/, final_results/**, *.log, *.tmp, *.temp, ロックファイル

### 2.3 archive（すぐ削除しない・通常運用から外す）

- **docs/archive/** 配下の古いスナップショット（参照用に残す場合は「読むだけ」と明記）
- **optuna_studies_backup_*/** は cleanup で削除対象に含めてよい（日数経過後）
- 手動で「archive」フォルダに退避した成果物は、必要がなければ後から削除してよい

### 2.4 delete（消してよいと確信できるもののみ）

- **空ディレクトリ**: 運用上不要な空ディレクトリは削除してよい
- **明らかな一時ファイル**: 拡張子 .tmp, .temp で内容が一時的なもの
- **重複バックアップ**: 同じ内容が別場所にあり、日数経過したバックアップは cleanup 対象

**注意**: 中身の意味が不明なものは「archive」扱いにして即削除しない。

---

## 3. logs と outputs の扱い

### 3.1 logs/

- **役割**: バッチ取得ログ、検証結果 JSON、rolling/AB 比較結果、手動メモ（.md）
- **Git**: ディレクトリは `logs/.gitkeep` で維持。中身は .gitignore（`logs/` で除外）
- **運用**: 日次・週次で古い .log を削除してよい。比較結果 JSON（rolling_validation_*.json 等）は実験の再現用に一定期間残すか、必要なら docs に要約を移す
- **保存ルール**: 重要な比較結果は `docs/` に要約を書き、ファイル名と日付をメモする

### 3.2 outputs/

- **役割**: 予測 JSON（predictions_*.json）、学習済みモデル（.joblib）、rolling 用サブディレクトリ（rolling_windows_*）
- **Git**: すべて .gitignore。コミットしない
- **運用**: 学習済みモデルは「本番用」「検証用」を決め、不要な古いモデルは cleanup 対象。予測 JSON は容量に応じて古い日付から削除してよい
- **保存ルール**: 本番用モデルは outputs/ または別の共有ストレージに名前規則で保存（例: baseline_b_model.joblib）。rolling 用は実行ごとに上書きしてよい

---

## 4. 学習済みモデルの扱い

- **保存場所**: 原則として **outputs/**（ルート）または **kyotei_predictor/outputs/**。設定では `Settings.ROOT_OUTPUTS_DIR = "outputs"`, `Settings.OUTPUT_DIR = "kyotei_predictor/outputs"` を参照
- **Git**: すべて ignore。コミットしない
- **命名例**: baseline_b_model.joblib, baseline_b_abtest.joblib, baseline_b_train202406.joblib, rolling_b_window_model.joblib
- **運用**: 本番・検証で使うモデルだけ残し、trial 別・古い rolling 用は cleanup で削除してよい

---

## 5. 比較実験結果の保存ルール

- **出力先**: 比較結果 JSON は **logs/** に保存（例: logs/rolling_validation_calibration_before_after.json）
- **ドキュメント**: 重要な数値・結論は **docs/** の該当 MD に書き、ファイル名を明記（例: docs/TIME_SERIES_VALIDATION.md に「保存先: logs/rolling_validation_*.json」）
- **再実行**: 同じスクリプトを再実行すれば logs/ が上書きされる。履歴が必要な場合は手動で別名コピーまたは docs に要約を残す

---

## 6. Cleanup の運用方法

### 6.1 現在の cleanup（scripts/cleanup_old_files.bat）

- **対象**: ルートの optuna_studies_backup_*、kyotei_predictor 配下の optuna_*、simple_test_tensorboard, ppo_tensorboard、logs/*.log（30日以上）、kyotei_predictor/logs/*.log（30日以上）
- **条件**: 7日（optuna 等）または 30日（ログ）より古いファイルを削除後、空ディレクトリを削除
- **実行**: Windows で `scripts\cleanup_old_files.bat`。macOS/Linux では未対応

### 6.2 今後の OS 非依存 cleanup 方針

1. **Python で共通 cleanup を用意する**: `python -m kyotei_predictor.cli.cleanup` で、日数指定・ドライラン・対象ディレクトリ指定ができるようにする（今回雛形を追加）。
2. **bat は当面残す**: Windows 運用があるため、cleanup_old_files.bat は削除せず、README で「同等の処理は Python で可能」と案内する。
3. **役割分担**:
   - **bat**: Windows で手軽に実行する用。中身は「何を消すか」の参考として残す。
   - **Python**: 全 OS で同じ挙動にしたい場合・CI で使う場合に利用。オプションで日数・ドライランを指定可能にする。

### 6.3 実行例（Python 雛形の場合）

```bash
# ドライラン（削除せず一覧だけ表示）
python -m kyotei_predictor.cli.cleanup --dry-run --days 7

# 7日より古い対象ファイルを削除
python -m kyotei_predictor.cli.cleanup --days 7

# 30日より古いログのみ
python -m kyotei_predictor.cli.cleanup --days 30 --targets logs
```

---

## 7. 今後の OS 非依存 cleanup の次の一手

1. **Python cleanup の拡張**: 雛形（cli/cleanup.py）に、optuna_* 配下・logs/*.log の日数指定削除を実装する。
2. **scripts/README に記載**: cleanup は「cleanup_old_files.bat（Windows）」と「python -m kyotei_predictor.cli.cleanup（全 OS）」の両方を案内する。
3. **CI での利用**: 必要なら GitHub Actions 等で週次で `cleanup --days 30 --targets logs` を回すことを検討する。

---

## 8. 削除実行履歴と今後の対象

### 8.1 今回実際に削除したもの（クリーンアップ実行時）

| 対象 | 内容 |
|------|------|
| **__pycache__/** | kyotei_predictor 配下の全 __pycache__ ディレクトリ（.venv は除外） |
| **.pytest_cache/** | ルートの .pytest_cache |

- **理由**: ビルド・テストで自動生成されるキャッシュのため、削除してもソースから再生成される。Git 管理外で削除が安全。
- **削除前後**: テスト（test_baseline_b, test_state_vector, test_verify_predictions, test_cleanup_regression）で問題なし。

### 8.2 今回削除しなかったもの

| 対象 | 理由 |
|------|------|
| logs/ の中身 | 比較結果 JSON やバッチログは手動または cleanup CLI（--days 指定）で削除する運用とする。一括削除は行わない。 |
| outputs/ の中身 | 予測 JSON・学習済みモデルは環境依存。主導線で使うモデルを残すため、今回は触らない。 |
| optuna_* 配下 | 最適化成果物。cleanup CLI で日数指定削除するか、手動で整理する。 |
| .gitkeep, README.md | ディレクトリ維持・説明のため残す。 |
| scripts/cleanup_old_files.bat | Windows 用の既存導線のため残す。 |

### 8.3 今後の cleanup 対象（CLI で消す運用）

- **古いログ**: `python -m kyotei_predictor.cli.cleanup --logs-only --days 30` で 30 日より古い .log を削除。
- **Optuna 成果物**: `python -m kyotei_predictor.cli.cleanup --days 7` で 7 日より古い optuna_* 内ファイルを削除（必要に応じて実行）。
- **キャッシュ**: 必要に応じて手動で `find . -type d -name __pycache__` の削除、または pytest 実行で再生成を許容。

### 8.4 手動で残すべき成果物

- **本番・検証用モデル**: outputs/baseline_b_model.joblib 等、主導線で参照する学習済みモデル。
- **直近の比較結果**: 再現性のため、重要な rolling_validation_*.json 等は一定期間 logs/ に残すか、要約を docs に記載。

### 8.5 定期 cleanup の推奨

1. **週次または月次**: `python -m kyotei_predictor.cli.cleanup --dry-run --days 30 --logs-only` で対象確認後、`--dry-run` を外して実行。
2. **キャッシュ**: リポジトリ整理時や CI 前に `__pycache__` / `.pytest_cache` を削除してよい（削除後はテストで再生成される）。
3. **回帰確認**: 削除後は `pytest kyotei_predictor/tests/test_baseline_b.py kyotei_predictor/tests/test_verify_predictions.py kyotei_predictor/tests/test_cleanup_regression.py` で安全を確認する。

---

## 9. 参照

- **.gitignore**: ルートの `.gitignore`（logs/, outputs/, optuna_*, kyotei_predictor/data/raw 等）
- **scripts/README.md**: 実行スクリプト一覧と cleanup の説明
- **設定**: `kyotei_predictor/config/settings.py`（OUTPUT_DIR, ROOT_LOGS_DIR, OPTUNA_* 等）
- **プロジェクトレイアウト**: docs/PROJECT_LAYOUT.md
- **cleanup 回帰テスト**: kyotei_predictor/tests/test_cleanup_regression.py
