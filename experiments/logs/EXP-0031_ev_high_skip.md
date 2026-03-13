# Experiment: EXP-0031 高EV帯除外（EXP-0015 + confidence_weighted 前提）

## experiment id

EXP-0031

## purpose

EXP-0015 条件 + confidence_weighted_sizing を前提に、高EV帯除外（EV percentile 上位 10% skip / 20% skip / skip なし）を比較する。EXP-0027 の示唆「高EV帯が損失源」が実装で有効か、weighted 維持のまま ROI 改善と損失・drawdown 縮小が両立するかを検証する。

## background

- ベースライン: EXP-0015（top_n_ev_gap_filter, top_n=3, ev=1.20, ev_gap=0.07）+ confidence_weighted（ev_gap_high=0.11, normal_unit=0.5）
- EXP-0027 で EV percentile 分析により高EV帯（top 1〜20%）が損失源と判明。本実験で「日付ごとにその日のレースを EV 順に並べ、上位 N% をベット対象から除外」する条件を評価する。

## baseline

- model: xgboost, calibration: sigmoid, features: extended_features, seed: 42, n_windows: 12
- 戦略: EXP-0015 + confidence_weighted（ev_gap_high=0.11, normal_unit=0.5）
- 比較: ev_skip_top_pct = 0（なし）, 0.1（10% skip）, 0.2（20% skip）

## command

```bash
PYTHONPATH=. python3 -m kyotei_predictor.tools.run_exp0031_ev_high_skip \
  --db-path kyotei_predictor/data/kyotei_races.sqlite \
  --n-windows 12
```

## results table

| variant        | ROI     | total_profit | max_drawdown | profit_per_1000_bets | bet_count |
|----------------|---------|--------------|--------------|----------------------|-----------|
| no_skip        | -14.20% | -206,545     | 232,595      | -14,045.9            | 14,705    |
| skip_top10pct  | **-9.69%**  | **-127,405** | **159,065** | **-9,572.13**        | 13,310    |
| skip_top20pct  | **-8.85%**  | **-103,665** | **133,205** | **-8,732.63**        | 11,871    |

## 解釈

- **ROI**: weighted 維持のまま高EV帯除外で大幅改善。no_skip -14.20% → skip_top10pct -9.69% → skip_top20pct -8.85%。EXP-0015 公式 -12.71% も本 run 内で上回る。
- **total_profit**: 損失幅が縮小（-206,545 → -127,405 → -103,665）。
- **max_drawdown**: 232,595 → 159,065 → 133,205 で改善。
- **profit_per_1000_bets**: -14,045.9 → -9,572.13 → -8,732.63 で改善。
- **bet_count**: 除外に伴い 14,705 → 13,310 → 11,871 に減少。
- **EXP-0027 の再現**: 高EV帯除外が有効であり、損失縮小と drawdown 改善が両立した。

## conclusion

- 高EV帯除外は EXP-0027 の示唆どおり有効。同一 run で no_skip より skip_top10pct / skip_top20pct が全指標で改善。
- 実運用では EXP-0015 + confidence_weighted + 高EV帯除外（10% または 20% skip）を推奨可能。

## judgment

- **adopt / hold / reject**: **adopt**
- 理由: ROI を大きく改善し、total_profit・max_drawdown・profit_per_1000_bets も改善。実運用候補として高EV帯除外（skip_top10pct または skip_top20pct）を採用する。

## result JSON

outputs/confidence_weighted_sizing_experiments/exp0031_ev_high_skip_results.json
