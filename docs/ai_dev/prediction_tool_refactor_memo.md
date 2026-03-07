# prediction_tool.py リファクタ整理メモ

## 1. file responsibilities

- **CLI**: `main()` — argparse で引数解釈、PredictionTool 初期化、run_complete_prediction / predict_races の分岐、結果保存・表示。
- **予測フロー**: `run_complete_prediction()`（完全統合）、`predict_races()`（既存データで予測）。いずれも load_model → レース一覧取得 → 各レースで 3連単予測 → selected_bets 付与（オプション）→ execution_summary / result 構築 → 返却。
- **パス・I/O**: `get_race_data_paths()`（DB または file）、`load_model()`、`save_prediction_result()`。
- **予測コア**: `predict_trifecta_probabilities()`（ファイル版）、`predict_trifecta_probabilities_from_data()`（辞書版）。PPO モデルと state_vector を使用。
- **出力構造**: 返却 Dict に `prediction_date`, `generated_at`, `model_info`, `execution_summary`, `predictions`, `venue_summaries`。execution_summary に `total_races`, `successful_predictions`, `execution_time_minutes`、EV 時は `ev_selection`。
- **補助**: `_aggregate_ev_metadata()`（モジュール級）、会場コード・サマリー・購入提案生成など多数のメソッド。

## 2. candidate extraction points

- **argparse**: `main()` 内の parser 構築・parse → 同一ファイル内の `_parse_prediction_tool_args()` に抽出可能（public は main のみ維持）。
- **実行結果の組み立て**: `predict_races` と `run_complete_prediction` で重複している「execution_summary 辞書の構築」と「result 辞書の構築」→ `_build_execution_summary(...)` と `_build_result_payload(...)` に抽出。
- **selected_bets 付与**: 両フローで同じブロック（ImprovementConfigManager + select_bets）が 2 回出現 → `_apply_selected_bets_to_prediction(self, prediction_dict, all_combinations)` に抽出し in-place で付与。
- **パス解決**: `load_model()` 内のデフォルト model パス解決は既に長いが、今回は触れず「責務を分ける」程度に留める。

## 3. risky public contracts

- **PredictionTool**: 外部から `PredictionTool` と `main` が import されている（predict_usecase, cli/predict, scheduled_data_maintenance, 複数テスト）。コンストラクタ引数・公開メソッド名・戻り値型は変更不可。
- **返却 Dict**: `predict_races` / `run_complete_prediction` の戻り値キー（`prediction_date`, `model_info`, `execution_summary`, `predictions`, `venue_summaries`）。`execution_summary` のキー（`total_races`, `successful_predictions`, `execution_time_minutes`, `ev_selection` など）。verify_predictions やドキュメントが前提にしている。
- **CLI**: 引数名（--predict-date, --venues, --model-path, --data-dir, --data-source, --db-path, --include-selected-bets, --complete-flow 等）は変更しない。
- **get_race_data_paths**: 戻り値 `List[Tuple[str, str, Optional[str], Optional[str]]]`（venue, race_number, race_path, odds_path）。テストが依存。

## 4. required regression tests

- 既存: test_prediction_tool_main（初期化、get_race_data_paths、run_complete_prediction の構造）、test_cli_smoke（--help）。
- 追加: test_result_payload_contract_keys — 返却 payload の契約テスト（prediction_date, model_info, execution_summary, predictions, venue_summaries および execution_summary の必須キー）。

---

## 5. 実施した分割（実施後）

- **モジュール級 helper**: `_build_execution_summary(predictions, execution_time_minutes, successful_predictions=None, **extra)` — execution_summary 辞書を組み立て。EV 集計は _aggregate_ev_metadata で追加。`_build_result_payload(prediction_date, model_info, execution_summary, predictions, venue_summaries)` — 返却用 payload を組み立て。
- **PredictionTool 内**: `_apply_selected_bets_to_prediction(self, prediction, all_combinations)` — 設定に基づき selected_bets（および ev 時は ev_selection_metadata）を in-place で付与。predict_races と run_complete_prediction の両方でこのメソッドを呼ぶように変更し、重複ブロックを削除。
- **public API**: PredictionTool の公開メソッド名・引数・返却構造は変更していない。main() と CLI 引数も変更していない。
