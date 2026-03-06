# OS 非依存実行方針（Portability Strategy）

このドキュメントは、競艇予測プロジェクトの実行構造を **OS 非依存** に寄せていく方針と現状をまとめたものです。開発環境が macOS であること、将来的に CI やクラウドで動かす可能性を踏まえ、**処理本体を Python CLI に寄せ、OS 依存スクリプトは薄いラッパーにする** 構成を目指します。

---

## 1. 現状の scripts 構造

| script | purpose | logic level | 対応 |
|--------|---------|-------------|------|
| run_optimization_config.bat | optimization_config.ini を読み最適化実行。venv 作成・有効化、ログ出力、cleanup、実行時間計算 | light orchestration | refactor（CLI 呼び出しに寄せ済み） |
| run_optimization.ps1 | 同上（PowerShell）。最適化後に verify_predictions を EVALUATION_MODE で実行 | light orchestration | refactor（CLI 呼び出しに寄せ済み） |
| run_optimization_simple.bat | INI 読み、venv の python で最適化のみ実行 | light orchestration | keep |
| run_optimization_batch.bat | 固定パラメータ（medium, 20, 2024-02）で最適化＋venv・cleanup | light orchestration | keep |
| run_learning_prediction_cycle.sh | 学習→予測→検証の順で tools を呼ぶ。DATA_DIR / YEAR_MONTH / PREDICT_DATE を環境変数で上書き可能 | light orchestration | keep（コメントで CLI 案内） |
| run_learning_prediction_cycle.bat | 同上（Windows）。固定で test_raw / 2024-05-01 | light orchestration | keep |
| fetch_one_race.bat | batch_fetch_all_venues を固定引数で 1 回呼ぶ | wrapper only | keep |
| run_fetch_one_race.py | 上と同等を subprocess で実行（OS 非依存） | wrapper only | keep |
| run_batch_fetch_1month.sh | YEAR_MONTH から日付範囲を計算し batch_fetch_all_venues を実行 | light orchestration | keep |
| run_fetch_5year_chunked.sh | check/list/next/range を引数で渡し fetch_5year_chunked を実行 | wrapper only | keep |
| check_batch_fetch_stuck.sh | ログ更新時刻・CPU でハング判定、--kill で終了 | business logic | keep（将来 Python 化は任意） |
| cleanup_old_files.bat | forfiles で Optuna 用ディレクトリ・ログを古いものから削除 | business logic | keep（将来 Python 化は任意） |

- **logic level**
  - **wrapper only**: Python コマンドを呼ぶだけ。パス・環境変数・python 起動のみ OS 依存。
  - **light orchestration**: INI の簡易パース、複数コマンドの順次実行、ログ・venv など。
  - **business logic**: ハング検知・削除条件などロジックがスクリプト内にある。

---

## 2. OS 依存の課題

- **Windows (.bat / .ps1)** と **Linux/macOS (.sh)** の二重メンテナンス（同じ処理が 2 系統で書かれている）。
- パス区切り・環境変数・venv の有効化方法が OS ごとに異なる。
- 開発は macOS、本番や CI が Linux/Windows の場合、スクリプトだけでは挙動差が出やすい。
- クラウドや CI では「単一の Python コマンド」で動かしたい需要がある。

---

## 3. Python CLI への移行方針

- **処理の主体は Python に集約** し、設定は `optimization_config.ini` を中心に使う。
- **CLI は config パスと override 引数** を受け取り、既存の tools（optimize_graduated_reward, verify_predictions, prediction_tool など）に委譲する。
- **scripts は「venv 有効化・カレントディレクトリ・ログ出力先の指定・python の起動」だけ** に限定し、ビジネスロジックは持たない。

### 目標となる CLI 入口

| コマンド | 役割 |
|----------|------|
| `python -m kyotei_predictor.cli.optimize` | 最適化（config + `--n-trials` / `--mode` / `--year-month` で上書き） |
| `python -m kyotei_predictor.cli.predict` | 予測（prediction_tool に転送、`--config` は将来拡張用） |
| `python -m kyotei_predictor.cli.verify` | 検証（config の EVALUATION_MODE を `--evaluation-mode` に反映） |
| `python -m kyotei_predictor.cli.report` | 検証・予測サマリ（簡易ダッシュボード） |

- 設定ファイル: 従来どおり **optimization_config.ini**（MODE, TRIALS, YEAR_MONTH, EVALUATION_MODE, VENV_PATH, LOG_DIR, CLEANUP_DAYS 等）。
- CLI は `--config <path>` で ini を指定可能。未指定時はカレントの `optimization_config.ini` を参照。

---

## 4. scripts の役割（整理後）

- **やること**
  - プロジェクトルートへの `cd`
  - 仮想環境の有効化（`venv\Scripts\Activate.bat` / `source venv/bin/activate` 等）
  - ログファイルへのリダイレクト・Tee（OS ごとのパス・コマンド）
  - **単一の Python 呼び出し**: `python -m kyotei_predictor.cli.optimize --config optimization_config.ini` など
- **やらないこと**
  - INI のパースや MODE/TRIALS の解釈（Python CLI に任せる）
  - 複数 Python コマンドの「順序や条件」の制御は、可能な範囲で 1 本の CLI にまとめるか、スクリプトは「1 回の python -m」に寄せる

既存の .bat / .ps1 / .sh は **削除せず**、上記の考え方で中身だけ薄いラッパーに寄せています。

---

## 5. CI / Mac / Windows / Linux の実行フロー

- **共通**
  - プロジェクトルートで `optimization_config.ini` を配置（または CI で生成）。
  - `python -m kyotei_predictor.cli.optimize --config optimization_config.ini` で最適化。
  - 検証は `python -m kyotei_predictor.cli.verify --config optimization_config.ini`（必要に応じて `--prediction` / `--data-dir` を追加）。
- **CI**
  - venv 作成 → `pip install -r requirements.txt` → 上記 CLI を実行。OS 別のシェルは可能な限り使わず、同じ Python コマンドで統一。
- **Mac / Linux**
  - 必要なら `scripts/run_optimization.ps1` に相当する処理を `.sh` で「venv 有効化 + 上記 python -m」のみ実行するラッパーにできる（現状は run_learning_prediction_cycle.sh が学習→予測→検証を実行）。
- **Windows**
  - `run_optimization_config.bat` / `run_optimization.ps1` が venv とログのみ担当し、実処理は `kyotei_predictor.cli.optimize` に委譲。

---

## 6. 将来的な完全 CLI 化のロードマップ

1. **短期（済）**: 最適化・検証の入口を `cli.optimize` / `cli.verify` に用意し、既存 scripts から「python -m kyotei_predictor.cli.optimize --config ...」を呼ぶ形に変更。
2. **中期**: `cli.predict` で `--config` から DATA_DIR 等を読むようにし、学習→予測→検証を一連のオプションで実行できるようにする（例: `--run-cycle` のようなフラグ）。
3. **長期**: cleanup・古いログ削除・実行時間計測などを Python 側に移し、scripts は「環境変数と python の起動だけ」にする。必要に応じて `check_batch_fetch_stuck` や `cleanup_old_files` のロジックを Python ツールとして実装。

---

## 参照

- 設定の詳細: `config_usage_guide.md` / ルートの `optimization_config.ini`
- 最適化の実行例: `docs/optimization/EXECUTION_EXAMPLES.md`、`guides/optimization_script.md`
- A→B 移行・レイアウト: `docs/PROJECT_LAYOUT.md`、`docs/ROADMAP_A_TO_B_BACKGROUND.md`
