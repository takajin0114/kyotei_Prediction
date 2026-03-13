# Experiment Leaderboard

このファイルは主要実験の比較表を管理する。

## ROI Leaderboard

- **正式 reference (n_w=12)**: 同一条件・n_windows=12 で比較した公式結果。
- **暫定 best (n_w=4 等)**: 少ない window 数のみで未確定。採用前に n_w=12 再評価を要する。

| Rank | Experiment ID | Model | Calibration | Features | Strategy | Parameters | overall_roi_selected | Notes |
|---|---|---|---|---|---|---|---|---|
| 1 | EXP-0015 | xgboost | sigmoid | extended_features | top_n_ev_gap_filter | top_n=3, ev=1.20, ev_gap=0.07 | **-12.71%** (n_w=12) | EV gap 局所探索で最良（adopt） |
| 2 | EXP-0013 | xgboost | sigmoid | extended_features | top_n_ev_gap_filter | top_n=3, ev=1.18, ev_gap=0.05 | **-13.81%** (n_w=12) | EV gap で曖昧レース skip（adopt） |
| 3 | EXP-0007 | xgboost | sigmoid | extended_features | top_n_ev | top_n=3, ev=1.18 | **-14.54%** (n_w=12) | EV 高解像度探索で最良（adopt） |
| - | EXP-0009 | xgboost | sigmoid | extended_features | top_n_ev_confidence | top_n=3, ev=1.15/1.18/1.20, conf=pred_prob/prob_gap/entropy | -26%〜-39% (n_w=12) | 採用見送り（現行 top_n_ev が優位） |
| - | EXP-0010 | xgboost | sigmoid | extended_features | race_filtered_top_n_ev | full grid: top_n=2,3 / ev=1.15,1.18,1.20 / pg=0.03,0.05,0.07 / ent=1.5,1.7 | 全条件でベースライン以下 (n_w=12) | レースフィルタ full grid 実施・ベースライン -14.54% を上回る組み合わせなし・採用見送り |
| - | EXP-0011 | xgboost | sigmoid | extended_features | top_n_ev_prob_pool | pool_k=3,5,8 / top_n=2,3 / ev=1.15,1.18,1.20 (n_w=12) | ベースライン超えず (n_w=12) | 確率上位K候補プール制限型。採用見送り。log: experiments/logs/EXP-0011_prob_pool_selection.md。 |
| - | EXP-0012 | xgboost | sigmoid | extended_features | top_n_ev_power_prob | alpha=0.7〜1.1 / top_n=2,3 / ev=1.15〜1.20 (n_w=12) | 結果は exp0012_power_prob_results.json 参照 | EV_adj=(prob^alpha)*odds。ベースライン比較は JSON の baseline_diff_roi。log: experiments/logs/EXP-0012_power_prob_ev.md。 |
| - | EXP-0014 | xgboost | sigmoid | extended_features | top_n_ev_conditional_prob_gap | pred_prob_gap 帯で (top_n,ev) 切替、複数パターン (n_w=12) | 全条件でベースライン -14.54% 以下 | 条件別サブ戦略化。採用見送り。log: experiments/logs/EXP-0014_conditional_sub_strategy.md。結果: outputs/conditional_sub_strategy_experiments/exp0014_conditional_results.json。 |
| - | EXP-0016 | xgboost | sigmoid | extended_features | top_n_ev_gap_filter | ev=1.19/1.20/1.21 × ev_gap=0.06/0.07/0.08 (n_w=12) | 最良 -12.71%（EXP-0015 と同点） | EXP-0015 ベスト近傍探索。ベスト更新なし。採用見送り。log: experiments/logs/EXP-0016_ev_gap_near_local_search.md。 |
| - | EXP-0017 | xgboost | sigmoid | extended_features | top_n_ev_gap_filter_entropy | ev=1.20, ev_gap=0.07, ent=1.2〜1.5 (n_w=12) | 最良 -19.06%（ent=1.4）, bets=1,703 | EV gap + entropy filter。全条件でベースライン -12.71% を下回り採用見送り。log: experiments/logs/EXP-0017_entropy_filter.md。 |
| - | EXP-0018 | xgboost | sigmoid | extended_features | top_n_ev_gap_filter_odds_band | ev=1.20, ev_gap=0.07, odds_low=1.2〜1.4, odds_high=20/25/30 (n_w=12) | 最良 -20.36%（odds_high=25）, bets=2,179 | EV gap + odds band filter。全条件でベースライン -12.71% を下回り採用見送り。log: experiments/logs/EXP-0018_odds_band_filter.md。 |
| - | EXP-0019 | xgboost | sigmoid | extended_features | top_n_ev_gap_filter_odds_band_bet_limit | ev=1.20, ev_gap=0.07, odds=1.3/25, max_bets_per_race=1/2 (n_w=12) | 最良 -14.25%（max=1）, bets=1,980 | odds_band に max_bets_per_race=1 で +6.11%pt 改善。全体1位は更新せず。odds_band 採用時は max=1 推奨。log: experiments/logs/EXP-0019_max_bet_limit.md。 |
| - | EXP-0020 | xgboost | sigmoid | extended_features | top_n_ev_gap_filter | ev=1.20, ev_gap=0.07, max_bets_per_race=None/1/2 (n_w=12) | 全条件 -12.71%（差なし） | EXP-0015 に max_bets_per_race を直接適用。改善なし。採用見送り。log: experiments/logs/EXP-0020_ev_gap_max_bets_per_race.md。 |
| - | EXP-0021 | xgboost | sigmoid | extended_features | top_n_ev_gap_filter | top_n=2,3,4 × ev=1.19,1.20,1.21 × ev_gap=0.06,0.07,0.08 (n_w=12) | 最良 -12.71%（top_n=3, ev=1.20, ev_gap=0.07） | EXP-0015 条件を含むグリッド再探索。top_n=2/4 系列はいずれも ROI 悪化、top_n=3 でも EXP-0015 ベースラインと同点止まりで**新ベストなし・採用見送り**。log: experiments/logs/EXP-0021_ev_gap_topn_local_search.md。 |
| - | EXP-0022 | xgboost | sigmoid | extended_features | top_n_ev_gap_venue_filter | top_n=3, ev=1.20, ev_gap=0.07, venue_ev_config={TODA:1.23, SUMINOE:1.17} (n_w=12) | 最良 -14.6%, bets=14,702 | 会場別 EV 閾値。同一 run ベースライン -14.68% より +0.08%pt 改善。EXP-0015 公式ベスト -12.71% は未達のため採用見送り。log: experiments/logs/EXP-0022_venue_filter.md。 |
| - | EXP-0022 | xgboost | sigmoid | extended_features | top_n_ev_gap_venue | top_n=3, ev=1.20, ev_gap=0.07, venue_config={TODA,HEIWAJIMA,SUMINOE} (n_w=12) | 最良 -14.58%, bets=14,699 | 会場別 ev・ev_gap。同一 run ベースライン -14.68% より +0.10%pt 改善。log: experiments/logs/EXP-0022_venue_strategy.md。 |
| - | EXP-0023 | xgboost | sigmoid | extended_features | top_n_ev_gap_filter + confidence_weighted_sizing | fixed vs ev_gap/prob_gap 2〜3段階 (n_w=12) | 最良 -14.31%（weighted_ev_gap_v1）, bets=14,705 | ROI は adopt 未達。利益指標（profit, drawdown, profit/1000bets）は fixed より改善。hold・実運用候補。log: experiments/logs/EXP-0023_confidence_weighted_fixed_sizing.md。 |
| - | EXP-0024 | xgboost | sigmoid | extended_features | top_n_ev_gap_filter + confidence_weighted_sizing (threshold sweep) | ev_gap_high=0.09/0.10/0.11, normal_unit=0.5/0.6/0.7 (n_w=12) | 最良 -14.20%（ev_gap_high=0.11, normal_unit=0.5）, bets=14,705 | 閾値スイープで 0.11 が最良。利益・drawdown・profit/1000bets 改善。hold・実運用推奨。log: experiments/logs/EXP-0024_confidence_weighted_sizing_threshold_sweep.md。 |
| - | EXP-0025 | xgboost | sigmoid | extended_features | confidence_weighted_sizing rollout (EXP-0015/0013/0007) | fixed vs weighted (ev_gap_high=0.11, normal_unit=0.5) (n_w=12) | 同一 run 最良 -13.61%（exp0013+weighted）, bets=14,994 | 3戦略とも weighted で ROI・profit・drawdown・profit/1000bets 改善。hold・実運用で全戦略に weighted 推奨。log: experiments/logs/EXP-0025_confidence_weighted_sizing_rollout.md。 |
| - | EXP-0026 | xgboost | sigmoid | extended_features | Kelly sizing (EXP-0015/0013/0007) | fixed vs confidence_weighted vs kelly_0.25/0.5/0.75 (n_w=12) | 最良 ROI は confidence_weighted -13.61%。Kelly は -22.6%〜-23% で ROI 悪化 | profit・drawdown は Kelly が小さい（リスク抑制）。efficiency は Kelly で 1bet あたり損失小。ROI 採用は reject、リスク目的で hold。log: experiments/logs/EXP-0026_kelly_sizing_experiment.md。 |
| - | EXP-0027 | xgboost | sigmoid | extended_features | EV percentile ROI analysis (EXP-0015/0013/0007) | top 1/5/10/20/50% / full by race EV (n_w=12) | 全帯で赤字。高EV帯（top1〜20%）が損失源、full が相対最良 | EV percentile 分析で有望 cutoff 候補を特定。高EV除外の次実験候補。log: experiments/logs/EXP-0027_ev_percentile_analysis.md。 |
| - | EXP-0028 | xgboost | sigmoid | extended_features | odds cap (EXP-0015/0013/0007) | odds_cap none / 30 / 50 / 80 (n_w=12) | 最良は none。cap で ROI 悪化 | 高EV帯損失原因の切り分け。高オッズ除外では ROI 改善せず。reject。log: experiments/logs/EXP-0028_odds_cap_experiment.md。 |
| - | EXP-0029 | xgboost | sigmoid vs isotonic | extended_features | probability calibration (EXP-0015/0013/0007) | baseline (sigmoid) vs calibrated (isotonic), n_w=12 | baseline が有利。isotonic で約5%pt悪化 | 確率キャリブレーション。isotonic は選別数約2倍・ROI 悪化。reject。log: experiments/logs/EXP-0029_probability_calibration.md。 |
| - | EXP-0030 | xgboost | sigmoid | extended_features | confidence_weighted formal baseline (EXP-0015) | fixed vs weighted (ev_gap_high=0.11, normal_unit=0.5), n_w=12 | 同一 run fixed -14.68%, weighted -14.20%, bets=14,705 | EXP-0015 条件で正式比較。weighted で ROI・profit・drawdown・profit/1000bets 改善。hold・実運用で fixed より weighted 推奨。log: experiments/logs/EXP-0030_confidence_weighted_formal_baseline.md。 |
| - | EXP-0031 | xgboost | sigmoid | extended_features | EV high skip (EXP-0015 + confidence_weighted) | no_skip / skip_top10pct / skip_top20pct, n_w=12 | 同一 run 最良 **-8.85%**（skip_top20pct）, bets=11,871 | 高EV帯除外で ROI・profit・drawdown 改善。adopt。log: experiments/logs/EXP-0031_ev_high_skip.md。 |
| - | EXP-0032 | xgboost | sigmoid | extended_features | EV high skip longer horizon (EXP-0015 + confidence_weighted) | no_skip / skip_top10pct / skip_top20pct, n_w=18 | 同一 run 最良 **-2.85%**（skip_top20pct）, bets=18,195 | longer horizon で skip_top20pct 優位再現。adopt。log: experiments/logs/EXP-0032_ev_high_skip_longer_horizon.md。 |
| - | EXP-0033 | xgboost | sigmoid | extended_features | EV high skip + EV cap (race-level) | skip_top10/20pct × ev_cap=none/3/4/5, n_w=18 | 最良 skip_top20pct+ev_cap_5.0: ROI **-2.27%**, profit=-23,625, max_dd=117,910, bets=10,564。EV cap 3/4 は ROI 悪化。adopt。log: experiments/logs/EXP-0033_ev_cap_experiment.md。 |
| - | EXP-0034 | xgboost | sigmoid | extended_features | EV cap 局所探索 (skip_top20pct 固定) | ev_cap=no_cap/4.5/5.0/5.5/6.0/6.5, n_w=18 | ev_cap_5.0 が最良のまま。4.5 は切りすぎ、5.5 以上は ROI・profit 悪化。reject。log: experiments/logs/EXP-0034_ev_cap_local_search.md。 |
| - | EXP-0035 | xgboost | sigmoid | extended_features | high EV skip 率局所探索 (ev_cap_5.0 固定) | skip_top10/15/20/25/30pct, n_w=18 | 全条件同一（ROI -2.27%、bets=10,564）。ev_cap が支配的で skip 率差なし。reject。log: experiments/logs/EXP-0035_skip_rate_local_search.md。 |
| - | EXP-0036 | xgboost | sigmoid | extended_features | EV帯ごとの成績分析 | EV帯別 bet_count/hit_rate/ROI/profit, n_w=18 | 黒字: 3–4, 4–5, 6–8。赤字: 5–6, >=10。ev_cap=5.0 の妥当性を支持。hold。log: experiments/logs/EXP-0036_ev_band_analysis.md。 |
| - | EXP-0037 | xgboost | sigmoid | extended_features | EV帯フィルタ戦略 | skip_top20pct + 3<=EV<5/4<=EV<5 等, n_w=18 | 最良 ev_band_3_5: ROI +18.71%, profit +83,955, max_dd 36,525。ev_band_4_5: ROI +33.78%。adopt。log: experiments/logs/EXP-0037_ev_band_strategy.md。 |
| - | EXP-0038 | xgboost | sigmoid | extended_features | EV band + probability フィルタ | skip_top20pct + 3<=EV<5 + prob>=0.05/0.08/0.10/0.12, n_w=18 | 最良 ev3_5_prob005: ROI +24.67%, profit +70,965, max_dd 18,940。adopt。log: experiments/logs/EXP-0038_ev_prob_band_strategy.md。 |
| - | EXP-0039 | xgboost | sigmoid | extended_features | EV band + prob + race内EV順位 | 3<=EV<5 + prob>=0.05 + rank≤3/≤5/2-5/2-7, n_w=18 | baseline と rank_le_3/5 は同一。rank_2_5/2_7 は bet 激減・赤字。reject。log: experiments/logs/EXP-0039_ev_prob_rank_strategy.md。 |
| - | EXP-0040 | xgboost | sigmoid | extended_features | ベットサイジング最適化 | 条件固定、unit=EV×prob cap 等, n_w=18 | 最良 size_by_ev_prob_capped: ROI +155.8%, profit +226,307。**参考値**（後段 stake 再計算のため過大評価。厳密値は EXP-0041）。log: experiments/logs/EXP-0040_bet_sizing_optimization.md。 |
| - | EXP-0041 | xgboost | sigmoid | extended_features | ベットサイジング厳密検証 | 条件固定、bet 単位で stake/payout 整合, n_w=18 | 全 variant 赤字。最良 baseline_fixed: ROI -4.39%, profit -9,210。**厳密再検証の正**。log: experiments/logs/EXP-0041_bet_sizing_verified.md。 |
| - | EXP-0042 | xgboost | sigmoid | extended_features | selection 条件厳密再検証 | stake=100 固定、selection のみ比較, n_w=18 | 最良 baseline_c（4≤EV<5）: ROI -5.17%, profit -8,410。次点 baseline_b（3≤EV<5+prob≥0.05）。log: experiments/logs/EXP-0042_selection_verified.md。 |
| 4 | EXP-0006 | xgboost | sigmoid | extended_features | top_n_ev | top_n=3, ev=1.20 | **-14.88%** (n_w=12) | **正式 reference**（従来 1 位） |
| 5 | EXP-0007 | xgboost | sigmoid | extended_features | top_n_ev | top_n=4, ev=1.05 | **-17.85%** (n_w=12) | top_n 局所探索で最良（hold） |
| 6 | EXP-0006 | xgboost | sigmoid | extended_features | top_n_ev | top_n=6, ev=1.00 | **-18.78%** (n_w=12) | 正式 reference 周辺の局所最適（adopt） |
| 7 | EXP-0006 | xgboost | sigmoid | extended_features | top_n_ev | top_n=3, ev=1.20 (grid) | -10.94% (n_w=6) | strategy grid; bet sizing capped_0.02 → -8.66% |
| 8 | EXP-0006 | xgboost | sigmoid | extended_features | top_n_ev | top_n=3, ev=1.25 (grid) | -11.15% (n_w=4) | **暫定 best**（n_w=4 のみ・未確定） |
| 9 | EXP-0006 | xgboost | sigmoid | extended_features | top_n_ev | top_n=6, ev=1.05 | -19.71% (n_w=12) | 正式 reference（top_n=6 系統・前回） |
| 10 | EXP-0005 | xgboost | sigmoid | extended_features | top_n_ev | top_n=6, ev=1.20 | -20.7% (n_w=12) | 旧 reference |
| 11 | EXP-0005 | lightgbm | sigmoid | extended_features | top_n_ev | - | -29.9% (n_w=12) | 安定性良好 |
| 12 | EXP-0004 | sklearn baseline | sigmoid | extended_features | top_n_ev | - | -27.7% (n_w=12) | sklearn reference |
| 13 | EXP-0001 | sklearn baseline | sigmoid | extended_features | top_n_ev | - | -28% | 旧 reference |
| - | EXP-0002 | sklearn baseline | sigmoid | extended_features_v2 | top_n_ev | - | -35% (n_w=2) | v2 比較・hold |
| - | EXP-0004 | sklearn baseline | sigmoid | extended_features_v2 | top_n_ev | - | -33.76% (n_w=12) | v2 正式比較・hold |

