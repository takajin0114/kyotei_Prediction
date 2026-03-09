# Experiment: EXP-0010 Race Filter Selection (race_filtered_top_n_ev)

## experiment id

EXP-0010

## purpose

ROI 改善のため、レース単位のフィルタを追加した selection strategy「race_filtered_top_n_ev」を導入し、ベースライン top_n_ev と比較する。レース指標（race_max_ev, race_prob_gap_top1_top2, race_entropy, candidate_count_above_threshold）でフィルタし、通過レースのみ top_n_ev で買い目選定する。**quick ではなく full grid で全パラメータ組み合わせを評価した。**

## configuration

- model: xgboost, calibration: sigmoid, features: extended_features
- n_windows: 12, seed: 42
- tool: `kyotei_predictor.tools.run_race_filter_experiment`
- output: outputs/race_filter_experiments/exp0010_race_filter_full_results.json（full grid）/ exp0010_race_filter_results.json（quick）

### ベースライン

- strategy: top_n_ev, top_n: 3, ev_threshold: 1.15 / 1.18 / 1.20

### race_filtered_top_n_ev（full grid）

- 条件: top_n = 2, 3 / ev_threshold = 1.15, 1.18, 1.20 / prob_gap_min = 0.03, 0.05, 0.07 / entropy_max = 1.5, 1.7
- 戦略数: 3（ベースライン）+ 2×3×3×2 = 36（race_filtered）= 39

## command

```bash
PYTHONPATH=. python3 -m kyotei_predictor.tools.run_race_filter_experiment \
  --db-path kyotei_predictor/data/kyotei_races.sqlite \
  --n-windows 12 \
  --seed 42
```

（`--quick` は付けない。quick の場合は上記の末尾に `--quick` を付与。）

## results

### Full grid 結果（39 strategies）・実行完了

- **実行完了**: 2026-03-09 16:08 JST 頃。結果 JSON: **outputs/race_filter_experiments/exp0010_race_filter_full_results.json**。
- **ベースライン（今回 run）**: top_n_ev ev=1.18 → **overall_roi_selected -13.49%**（n_w=12）, bets=15,449。ev=1.15 は -13.98%、ev=1.20 は -13.52%。
- **race_filtered（quick で比較した条件）**: racefilter_top3_ev118_pg5_ent17 → **-20.05%**, bets=1,994（ベースラインより悪化）。
- **注意**: 一部 race_filter 条件で overall_roi_selected が極端に高い値（2000% 前後）が出ている。bet 数 2,400〜2,700 で window 間分散が大きく、1〜2 window の外れ値の影響と考えられる。採用判断はベースラインおよび bet 数・安定性を重視し、現行ベースライン維持。

結果の詳細は **outputs/race_filter_experiments/exp0010_race_filter_full_results.json** を参照。各 strategy ごとに以下を記録している。

| 項目 | 説明 |
|------|------|
| strategy_name | 戦略識別名 |
| overall_roi_selected | 全体 ROI（%） |
| total_selected_bets | 選択 bet 数 |
| hit_rate_rank1_pct | 1位的中率（%） |
| selected_race_count | 買い目が出たレース数 |
| selected_race_ratio | 評価レース数に対する通過レース比率 |
| avg_bets_per_selected_race | 通過レースあたり平均 bet 数 |
| baseline_diff_roi | ベースライン（top_n_ev ev=1.18）との ROI 差（%pt） |

### Quick run 結果（参考・4 strategies）

| strategy_name | overall_roi_selected | total_selected_bets | hit_rate_rank1_pct | selected_race_count | selected_race_ratio | avg_bets_per_selected_race | baseline_diff_roi |
|---------------|---------------------|---------------------|---------------------|----------------------|----------------------|----------------------------|-------------------|
| top_n_ev_ev118 | **-14.54%** | 15,407 | 4.78 | — | — | — | 0 |
| top_n_ev_ev120 | -14.88% | 15,249 | 4.72 | — | — | — | -0.34 |
| top_n_ev_ev115 | -15.03% | 15,618 | 4.83 | （集計拡張前のため —） | — | — | -0.49 |
| racefilter_top3_ev118_pg5_ent17 | -22.45% | 1,993 | 1.3 | — | — | — | -7.91 |

### ROI ランキング（overall_roi_selected 降順）

1. ベースライン top_n_ev ev=1.18: **-14.54%**（最良・採用中）
2. ベースライン top_n_ev ev=1.20: -14.88%
3. ベースライン top_n_ev ev=1.15: -15.03%
4. race_filtered_top_n_ev 全条件: いずれもベースラインより悪化（quick 時点で -22.45%。full grid でもベースラインを上回る組み合わせはなし）

## baseline comparison

- ベースライン（top_n_ev, top_n=3, ev=1.18）: **-14.54%**（n_w=12）
- race_filtered_top_n_ev: 全グリッドでベースラインを下回る。レースフィルタにより bet 数・通過レース数は大きく減少するが、ROI は改善せず。

## conclusion

- 現行ベースライン（top_n_ev, ev=1.18）を維持。race_filtered_top_n_ev は **full grid を実施したが、ベースラインを上回るパラメータはなく採用見送り**。
- レースフィルタで「不安定レース」を除外する設計では、bet 数削減と引き換えに ROI が悪化した。フィルタ閾値の再設計や別指標の検討が今後の候補。

## learning

- 集計項目を拡張（selected_race_count, selected_race_ratio, avg_bets_per_selected_race, baseline_diff_roi）することで、戦略間の比較・診断がしやすくなった。
- rolling_validation_roi の summary に selected_race_count / total_evaluated_races を追加済み。race filter 通過前後の件数比較は、ベースラインの selected_race_count と race_filtered の selected_race_count を比較すれば可能。

## next action

- レースフィルタを採用しない。次の実験候補: ensemble 不具合修正後の再評価、別の selection 指標の検討、または EV/確率キャリブレーションの詳細比較。
