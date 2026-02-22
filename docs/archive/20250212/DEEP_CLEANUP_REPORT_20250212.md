# ソース深堀り整理レポート

**実施日**: 2025-02-12  
**対象**: kyotei_predictor パッケージ全体

---

## 1. 実施した修正（適用済み）

### 1.1 不足モジュールの追加

| ファイル | 内容 |
|----------|------|
| **utils/compression.py**（新規） | `DataCompressor` を定義。`hit_rate_monitor.py` が `kyotei_predictor.utils.compression` を参照していたが実体がなく ImportError になっていたため、`save_compressed_json` / `load_compressed_json` を実装して追加。 |
| **utils/__init__.py** | `DataCompressor` をエクスポートに追加。 |

### 1.2 インポートの統一とパス解決

| ファイル | 変更内容 |
|----------|----------|
| **data_integration.py** | `from race_data_fetcher import ...` を廃止し、`from kyotei_predictor.tools.fetch.race_data_fetcher import fetch_complete_race_data, fetch_race_entry_data, fetch_race_result_data` に変更。CWD に依存しないインポートに統一。 |
| **app.py** | (1) `tools.fetch` / `tools.viz` / `errors` の裸インポートを廃止し、`kyotei_predictor.tools.fetch` / `kyotei_predictor.tools.viz` / `kyotei_predictor.errors` に変更。(2) `data/` / `outputs/` を CWD 基準から `Path(__file__).resolve().parent` 基準に変更（`DATA_DIR`, `OUTPUTS_DIR`, `project_root` を使用）。(3) `python app.py` で起動してもパッケージが解決できるよう、起動時に親ディレクトリを `sys.path` に 1 回だけ追加。 |

### 1.3 会場マッピングの一元化

| ファイル | 変更内容 |
|----------|----------|
| **tools/common/venue_mapping.py** | 約 290 行の重複実装を削除し、`kyotei_predictor.utils.venue_mapping` からの再エクスポートに変更。`VENUE_MAPPING` および関数類は従来どおり利用可能。 |
| **utils/venue_mapping.py** | モジュール直下のエイリアスに `print_venue_mapping` を追加（`tools.common.venue_mapping` の再エクスポートで参照されるため）。 |

### 1.4 パイプラインのパッケージ化

| ファイル | 変更内容 |
|----------|----------|
| **pipelines/__init__.py**（新規） | `KyoteiEnvManager`, `vectorize_race_state`, `action_to_trifecta`, `TrifectaProbabilityCalculator` をエクスポート。`from kyotei_predictor.pipelines import ...` で利用可能。 |

---

## 2. 意図的に残している重複・仕様

### 2.1 エラー類の二系統

- **errors.py（パッケージ直下）**  
  Flask 用。`APIError` に `status_code`, `payload`, `to_dict()` を持たせ、`register_error_handlers(app)` でアプリに登録。**app.py はこちらを参照。**
- **utils/exceptions.py**  
  `KyoteiError` を基底に `APIError`, `PredictionError` などを定義。`status_code` は持たない。他モジュールの汎用エラー用。
- **prediction_engine.py**  
  同ファイル内で `PredictionError`, `DataValidationError`, `AlgorithmError` を定義。エンジン専用の意味づけのため、現状はそのまま利用。

**方針**: Flask 用は `errors.py`、それ以外は `utils.exceptions` または各モジュールの例外を用途に応じて使い分け。将来的に `utils.exceptions.APIError` に `status_code` を追加して一本化することは可能。

### 2.2 sys.path の追加

多くのツール・テストで `sys.path.append` / `sys.path.insert` が使われている。

- **推奨実行方法**: プロジェクトルート（内側の `kyotei_Prediction/`）で  
  `python -m kyotei_predictor.tools.xxx` または `python -m kyotei_predictor.tests.xxx` で実行すると、パス追加に依存しづらくなる。
- **app.py**: 今回、`python app.py` で起動しても動くように親ディレクトリを 1 回だけ `sys.path` に追加する処理を入れた。
- **legacy 配下**: `sys.path.append('.')` に依存しているスクリプトは、ルートで実行する前提でそのまま残してある。

---

## 3. ディレクトリ・モジュール構成のメモ

### 3.1 __init__.py の有無

- **あり**: `utils/`, `pipelines/`, `tools/batch/`, `tools/optimization/`, `tools/evaluation/`
- **なし**: `config/`（`config.improvement_config_manager` 等は namespace package としてインポート可能）

### 3.2 設定の参照

- `pipelines/kyotei_env.py` および `tools/optimization/optimize_graduated_reward.py` は  
  `from ..config.improvement_config_manager` または `from config.improvement_config_manager` で設定を参照。  
  実行時に「`kyotei_predictor` の親ディレクトリが sys.path に入っている」前提で動作。

### 3.3 予測ツールの場所

- ドキュメントに「tools/prediction/prediction_tool.py」とある場合があるが、実体は **tools/prediction_tool.py**（`prediction` サブディレクトリはなし）。

---

## 4. 今後の整理候補（未実施）

- **型ヒント・docstring**: 一部モジュールでは未整備。順次 `typing` と docstring を揃えると保守性が上がる。
- **legacy の sys.path**: `sys.path.append('.')` に依存しているスクリプトを、可能な範囲で `python -m` 実行に寄せると、実行方法が分かりやすくなる。
- **prediction_engine の例外**: `PredictionError` を `utils.exceptions.PredictionError` に寄せ、`DataValidationError` / `AlgorithmError` をそのサブクラスとして `utils.exceptions` にまとめる refactor は可能（影響範囲が大きいため今回は見送り）。
- **config/__init__.py**: 現状は namespace package のまま。明示的にパッケージにしたい場合は空の `config/__init__.py` を追加するだけでよい。

---

## 5. 修正後のインポート確認

プロジェクトルート（内側の `kyotei_Prediction/`）で以下を実行して確認済み。

```text
from kyotei_predictor.utils import Config, VenueMapper, DataCompressor
from kyotei_predictor.pipelines import KyoteiEnvManager, TrifectaProbabilityCalculator
from kyotei_predictor.tools.common.venue_mapping import VENUE_MAPPING
# OK, 22 venues (utils の会場マッピングは metaboatrace の有無で件数が変わる場合あり)
```

---

**レポート作成**: 2025-02-12