## EV Threshold Sweep (ev_threshold_only, EXP-0005)

| ev_threshold | overall_roi | mean_roi | median_roi | bet_count | profit | max_drawdown |
|---|---|---|---|---|---|---|
| 1.05 | -48.95% | -49.05 | -50.38 | 212614 | -10,406,510 | 10,406,510 |
| 1.10 | -49.56% | -49.65 | -49.48 | 204223 | -10,121,210 | 10,121,210 |
| 1.15 | -50.83% | -50.95 | -49.52 | 196230 | -9,974,130 | 9,974,130 |
| 1.20 | -51.23% | -51.49 | -51.53 | 188699 | -9,667,800 | 9,667,800 |
| 1.25 | -51.35% | -51.61 | -51.55 | 181616 | -9,325,560 | 9,325,560 |

## Bet Sizing 比較（正式表, n_w=12）

selection 条件ごとの bet sizing 比較。overall_roi_selected / profit / max_drawdown / total_selected_bets を記載。

### 条件: top_n=3, ev=1.18（EXP-0007）、EXP-0013 ev_gap=0.05（現2位 -13.81%）、EXP-0015 ev=1.20 ev_gap=0.07（現1位 -12.71%, selected_bets=14,700）

| bet_sizing | overall_roi_selected | profit | max_drawdown | total_selected_bets |
|------------|---------------------|--------|--------------|---------------------|
| fixed | -14.54% | -224,090 | 279,680 | 15,407 |
| half_kelly | -96.69% | -100,000 | 100,000 | 15,407 |
| capped_kelly_0.02 | -8.17% | -99,999.75 | 274,447 | 15,407 |
| capped_kelly_0.05 | -38.17% | -99,999.91 | 99,999.90 | 15,407 |

