# Experiment: EXP-0049 switch_dd 閾値感度確認

## experiment id

EXP-0049

## purpose

EXP-0048 で有効だった「累積DD閾値で stake=80 に落とす」方式について、閾値 3000 / 4000 / 5000 / 6000 / 7000 の違いで total_profit・max_drawdown・ROI・worst_window_profit のバランスがどう変わるか確認し、実運用向け推奨閾値を決める。

## DB 存在確認結果と使用パス

- **確認したパス**: `kyotei_predictor/data/kyotei_races.sqlite`（リポジトリルート基準）。
- **実在確認**: 起動時に `_resolve_db_path()` で解決し `exists()` を確認。ローカルで実在を確認済み。
- **使用パス**: 未指定時は `_REPO_ROOT / "kyotei_predictor" / "data" / "kyotei_races.sqlite"`。本実行ではデフォルトを使用。

## 評価ロジック

- 選抜: d_hi475 固定（skip_top20pct + 4.30≤EV<4.75 + prob≥0.05）。
- 通常 stake=100、保守 stake=80。累積DD（normal_only の window 利益を基準に算出）が閾値以上になった window は stake=80、それ以外は stake=100。
- n_windows = 24。

## 比較対象（DD閾値）

| variant            | DD閾値 | 説明 |
|--------------------|--------|------|
| normal_only        | —      | 常に stake=100 |
| conservative_only  | —      | 常に stake=80 |
| switch_dd3000      | 3000   | 累積DD≥3000 で当該 window を 80 |
| switch_dd4000      | 4000   | 累積DD≥4000 で当該 window を 80 |
| switch_dd5000      | 5000   | 累積DD≥5000 で当該 window を 80（EXP-0048 推奨） |
| switch_dd6000      | 6000   | 累積DD≥6000 で当該 window を 80 |
| switch_dd7000      | 7000   | 累積DD≥7000 で当該 window を 80 |

## 実装内容

- ツール: `kyotei_predictor/tools/run_exp0049_dd_threshold_sensitivity_verified.py`
- EXP-0048 と同様に日別の stake=100/80 時の損益を事前計算し、ref_profit（normal_only の window 別利益）から累積DDを算出。各閾値で stake_schedule を決めて集計。

## 実行コマンド

```bash
cd /path/to/kyotei_Prediction
python3 -m kyotei_predictor.tools.run_exp0049_dd_threshold_sensitivity_verified --n-windows 24
```

## 結果表（n_windows=24）

| variant            | ROI     | total_profit | max_drawdown | profit/1k   | bet_count | total_stake | prof_w | lose_w | longest_lose | worst_w  |
|--------------------|---------|--------------|--------------|-------------|-----------|-------------|--------|--------|--------------|----------|
| normal_only        | 13.65%  | 9,610        | 9,420        | 13,650.57   | 704       | 70,400      | 10     | 14     | 4            | -2,810   |
| conservative_only  | 13.65%  | 7,688        | 7,536        | 10,920.45   | 704       | 56,320      | 10     | 14     | 4            | -2,248   |
| switch_dd3000      | 18.66%  | 11,534       | 8,134        | 16,383.52   | 704       | 61,800      | 10     | 14     | 4            | -2,800   |
| switch_dd4000      | **18.24%** | **11,744** | **7,766**    | **16,681.82** | 704   | 64,400      | 10     | 14     | 4            | -2,800   |
| switch_dd5000      | 16.33%  | 10,814       | 7,766        | 15,360.80   | 704       | 66,220      | 10     | 14     | 4            | -2,800   |
| switch_dd6000      | 14.64%  | 9,886        | 8,694        | 14,042.61   | 704       | 67,520      | 10     | 14     | 4            | -2,810   |
| switch_dd7000      | 14.46%  | 9,808        | 8,772        | 13,931.82   | 704       | 67,840      | 10     | 14     | 4            | -2,810   |

## 解釈

- **switch_dd4000**: total_profit 11,744 で最大。max_drawdown 7,766 は switch_dd5000 と同水準。ROI 18.24%、worst_w -2,800。**利益と DD のバランスが最も良い**。
- **switch_dd3000**: profit 11,534、max_dd 8,134。4000 より利益はやや少なく、DD は約 368 悪化。閾値を下げすぎると保守化が早く利益が減る一方、DD は 3000 の方がやや大きい。
- **switch_dd5000**: EXP-0048 推奨。profit 10,814、max_dd 7,766。4000 より利益が約 930 少ないが、DD は同一。
- **switch_dd6000 / 7000**: 閾値を上げると保守化が遅れ、profit は 9808〜9886、max_dd は 8694〜8772 と normal に近づき、DD 改善が小さくなる。

## 採用判断

- **結論**: **2) 別閾値へ更新**とする。
- **推奨閾値**: **switch_dd4000**（累積DD≥4000 で当該 window を stake=80）。total_profit を最大にしつつ、max_drawdown は switch_dd5000 と同水準（7,766）を維持。
- **実運用**: EXP-0048 の「DD 切替オプション」の推奨を **switch_dd5000 → switch_dd4000** に更新する。
- **judgment**: **adopt**（推奨閾値を 5000 から 4000 に更新）。結果 JSON: outputs/selection_verified/exp0049_dd_threshold_sensitivity_verified_results.json。
