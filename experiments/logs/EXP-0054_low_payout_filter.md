# EXP-0054: Low Payout Regime Filter Experiment

## 目的

EXP-0053 で「利益悪化は低配当ヒット偏重で説明できる」と確認された。本実験では、baseline（d_hi475 + switch_dd4000）に**低配当寄りを避けるフィルタ**を追加し、profit / max_drawdown の改善と bet_count のバランスを検証する。

## 条件

- **baseline**: d_hi475（skip_top20pct, 4.30≤EV<4.75, prob≥0.05）+ switch_dd4000
- **追加条件**:
  - CASE1: EV ≥ 4.50
  - CASE2: EV ≥ 4.60
  - CASE3: predicted_odds ≥ 10
  - CASE4: predicted_odds ≥ 12
  - CASE5: predicted_odds ≥ 15
  - CASE6: top1_probability ≤ 0.35（堅いレース回避）
- **評価**: ROI, total_profit, max_drawdown, profit_per_1000_bets, bet_count, longest_losing_streak
- **n_windows**: 36 / **block_size**: 6

## 実行コマンド

```bash
python3 -m kyotei_predictor.tools.run_exp0054_low_payout_filter --n-windows 36
```

## 結果サマリ

| variant                | ROI     | total_profit | max_drawdown | profit/1k   | bet_count | longest_lose |
|------------------------|---------|--------------|--------------|-------------|-----------|--------------|
| baseline               | 0.53%   | 484          | 15,886       | 469.45      | 1,031     | 4            |
| CASE1_ev_ge_450        | 11.12%  | 5,772        | 8,838        | 9,783.05    | 590       | 9            |
| CASE2_ev_ge_460        | 58.72%  | 17,592       | 6,422        | 51,288.63   | 343       | 9            |
| CASE3_odds_ge_10       | 9.28%   | 5,266        | 15,814       | 8,241.0     | 639       | 5            |
| CASE4_odds_ge_12       | 11.75%  | 6,012        | 14,358       | 10,455.65   | 575       | 5            |
| CASE5_odds_ge_15       | 19.15%  | 8,520        | 12,810       | 17,040.0    | 500       | 10           |
| CASE6_top1_prob_le_035 | 18.47%  | 8,764        | 12,618       | 16,442.78   | 533       | 5            |

## 解釈

1. **低配当フィルタで profit / DD は改善**: 全 CASE で baseline より ROI・total_profit が高く、CASE2 を除き max_drawdown も baseline 以下（CASE2 は 6,422 で大幅改善）。
2. **EV 底上げ（CASE1/2）**: EV≥4.50/4.60 で bet 数が 590/343 に減少。CASE2 は ROI 58.72%・profit 17,592 で最も良いが、bet_count は約 1/3 に減り、longest_losing_streak=9 と伸びている。
3. **予想オッズ下限（CASE3/4/5）**: odds≥10/12/15 で bet 数 639/575/500。profit・DD は改善し、longest_lose は CASE3/4 で 5、CASE5 で 10。
4. **堅いレース回避（CASE6）**: top1_prob≤0.35 で bet 533。ROI 18.47%・profit 8,764・max_dd 12,618・longest_lose 5 と、profit/DD/連敗のバランスが良い。

## 採用判断

- **低配当フィルター**: profit / DD は明確に改善。bet_count は減少するが、CASE4（575）、CASE5（500）、CASE6（533）は運用可能水準。
- **推奨候補**: **CASE6**（堅いレース回避）は bet 数・longest_lose・DD のバランスが良い。**CASE2**（EV≥4.60）は数値上最良だが bet 343・longest_lose 9 のためリスクを考慮した採用判断が必要。
- **判断**: 分析結果として **hold**。運用変更する場合は CASE6 または CASE4/CASE5 を候補とし、別途 n_windows 延長・out-of-sample で再評価を推奨。

## 結果 JSON

- `outputs/selection_verified/exp0054_low_payout_filter_results.json`
