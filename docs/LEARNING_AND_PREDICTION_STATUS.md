# 学習・予想を動かすための現状整理

**目的**: まず「学習」と「予想」を動くようにするために、現状と手順を整理する。  
**最終更新**: 2025-02-12

---

## 1. 全体の流れ

```
[1] 学習データの準備  →  [2] 学習（最適化 or 訓練）  →  [3] モデル保存  →  [4] 予想実行
```

- **学習**: PPO モデルを「レースデータ＋オッズデータ」で訓練し、`best_model.zip` を出力する。
- **予想**: その `best_model.zip` を読み込み、指定日のレースについて 3連単上位20組・購入提案を出力する。

**重要**: 予想を動かすには、**先に1回は学習を実行して `best_model.zip` を作っておく必要**があります。

---

## 2. 現状の整理

### 2.1 学習（モデルを作る）

| 項目 | 内容 |
|------|------|
| **メインの入口** | ① **Optuna 最適化**（推奨）: `optimize_graduated_reward.py` でハイパーパラメータ探索＋学習。② **単純訓練**: `train_with_graduated_reward.py` で固定パラメータで学習。 |
| **実行方法** | ① プロジェクトルート（内側の `kyotei_Prediction/`）で `run_optimization_config.bat`（設定は `optimization_config.ini`）。または `python -m kyotei_predictor.tools.optimization.optimize_graduated_reward --fast-mode --n-trials 2 --year-month 2024-05` など。② `python -m kyotei_predictor.tools.batch.train_with_graduated_reward`（要データあり）。 |
| **必要なデータ** | `kyotei_predictor/data/raw/` に **race_data_YYYY-MM-DD_会場_RN.json** と **odds_data_YYYY-MM-DD_会場_RN.json** のペアが同じ日・会場・レース番号で存在すること。サブディレクトリも検索される。 |
| **データの出所** | `batch_fetch_all_venues.py` や `race_data_fetcher` / `odds_fetcher` で取得。未取得の場合は `data/raw` は空。 |
| **学習結果の保存先** | 実行時のカレントディレクトリがプロジェクトルート（内側 `kyotei_Prediction/`）の場合: `./optuna_models/graduated_reward_best/best_model.zip`（最良モデル）、`./optuna_models/graduated_reward_checkpoints/`（チェックポイント）。Optuna の場合はさらに `./optuna_models/trial_N/best_model.zip` に各試行分が保存され、最良が上記にコピーされる。 |
| **注意** | スクリプト内の `data_dir` デフォルトは `kyotei_predictor/data/raw`（プロジェクトルート基準の相対パス）。`run_optimization_config.bat` はプロジェクトルートで `python kyotei_predictor\...` を実行するため、そのまま `kyotei_predictor/data/raw` を参照する。 |

### 2.2 予想（学習済みモデルで予測する）

| 項目 | 内容 |
|------|------|
| **入口** | `prediction_tool.py`（`PredictionTool` クラス）。コマンド例: `python -m kyotei_predictor.tools.prediction_tool --predict-date 2024-07-12`（会場指定は `--venues KIRYU,TODA`、データディレクトリは `--data-dir kyotei_predictor/data/test_raw` など）。 |
| **モデルの読み込み** | `PROJECT_ROOT / "optuna_models" / "graduated_reward_best" / "best_model.zip"` を参照。存在しなければ `optuna_models/graduated_reward_checkpoints/` 内の最新 `.zip` をフォールバック。`PROJECT_ROOT` は `prediction_tool.py` の位置から見て「プロジェクトルート（内側の kyotei_Prediction フォルダ）」を指す。 |
| **データディレクトリ** | 未指定時は `kyotei_predictor/data/raw`。`--data-dir` で別ディレクトリ（例: `kyotei_predictor/data/test_raw`）を指定可能。リポジトリ内データで予測する場合は `--data-dir` を使用する。 |
| **予想に使うデータ** | 指定日の出走データは **その場で取得**（`fetch_pre_race_data`）。直前情報は取得できた場合のみ含まれる。オッズは期待値・購入提案計算に使用（未取得でも予測自体は継続し、期待値は暫定値）。学習用の `data/raw` の有無は予想実行には不要（ただしモデルが学習済みである必要あり）。 |
| **出力** | JSON で保存（例: `outputs/predictions_YYYY-MM-DD.json`）。Web 表示用のテンプレートも利用可能。 |

### 2.3 データまわり

| 場所 | 役割 | 現状 |
|------|------|------|
| `kyotei_predictor/data/raw/` | 学習用のレース＋オッズ JSON。`race_data_*` と `odds_data_*` のペアが必要。 | .gitignore で除外。中身は手元で取得して配置する必要あり。 |
| `kyotei_predictor/data/kyotei_races.sqlite`（予定） | 学習用のレース＋オッズを SQLite DB で保管。 | DB 化方針は [DATA_STORAGE_AND_DB.md](DATA_STORAGE_AND_DB.md) を参照。実装後は `--data-source db` 等で参照予定。 |
| `kyotei_predictor/data/test_raw/` | テスト用サンプル（例: 2024-05-01 の BIWAKO, GAMAGORI 等）。 | サンプルが入っている。学習の試験用に `--data-dir` でここを指定可能。 |
| 取得コマンド例 | 全会場・指定日: `batch_fetch_all_venues.py` やデータ取得バッチ。 | 別途実行してから学習を行う。取得結果は JSON；DB を使う場合は別途 JSON→DB 投入を行う。 |

