# 予想ツール（Prediction Tool）

## 概要

- 競艇レースの3連単予測と購入方法提案を自動化するツールです。
- 強化学習モデル（PPO）を用いて、各レースの上位20組の3連単組み合わせとその確率・期待値を出力します。
- 購入方法（流し・ボックス等）の提案も自動生成します。
- バッチスケジューラ（scheduled_data_maintenance.py）から自動実行・日次運用が可能です。

## 主な機能

- レース前データ取得（race_data, odds_data）
- 3連単上位20組の予測・確率・期待値計算
- 購入方法（流し・ボックス等）の提案
- JSON形式での予測結果保存
- Web表示用データ生成（今後拡張予定）

## 実行方法

### 単体実行
```sh
python -m kyotei_predictor.tools.prediction_tool --predict-date 2025-07-07 --venues KIRYU,TODA
```
- `--predict-date` : 予測対象日（YYYY-MM-DD）
- `--venues` : 対象会場（カンマ区切り、省略時は全会場）
- `--model-path` : 任意、モデルファイルパス
- `--output-dir` : 任意、出力先ディレクトリ

### バッチスケジューラからの自動実行
```sh
python -m kyotei_predictor.tools.scheduled_data_maintenance --run-now
```
- 日次バッチの一部として、前日データ取得・品質チェック・当日予測を一括実行します。

### 予測のみ実行
```sh
python -m kyotei_predictor.tools.scheduled_data_maintenance --prediction-only --predict-date 2025-07-07 --venues KIRYU
```

## 出力例

- `outputs/predictions_2025-07-07.json` に保存されます。
- 構造例：
```json
{
  "prediction_date": "2025-07-07",
  "generated_at": "2025-07-11T20:29:19.011Z",
  "model_info": { ... },
  "execution_summary": { ... },
  "predictions": [
    {
      "venue": "KIRYU",
      "race_number": 1,
      "race_time": "12:34",
      "top_20_combinations": [
        {"combination": "1-2-3", "probability": 0.12, "expected_value": 3.5, "rank": 1},
        ...
      ],
      "purchase_suggestions": [
        {"type": "box", "description": "1-2-3 ボックス", ...},
        ...
      ],
      "risk_level": "medium"
    },
    ...
  ],
  "venue_summaries": [ ... ]
}
```

## 今後の展望
- Web表示用のHTML/JSテンプレートの追加
- 予測結果の可視化・分析機能の拡充
- モデルの自動更新・精度向上
- 購入提案ロジックの高度化

---

詳細は `kyotei_predictor/tools/prediction_tool.py` および `scheduled_data_maintenance.py` を参照してください。 