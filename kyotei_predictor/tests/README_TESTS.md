# テスト概要（リファクタリング向け）

## 次にやること

**詳細は [docs/NEXT_STEPS.md](../../docs/NEXT_STEPS.md) を参照。**

- **優先**: 失敗しているテストの修正 or スキップ（kyotei_env, optimization_minimal, phase3, racer_error_handling, fetcher の mocker）
- **メイン拡充**: app.py のテスト、PredictionEngine の他アルゴリズム、PredictionTool の run_complete_prediction 等
- **カバレッジ**: メイン処理・pipelines のカバー拡大、目標値の明文化
- **環境**: pytest-mock / schedule / psutil の整理、CI で pytest 実行

---

## テスト優先順位（メイン処理を最優先）

**方針: プロジェクトのメイン処理から優先してテストする。**

### 第1優先：メイン処理（予測の中心）

| 優先度 | モジュール | 役割 | テストファイル |
|--------|------------|------|----------------|
| 1 | `prediction_engine.py` | 予測エンジン（アルゴリズム実行・検証・結果整形） | `test_prediction_engine_main.py` |
| 2 | `data_integration.py` | データ取得・検証・統合（sample/file/live） | `test_data_integration_main.py` |
| 3 | `tools/prediction_tool.py` | 予測CLI（run_complete_prediction, predict_races, データパス取得） | `test_prediction_tool_main.py` |
| 4 | `app.py` | Web エントリ（ルート・API） | `test_app_flask.py` |

### 第2優先：メイン処理の依存・パイプライン

| モジュール | 役割 |
|------------|------|
| `pipelines/state_vector.py` | レース→状態ベクトル（予測入力の一部） |
| `pipelines/kyotei_env.py` | 強化学習環境・報酬計算 |
| `pipelines/trifecta_*.py` | 3連単確率・モデル |

### 第3優先：周辺・インフラ

| モジュール | 役割 |
|------------|------|
| `config/settings.py` | 設定・パス |
| `utils/*` | 圧縮・例外・ログ・Config |
| `data/race_db.py` | 学習用DB |
| `tools/verify_predictions.py` 等 | 検証・バッチ |

**責務分離（A→B 共通基盤）**: 予測は `all_combinations`（候補とスコア）まで。買い目選定は `tools/betting` の `select_bets` の責務。評価指標は `tools/evaluation/metrics` で共通化（[EVALUATION_METRICS_SPEC](../../docs/EVALUATION_METRICS_SPEC.md) 参照）。

---

## 実行方法（今後この手順で実行できる）

### 1. 環境準備（初回のみ）

プロジェクトルートで仮想環境を作成し、依存と pytest を入れます。

```bash
# プロジェクトルートに移動
cd /path/to/kyotei_Prediction

# 仮想環境作成（.venv または venv）
python3 -m venv .venv

# 有効化（実行のたびに不要。有効化すると pytest を直接叩ける）
source .venv/bin/activate   # macOS/Linux
# .venv\Scripts\activate    # Windows

# 依存インストール（requirements.txt に pytest が無い場合は追加で入れる）
.venv/bin/pip install -r requirements.txt
.venv/bin/pip install pytest pytest-mock
```

### 2. テスト実行コマンド

**推奨: 仮想環境の Python で pytest を直接指定（有効化していなくても動く）**

```bash
# プロジェクトルートで
.venv/bin/python -m pytest kyotei_predictor/tests/ -v --tb=short
```

**メイン処理のテストのみ（Flask・PredictionEngine・PredictionTool・DataIntegration）:**

```bash
.venv/bin/python -m pytest \
  kyotei_predictor/tests/test_app_flask.py \
  kyotei_predictor/tests/test_prediction_engine_main.py \
  kyotei_predictor/tests/test_prediction_tool_main.py \
  kyotei_predictor/tests/test_data_integration_main.py \
  -v --tb=short
```

**全テスト（Selenium 依存の Web テストを除く）:**

```bash
.venv/bin/python -m pytest kyotei_predictor/tests/ \
  --ignore=kyotei_predictor/tests/web_display/ \
  --ignore=kyotei_predictor/tests/ai/ \
  --ignore=kyotei_predictor/tests/data/ \
  --ignore=kyotei_predictor/tests/test_web_display.py \
  --ignore=kyotei_predictor/tests/test_web_display_simple.py \
  --ignore=kyotei_predictor/tests/test_web_display_phase3_fixes.py \
  --ignore=kyotei_predictor/tests/test_system_status_page.py \
  -v --tb=short
```

**有効化している場合の例:**

```bash
source .venv/bin/activate
pytest kyotei_predictor/tests/ -v --tb=short
```

**CI**: `main` / `master` への push および PR で `.github/workflows/pytest.yml` が実行され、上記と同様の除外オプションで pytest が走ります。失敗するとマージをブロックする想定です。

