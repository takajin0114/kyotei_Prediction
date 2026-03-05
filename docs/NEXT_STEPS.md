# 次にやること

リポジトリの現状を踏まえた「次にやるべきこと」の整理です。優先度の高い順に並べています。

---

## 1. テスト：失敗しているテストの修正

以下のテストが現状失敗またはエラーになっています。修正するか、条件付きスキップにすると全体がグリーンになります。

| 対象 | 内容 | 対応案 |
|------|------|--------|
| `test_kyotei_env.py` | 報酬計算の期待値ずれ（1440 vs 900 等）、`mocker` fixture 未定義 | 期待値を現行ロジックに合わせる。`pytest-mock` を入れるか、`unittest.mock.patch` に置き換える。 |
| `test_optimization_minimal.py` | データなしで「No valid race-odds pairs」 | 一時ディレクトリに最小の race/odds ペアを用意するか、データなし時はスキップする。 |
| `test_phase3_purchase_suggestions.py`<br>`test_purchase_suggestions_fix.py` | HTML/JS 内の文言（`purchase-suggestions-section` 等）に依存 | 文言変更に合わせて期待値を更新するか、テスト対象を安定した要素に変更する。 |
| `test_racer_error_handling.py` | `call_count` のモック誤り、パスがディレクトリになる | モックの使い方と一時ファイル/ディレクトリの与え方を修正。 |
| `test_odds_fetcher.py`<br>`test_race_data_fetcher.py` | 一部テストで `mocker` 未定義等の ERROR | `pytest-mock` の有無を確認し、必要なら `unittest.mock` に統一。 |

**ゴール**: 上記を修正 or スキップし、`pytest` 実行で failed/error をゼロに近づける。

---

## 2. テスト：メイン処理の拡充

README_TESTS.md の「第1優先」に沿って、まだ薄い部分を増やす。

| やること | 詳細 |
|----------|------|
| **app.py のテスト** | Flask `test_client` で `/`, `/predictions`, `/api/race_data` 等のルートとレスポンスをテストする。 |
| **PredictionEngine** | `equipment_focused` / `comprehensive` / `relative_strength` の入力・出力のテストを追加する。 |
| **PredictionTool** | `run_complete_prediction` や `predict_races` をモックで囲み、ネットワーク・モデルなしで実行パスを通すテストを検討する。 |
| **DataIntegration** | `get_race_data(source="sample")` や `source="live"` をモックしたテスト（必要なら）。 |

---

## 3. テスト：カバレッジの向上

- `pytest --cov=kyotei_predictor` で計測し、**メイン処理（prediction_engine, data_integration, prediction_tool）** のカバーを増やす。
- 続いて **pipelines**（kyotei_env, trifecta_probability 等）、**utils**（config, logger, common, venue_mapping）の未カバー行を減らす。
- 目標値（例: メイン 80%、全体 50% 等）を README_TESTS.md や CI に書いておくとよい。

---

## 4. 依存・環境の整理

| やること | 詳細 |
|----------|------|
| **pytest-mock** | `test_kyotei_env.py` 等で `mocker` を使うなら `pytest-mock` を requirements に追加し、CI でインストールする。 |
| **schedule / psutil** | `test_imports_smoke.py` で `importorskip` している。本番で使うなら requirements に明記する。 |
| **Selenium** | Web E2E テスト用。必要なら requirements に分離して記載する。 |

---

## 5. ドキュメント・運用

| やること | 詳細 |
|----------|------|
| **README ルート** | テストの実行方法（メインのみ / 全体）を 1 行で書いておく。例: 「テスト: `pytest kyotei_predictor/tests/`」 |
| **CI** | GitHub Actions 等で、上記の `pytest` コマンド（必要なら `--ignore=web_display` 等）を回し、失敗したらブロックする。 |
| **NEXT_STEPS の更新** | 上記を進めたら、このファイルの「次にやること」を更新・チェック off する。 |

---

## 6. コード・リファクタ（任意）

- **メイン処理のテストしやすさ**: PredictionEngine / DataIntegration / PredictionTool の依存（I/O・API）をインターフェースに寄せ、テストで差し替えやすくする。
- **定数・設定の集約**: 報酬値や閾値がテストと実装でずれないよう、1 箇所で定義する。

---

## チェックリスト（進めたら ✓）

- [ ] 失敗テストの修正 or スキップ（1）
- [ ] app.py のルート・API テスト追加（2）
- [ ] PredictionEngine / PredictionTool のテスト拡充（2）
- [ ] カバレッジ計測と目標の明文化（3）
- [ ] pytest-mock / schedule / psutil の整理（4）
- [ ] ルート README にテスト実行方法を追記（5）
- [ ] CI で pytest 実行（5）
