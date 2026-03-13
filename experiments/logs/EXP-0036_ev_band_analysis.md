# Experiment: EXP-0036 EV帯ごとの成績分析

## experiment id

EXP-0036

## purpose

「どのEV帯が利益を出しているか」を確認し、EV cap=5.0 が最適である根拠を EV 帯別 ROI で検証する。

## setup

- ベース: EXP-0015 + confidence_weighted（ev_gap_high=0.11, normal_unit=0.5）
- n_windows: 18
- EV: レース単位 max_ev = max(probability×odds) over selected_bets
- EV 帯: EV<1, 1<=EV<2, 2<=EV<3, 3<=EV<4, 4<=EV<5, 5<=EV<6, 6<=EV<8, 8<=EV<10, EV>=10
- hit_rate: その帯で払戻>0 のレース数 / レース数（レース当選率）

## command

```bash
cd /path/to/kyotei_Prediction
python3 -m kyotei_predictor.tools.run_exp0036_ev_band_analysis \
  --db-path kyotei_predictor/data/kyotei_races.sqlite \
  --n-windows 18
```

## EV band vs ROI (n_windows=18)

| ev_band   | ev_range      | bet_count | race_count | hit_rate_pct | roi_pct  | total_profit |
|-----------|---------------|-----------|------------|--------------|----------|--------------|
| EV_lt_1   | 0<=EV<1       | 0         | 0          | —            | —        | 0            |
| EV_1_2    | 1<=EV<2       | 2,787     | 2,257      | 5.36         | -21.89%  | -60,190      |
| EV_2_3    | 2<=EV<3       | 3,212     | 2,217      | 6.13         | -14.98%  | -47,390      |
| EV_3_4    | 3<=EV<4       | 2,486     | 1,657      | 7.30         | **+6.07%**  | **+14,800**  |
| EV_4_5    | 4<=EV<5       | 2,079     | 1,421      | 7.04         | **+33.78%** | **+69,155**  |
| EV_5_6    | 5<=EV<6       | 1,631     | 1,158      | 8.12         | -22.59%  | -36,365      |
| EV_6_8    | 6<=EV<8       | 2,544     | 1,801      | 6.27         | **+4.05%**  | **+10,190**  |
| EV_8_10   | 8<=EV<10      | 1,644     | 1,187      | 5.14         | -2.49%   | -4,060       |
| EV_ge_10  | EV>=10        | 6,197     | 4,442      | 2.75         | -27.65%  | -170,860     |

## interpretation

1. **EV帯ごとの ROI**
   - **黒字帯**: EV_3_4（+6.07%）、EV_4_5（+33.78%）、EV_6_8（+4.05%）。特に **4<=EV<5 が最良**（ROI +33.78%、profit +69,155）。
   - **赤字帯**: EV_1_2（-21.89%）、EV_2_3（-14.98%）、EV_5_6（-22.59%）、EV_8_10（-2.49%）、EV_ge_10（-27.65%）。**EV>=10 が最大損失**（-170,860）。

2. **EV帯ごとの hit_rate**
   - 黒字帯の EV_3_4 / EV_4_5 は 7% 前後。EV_5_6 は 8.12% と高いが ROI は大きくマイナス（オッズが過大評価されやすい帯と解釈）。EV_ge_10 は 2.75% と低く、高 EV 帯は実際の当選が少ない。

3. **どのEV帯を買うべきか**
   - **買うべき帯**: 4<=EV<5（最良）、3<=EV<4、6<=EV<8 も黒字。
   - **避けるべき帯**: EV>=10、5<=EV<6、1<=EV<2、2<=EV<3。

4. **EV cap=5.0 が本当に最適か**
   - **支持される**。cap=5.0 は「5<=EV<6 以降を除外」に相当。EV_4_5 は含めつつ、EV_5_6（-22.59%）と EV_ge_10（-27.65%）を除外できる。EV_6_8 は黒字だが、EV_5_6 / EV_8_10 / EV_ge_10 をまとめて切る cap=5.0 の方が全体 ROI を改善している（EXP-0033/0034 の結果と整合）。cap=6 にすると EV_5_6 が混ざり、cap=5 より悪化するため、**ev_cap=5.0 は妥当**。

## judgment

- **hold**（分析のみ。実運用は現行 skip_top20pct + ev_cap_5.0 を維持）
- EV 帯分析により、黒字帯（3–4, 4–5, 6–8）と赤字帯（5–6, 8–10, >=10）が明確化。ev_cap=5.0 の採用根拠が補強された。

## result files

- outputs/ev_distribution_analysis/exp0036_ev_band_analysis_results.json
- outputs/ev_distribution_analysis/exp0036_ev_band_analysis_results.csv
