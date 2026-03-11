# Experiment: EXP-0022 venue 別 ev ・ ev_gap 戦略（top_n_ev_gap_venue）

## experiment id

EXP-0022

## purpose

top_n_ev_gap_filter をベースに会場ごとに ev と ev_gap を変更する top_n_ev_gap_venue 戦略を評価し、ROI 改善を検証する。

## background

- 現行ベスト: EXP-0015（top_n=3, ev=1.20, ev_gap=0.07, ROI -12.71%）。
- 会場ごとに予測・オッズ特性が異なるため、会場別に ev と ev_gap の両方を設定（venue_config）し、ベット選定を最適化する。

## config

- model: xgboost, calibration: sigmoid, features: extended_features
- strategy: top_n_ev_gap_filter（ベースライン）、top_n_ev_gap_venue（会場別 ev ・ ev_gap）
- top_n: 3, デフォルト ev: 1.20, デフォルト ev_gap: 0.07
- venue_config（会場別 ev ・ ev_gap）:
  - TODA: ev=1.23, ev_gap=0.07
  - HEIWAJIMA: ev=1.21, ev_gap=0.07
  - SUMINOE: ev=1.18, ev_gap=0.07
- n_windows: 12, seed: 42
- tool: `kyotei_predictor.tools.run_venue_strategy_experiment`
- output: outputs/venue_strategy_experiments/exp0022_venue_strategy_results.json

## command

```bash
PYTHONPATH=. python3 -m kyotei_predictor.tools.run_venue_strategy_experiment \
  --db-path kyotei_predictor/data/kyotei_races.sqlite \
  --n-windows 12
```

## results

| strategy_name | strategy | overall_roi_selected | total_selected_bets | hit_rate_rank1_pct | baseline_diff_roi |
|---------------|----------|----------------------|---------------------|--------------------|-------------------|
| baseline_evgap_0x07_top3ev120 | top_n_ev_gap_filter | -14.68% | 14,705 | 4.50% | -1.97% |
| venue_ev120_evgap0x07 | top_n_ev_gap_venue | **-14.58%** | 14,699 | 4.51% | -1.87% |

## best candidate

- strategy_name: **venue_ev120_evgap0x07**
- strategy: top_n_ev_gap_venue
- top_n: 3, デフォルト ev: 1.20, ev_gap: 0.07
- venue_config: TODA ev=1.23/ev_gap=0.07, HEIWAJIMA ev=1.21/ev_gap=0.07, SUMINOE ev=1.18/ev_gap=0.07
- overall_roi_selected: **-14.58%**
- total_selected_bets: 14,699
- hit_rate_rank1_pct: 4.51%

## learning

- 会場別に ev と ev_gap を設定する top_n_ev_gap_venue により、同一 run ベースライン（-14.68%）より **+0.10%pt 改善**（-14.58%）。
- EXP-0015 公式ベスト -12.71% には今回の run では未達。会場別パラメータの追加チューニングや他会場の拡張は今後の検討課題。