---

## legacy 削除について

`kyotei_predictor/tools/legacy/` は不要のため削除済みです。  
`test_legacy_import.py` も削除済みです。

## 重要：全資産をカバーしているわけではありません

**「全ての資産に対してテストカバーできている」状態ではありません。**  
上記のとおり、**メイン処理を第1優先**でテストを追加・拡充しています。

---

## 新規追加したテスト（メイン＋周辺）

### メイン処理（第1優先）

| ファイル | 対象 | 内容 |
|----------|------|------|
| `test_app_flask.py` | `app.py` (Flask) | GET /, /predictions, /api/race_data, POST /api/predict, /api/races, /api/weather, 静的ファイル 404 |
| `test_prediction_engine_main.py` | `prediction_engine.PredictionEngine` | predict(), データ検証, 未知アルゴリズム, basic / rating_weighted / equipment_focused / comprehensive / relative_strength |
| `test_data_integration_main.py` | `data_integration.DataIntegration` | 検証, race_id 抽出, get_race_entries_summary, get_race_data(source=file) |
| `test_prediction_tool_main.py` | `tools.prediction_tool.PredictionTool` | 初期化, get_race_data_paths, run_complete_prediction(prediction_only=True) のモックテスト |

### 周辺・インフラ

| ファイル | 対象モジュール | 内容 |
|----------|----------------|------|
| `test_compression.py` | `utils.compression` | DataCompressor の save/load |
| `test_exceptions_extended.py` | `utils.exceptions` | ValidationError, ConfigError, handle_exception, ErrorHandler |
| `test_verify_predictions.py` | `tools.verify_predictions` | get_actual_trifecta_from_race_data, get_odds_for_combination, run_verification |
| 他 | config, data.race_db, errors, pipelines.* 等 | 既存・上記優先順位に沿って拡充 |

---

## 既存テストで失敗しがちなもの（要修正・スキップ）

- `test_kyotei_env.py`: 報酬計算の期待値ずれ、mocker fixture（pytest-mock 要確認）
- `test_optimization_minimal.py`: データなしディレクトリで「No valid race-odds pairs」→ データ用意 or スキップ
- `test_phase3_purchase_suggestions.py` / `test_purchase_suggestions_fix.py`: HTML/JS 文言変更に依存
- `test_racer_error_handling.py`: モック・パスまわり

これらはリファクタ前からある要因です。

## カバレッジ目標と計測（3.2.1）

**目標（README_TESTS 上の目安）**

| 対象 | 目標 | 備考 |
|------|------|------|
| メイン処理 | 80% 以上 | prediction_engine, data_integration, prediction_tool, app |
| プロジェクト全体 | 50% 以上 | kyotei_predictor 配下の本番コード |

**計測方法**

プロジェクトルートで実行。`.coveragerc` により `kyotei_predictor` の本番コードのみ計測（`tests` は omit）されます。

```bash
# カバレッジ付きでテスト実行（pytest-cov が必要: pip install pytest-cov）
.venv/bin/python -m pytest kyotei_predictor/tests/ \
  --cov=kyotei_predictor \
  --cov-report=term-missing \
  --cov-report=html:htmlcov \
  --ignore=kyotei_predictor/tests/web_display/ \
  --ignore=kyotei_predictor/tests/ai/ \
  --ignore=kyotei_predictor/tests/data/ \
  --ignore=kyotei_predictor/tests/test_web_display.py \
  --ignore=kyotei_predictor/tests/test_web_display_simple.py \
  --ignore=kyotei_predictor/tests/test_web_display_phase3_fixes.py \
  --ignore=kyotei_predictor/tests/test_system_status_page.py \
  -v --tb=short
```

- `--cov-report=term-missing`: ターミナルに未カバー行を表示
- `--cov-report=html:htmlcov`: `htmlcov/index.html` でブラウザ確認可能

目標に届かない場合は、メイン処理のテスト拡充や pipelines・utils の単体追加で計測を続ける。

---

## カバー状況の目安

| レベル | 内容 | 例 |
|--------|------|-----|
| **メイン処理（第1優先）** | 予測エンジン・データ統合・予測ツールの単体テスト | test_prediction_engine_main, test_data_integration_main, test_prediction_tool_main, test_app_flask |
| **単体テストあり** | 関数・クラスの挙動を assert で検証 | config.settings, data.race_db, utils.compression, errors |
| **インポートのみ（smoke）** | 「import できる」ことだけ確認 | test_imports_smoke |

## カバレッジ 100% を目指す場合

- **計測**: 上記「カバレッジ目標と計測」のコマンドを使用。`pytest-cov` で本番コードのみ計測（tests は omit）。
- **100% に近づけるには**: メイン処理のテストを拡充したうえで、pipelines・utils・tools 各所の単体テストを追加する必要があります。
