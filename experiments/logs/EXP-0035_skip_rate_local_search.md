# Experiment: EXP-0035 high EV skip 率局所探索（ev_cap_5.0 固定）

## experiment id

EXP-0035

## purpose

EXP-0033/0034 のベスト条件「skip_top20pct + ev_cap_5.0」が本当に最適か、skip 率を 10%〜30% で動かしたときに ROI / total_profit / max_drawdown をさらに改善できるかを確認する。

## setup

- ベース: EXP-0015 + confidence_weighted（ev_gap_high=0.11, normal_unit=0.5）
- EV cap: **ev_cap_5.0 固定**（race-level、max_ev > 5.0 のレースを除外）
- 比較: skip_top10pct / 15pct / 20pct / 25pct / 30pct

- n_windows: 18
- 予測: outputs/ev_cap_experiments/rolling_roi_predictions を利用

## command

```bash
cd /path/to/kyotei_Prediction
python3 -m kyotei_predictor.tools.run_exp0035_skip_rate_local_search \
  --db-path kyotei_predictor/data/kyotei_races.sqlite \
  --n-windows 18
```

## results table (n_windows=18, ev_cap_5.0)

| skip_variant   | ROI     | total_profit | max_drawdown | profit_per_1000_bets | bet_count |
|----------------|---------|--------------|--------------|----------------------|-----------|
| skip_top10pct  | -2.27%  | -23,625      | 117,910      | -2,236.37            | 10,564    |
| skip_top15pct  | -2.27%  | -23,625      | 117,910      | -2,236.37            | 10,564    |
| skip_top20pct  | -2.27%  | -23,625      | 117,910      | -2,236.37            | 10,564    |
| skip_top25pct  | -2.27%  | -23,625      | 117,910      | -2,236.37            | 10,564    |
| skip_top30pct  | -2.27%  | -23,625      | 117,910      | -2,236.37            | 10,564    |

**全条件で同一結果。**

## interpretation

1. **skip 率を変えても結果が同じ理由**
   - ev_cap_5.0 をかけた時点で、max_ev > 5.0 のレースはすべて除外される。本データでは、cap 通過レース（max_ev ≤ 5.0）が、どの skip 率（10%〜30%）で残す「上位 N% 除外」の対象外に収まっていると解釈できる。つまり **ev_cap が支配的**で、10%〜30% の skip では「残すレース集合」が変わらなかった。

2. **skip_top20pct が最適か**
   - 本実験の範囲では 10〜30% はすべて同性能のため、**差は出ていない**。実運用候補は従来どおり skip_top20pct + ev_cap_5.0 でよい。

3. **25% / 30% で改善するか**
   - 本 run では 20% と同一。改善は確認されず。

4. **15% で bet_count を維持しつつ改善するか**
   - 本 run では 20% と同一。bet_count も指標も差なし。

## judgment

- **reject**（実運用条件の変更は行わない）
- 10%〜30% の skip 率では全条件同一結果。ev_cap_5.0 が支配的であり、skip 率の局所探索ではベスト更新なし。実運用は **skip_top20pct + ev_cap_5.0**（EXP-0033/0034 ベスト）を維持する。

## result JSON

- outputs/high_ev_skip_experiments/exp0035_skip_rate_local_search_results.json
