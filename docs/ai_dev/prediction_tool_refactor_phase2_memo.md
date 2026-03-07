# prediction_tool.py 第2段リファクタ整理メモ

## 1. remaining duplicate methods

- **`_get_ratio_from_odds_data`**: 2箇所で定義（568行目と1203行目）。ロジックは同一。後者がクラスで有効になっているため、**後者を削除**し前者のみ残す。
- **`predict_trifecta_probabilities_from_data`**: 2箇所で定義（541行目と1216行目）。前者は `build_race_state_vector(race_data, None)` を直接使用。後者は `self.vectorize_race_state_from_data` を使用し、model/policy の None チェックあり。実行時は後者が有効。**前者を削除**し後者のみ残す。

## 2. argparse responsibilities

- main() 内で ArgumentParser を構築し、全引数（--predict-date, --venues, --model-path, --output-dir, --data-dir, --data-source, --db-path, --verbose, --fetch-data, --prediction-only, --risk-level, --complete-flow, --include-selected-bets）を追加して parse_args()。
- 分岐: args.complete_flow なら run_complete_prediction、否则 predict_races（このとき --predict-date 必須）。
- 結果の保存・表示。

## 3. risky contracts to preserve

- CLI 引数名・型・choices・default は変更しない。
- main() の外部シグネチャ（引数なしで sys.argv を読む）は維持。
- PredictionTool の公開メソッド名・返却構造は変更しない。
- predict_trifecta_probabilities_from_data の戻り値形式（120件の combination/probability/expected_value/ratio/rank）は維持。

## 4. smallest safe extraction plan

1. **argparse 分離**: `_build_prediction_tool_parser()` で parser を構築して返す。`_parse_prediction_tool_args(argv=None)` で parser を組み立てて `parse_args(argv)` を返す。main() は args = _parse_prediction_tool_args() を呼び、以降は tool 初期化・分岐・保存・表示のみ。
2. **重複削除**: 2つ目の `_get_ratio_from_odds_data`（1203–1213行）を削除。1つ目の `predict_trifecta_probabilities_from_data`（541–565行）を削除。残る実装は1つずつにする。

---

## 5. 実施内容（実施後）

- **argparse 分離**: `_build_prediction_tool_parser()` で parser を構築、`_parse_prediction_tool_args(argv=None)` でパース。main() は args = _parse_prediction_tool_args() のうえで tool 初期化・分岐・保存・表示のみ。
- **重複削除**: 2つ目の `_get_ratio_from_odds_data` を削除（1つ目のみ残す）。1つ目の `predict_trifecta_probabilities_from_data` を削除（後方の実装のみ残す。vectorize_race_state_from_data と model チェックあり）。
- **追加テスト**: test_parse_prediction_tool_args_defaults_and_flags（パースとデフォルト）、test_get_ratio_from_odds_data_pure（倍率取得の同一入力→同一出力）。