### 条件: top_n=3, ev=1.20（正式 reference）

| bet_sizing | overall_roi_selected | profit | max_drawdown | total_selected_bets |
|------------|---------------------|--------|--------------|---------------------|
| fixed | -14.88% | -226,920 | 283,570 | 15,249 |
| half_kelly | -96.69% | -100,000 | 100,000 | 15,249 |
| capped_kelly_0.02 | -8.66% | -99,999.76 | 247,197 | 15,249 |
| capped_kelly_0.05 | -38.11% | -99,999.90 | 99,999.90 | 15,249 |

### 条件: top_n=6, ev=1.00（正式 reference 周辺の局所最適）

| bet_sizing | overall_roi_selected | profit | max_drawdown | total_selected_bets |
|------------|---------------------|--------|--------------|---------------------|
| fixed | -18.78% | -453,890 | 487,750 | 24,172 |
| half_kelly | -96.79% | -100,000 | 100,000 | 24,172 |
| capped_kelly_0.02 | -23.51% | -99,999.76 | 99,999.76 | 24,172 |
| capped_kelly_0.05 | -47.70% | -99,999.90 | 99,999.90 | 24,172 |

### 条件: top_n=6, ev=1.05（EXP-0007 Task1）

| bet_sizing | overall_roi_selected | profit | max_drawdown | bet_count |
|------------|---------------------|--------|--------------|-----------|
| fixed | -19.71% | -462,310 | 493,400 | 23,461 |
| half_kelly | -96.79% | -100,000 | 100,000 | 23,461 |
| capped_kelly_0.02 | -23.92% | -99,999.75 | 99,999.75 | 23,461 |
| capped_kelly_0.05 | -48.01% | -99,999.91 | 99,999.91 | 23,461 |

