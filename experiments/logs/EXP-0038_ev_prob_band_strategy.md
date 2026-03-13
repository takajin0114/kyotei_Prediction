# Experiment: EXP-0038 EV band + probability フィルタ

## experiment id

EXP-0038

## purpose

EXP-0037 で skip_top20pct + EV band（3≤EV<5）が有効であることが確認されたが、EV フィルタだけでは低確率のノイズ穴が含まれる可能性がある。EV band（3≤EV<5）に probability フィルタ（prob ≥ threshold）を追加し、ROI とドローダウンの改善を検証する。

## setup

- ベース: skip_top20pct + EV band 3≤EV<5（EXP-0037 ev_band_3_5 と同一）
- 比較: baseline（確率フィルタなし）、prob≥0.05 / 0.08 / 0.10 / 0.12
- n_windows=18、既存 rolling predictions 使用（outputs/ev_cap_experiments/rolling_roi_predictions）

## implementation

- ツール: `kyotei_predictor/tools/run_exp0038_ev_prob_band_strategy.py`
- 各日付で: レースを max_ev 降順 → skip_top20pct → EV band 3≤EV<5 → probability フィルタ → 集計
- 確率は「selected_bets のうち max EV を達成する組み合わせの予測確率」を使用

## command

```bash
cd /path/to/kyotei_Prediction
python3 -m kyotei_predictor.tools.run_exp0038_ev_prob_band_strategy \
  --db-path kyotei_predictor/data/kyotei_races.sqlite \
  --n-windows 18
```

## results table (n_windows=18, skip_top20pct, 3≤EV<5)

| variant             | ROI     | total_profit | max_drawdown | profit_per_1000_bets | bet_count |
|---------------------|---------|--------------|--------------|----------------------|-----------|
| ev_band_3_5         | 18.71%  | 83,955       | 36,525       | 18,391.02            | 4,565     |
| ev3_5_prob005       | **24.67%** | 70,965    | **18,940**   | **24,244.96**        | 2,927     |
| ev3_5_prob008       | 19.82%  | 48,575       | 22,000       | 19,437.78            | 2,499     |
| ev3_5_prob010       | 13.52%  | 30,515       | 26,995       | 13,255.86            | 2,302     |
| ev3_5_prob012       | 4.30%   | 9,125        | 38,880       | 4,220.63             | 2,162     |

## interpretation

1. **probability フィルタの効果**  
   **ev3_5_prob005**（3≤EV<5 AND prob≥0.05）が baseline（ev_band_3_5）を上回る。ROI 18.71% → **24.67%**、max_drawdown 36,525 → **18,940**、profit_per_1000_bets 18,391 → **24,245**。低確率ノイズを除外することで効率とリスクが改善。

2. **total_profit**  
   baseline が最大（83,955）。prob005 は 70,965 で bet 数減少に伴いやや減少するが、1 bet あたり効率は向上。

3. **max_drawdown**  
   prob005 が最小（18,940）。prob008 も 22,000 で baseline より改善。prob012 は 38,880 で悪化（絞りすぎで変動増）。

4. **閾値とトレードオフ**  
   prob≥0.08/0.10/0.12 と上げるほど bet 数が減り、ROI は prob008 で 19.82% まで維持するが、prob010・prob012 では低下。利益効率とリスクのバランスは **prob005** が最良。

## judgment

- **adopt**
- **ev3_5_prob005**（3≤EV<5 AND prob≥0.05）を採用。ROI・max_drawdown・profit_per_1000_bets のいずれも baseline（ev_band_3_5）を上回り、利益効率とリスクのバランスが良い。実運用候補を **skip_top20pct + 3≤EV<5 + prob≥0.05** に更新する。

## result JSON

- outputs/ev_prob_band_strategy/exp0038_ev_prob_band_strategy_results.json
