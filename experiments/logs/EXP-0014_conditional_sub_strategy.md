# Experiment: EXP-0014 条件別サブ戦略化（pred_prob_gap 帯）

## experiment id

EXP-0014

## purpose

全レース一律の selection ではなく、**レース条件（pred_prob_gap 帯）ごとに top_n / ev_threshold を切り替える**実験。pred_prob_gap = 1位と2位の予測確率差。説明可能性と実装負荷のバランスから pred_prob_gap 帯を採用。ベースライン top_n_ev (top_n=3, ev=1.18) と比較し ROI 改善を図る。

## configuration

- model: xgboost, calibration: sigmoid, features: extended_features
- n_windows: 12, seed: 42
- tool: `kyotei_predictor.tools.run_conditional_sub_strategy_experiment`
- output: outputs/conditional_sub_strategy_experiments/exp0014_conditional_results.json

### ベースライン

- top_n_ev: top_n=3, ev_threshold=1.18（-14.54%, n_w=12）

### 条件別サブ戦略（top_n_ev_conditional_prob_gap）

- band_edges で pred_prob_gap を帯に分割し、各帯に (top_n, ev_threshold) を指定。
- パターン: condpg_03_07, condpg_04_08, condpg_05_10, condpg_03_07_strict_high, condpg_02_06

## command

```bash
PYTHONPATH=. python3 -m kyotei_predictor.tools.run_conditional_sub_strategy_experiment \
  --db-path kyotei_predictor/data/kyotei_races.sqlite \
  --n-windows 12 \
  --seed 42
```

## results

| strategy_name | condition_definition | overall_roi_selected | total_selected_bets | hit_rate_rank1_pct | baseline_diff_roi |
|---------------|----------------------|---------------------|---------------------|---------------------|---------------------|
| baseline_top_n_ev | — | **-14.54%** | 15,407 | 4.78% | 0.0% |
| condpg_03_07 | [0.03, 0.07], (2,1.20)/(3,1.18)/(3,1.18) | -15.64% | 14,219 | 4.70% | -1.1% |
| condpg_04_08 | [0.04, 0.08], (2,1.20)/(3,1.18)/(3,1.18) | -16.03% | 14,058 | 4.68% | -1.49% |
| condpg_05_10 | [0.05, 0.10], (2,1.20)/(3,1.18)/(3,1.18) | -16.27% | 13,944 | 4.67% | -1.73% |
| condpg_03_07_strict_high | [0.03, 0.07], (2,1.20)/(3,1.18)/(3,1.15) | -15.64% | 14,219 | 4.70% | -1.1% |
| condpg_02_06 | [0.02, 0.06], (2,1.20)/(3,1.18)/(3,1.18) | -16.31% | 14,423 | 4.72% | -1.77% |

## baseline comparison

- ベースライン top_n_ev top_n=3 ev=1.18: **-14.54%**（n_w=12）
- 条件別サブ戦略の**全パターンがベースラインを下回った**（-1.1%pt 〜 -1.77%pt）。ベースラインを**上回った条件はなし**。

## conclusion

- **実行完了**: 実験実行済み。結果 JSON: outputs/conditional_sub_strategy_experiments/exp0014_conditional_results.json。
- **結論**: pred_prob_gap 帯による条件別サブ戦略は**採用見送り**。現行ベースライン（top_n_ev 3/1.18）のままが最良。曖昧帯で top_n=2 / ev=1.20 に厳格化すると bet 数は減るが ROI は悪化した。

## learning

- pred_prob_gap で帯分けし「曖昧なレースは厳しめの (top_n, ev)」にしても、このデータ・window では ROI 改善に寄与しなかった。
- 条件別化の他の切り口（entropy 帯・1位候補オッズ帯・venue/race_class）は未実施。必要に応じて別実験で検証可能。

## next action

- 採用しない。leaderboard には履歴として追記。
- 現行ベスト戦略（EXP-0013 top_n_ev_gap_filter または ベースライン top_n_ev）を維持。
- 他の条件軸（entropy 帯など）の実験は優先度を下げ、必要時に実施。