### 2.4 学習データの前提（重要）

- 学習は **race_data_YYYY-MM-DD_会場_RN.json** と **odds_data_YYYY-MM-DD_会場_RN.json** の**ペア**が必須です。
- 同じ日・会場・レース番号の 2 ファイルが揃っていないと、そのレースはエピソードに使われません。片方だけ・日付や会場名の不一致があると「No race files」や「No odds files」になります。
- データ取得バッチでは、レースデータとオッズの両方を取得し、ペアで揃えてから学習を実行してください。

### 2.5 環境・依存関係（学習も予測も同じ venv で）

- **学習**と**予測**は、同じ仮想環境（venv）で実行することを推奨します。別環境だと `metaboatrace` や `requests` がなく予測でエラーになることがあります。
- 手順: プロジェクトルートで `python -m venv venv` → `venv\Scripts\activate` → `pip install -r requirements.txt`。`requirements.txt` は UTF-8（BOM なし）で保存されているため、Windows でも `pip install -r requirements.txt` が通ります。
- 学習・予測のどちらも、**プロジェクトルート（内側の kyotei_Prediction/）をカレント**にして実行してください。

---

## 3. 「まず動かす」ための手順（最小）

### Step 1: 学習を 1 回動かす（モデルを作る）

1. **データを用意する**
   - 案 A: `kyotei_predictor/data/raw/` に、既に取得済みの `race_data_*.json` と `odds_data_*.json` を置く（年月は `optimization_config.ini` の `YEAR_MONTH` か、後述の `--year-month` に合わせる）。
   - 案 B: テスト用なら **test_raw を流用**。プロジェクトルートで:
     ```bat
     python -m kyotei_predictor.tools.optimization.optimize_graduated_reward --data-dir kyotei_predictor/data/test_raw --year-month 2024-05 --fast-mode --n-trials 2
     ```
     （本番用には `data/raw` に十分なデータを用意したうえで、`--data-dir kyotei_predictor/data/raw` と適切な `--year-month` を指定する。）

2. **実行ディレクトリ**
   - 必ず **プロジェクトルート（内側の `kyotei_Prediction/`）** で実行する。  
   - そうすると `./optuna_models/graduated_reward_best/best_model.zip` に保存される。

3. **バッチで実行する場合**
   - `optimization_config.ini` の `YEAR_MONTH` を、用意したデータの年月（例: 2024-05）に合わせる。
   - `run_optimization_config.bat` を実行。  
   - 初回は `MODE=fast`, `TRIALS=2` などにして動作確認するとよい。

4. **確認**
   - 終了後、`optuna_models/graduated_reward_best/best_model.zip` が存在することを確認する。

### Step 2: 予想を動かす

1. **同じプロジェクトルート**で:
   ```bat
   python -m kyotei_predictor.tools.prediction_tool --predict-date 2024-07-12
   ```
   - 日付は任意。その日の出走データを **data/raw** 内のファイルから参照して予測する。
   - 会場を絞る: `--venues KIRYU,TODA`
   - **リポジトリ内の test_raw で予測する場合**（学習と同一データで検証）:
     ```bat
     python -m kyotei_predictor.tools.prediction_tool --predict-date 2024-05-01 --venues TODA,KIRYU --data-dir kyotei_predictor/data/test_raw
     ```

2. **モデルが見つからない場合**
   - 「モデルファイルが見つかりません」と出る → Step 1 がまだ、または別ディレクトリで学習して `best_model.zip` がプロジェクトルートの `optuna_models/graduated_reward_best/` にない。
   - 学習をプロジェクトルートでやり直すか、`best_model.zip` を上記パスに配置する。

3. **出力**
   - コンソール出力のほか、JSON が `outputs/` などに保存される（スクリプトの仕様に従う）。

---

## 4. よくある問題と確認ポイント

| 現象 | 確認すること |
|------|----------------|
| 学習で「No race files found」 | `--data-dir` のディレクトリに `race_data_*.json` が存在するか。`year_month` を指定している場合、ファイル名の日付がその年月か。 |
| 学習で「No odds files」 | 同じ日・会場・レースの `odds_data_*.json` があるか。`race_data_` と `odds_data_` はペアで必要。 |
| 予想で「モデルファイルが見つかりません」 | プロジェクトルートで学習し、`optuna_models/graduated_reward_best/best_model.zip` ができているか。別フォルダで実行していないか。 |
| バッチで学習するがモデルが残らない | 実行時のカレントディレクトリがプロジェクトルートか。`run_optimization_config.bat` はそのフォルダでダブルクリックまたは `cd` してから実行する。 |
| データがない | 先に `batch_fetch_all_venues.py` などでデータ取得し、`kyotei_predictor/data/raw/` に配置する。テストだけなら `test_raw` を `--data-dir` で指定。 |

---

## 5. 参照ドキュメント・スクリプト

- **最適化の詳細**: `docs/optimization/OPTIMIZATION_GUIDE.md`, `docs/optimization/EXECUTION_EXAMPLES.md`
- **設定**: ルートの `optimization_config.ini`, `docs/config_usage_guide.md`
- **バッチ**: `run_optimization_config.bat`, `BATCH_USAGE_GUIDE.md`
- **予測ツール**: `kyotei_predictor/tools/prediction_tool.py`（docstring 内に使用例あり）
- **環境**: `pipelines/kyotei_env.py`（学習用の強化学習環境。`race_data_*` と `odds_data_*` のペアを参照）

---

**作成日**: 2025-02-12
