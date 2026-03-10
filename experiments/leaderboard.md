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
- 比較値の出典: overall_roi_selected は rolling_validation_roi の total_payout / total_bet から算出。n_windows=12 は同一条件。
- EXP-0005 ev_threshold_sweep: ev_threshold_only 戦略で threshold 1.05〜1.25 を比較（n_w=6）。最良 ROI は ev=1.05 で -48.95%。
- この表は主に overall_roi_selected で比較する
- 同程度なら安定性（std_roi_selected）も考慮する
- extended_features_v2 は n_windows=12 でも extended_features より ROI 悪化 → hold
- AI は新しい提案をする前に leaderboard を確認すること
