# Chat Context

AI レビュー用。実験・leaderboard 更新後に `python3 scripts/generate_chat_context.py` で再生成すること。

---

# Project Goal

競艇予測AIのROI最大化（rolling validation n_w=12 における overall_roi_selected の改善）。

---

# Current Production Strategy

現在採用している戦略（leaderboard #1 に基づく）。

- model: xgboost
- calibration: sigmoid
- strategy: top_n_ev_gap_filter
- top_n: 3
- ev_threshold: 1.20
- ev_gap_threshold: 0.07
- seed: 42
- features: extended_features
- validation windows: 12

---

# Best Historical Result (Leaderboard #1)

leaderboard の 1 位。

- strategy: top_n_ev_gap_filter, top_n=3, ev=1.20, ev_gap_threshold=0.07
- ROI: **-12.71%** (n_w=12)
- selected_bets: 14,700（experiments/leaderboard.md の Bet Sizing 表参照）
- validation windows: 12

---

# Latest Experiment

<!-- update_chat_context.py が自動更新 -->

- **最新 EXP**: EXP-0024
- **概要**: confidence-weighted sizing の閾値微調整。weighted_ev_gap_v1 を基準に ev_gap_high を 0.09 / 0.10 / 0.11、normal_unit を 0.5 / 0.6 / 0.7（ev_gap_high=0.10 時）で sweep。n_w=12。
- **結果**: 最良は ev_gap_high=0.11, normal_unit=0.5（ROI -14.20%、fixed 比 +0.48%pt）。total_profit・max_drawdown・profit_per_1000_bets も fixed および EXP-0023 の 0.10 より改善。ROI は EXP-0015 未達で adopt 見送り。利益効率・リスク改善のため hold・実運用推奨。
- **ログ**: experiments/logs/EXP-0024_confidence_weighted_sizing_threshold_sweep.md
- **結果 JSON**: outputs/confidence_weighted_sizing_experiments/exp0024_confidence_weighted_sizing_threshold_sweep_results.json

# Leaderboard Summary

<!-- update_chat_context.py が自動更新 -->

