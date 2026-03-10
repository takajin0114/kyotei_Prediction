# Experiment: EXP-0021 top_n × ev × ev_gap 局所探索（top_n_ev_gap_filter）

## experiment id

EXP-0021

## purpose

EXP-0015 周辺の局所探索を **top_n も含めて** 再実施する。現行ベスト -12.71% を上回る条件があるか確認する。

## background

- 現行ベスト: EXP-0015（top_n=3, ev=1.20, ev_gap=0.07, ROI -12.71%）。
- EXP-0016 では ev × ev_gap のみの近傍探索（top_n=3 固定）で同点 -12.71% が最良だった。
- EXP-0020 では max_bets_per_race を直接適用しても差なし。
- 今回は top_n を 2, 3, 4 に広げたグリッドで探索する。

## configuration

- model: xgboost, calibration: sigmoid, features: extended_features
- strategy: top_n_ev_gap_filter
- n_windows: 12, seed: 42
- tool: `kyotei_predictor.tools.run_ev_gap_topn_local_search_experiment`
- output: outputs/ev_gap_experiments/exp0021_ev_gap_topn_local_search_results.json

## search grid

- top_n: 2, 3, 4
- ev_threshold: 1.19, 1.20, 1.21
- ev_gap_threshold: 0.06, 0.07, 0.08
- 計 3 × 3 × 3 = **27 条件**（EXP-0015 条件 top_n=3, ev=1.20, ev_gap=0.07 を含む）

## command

```bash
PYTHONPATH=. python3 -m kyotei_predictor.tools.run_ev_gap_topn_local_search_experiment \
  --db-path kyotei_predictor/data/kyotei_races.sqlite \
  --n-windows 12 \
  --seed 42
```

## results

| strategy_name | top_n | ev_threshold | ev_gap_threshold | overall_roi_selected | total_selected_bets | hit_rate_rank1_pct | baseline_diff_roi |
|---------------|-------|--------------|------------------|----------------------|---------------------|---------------------|-------------------|
| evgap_0x06_top2ev119 | 2 | 1.19 | 0.06 | -13.75% | 12,533 | 4.40% | -1.04% |
| evgap_0x07_top2ev119 | 2 | 1.19 | 0.07 | -14.13% | 12,463 | 4.37% | -1.42% |
| evgap_0x08_top2ev119 | 2 | 1.19 | 0.08 | -13.79% | 12,394 | 4.35% | -1.08% |
| evgap_0x06_top2ev120 | 2 | 1.20 | 0.06 | -13.58% | 12,487 | 4.38% | -0.87% |
| evgap_0x07_top2ev120 | 2 | 1.20 | 0.07 | -13.95% | 12,417 | 4.35% | -1.24% |
| evgap_0x08_top2ev120 | 2 | 1.20 | 0.08 | -13.62% | 12,348 | 4.33% | -0.91% |
| evgap_0x06_top2ev121 | 2 | 1.21 | 0.06 | -13.31% | 12,439 | 4.37% | -0.60% |
| evgap_0x07_top2ev121 | 2 | 1.21 | 0.07 | -13.68% | 12,369 | 4.34% | -0.97% |
| evgap_0x08_top2ev121 | 2 | 1.21 | 0.08 | -13.35% | 12,301 | 4.32% | -0.64% |
| evgap_0x06_top3ev119 | 3 | 1.19 | 0.06 | -16.75% | 14,835 | 4.46% | -4.04% |
| evgap_0x07_top3ev119 | 3 | 1.19 | 0.07 | -15.71% | 14,763 | 4.44% | -3.00% |
| evgap_0x08_top3ev119 | 3 | 1.19 | 0.08 | -14.55% | 14,683 | 4.50% | -1.84% |
| evgap_0x06_top3ev120 | 3 | 1.20 | 0.06 | -13.03% | 14,780 | 4.38% | -0.32% |
| evgap_0x07_top3ev120 | 3 | 1.20 | 0.07 | **-12.71%** | 14,700 | 4.35% | **0.00%** |
| evgap_0x08_top3ev120 | 3 | 1.20 | 0.08 | -14.31% | 14,621 | 4.49% | -1.60% |
| evgap_0x06_top3ev121 | 3 | 1.21 | 0.06 | -14.07% | 14,717 | 4.53% | -1.36% |
| evgap_0x07_top3ev121 | 3 | 1.21 | 0.07 | -14.35% | 14,640 | 4.50% | -1.64% |
| evgap_0x08_top3ev121 | 3 | 1.21 | 0.08 | -13.99% | 14,557 | 4.48% | -1.28% |
| evgap_0x06_top4ev119 | 4 | 1.19 | 0.06 | -18.42% | 16,925 | 4.63% | -5.71% |
| evgap_0x07_top4ev119 | 4 | 1.19 | 0.07 | -18.63% | 16,837 | 4.60% | -5.92% |
| evgap_0x08_top4ev119 | 4 | 1.19 | 0.08 | -18.27% | 16,739 | 4.58% | -5.56% |
| evgap_0x06_top4ev120 | 4 | 1.20 | 0.06 | -18.18% | 16,853 | 4.61% | -5.47% |
| evgap_0x07_top4ev120 | 4 | 1.20 | 0.07 | -18.39% | 16,765 | 4.58% | -5.68% |
| evgap_0x08_top4ev120 | 4 | 1.20 | 0.08 | -18.02% | 16,667 | 4.56% | -5.31% |
| evgap_0x06_top4ev121 | 4 | 1.21 | 0.06 | -17.83% | 16,772 | 4.61% | -5.12% |
| evgap_0x07_top4ev121 | 4 | 1.21 | 0.07 | -18.05% | 16,685 | 4.57% | -5.34% |
| evgap_0x08_top4ev121 | 4 | 1.21 | 0.08 | -17.68% | 16,588 | 4.56% | -4.97% |