運用は fixed を推奨（Kelly 系は資金制約で破綻リスクあり）。

## EXP-0008 Fractional Kelly / Calibration / Ensemble（n_w=12）

- **条件**: reference 固定（xgboost, top_n=3, ev=1.20）。詳細は experiments/logs/EXP-0008_fractional_kelly.md。

### Task1: Fractional Kelly（selection 固定、bet_count=15,249）

| kelly_cap | overall_roi_selected | profit | max_drawdown |
|-----------|---------------------|--------|--------------|
| 0.002 | -14.91% | -99,805 | 167,006 |
| 0.005 | -10.23% | -99,999 | 255,861 |
| 0.01 | **-6.99%** | -99,999 | 356,340 |
| 0.02 | -8.66% | -99,999 | 247,197 |

### Task2: Calibration comparison

| calibration | overall_roi_selected | profit | bet_count |
|-------------|---------------------|--------|-----------|
| none | -15.80% | -460,470 | 29,150 |
| sigmoid | **-14.88%** | -226,920 | 15,249 |

### Task3: Model comparison

| model | overall_roi_selected | profit | bet_count |
|-------|---------------------|--------|-----------|
| xgboost | **-14.88%** | -226,920 | 15,249 |
| lightgbm | -20.90% | -319,010 | 15,262 |
| ensemble | （不具合・要修正） | - | 0 |