| Rank | Experiment ID | Parameters | overall_roi_selected | selected_bets | Notes |
|------|----------------|-----------|----------------------|----------------|-------|
| 1 | EXP-0015 | top_n_ev_gap_filter, top_n=3, ev=1.20, ev_gap=0.07 | **-12.71%** (n_w=12) | 14,700 | EV gap 局所探索で最良（adopt） |
| 2 | EXP-0013 | top_n_ev_gap_filter, top_n=3, ev=1.18, ev_gap=0.05 | **-13.81%** (n_w=12) | 14,994 | EV gap で曖昧レース skip（adopt） |
| 3 | EXP-0007 | top_n=3, ev=1.18 | **-14.54%** (n_w=12) | — | EV 高解像度探索で最良（adopt） |
| 4 | EXP-0006 | top_n=3, ev=1.20 | **-14.88%** (n_w=12) | — | **正式 reference**（従来 1 位） |
| 5 | EXP-0007 | top_n=4, ev=1.05 | **-17.85%** (n_w=12) | — | top_n 局所探索で最良（hold） |
| — | EXP-0011 | top_n_ev_prob_pool | ベースライン超えず | — | 採用見送り |
| — | EXP-0012 | top_n_ev_power_prob (alpha×top_n×ev) | ベースライン未達 | — | 全条件採用見送り。最良 -26.28%。 |
| — | EXP-0014 | top_n_ev_conditional_prob_gap (pred_prob_gap 帯) | ベースライン未達 | — | 条件別サブ戦略。採用見送り。 |
| — | EXP-0016 | top_n_ev_gap_filter 近傍 (ev=1.19〜1.21, ev_gap=0.06〜0.08) | 最良 -12.71%（同点） | — | ベスト更新なし。採用見送り。 |
| — | EXP-0017 | top_n_ev_gap_filter_entropy (ev=1.20, ev_gap=0.07, ent=1.2〜1.5) | 最良 -19.06%（ent=1.4） | 1,529〜1,801 | 全条件ベースライン未達。採用見送り。 |
| — | EXP-0018 | top_n_ev_gap_filter_odds_band (ev=1.20, ev_gap=0.07, odds_low/high) | 最良 -20.36%（odds_high=25） | 1,867〜2,388 | 全条件ベースライン未達。採用見送り。 |
| — | EXP-0019 | top_n_ev_gap_filter_odds_band_bet_limit (odds=1.3/25, max=1/2) | 最良 -14.25%（max=1） | 1,980 / 2,167 | odds_band に max=1 で +6.11%pt。全体1位は更新せず。odds_band 時は max=1 推奨。 |
| — | EXP-0020 | top_n_ev_gap_filter + max_bets_per_race (None/1/2) | 全条件 -12.71% | 14,700 | EXP-0015 に max を直接適用。改善なし。採用見送り。 |
| — | EXP-0021 | top_n_ev_gap_filter (top_n×ev×ev_gap 局所探索) | 最良 -12.71%（top_n=3, ev=1.20, ev_gap=0.07） | 14,700 | EXP-0015 条件を含む再探索。top_n=2/4 系列はいずれも ROI 悪化、top_n=3 でも EXP-0015 と同点で新ベストなし（reject）。 |
| — | EXP-0022 | top_n_ev_gap_venue_filter (venue_ev_config) | 最良 -14.6%, bets=14,702 | 14,702 | 会場別 EV。同一 run ベースラインより +0.08%pt。EXP-0015 未達で採用見送り。 |
| — | EXP-0022 | top_n_ev_gap_venue (venue_config ev+ev_gap) | 最良 -14.58%, bets=14,699 | 14,699 | 会場別 ev・ev_gap。同一 run ベースラインより +0.10%pt 改善。 |
| — | EXP-0023 | top_n_ev_gap_filter + confidence_weighted_sizing | 最良 -14.31%（weighted_ev_gap_v1）, bets=14,705 | 14,705 | ROI は adopt 未達。利益指標改善。hold・実運用候補。 |
| — | EXP-0024 | confidence_weighted_sizing threshold sweep | 最良 -14.20%（ev_gap_high=0.11, normal_unit=0.5）, bets=14,705 | 14,705 | 閾値スイープで 0.11 が最良。利益・drawdown・efficiency 改善。hold・実運用推奨。 |

詳細は experiments/leaderboard.md 参照。

# Current Findings

