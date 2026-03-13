# Experiment: EXP-0034 EV cap 局所探索（skip_top20pct 固定）

## experiment id

EXP-0034

## purpose

EXP-0033 のベスト条件「skip_top20pct + ev_cap_5.0」が本当に最適か、5.0 近傍の cap 値で ROI / total_profit / max_drawdown をさらに改善できるかを局所探索で確認する。

## setup

- ベース: EXP-0015 + confidence_weighted（ev_gap_high=0.11, normal_unit=0.5）
- EV high skip: **skip_top20pct 固定**
- EV cap（race-level）: レース内最大 EV（probability × odds）が cap を超えるレースを丸ごと除外

### 比較条件

- no_cap
- ev_cap_4.5 / 5.0 / 5.5 / 6.0 / 6.5

- n_windows: 18
- 既存予測: outputs/ev_cap_experiments/rolling_roi_predictions を利用（EXP-0033 と同一）

## command

```bash
cd /path/to/kyotei_Prediction
python3 -m kyotei_predictor.tools.run_exp0034_ev_cap_local_search \
  --db-path kyotei_predictor/data/kyotei_races.sqlite \
  --n-windows 18
```

## results table (n_windows=18, skip_top20pct)

| ev_cap_variant | ROI     | total_profit | max_drawdown | profit_per_1000_bets | bet_count |
|----------------|---------|--------------|--------------|----------------------|-----------|
| no_cap         | -2.85%  | -51,160      | 133,205      | -2,811.76            | 18,195    |
| ev_cap_4.5     | -13.48% | -127,225     | 133,775      | -13,269.19           | 9,588     |
| ev_cap_5.0     | **-2.27%** | **-23,625** | **117,910**  | **-2,236.37**        | 10,564    |
| ev_cap_5.5     | -3.80%  | -42,535      | 116,510      | -3,741.31            | 11,369    |
| ev_cap_6.0     | -4.99%  | -59,990      | 127,915      | -4,919.23            | 12,195    |
| ev_cap_6.5     | -7.10%  | -90,490      | 128,260      | -6,995.21            | 12,936    |

ベースライン: skip_top20pct + ev_cap_5.0（EXP-0033 ベスト）

## interpretation

1. **ev_cap=5.0 が最適か**
   - **yes**。cap 付き条件のなかで ev_cap_5.0 が ROI・total_profit・profit_per_1000_bets で最良。max_drawdown は ev_cap_5.5 がわずかに小さい（116,510 vs 117,910）が、ROI・total_profit は 5.0 が明確に優位。

2. **5.5 / 6.0 で bet_count を維持しつつ ROI 改善できるか**
   - **no**。5.5・6.0・6.5 はいずれも ROI と total_profit が悪化。bet_count は増えるが損失も増え、効率（profit_per_1000_bets）も悪化。

3. **4.5 は切りすぎか**
   - **yes**。ev_cap_4.5 は ROI -13.48%、total_profit -127,225 と大きく悪化。切りすぎで有用なレースまで除外している。

4. **no_cap との比較**
   - no_cap は ROI が -2.85% で 5.0 より 0.58%pt 悪いが、total_profit（-51,160）と max_drawdown（133,205）は 5.0 より悪い。実運用では「利益・リスク」を総合すると ev_cap_5.0 が有利。

## judgment

- **reject**（ev_cap の変更は行わない）
- 局所探索の結果、**ev_cap=5.0 を上回る cap 値は存在しない**。4.5 は切りすぎ、5.5 以上は ROI・profit 悪化。実運用候補は引き続き **skip_top20pct + ev_cap_5.0**（EXP-0033 ベスト）とする。

## result JSON

- outputs/ev_cap_experiments/exp0034_ev_cap_local_search_results.json