## Notes

- **EXP-0006**: (1) **正式 reference (n_w=12)**: 2位 top_n=3, ev=1.20 **-14.88%**（従来 1 位）。top_n=6, ev=1.00 **-18.78%**（局所最適 adopt）。(2) **暫定 best (n_w=4)**: top_n=3, ev=1.25 で -11.15% は window 数少のため未確定。(3) bet sizing は fixed 推奨。ev_threshold_only は **reject**。
- **EXP-0007**: (1) **top_n=3 EV 高解像度探索**: ev=1.18 が **-14.54%** で 1 位（adopt）。ev=1.20 は -14.88%。(2) **bet sizing 正式比較**: 条件 top_n=3, ev=1.18 で fixed -14.54%, capped_kelly_0.02 -8.17%。運用は fixed 推奨。(3) 従来 EXP-0007: top_n=4, ev=1.05 で -17.85%（hold）。calibration 比較は experiments/logs/EXP-0007_strategy_optimization.md。今回の局所探索は experiments/logs/EXP-0007_bet_sizing_and_local_search.md。
- **EXP-0008**: (1) **Fractional Kelly**: cap=0.01 で ROI 最良 -6.99%（資金制約で破綻リスクあり、運用は fixed 推奨）。(2) **Calibration**: sigmoid -14.88% > none -15.80%。(3) **Model**: xgboost -14.88% > lightgbm -20.90%。ensemble は bet_count=0 の不具合あり要修正。log: experiments/logs/EXP-0008_fractional_kelly.md。
- **EXP-0009**: selection strategy 拡張。top_n_ev と top_n_ev_confidence（EV×信頼度）を比較。top_n=3, ev=1.15/1.18/1.20, confidence_type=pred_prob/prob_gap/entropy_adjusted。**結果**: 現行 top_n_ev が最良（-14.54%）。top_n_ev_confidence は全条件で -26%〜-39%、bet 数約35k で ROI 悪化。採用見送り。log: experiments/logs/EXP-0009_selection_confidence_sweep.md。
- **EXP-0010**: race_filtered_top_n_ev を **full grid** で実施。レース指標でフィルタし通過レースのみ top_n_ev。ベースライン top_n_ev ev=1.18（-14.54%）を上回る組み合わせはなく採用見送り。集計項目拡張（selected_race_count, selected_race_ratio, avg_bets_per_selected_race, baseline_diff_roi）を実施。log: experiments/logs/EXP-0010_race_filter_selection.md。結果 JSON: outputs/race_filter_experiments/exp0010_race_filter_full_results.json。
- **EXP-0011**: 確率上位K候補プール制限型 selection（top_n_ev_prob_pool）を評価。**結果**: ベースラインを超えず採用見送り。log: experiments/logs/EXP-0011_prob_pool_selection.md。
- **EXP-0012**: EV スコア再設計（top_n_ev_power_prob）。EV_adj = (pred_prob ** alpha) * odds。alpha=0.7,0.8,0.9,1.0,1.1 × top_n=2,3 × ev=1.15,1.17,1.18,1.19,1.20。ベースライン top_n_ev 3/1.18 と比較。結果は outputs/power_prob_experiments/exp0012_power_prob_results.json。tool: `python3 -m kyotei_predictor.tools.run_power_prob_experiment`。log: experiments/logs/EXP-0012_power_prob_ev.md。
- **EXP-0013**: EV gap strategy（top_n_ev_gap_filter）。ev_gap = ev_rank1 - ev_rank2。ev_gap < threshold ならレースを skip。ev_gap_threshold=0.02,0.03,0.05,0.07 で sweep。**結果**: ev_gap=0.05 が最良 **-13.81%**（n_w=12）、ベースライン -14.54% を +0.73%pt 上回り**採用**。tool: `python3 -m kyotei_predictor.tools.run_ev_gap_experiment`。log: experiments/logs/EXP-0013_ev_gap_strategy.md。結果: outputs/ev_gap_experiments/exp0013_ev_gap_results.json。
- **EXP-0014**: 条件別サブ戦略化（top_n_ev_conditional_prob_gap）。pred_prob_gap 帯ごとに (top_n, ev) を切り替え。**結果**: 全パターンでベースライン -14.54% を下回り**採用見送り**。tool: `python3 -m kyotei_predictor.tools.run_conditional_sub_strategy_experiment`。log: experiments/logs/EXP-0014_conditional_sub_strategy.md。結果: outputs/conditional_sub_strategy_experiments/exp0014_conditional_results.json。
- **EXP-0015**: EV gap 局所探索。ev_threshold × ev_gap_threshold のグリッド（ev=1.17〜1.20, ev_gap=0.03〜0.07）。**結果**: ev=1.20, ev_gap=0.07 が最良 **-12.71%**（n_w=12）、EXP-0013 ベスト -13.81% を +1.10%pt 上回り**採用**。tool: `python3 -m kyotei_predictor.tools.run_ev_gap_local_search_experiment`。log: experiments/logs/EXP-0015_ev_gap_local_search.md。結果: outputs/ev_gap_experiments/exp0015_ev_gap_local_search_results.json。
- **EXP-0016**: EXP-0015 ベスト近傍探索。ev=1.19/1.20/1.21 × ev_gap=0.06/0.07/0.08。**結果**: 最良は ev=1.20, ev_gap=0.07 のまま（-12.71%）。ベスト更新なし**採用見送り**。tool: `python3 -m kyotei_predictor.tools.run_ev_gap_near_local_search_experiment`。log: experiments/logs/EXP-0016_ev_gap_near_local_search.md。結果: outputs/ev_gap_experiments/exp0016_ev_gap_near_local_search_results.json。
- **EXP-0017**: EV gap + entropy filter（top_n_ev_gap_filter_entropy）。skip if race_entropy > threshold。entropy_threshold=1.2,1.3,1.4,1.5。**結果**: 全条件でベースライン -12.71% を下回り**採用見送り**。最良 ent=1.4 で -19.06%（bets=1,703）。tool: `python3 -m kyotei_predictor.tools.run_ev_gap_entropy_experiment`。log: experiments/logs/EXP-0017_entropy_filter.md。結果: outputs/ev_gap_experiments/exp0017_ev_gap_entropy_results.json。
- **EXP-0018**: EV gap + odds band filter（top_n_ev_gap_filter_odds_band）。skip if odds_rank1 < odds_low or > odds_high。odds_low=1.2,1.3,1.4 × odds_high=20,25,30。**結果**: 全条件でベースライン -12.71% を下回り**採用見送り**。最良 odds_high=25 で -20.36%（bets=2,179）。tool: `python3 -m kyotei_predictor.tools.run_ev_gap_odds_band_experiment`。log: experiments/logs/EXP-0018_odds_band_filter.md。結果: outputs/ev_gap_experiments/exp0018_ev_gap_odds_band_results.json。
- **EXP-0019**: EV gap + odds band + max bets per race（top_n_ev_gap_filter_odds_band_bet_limit）。odds_low=1.3, odds_high=25 のうえで max_bets_per_race=1,2。**結果**: max=1 で -14.25%（ベースライン -20.36% から +6.11%pt 改善）。全体1位は EXP-0015 のまま。odds_band 採用時は max_bets_per_race=1 推奨。tool: `python3 -m kyotei_predictor.tools.run_ev_gap_odds_band_bet_limit_experiment`。log: experiments/logs/EXP-0019_max_bet_limit.md。結果: outputs/ev_gap_experiments/exp0019_ev_gap_odds_band_bet_limit_results.json。
- **EXP-0020**: top_n_ev_gap_filter（EXP-0015 条件）に max_bets_per_race を直接適用。max_bets_per_race=None, 1, 2 で比較。**結果**: 全条件で ROI -12.71%（差なし）。ベスト更新なし**採用見送り**。tool: `python3 -m kyotei_predictor.tools.run_ev_gap_max_bets_experiment`。log: experiments/logs/EXP-0020_ev_gap_max_bets_per_race.md。結果: outputs/ev_gap_experiments/exp0020_ev_gap_max_bets_results.json。
- **EXP-0021**: top_n × ev × ev_gap 局所探索（top_n=2,3,4 × ev=1.19,1.20,1.21 × ev_gap=0.06,0.07,0.08）。**結果**: 最良は EXP-0015 と同一条件（top_n=3, ev=1.20, ev_gap=0.07, ROI -12.71%）で、ROI 改善は確認されず**新ベストなし・採用見送り**。top_n=2 系列は -13% 台、top_n=4 系列は -18% 前後といずれも悪化。tool: `python3 -m kyotei_predictor.tools.run_ev_gap_topn_local_search_experiment`。log: experiments/logs/EXP-0021_ev_gap_topn_local_search.md。結果: outputs/ev_gap_experiments/exp0021_ev_gap_topn_local_search_results.json。
- **EXP-0024**: confidence-weighted sizing 閾値スイープ（ev_gap_high=0.09/0.10/0.11, normal_unit=0.5/0.6/0.7）。**結果**: ev_gap_high=0.11, normal_unit=0.5 が最良（ROI -14.20%、profit -206,545、max_drawdown 232,595、profit_per_1000_bets -14,045.9）。EXP-0023 の 0.10 より改善。ROI は EXP-0015 未達で adopt 見送り。利益・drawdown・efficiency 改善のため **hold**・実運用推奨。tool: `python3 -m kyotei_predictor.tools.run_confidence_weighted_sizing_threshold_sweep`。log: experiments/logs/EXP-0024_confidence_weighted_sizing_threshold_sweep.md。結果: outputs/confidence_weighted_sizing_experiments/exp0024_confidence_weighted_sizing_threshold_sweep_results.json。
- **EXP-0025**: confidence-weighted sizing を EXP-0015/0013/0007 の 3 戦略に横展開。fixed vs weighted（ev_gap_high=0.11, normal_unit=0.5）を n_w=12 で比較。**結果**: 3 戦略とも weighted で ROI・profit・max_drawdown・profit_per_1000_bets が fixed より改善。同一 run 最良は exp0013+weighted -13.61%。ROI 1 位は EXP-0015 公式 -12.71% のまま。**hold**・実運用で全戦略に weighted 推奨。tool: `python3 -m kyotei_predictor.tools.run_confidence_weighted_sizing_rollout`。log: experiments/logs/EXP-0025_confidence_weighted_sizing_rollout.md。結果: outputs/confidence_weighted_sizing_experiments/exp0025_confidence_weighted_sizing_rollout_results.json。
- **EXP-0026**: Kelly sizing（unit = kelly_fraction * edge / odds, fraction=0.25/0.5/0.75）を EXP-0015/0013/0007 で fixed・confidence_weighted と比較。**結果**: ROI は Kelly が -22.6%〜-23% で fixed/confidence_weighted より悪化。**profit**: Kelly は総損失・max_drawdown が小さい（リスク抑制）。**efficiency**: profit_per_1000_bets は Kelly で 1 bet あたり損失が小さい。ROI 採用は **reject**、リスク重視時は **hold**。tool: `python3 -m kyotei_predictor.tools.run_kelly_sizing_experiment`。log: experiments/logs/EXP-0026_kelly_sizing_experiment.md。結果: outputs/confidence_weighted_sizing_experiments/exp0026_kelly_sizing_experiment_results.json。
- **EXP-0027**: EV percentile 別 ROI 分析。レースを最大 EV 順に並べ top 1/5/10/20/50% / full で集計。**結果**: 全帯で赤字。高 EV 帯（top 1〜20%）が損失源（ROI -42%〜-100%）。full が相対最良。EV percentile 分析により有望 cutoff 候補（高 EV 除外）を特定。tool: `python3 -m kyotei_predictor.tools.analyze_ev_percentile_roi`。log: experiments/logs/EXP-0027_ev_percentile_analysis.md。結果: outputs/confidence_weighted_sizing_experiments/exp0027_ev_percentile_analysis_results.json。
- **EXP-0028**: オッズキャップ実験（高 EV 帯の損失原因切り分け）。odds_cap none / 30 / 50 / 80 を EXP-0015/0013/0007 で比較。**結果**: 最良は none。cap をかけると ROI 悪化（-14%〜-18%）。高オッズ除外では ROI 改善せず。**reject**。tool: `python3 -m kyotei_predictor.tools.run_odds_cap_experiment`。log: experiments/logs/EXP-0028_odds_cap_experiment.md。結果: outputs/confidence_weighted_sizing_experiments/exp0028_odds_cap_experiment_results.json。
- **EXP-0029**: 確率キャリブレーション（isotonic）実験。baseline（sigmoid）vs calibrated（isotonic）を EXP-0015/0013/0007 で比較、n_w=12。**結果**: 全戦略で baseline が有利。isotonic は ROI 約 5%pt 悪化・選別数約 2 倍。**reject**。log: experiments/logs/EXP-0029_probability_calibration.md。
- **EXP-0030**: EXP-0015 条件で fixed vs confidence_weighted sizing を正式比較。同一 run で fixed -14.68%、weighted -14.20%。total_profit・max_drawdown・profit_per_1000_bets は weighted で改善。EXP-0024/0025 の知見を EXP-0015 ベスト条件で再現。**hold**・実運用で fixed より weighted 推奨。tool: `python3 -m kyotei_predictor.tools.run_exp0030_confidence_weighted_formal_baseline`。log: experiments/logs/EXP-0030_confidence_weighted_formal_baseline.md。結果: outputs/confidence_weighted_sizing_experiments/exp0030_confidence_weighted_formal_baseline_results.json。
- **EXP-0031**: EXP-0015 + confidence_weighted を前提に高EV帯除外（no_skip / skip_top10pct / skip_top20pct）を比較、n_w=12。**結果**: 同一 run で skip_top20pct が最良（ROI -8.85%、total_profit -103,665、max_drawdown 133,205、profit_per_1000_bets -8,732.63、bet_count 11,871）。EXP-0027 の示唆どおり高EV帯除外が有効。**adopt**。tool: `python3 -m kyotei_predictor.tools.run_exp0031_ev_high_skip`。log: experiments/logs/EXP-0031_ev_high_skip.md。結果: outputs/confidence_weighted_sizing_experiments/exp0031_ev_high_skip_results.json。
- **EXP-0032**: EXP-0031 の正式評価。no_skip / skip_top10pct / skip_top20pct を longer horizon（n_w=18）で比較。**結果**: 同一 run で skip_top20pct が最良（ROI -2.85%、total_profit -51,160、max_drawdown 133,205、profit_per_1000_bets -2,811.76、bet_count 18,195）。skip_top20pct の ROI 改善が期間延長で再現。**adopt**。tool: `python3 -m kyotei_predictor.tools.run_exp0032_ev_high_skip_longer_horizon`。log: experiments/logs/EXP-0032_ev_high_skip_longer_horizon.md。結果: outputs/ev_high_skip_experiments/exp0032_ev_high_skip_longer_horizon_results.json。
- **EXP-0033**: EV high skip 戦略（skip_top10/20pct）に race-level EV cap（max_ev > cap のレース除外）を追加。**結果**: skip_top20pct+ev_cap_5.0 が最良（ROI -2.27%、total_profit -23,625、max_drawdown 117,910、profit_per_1000_bets -2,236.37、bet_count 10,564）。cap=3.0/4.0 は ROI 悪化（-18.19% / -11.11%）で reject。**adopt**。tool: `python3 -m kyotei_predictor.tools.run_exp0033_ev_cap_experiment`。log: experiments/logs/EXP-0033_ev_cap_experiment.md。結果: outputs/ev_cap_experiments/exp0033_ev_cap_experiment_results.json。
- **EXP-0038**: EV band（3<=EV<5）に probability フィルタ（prob>=0.05/0.08/0.10/0.12）を追加。**結果**: ev3_5_prob005 が最良（ROI +24.67%、total_profit +70,965、max_drawdown 18,940、bet_count 2,927）。**adopt**。tool: `python3 -m kyotei_predictor.tools.run_exp0038_ev_prob_band_strategy`。log: experiments/logs/EXP-0038_ev_prob_band_strategy.md。結果: outputs/ev_prob_band_strategy/exp0038_ev_prob_band_strategy_results.json。
- **EXP-0039**: EV band + prob に race 内 EV 順位フィルタを追加（rank≤3/≤5/2-5/2-7）。**結果**: baseline と rank_le_3/rank_le_5 は同一（21.30%、2,465 bets）。rank_2_5/rank_2_7 は bet 59 で ROI -81.42%。**reject**。tool: `python3 -m kyotei_predictor.tools.run_exp0039_ev_prob_rank_strategy`。log: experiments/logs/EXP-0039_ev_prob_rank_strategy.md。結果: outputs/ev_prob_rank_strategy/exp0039_ev_prob_rank_strategy_results.json。
- **EXP-0040**: 採用条件固定でベットサイジングのみ変更（fixed / EV比例 / prob比例 / EV×prob / capped）。**結果**: size_by_ev_prob_capped が最良（ROI +155.8%、total_profit +226,307、max_drawdown 3,081）。**adopt**。tool: `python3 -m kyotei_predictor.tools.run_exp0040_bet_sizing_optimization`。log: experiments/logs/EXP-0040_bet_sizing_optimization.md。結果: outputs/bet_sizing_optimization/exp0040_bet_sizing_optimization_results.json。
- 比較値の出典: overall_roi_selected は rolling_validation_roi の total_payout / total_bet から算出。n_windows=12 は同一条件。
- EXP-0005 ev_threshold_sweep: ev_threshold_only 戦略で threshold 1.05〜1.25 を比較（n_w=6）。最良 ROI は ev=1.05 で -48.95%。
- この表は主に overall_roi_selected で比較する
- 同程度なら安定性（std_roi_selected）も考慮する
- extended_features_v2 は n_windows=12 でも extended_features より ROI 悪化 → hold
- AI は新しい提案をする前に leaderboard を確認すること
