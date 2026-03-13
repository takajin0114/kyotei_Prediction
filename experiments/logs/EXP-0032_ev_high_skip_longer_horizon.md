# Experiment: EXP-0032 高EV帯除外 longer horizon 比較

## experiment id

EXP-0032

## purpose

EXP-0031 の結果を正式評価するため、no_skip / skip_top10pct / skip_top20pct を longer horizon（n_windows=18）で比較する。skip_top20pct の ROI 改善が期間を延ばしても再現するか、bet_count 減少を許容しても実運用で優位か、skip_top10pct が安定運用向きかを確認する。

## baseline

- 戦略: EXP-0015（top_n_ev_gap_filter, top_n=3, ev=1.20, ev_gap=0.07）
- sizing: confidence_weighted（ev_gap_high=0.11, normal_unit=0.5）
- 比較: no_skip, skip_top10pct, skip_top20pct
- n_windows: **18**（longer horizon）

## command

```bash
PYTHONPATH=. python3 -m kyotei_predictor.tools.run_exp0032_ev_high_skip_longer_horizon \
  --db-path kyotei_predictor/data/kyotei_races.sqlite \
  --n-windows 18
```

## results table (n_windows=18)

| variant        | ROI     | total_profit | max_drawdown | profit_per_1000_bets | bet_count |
|----------------|---------|--------------|--------------|----------------------|-----------|
| no_skip        | -10.06% | -224,720     | 250,770      | -9,952.17            | 22,580    |
| skip_top10pct  | **-5.03%**  | **-101,510** | **159,065** | **-4,973.3**         | 20,411    |
| skip_top20pct  | **-2.85%**  | **-51,160**  | **133,205** | **-2,811.76**        | 18,195    |

## 確認ポイント

1. **skip_top20pct の ROI 改善が期間延長で再現するか**  
   - 再現した。n_w=18 でも no_skip -10.06% に対し skip_top20pct -2.85% で、約 7.2%pt 改善。EXP-0031（n_w=12）と同様の順序（skip_top20pct > skip_top10pct > no_skip）で、longer horizon でも高EV帯除外の優位性が確認できた。

2. **bet_count 減少を許容しても実運用で優位か**  
   - 優位と判断。skip_top20pct は bet_count 18,195（no_skip 22,580 より約 19% 減）だが、ROI・total_profit・max_drawdown・profit_per_1000_bets はいずれも no_skip より良好。損失・ドローダウン縮小と効率改善が両立している。

3. **skip_top10pct の方が安定運用向きか**  
   - skip_top10pct は bet_count 20,411 で skip_top20pct より多く、ROI -5.03% は no_skip より大幅改善しつつ skip_top20pct よりは悪化。実運用で「bet 数は多めに取りたい」場合は skip_top10pct、「ROI とリスクを最優先」なら skip_top20pct の選択が妥当。

## conclusion

- longer horizon（n_w=18）でも高EV帯除外の有効性は再現した。EXP-0031 の結論を支持する。
- 採用判断: **adopt**（EXP-0031 の正式評価として longer horizon でも adopt を維持）。

## judgment

- **adopt / hold / reject**: **adopt**
- 理由: n_windows=18 でも skip_top20pct が最良 ROI・最小損失・最小 drawdown を達成。実運用では skip_top20pct を推奨し、bet 数重視時は skip_top10pct を選択肢とする。

## result JSON

outputs/ev_high_skip_experiments/exp0032_ev_high_skip_longer_horizon_results.json
