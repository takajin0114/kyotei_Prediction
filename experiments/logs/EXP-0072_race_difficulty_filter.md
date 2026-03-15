# EXP-0072: Race Difficulty Filter

## 実験目的

CASE2（4.50 ≤ EV < 4.75, prob ≥ 0.05）は ROI 型戦略であり bet_count が減少している。レース単位で難易度を評価し、難しいレースを除外することで ROI / total_profit / max_drawdown の改善を狙う。

## 実装内容

- **ツール**: `kyotei_predictor/tools/run_exp0072_race_difficulty_filter.py`
- **出力**: `outputs/race_difficulty/exp0072_race_difficulty.json`（outputs は gitignore のため未コミット）
- 予測: 既存 calib_sigmoid rolling prediction（EXP-0070/EXP-0071 と同じ参照元）を使用。

## difficulty 指標

レース単位で `all_combinations` から以下を算出。

| 指標 | 説明 |
|------|------|
| top1_prob | レース内最大確率（1位候補の確率） |
| entropy | H = -Σ(p/Σp) log(p/Σp)。確率分布のエントロピー |
| prob_gap | 1位と2位の確率差（top1 - top2） |
| prob_std | レース内確率の標準偏差 |
| prob_max | 最大確率（top1_prob と同値） |

## 比較 CASE

| variant | 条件 | 意味 |
|---------|------|------|
| CASE0 | なし | difficulty filter なし（baseline） |
| CASE1 | top1_prob ≥ 0.35 | 本命確率が高いレースのみ |
| CASE2 | top1_prob ≥ 0.40 | より厳しく本命型に限定 |
| CASE3 | prob_gap ≥ 0.05 | 1-2位の確率差が大きいレースのみ |
| CASE4 | entropy ≤ 1.50 | 予測がばらつかない（低エントロピー）レースのみ |
| CASE5 | entropy ≤ 1.30 | より厳しく低エントロピーに限定 |

## 実験条件

- calibration: sigmoid
- risk control: switch_dd4000
- selection: 4.50 ≤ EV < 4.75, prob ≥ 0.05（固定）
- skip_top20pct: 適用
- n_windows: 36
- switch_dd4000 の ref_profit: CASE0（difficulty filter なし）で算出し全 variant で共通 schedule

## 実験結果

| variant | ROI | total_profit | max_drawdown | profit_per_1000_bets | bet_count | longest_losing_streak |
|---------|-----|--------------|--------------|----------------------|-----------|------------------------|
| CASE0 | **8.29%** | **4,524** | **9,266** | **7,667.8** | 590 | 9 |
| CASE1 | -21.31% | -5,744 | 6,840 | -19,604.1 | 293 | 8 |
| CASE2 | -12.83% | -3,124 | 4,560 | -11,833.33 | 264 | 7 |
| CASE3 | 5.73% | 2,634 | 11,260 | 5,299.8 | 497 | 10 |
| CASE4 | -11.30% | -1,214 | 3,512 | -10,376.07 | 117 | 5 |
| CASE5 | -13.78% | -1,334 | 3,052 | -12,584.91 | 106 | 5 |

- CASE0（baseline）が ROI・total_profit・max_drawdown・profit_per_1000_bets のすべてで最良。
- top1_prob フィルタ（CASE1/CASE2）は bet 減・利益悪化。
- prob_gap フィルタ（CASE3）は CASE0 より ROI・profit・profit/1k で劣り、max_dd も悪化。
- entropy フィルタ（CASE4/CASE5）は bet 激減・赤字。

## 採用判断

- **reject**。いずれの difficulty filter も baseline（CASE0）を上回らなかった。レース難易度フィルタは今回の閾値・指標では採用しない。主軸は CASE2 selection（4.50≤EV<4.75, prob≥0.05）＋ difficulty filter なしのまま維持する。

## 考察

- 難易度で「易しいレース」に絞ると bet_count が減り、今回の閾値では利益・ROI が悪化した。EXP-0060（CASE2 race hardness: top1_prob≤0.35/0.40）と同様、top1 が高いレースに限定する方向では改善しなかった。
- entropy で「予測がはっきりしているレース」に絞る（entropy≤1.50/1.30）も、bet が 117/106 に減り損失に転じた。
- 結果 JSON は `outputs/race_difficulty/exp0072_race_difficulty.json`。outputs は gitignore のため未コミット。
