# Experiment: EXP-0017 EV gap + entropy filter

## experiment id

EXP-0017

## purpose

EV gap 系（top_n_ev_gap_filter）に **entropy filter** を追加検証する。  
条件: skip if race_entropy > threshold。高エントロピー（予測がばらつく）レースを除外し ROI 改善を図る。

## configuration

- model: xgboost, calibration: sigmoid, features: extended_features
- strategy: top_n_ev_gap_filter（ベースライン）、top_n_ev_gap_filter_entropy（entropy 付き）
- top_n: 3, ev_threshold: 1.20, ev_gap_threshold: 0.07（EXP-0015 ベストと同一）
- n_windows: 12, seed: 42
- tool: `kyotei_predictor.tools.run_ev_gap_entropy_experiment`
- output: outputs/ev_gap_experiments/exp0017_ev_gap_entropy_results.json

### ベースライン

- top_n_ev_gap_filter（entropy なし）: ev=1.20, ev_gap=0.07 → **-12.71%**, selected_bets=14,700

### entropy_threshold 候補

- 1.2, 1.3, 1.4, 1.5（skip if race_entropy > threshold）

## command

```bash
PYTHONPATH=. python3 -m kyotei_predictor.tools.run_ev_gap_entropy_experiment \
  --db-path kyotei_predictor/data/kyotei_races.sqlite \
  --n-windows 12 \
  --seed 42
```

## results

| strategy_name | entropy_threshold | ev_threshold | ev_gap_threshold | overall_roi_selected | total_selected_bets | hit_rate_rank1_pct | baseline_diff_roi |
|---------------|-------------------|--------------|------------------|---------------------|---------------------|---------------------|-------------------|
| baseline_evgap_top3ev120_evgap0x07 | — | 1.20 | 0.07 | **-12.71%** | 14,700 | 4.35% | 0.0% |
| evgap_ent_1x2_top3ev120_evgap0x07 | 1.2 | 1.20 | 0.07 | -21.28% | 1,529 | 1.02% | -8.57% |
| evgap_ent_1x3_top3ev120_evgap0x07 | 1.3 | 1.20 | 0.07 | -21.41% | 1,621 | 1.08% | -8.70% |
| evgap_ent_1x4_top3ev120_evgap0x07 | 1.4 | 1.20 | 0.07 | -19.06% | 1,703 | 1.14% | -6.35% |
| evgap_ent_1x5_top3ev120_evgap0x07 | 1.5 | 1.20 | 0.07 | -19.81% | 1,801 | 1.21% | -7.10% |

## baseline comparison

- ベースライン（EV gap のみ）: **-12.71%**（n_w=12）, 14,700 bets
- entropy filter を追加した全条件（ent=1.2〜1.5）で **ベースラインを下回った**。最良でも ent=1.4 で -19.06%（-6.35%pt）。bet 数も 1,529〜1,801 に激減し、レース skip が過多。

## conclusion

- **実行完了**: 実験実行済み。結果 JSON: outputs/ev_gap_experiments/exp0017_ev_gap_entropy_results.json。
- **結論**: EV gap + entropy filter は **採用見送り（reject）**。entropy でレースを追加 skip すると bet 数が減りすぎ、ROI も悪化。現行ベストは EXP-0015（top_n_ev_gap_filter, ev=1.20, ev_gap=0.07）のまま維持。

## learning

- race_entropy > threshold で skip すると、通過レースが少なくなり bet 数が 1/10 以下に。その結果、分散が大きくなり ROI が -19%〜-21% に悪化。EV gap のみのフィルタが現時点では最良。

## next action

- 採用見送り: EXP-0017。1 位は EXP-0015 のまま。
- 他軸（別の entropy 定義・閾値の緩い範囲など）は必要に応じて検討。
