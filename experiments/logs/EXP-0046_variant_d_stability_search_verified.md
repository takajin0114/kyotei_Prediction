# Experiment: EXP-0046 variant_d 近傍安定化探索

## experiment id

EXP-0046

## purpose

EXP-0045 で主軸化した variant_d（skip_top20pct + 4.30≤EV<4.80 + prob≥0.05）を基準に、ROI を維持または改善しつつ max_drawdown・longest_losing_streak・worst_window_profit を悪化させない方向で、実運用向けの安定版を探す。

## DB 存在確認結果と使用パス

- **確認したパス**: `kyotei_predictor/data/kyotei_races.sqlite`（リポジトリルート基準）。
- **実在確認**: 起動時に `_resolve_db_path()` で解決し `exists()` を確認。ローカルで実在を確認済み。
- **使用パス**: 未指定時は `_REPO_ROOT / "kyotei_predictor" / "data" / "kyotei_races.sqlite"`。本実行ではデフォルトを使用。

## 評価ロジック（EXP-0045 と同一）

- stake = 100（全 bet 固定）
- hit のとき payout = stake × odds、外れのとき payout = 0
- profit = payout - stake
- n_windows = 24

## 比較対象 variant

| variant     | ev_lo | ev_hi | prob_min | 条件 |
|-------------|-------|-------|----------|------|
| reference_2 | 4.3   | 4.9   | 0.05     | 4.3≤EV<4.9, prob≥0.05 |
| d_base      | 4.30  | 4.80  | 0.05     | EXP-0045 主軸（ベースライン） |
| d_p055      | 4.30  | 4.80  | 0.055    | prob 強化 |
| d_p060      | 4.30  | 4.80  | 0.06     | prob 強化 |
| d_hi475     | 4.30  | 4.75  | 0.05     | EV 上限を少し絞る |
| d_lo435     | 4.35  | 4.80  | 0.05     | EV 下限を少し上げる |
| d_mid       | 4.35  | 4.75  | 0.05     | 帯を中央に |
| d_mid_p055  | 4.35  | 4.75  | 0.055    | 帯中央 + prob 強化 |

## 実装内容

- ツール: `kyotei_predictor/tools/run_exp0046_variant_d_stability_search_verified.py`
- EXP-0045 の verified ロジックを流用。SELECTION_VARIANTS のみ variant_d 近傍（上記 8 条件）に変更。
- 必須指標をすべて出力: ROI, total_profit, max_drawdown, profit_per_1000_bets, bet_count, profitable_windows, losing_windows, longest_losing_streak, worst_window_profit, median_window_profit, window_profit_std, early_half_profit, late_half_profit。

## 実行コマンド

```bash
cd /path/to/kyotei_Prediction
python3 -m kyotei_predictor.tools.run_exp0046_variant_d_stability_search_verified --n-windows 24
```

## 結果表（n_windows=24, stake=100）

| variant     | ROI     | total_profit | max_drawdown | profit/1k   | bet_count | prof_w | lose_w | longest_lose | worst_w  | median_w | early_half | late_half |
|-------------|---------|--------------|--------------|-------------|-----------|--------|--------|--------------|----------|----------|------------|-----------|
| reference_2 | -2.36%  | -2,120       | 15,040       | -2,355.56   | 900       | 6      | 18     | 6            | -3,600   | -1,045   | -6,990     | 4,870     |
| d_base      | 7.02%   | 5,420        | 11,820       | 7,020.73    | 772       | 10     | 14     | 4            | -3,100   | -770     | -3,470     | 8,890     |
| d_p055      | -2.61%  | -1,970       | 14,110       | -2,609.27   | 755       | 9      | 15     | 4            | -3,000   | -725     | -12,060    | 10,090    |
| d_p060      | -11.41% | -8,410       | 16,490       | -11,411.13  | 737       | 8      | 16     | 4            | -3,400   | -835     | -11,260    | 2,850     |
| d_hi475     | **13.65%** | **9,610** | **9,420**    | **13,650.57** | 704   | 10     | 14     | **4**        | **-2,810** | **-425** | -270       | 9,880     |
| d_lo435     | 10.40%  | 7,230        | 11,800       | 10,402.88   | 695       | 9      | 15     | 6            | -2,910   | -785     | -3,250     | 10,480    |
| d_mid       | 18.21%  | 11,420       | 9,400        | 18,213.72   | 627       | 10     | 14     | 6            | -2,710   | -770     | -50        | 11,470    |
| d_mid_p055  | 6.26%   | 3,830        | 10,990       | 6,258.17    | 612       | 9      | 15     | 6            | -2,610   | -785     | -8,740     | 12,570    |

## 解釈

- **d_hi475**（4.30≤EV<4.75, prob≥0.05）: d_base と比べ **ROI 13.65%**（+6.63%pt）、**total_profit 9,610**（+4,190）、**max_drawdown 9,420**（-2,400 改善）、**longest_losing_streak 4**（維持）、**worst_window_profit -2,810**（-290 改善）、**median_window_profit -425**（改善）。DD・連敗耐性・worst_w をすべて維持または改善しつつ ROI・profit も伸ばしている。**安定版として最有力**。
- **d_mid**（4.35≤EV<4.75, prob≥0.05）: ROI 18.21%、profit 11,420、max_dd 9,400 と最高水準だが **longest_losing_streak=6** で d_base の 4 から悪化。主軸にはしないが「攻め版」として 2 本立ての一方にできる。
- **d_lo435**: ROI 10.40% だが longest_lose=6 で悪化。採用見送り。
- **d_p055 / d_p060**: prob を強めると全体で赤字または悪化。採用見送り。
- **d_mid_p055**: ROI 6.26%、longest_lose=6。d_base より劣るため主軸候補外。

## 採用判断

- **主軸を安定版へ更新**する。d_base より ROI・profit・max_drawdown・worst_window_profit・median のいずれも維持または改善し、longest_losing_streak も 4 のままである **d_hi475** を実運用主軸とする。
- **実運用候補の更新**:
  - **主軸（安定版）**: **skip_top20pct + 4.30≤EV<4.75 + prob≥0.05**（d_hi475）。ROI 13.65%、max_dd 9,420、longest_lose 4、worst_w -2,810。
  - **攻め版（サブ）**: skip_top20pct + 4.35≤EV<4.75 + prob≥0.05（d_mid）。ROI 18.21% だが連敗 6 のリスクあり。リスク許容時のみ。
- **judgment**: **adopt**（主軸を安定版 d_hi475 に更新）。結果 JSON: outputs/selection_verified/exp0046_variant_d_stability_search_verified_results.json。
