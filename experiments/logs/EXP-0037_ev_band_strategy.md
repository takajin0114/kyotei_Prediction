# Experiment: EXP-0037 EV帯フィルタ戦略

## experiment id

EXP-0037

## purpose

EV が利益を出している帯だけを購入した場合に ROI が改善するかを検証する。EXP-0036 の黒字帯（3–4, 4–5, 6–8）に基づき、EV 帯フィルタを適用した戦略をベースライン（EV<=5）と比較する。

## setup

- ベース: EXP-0015 + confidence_weighted、n_windows=18
- skip_top20pct 適用後、EV 帯でフィルタ
- 比較: baseline（EV<=5）、3<=EV<5、3<=EV<6、3<=EV<8、4<=EV<5、4<=EV<6

## command

```bash
cd /path/to/kyotei_Prediction
python3 -m kyotei_predictor.tools.run_exp0037_ev_band_strategy \
  --db-path kyotei_predictor/data/kyotei_races.sqlite \
  --n-windows 18
```

## results table (n_windows=18, skip_top20pct)

| variant             | ROI     | total_profit | max_drawdown | profit_per_1000_bets | bet_count |
|---------------------|---------|--------------|--------------|----------------------|-----------|
| baseline_ev_lte_5   | -2.27%  | -23,625      | 117,910      | -2,236.37            | 10,564    |
| ev_band_3_5        | **+18.71%** | **+83,955** | **36,525**   | +18,391.02            | 4,565     |
| ev_band_3_6        | +7.81%  | +47,590      | 49,210       | +7,680.76             | 6,196     |
| ev_band_3_8        | +6.71%  | +57,780      | 73,300       | +6,610.98             | 8,740     |
| ev_band_4_5        | **+33.78%** | +69,155  | 48,505       | **+33,263.59**        | 2,079     |
| ev_band_4_6        | +8.97%  | +32,790      | 55,035       | +8,838.27             | 3,710     |

## interpretation

1. **EV帯フィルタで ROI が大きく改善するか**  
   **する**。ベースライン（EV<=5）は ROI -2.27% だったが、黒字帯のみに絞ると全条件でプラス ROI。3<=EV<5 で +18.71%、4<=EV<5 で +33.78%。

2. **total_profit**  
   最大は **ev_band_3_5**（+83,955）。ev_band_4_5 は +69,155、ev_band_3_8 は +57,780。

3. **max_drawdown**  
   最小は **ev_band_3_5**（36,525）。ev_band_4_5 は 48,505。ベースライン 117,910 から大幅に低下。

4. **profit_per_1000_bets**  
   最大は **ev_band_4_5**（+33,264）。ev_band_3_5 は +18,391。

5. **採用候補**  
   - **ev_band_3_5**: total_profit 最大・max_drawdown 最小・bet_count 4,565。実運用の第一候補。
   - **ev_band_4_5**: ROI・profit_per_1000 最大だが bet_count 2,079 と少なめ。効率重視なら選択肢。

## judgment

- **adopt**
- 利益を出している EV 帯（3<=EV<5 または 4<=EV<5）に限定することで、ベースラインを大きく上回る ROI・total_profit・max_drawdown 改善を確認。実運用候補を **skip_top20pct + ev_band 3<=EV<5**（ev_band_3_5）に更新する。ROI 最優先の場合は **4<=EV<5**（ev_band_4_5）を選択可能。

## result JSON

- outputs/ev_band_strategy/exp0037_ev_band_strategy_results.json
