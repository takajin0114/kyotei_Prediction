# リファクタ整理メモ（変更前）

## 1. refactor candidates

- **テスト・ドキュメント入口の統一**: README は `kyotei_predictor/tests/` を指定。tests/improvement_tests も存在。実行手順を README_TESTS と README で一致させる。
- **責務分離**: application（baseline_predict_usecase, baseline_train_usecase）／infrastructure（baseline_model_repository, file_loader）／cli（baseline_predict, baseline_train）は既に分離済み。prediction_tool.py が長大（1300行超）で CLI とビジネスロジックが混在している可能性。
- **長いファイル**: tools/prediction_tool.py, application/baseline_predict_usecase.py。長すぎる関数の分割候補。
- **重複**: 買い目パラメータ取得（config 読込）が usecase と CLI で重複しうる。
- **命名・型**: 返り値の型ヒント・docstring の不足箇所がある。
- **magic number**: 定数化できる数値が散在。

## 2. risky areas

- **ROI 計算・評価指標**: tools/evaluation/metrics.py — 変更しない。テストの期待値ミス（mean_reward）のみ修正。
- **買い目選定ロジック**: utils/betting_selector.py, strategy 条件（top_n, ev_threshold）— 変更しない。
- **baseline_predict_usecase の返却構造**: model_info, execution_summary, predictions のキーは verify / 既存ツールが依存するため変更しない。
- **モデルメタデータ形式**: .meta.json の model_type, calibration, seed — 互換性のため変更しない。

## 3. missing tests

- **metadata / config**: baseline_model_repository の load/save metadata、旧フォーマット互換。strategy summary の主要キー（model_info, execution_summary）の contract test。
- **Strategy B 主経路**: run_baseline_predict の返却構造（model_info, execution_summary, conditions）が崩れないことの contract test。
- **CLI**: baseline_predict --help が落ちない、引数パース、usecase 呼び出し契約の軽量テスト。
- **ドキュメントとズレやすい箇所**: テストパス（kyotei_predictor/tests/）、主要設定値、出力 JSON キー（prediction_date, model_info, execution_summary, predictions）。

## 4. safe first steps

1. 既存失敗テストの修正のみ（test_evaluation_metrics: mean_reward 期待値を 0.0 に）。
2. metadata / strategy summary の contract テストを追加（load_baseline_model_metadata, run_baseline_predict 返却キー）。
3. CLI --help と引数パースの smoke テスト追加。
4. README と README_TESTS のテスト実行手順の表記を確認・軽く同期。
5. 長大ファイルの「分割」は行わず、docstring と型ヒントの最小限追加に留める。
6. ドキュメント（docs/README.md, PROJECT_LAYOUT）と実構造のズレがあれば文言のみ修正。

---

## 対応した項目（実施後）

- 既存失敗テスト修正: `test_evaluation_metrics.py` の `mean_reward` 期待値を 0.0 に修正（計算と一致）。
- 追加テスト: `test_baseline_contracts.py`（メタデータ load/save、run_baseline_predict 返却キー契約）、`test_cli_smoke.py`（baseline_predict / prediction_tool --help）。
- ドキュメント同期: `kyotei_predictor/tests/README_TESTS.md` に contract/smoke テストを追記。`docs/PROJECT_LAYOUT.md` にテスト配置・実行の一文を追加。
- ROI 計算・買い目ロジック・主戦略条件は変更していない。
- **prediction_tool 分割**: execution_summary / result payload の組み立てを `_build_execution_summary` / `_build_result_payload` に抽出。selected_bets 付与を `_apply_selected_bets_to_prediction` に集約。詳細は [prediction_tool_refactor_memo.md](prediction_tool_refactor_memo.md)。
