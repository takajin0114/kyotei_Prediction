# EXP-0063: Selected Race EV Filter Experiment

## 実験目的

EXP-0062 では race_ev = Σ(prob×odds) を**全120通り**で計算したため理論的に≈1となりフィルタとして機能しなかった。今回は**実際に賭ける bet**（d_hi475 で選ばれる bet）のみで **race_selected_ev** を計算し、レースをフィルタした場合の効果を評価する。

- race_selected_ev = Σ(selected_prob × odds)（selected = d_hi475 通過 bet）

## 実装内容

- 予測・オッズは既存と同様に DB/repo から取得。
- 各レースで `_all_bets_for_race` → d_hi475 でフィルタした **selected** に対して race_selected_ev = Σ(prob × odds) を算出。
- 5 条件: CASE0（なし）、CASE1≥1.05、CASE2≥1.10、CASE3≥1.15、CASE4≥1.20。
- 通過レースに d_hi475 + switch_dd4000 を適用。n_windows=12。

## 実験条件

| 項目 | 値 |
|------|-----|
| n_windows | 12 |
| 戦略 | d_hi475 + switch_dd4000 |
| 予測 | outputs/ev_cap_experiments/rolling_roi_predictions |
| DB | kyotei_races.sqlite |
| train_days / test_days / step_days | 30 / 7 / 7 |

## 結果表（n_windows=12）

| variant | ROI | total_profit | max_drawdown | profit_per_1000_bets | bet_count | longest_losing_streak |
|---------|-----|--------------|--------------|----------------------|-----------|------------------------|
| CASE0_baseline | 3.29% | 934 | 7,766 | 2,865.03 | 326 | 3 |
| CASE1_race_selected_ev_ge_105 | 11.31% | 2,942 | 6,178 | 9,872.48 | 298 | 3 |
| CASE2_race_selected_ev_ge_110 | 11.31% | 2,942 | 6,178 | 9,872.48 | 298 | 3 |
| CASE3_race_selected_ev_ge_115 | 11.31% | 2,942 | 6,178 | 9,872.48 | 298 | 3 |
| CASE4_race_selected_ev_ge_120 | 11.31% | 2,942 | 6,178 | 9,872.48 | 298 | 3 |

## 考察

- **Selected Race EV フィルタは有効**: CASE1（race_selected_ev≥1.05）以降で、CASE0 比べて ROI 3.29%→11.31%、total_profit 934→2,942、max_drawdown 7,766→6,178、profit_per_1000_bets 2,865→9,872 と改善。bet_count は 326→298 に減少。
- CASE1〜CASE4 は同一結果（対象期間で race_selected_ev≥1.05 を満たすレースが閾値 1.20 以下でほぼ同じ集合だったと解釈）。閾値の差は n_w 拡大や別期間で再評価すると出る可能性がある。
- **採用判断**: race_selected_ev≥1.05 をレースフィルタとして採用する価値あり。実運用では CASE1（1.05）を推奨し、n_w=24/30/36 での頑健性確認を推奨。

---

- 実行コマンド: `python3 -m kyotei_predictor.tools.run_exp0063_selected_race_ev_filter --n-windows 12`
- 結果 JSON: `outputs/selected_race_ev_filter/exp0063_selected_race_ev_filter_results.json`