- **EXP-0015**: top_n_ev_gap_filter（ev=1.20, ev_gap=0.07）が現行ベスト **-12.71%**（n_w=12）。EXP-0013 ベスト -13.81% を 1.10%pt 上回り採用。
- **EXP-0016**: EXP-0015 ベスト近傍（ev=1.19〜1.21, ev_gap=0.06〜0.08）を探索。最良は同点 -12.71%。ベスト更新なしで採用見送り。
- **EXP-0017**: EV gap + entropy filter（skip if race_entropy > threshold）。ent=1.2〜1.5 で全条件ベースライン -12.71% を下回り採用見送り。bet 数が 1,500〜1,800 に激減し ROI 悪化。
- **EXP-0018**: EV gap + odds band filter（skip if odds_rank1 < odds_low or > odds_high）。odds_low=1.2〜1.4 × odds_high=20,25,30 で全条件ベースライン -12.71% を下回り採用見送り。最良 odds_high=25 で -20.36%（bets=2,179）。
- **EXP-0019**: odds_band（1.3, 25）に max_bets_per_race=1 を追加すると -20.36% → -14.25%（+6.11%pt）。全体1位は EXP-0015 のまま。odds_band 採用時は max_bets_per_race=1 推奨。
- **EXP-0020**: top_n_ev_gap_filter（EXP-0015 条件）に max_bets_per_race=None/1/2 を直接適用。全条件で ROI -12.71%、差なし。採用見送り。
- **EXP-0021**: top_n × ev × ev_gap 局所探索（top_n=2,3,4 × ev=1.19,1.20,1.21 × ev_gap=0.06,0.07,0.08）。最良は EXP-0015 と同一条件（top_n=3, ev=1.20, ev_gap=0.07, ROI -12.71%）で、新ベストは出ず採用見送り。top_n=2 は -13% 台、top_n=4 は -18% 前後と悪化。
- **EXP-0022**: (1) venue 別 EV（top_n_ev_gap_venue_filter）最良 -14.6%（bets=14,702）。(2) venue 別 ev・ev_gap（top_n_ev_gap_venue）最良 -14.58%（bets=14,699）、同一 run ベースラインより +0.10%pt 改善。
- **EXP-0023**: confidence-weighted fixed sizing（ev_gap / pred_prob_gap で 2〜3 段階）。weighted_ev_gap_v1 が最良（ROI -14.31%、profit・drawdown・profit/1000bets 改善）。ROI は EXP-0015 未達で adopt 見送り。利益指標では改善あり。**ROI 最適化から利益最大化フェーズへ移行中**の検証。
- **EXP-0024**: confidence-weighted sizing 閾値スイープ（ev_gap_high=0.09/0.10/0.11, normal_unit=0.5/0.6/0.7）。ev_gap_high=0.11, normal_unit=0.5 が最良（ROI -14.20%、profit・drawdown・profit/1000bets で EXP-0023 より改善）。ROI は EXP-0015 未達で adopt 見送り。利益効率・リスク改善のため **hold**・実運用推奨。
- EV threshold を下げると bet 数が増える。ev=1.18 が従来 1 位（-14.54%）、ev=1.20 が 2 位（-14.88%）。
- top_n が大きいと ROI が悪化する傾向（top_n=3 が最良、top_n=6 で -18.78%）。
- bet sizing は fixed が最良。Kelly 系は資金制約で破綻リスクあり。
- calibration は sigmoid が none より有利（-14.88% vs -15.80%）。
- xgboost が lightgbm より ROI 良好（-14.88% vs -20.90%）。
- EXP-0010: race_filtered_top_n_ev は full grid で全条件ベースライン以下。レースフィルタで bet 数は減るが ROI は未改善。
- EXP-0011: top_n_ev_prob_pool はベースライン（top_n_ev 3/1.18）を超えず採用見送り。
- EXP-0012: top_n_ev_power_prob は全グリッドでベースライン未達。採用見送り。
- EXP-0014: pred_prob_gap 帯による条件別サブ戦略は全パターンでベースライン（-14.54%）を下回り採用見送り。

---

# Open Questions

- EXP-0008 Task3: ensemble（確率平均）で bet_count=0 となる不具合。予測マージ／パス参照の修正が必要。
- 暫定 best（n_w=4）top_n=3, ev=1.25 は n_w=12 再評価が未実施。

---

# Next Experiments

- 現行ベスト戦略: top_n_ev_gap_filter, top_n=3, ev=1.20, ev_gap_threshold=0.07（ROI -12.71%）。EXP-0015 で採用。
- **ROI 最適化から利益最大化フェーズへ移行中**。EXP-0024 で ev_gap_high=0.11, normal_unit=0.5 が最良と確認。confidence-weighted 実運用時はこの閾値を推奨。
- 次の実験候補: confidence-weighted × max_bets_per_race（テーマ B）、venue 別 × weighted sizing（テーマ C）を必要時に実施。
- 会場別パラメータ拡張・別軸（モデル・特徴量・calibration）の検討を継続。
- ensemble 不具合修正後の再評価。
- 条件別サブ戦略の他軸（entropy 帯・1位オッズ帯・venue/race_class）は必要時に検討（EXP-0014 で pred_prob_gap 帯は見送り）。
- top_n / EV threshold の追加 sweep（必要に応じて）。
- probability calibration の詳細比較（必要に応じて）。
