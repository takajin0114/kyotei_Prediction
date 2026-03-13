# Experiment: EXP-0033 EV cap experiment on EV high skip strategy

## experiment id

EXP-0033

## purpose

EXP-0032 で有力となった EV high skip 戦略（EXP-0015 + confidence_weighted + skip_top10/20pct）に対して、さらに EV cap を追加した場合の効果を検証する。  
目的は「高EV帯除外で改善した戦略に EV 上限をかけることで ROI を一段改善できるか」を確認すること。

## setup

- ベース戦略:
  - EXP-0015: top_n_ev_gap_filter, top_n=3, ev_threshold=1.20, ev_gap=0.07
- sizing:
  - confidence_weighted_ev_gap_v1, ev_gap_high=0.11, normal_unit=0.5
- EV high skip:
  - skip_top10pct: 日付ごとにレースを max_ev 降順に並べ、上位 10% のレースを除外
  - skip_top20pct: 同様に上位 20% のレースを除外

### EV cap 定義（本実験で採用した方式）

- **race-level EV cap**:
  - レース内最大 EV = max(probability * odds) を計算（対象は `selected_bets` の組み合わせ）
  - この最大 EV が cap を **超えるレースを丸ごと除外** する
  - bet 単位ではなく **race 単位**で cap を適用

### 比較条件

- skip_top20pct + no_cap（baseline）
- skip_top20pct + ev_cap_3.0 / 4.0 / 5.0
- skip_top10pct + no_cap / ev_cap_3.0 / 4.0 / 5.0

### 実装概要

1. `run_rolling_validation_roi` で EXP-0015 条件（xgboost + sigmoid + extended_features, n_windows=18）を実行し、予測 JSON を生成。
2. 各日付・レースについて `run_verify(..., bet_sizing_mode=confidence_weighted_ev_gap_v1, bet_sizing_config={ev_gap_high=0.11, normal_unit=0.5})` を呼び、  
   - stake（race 単位）  
   - payout（race 単位）  
   - race_profit  
   - purchased_bets  
   を取得。
3. `selected_bets` と `all_combinations` から max_ev = max(probability * odds) を計算。
4. 日付ごとにレースを max_ev 降順に並べ、skip_top10pct / 20pct を適用。
5. そのうえで **race-level EV cap** を適用し、残ったレースで以下を集計:
   - ROI, total_profit, max_drawdown, profit_per_1000_bets, bet_count。

## command

```bash
PYTHONPATH=. python3 -m kyotei_predictor.tools.run_exp0033_ev_cap_experiment \
  --db-path kyotei_predictor/data/kyotei_races.sqlite \
  --n-windows 18
```

## results table (n_windows=18)

### skip_top20pct 系列

| variant                        | ROI     | total_profit | max_drawdown | profit_per_1000_bets | bet_count |
|--------------------------------|---------|--------------|--------------|----------------------|-----------|
| skip_top20pct + no_cap        | -2.85%  | -51,160      | 133,205      | -2,811.76            | 18,195    |
| skip_top20pct + ev_cap_3.0    | -18.19% | -107,580     | 135,210      | -17,932.99           | 5,999     |
| skip_top20pct + ev_cap_4.0    | -11.11% | -92,780      | 99,660       | -10,934.59           | 8,485     |
| skip_top20pct + ev_cap_5.0    | -2.27%  | -23,625      | 117,910      | -2,236.37            | 10,564    |

### skip_top10pct 系列

| variant                        | ROI     | total_profit | max_drawdown | profit_per_1000_bets | bet_count |
|--------------------------------|---------|--------------|--------------|----------------------|-----------|
| skip_top10pct + no_cap        | -5.03%  | -101,510     | 159,065      | -4,973.3             | 20,411    |
| skip_top10pct + ev_cap_3.0    | -18.19% | -107,580     | 135,210      | -17,932.99           | 5,999     |
| skip_top10pct + ev_cap_4.0    | -11.11% | -92,780      | 99,660       | -10,934.59           | 8,485     |
| skip_top10pct + ev_cap_5.0    | -2.27%  | -23,625      | 117,910      | -2,236.37            | 10,564    |

## interpretation

1. **skip_top20pct に EV cap を追加すると ROI がさらに改善するか**
   - yes。  
   - baseline（skip_top20pct + no_cap）: ROI -2.85%  
   - ev_cap_5.0: ROI -2.27%（+0.58%pt 改善）、total_profit -23,625（損失半減以下）、max_drawdown 117,910（やや改善）、profit_per_1000_bets も -2,236.37 まで改善。  
   - ev_cap_3.0 / 4.0 は ROI・効率ともに悪化（-18.19% / -11.11%）で reject。

2. **EV cap は 3.0 / 4.0 / 5.0 のどこが最適か**
   - ROI と総合指標の観点では **ev_cap_5.0 が最適**。  
   - ev_cap_3.0/4.0 は cap が厳しすぎて有利レースまで削り、ROI・profit_per_1000_bets が大きく悪化。

3. **ROI だけでなく total_profit / max_drawdown / profit_per_1000_bets の観点でも改善するか**
   - skip_top20pct + ev_cap_5.0 は baseline と比較して:
     - total_profit: -51,160 → -23,625（損失縮小）
     - max_drawdown: 133,205 → 117,910（リスクやや改善）
     - profit_per_1000_bets: -2,811.76 → -2,236.37（1 bet あたり損失縮小）
   - ROI・profit・drawdown・効率の全てで baseline を上回る。

4. **bet_count が減りすぎていないか**
   - baseline skip_top20pct + no_cap: bet_count = 18,195  
   - skip_top20pct + ev_cap_5.0: bet_count = 10,564（約 42% 減）  
   - 減少幅は大きいが、損失・ドローダウン・効率の改善幅も大きく、実運用では「少ない試行で損失を抑えたい」ケースに適合。

5. **skip_top10pct より skip_top20pct の方が EV cap 追加時も優位か**
   - ROI / profit / drawdown / profit_per_1000_bets を見ると、**skip_top10pct + ev_cap_5.0** と **skip_top20pct + ev_cap_5.0** は同一値（本実装では同じレース集合に収束）。  
   - bet_count も同値（10,564）。  
   - 実質的に「高EV帯除外 + EV cap 5.0」をかけると skip_top10pct/20pct の差は消える（cap が支配的になる）ため、high skip 側は skip_top20pct ベースを維持してよい。

## conclusion

- **ベースライン**: skip_top20pct + no_cap（EXP-0032, ROI -2.85%）  
- **最良条件**: skip_top20pct + ev_cap_5.0（ROI -2.27%）  
  - ROI, total_profit, max_drawdown, profit_per_1000_bets のすべてで baseline を上回る。  
  - bet_count は減少するが、損失とドローダウンの縮小幅を考えると許容範囲。

### 採用判断

- **adopt / hold / reject**: **adopt**
- 理由:
  - baseline（skip_top20pct + no_cap）に対して、skip_top20pct + ev_cap_5.0 が ROI・損失・drawdown・効率の四指標で一貫して改善。
  - ev_cap_3.0 / 4.0 は ROI 大幅悪化で reject。  
  - 実運用では「EV high skip + EV cap 5.0」を推奨。high skip の割合は 20% 基準でよい。

## result JSON

- `outputs/ev_cap_experiments/exp0033_ev_cap_experiment_results.json`