## best candidate

- strategy_name: **evgap_0x07_top3ev120**
- strategy: top_n_ev_gap_filter
- top_n: 3
- ev_threshold: 1.20
- ev_gap_threshold: 0.07
- overall_roi_selected: **-12.71%**
- total_selected_bets: 14,700
- hit_rate_rank1_pct: 4.35%
- baseline_diff_roi: **0.00%**（EXP-0015 ベースラインと同一）

## baseline comparison

- ベースライン EXP-0015 ベスト: top_n=3, ev=1.20, ev_gap=0.07 → **-12.71%**（n_w=12）, 14,700 bets
- EXP-0021 での最良条件（evgap_0x07_top3ev120）は **同一条件・同一 ROI -12.71%**。
- 他の組み合わせはすべて baseline_diff_roi < 0（ROI 悪化）であり、**ベースラインを上回る条件は存在しなかった**。

## conclusion

- **実行完了**: 実験実行済み。結果 JSON: `outputs/ev_gap_experiments/exp0021_ev_gap_topn_local_search_results.json`。
- **結論**:
  - top_n=2 系列: ROI は -13.31%〜-14.13% 程度で、EXP-0015 ベースライン（-12.71%）より悪化。
  - top_n=3 系列: EXP-0015 条件（ev=1.20, ev_gap=0.07）が引き続き最良 **-12.71%**。近傍の ev/ev_gap 変更では改善なし。
  - top_n=4 系列: ROI は -17.68%〜-18.63% と大幅に悪化。
  - **新しいベスト条件は見つからず、現行ベストは EXP-0015 のまま維持。EXP-0021 は採用見送り（reject）。**

## learning

- top_n を 2 に減らすと bet 数は減るが、ROI は -13% 台に留まり、EXP-0015 ベースライン（top_n=3）の -12.71% を下回る。
- top_n を 4 に増やすと bet 数は大きく増える一方で、ROI は -18% 前後まで悪化し、明確に劣化する。
- EXP-0016 と合わせて、top_n=3, ev=1.20, ev_gap=0.07 付近は **top_n/ev/ev_gap を多少動かしても改善が出ない局所最適**である可能性が高い。
- ROI 観点では、top_n/ev/ev_gap の単純なグリッド拡張よりも、別軸（モデル・特徴量・calibration・他戦略）を検討する余地が大きい。

## next action

- 現行ベスト戦略は引き続き **EXP-0015（top_n=3, ev=1.20, ev_gap=0.07, ROI -12.71%）** を採用。
- EXP-0021 は **「EXP-0015 周辺の top_n/ev/ev_gap の再探索では新ベストなし」** という結論として leaderboard / chat_context / project_status に反映済みとする。
- 次の候補としては、以下のような別軸の検討が妥当:
  - モデル・特徴量・calibration の改善（例: feature set 拡張の再設計・calibration の詳細比較）。
  - 条件別サブ戦略の別軸（entropy 帯・1位オッズ帯・venue/race_class）での再検討（pred_prob_gap 帯は EXP-0014 で見送り済み）。
  - ensemble 不具合修正後の再評価。
