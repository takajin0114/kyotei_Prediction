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

- **最新 EXP**: EXP-0018
- **概要**: EV gap + odds band filter（top_n_ev_gap_filter_odds_band）。skip if odds_rank1 < odds_low or > odds_high。odds_low=1.2,1.3,1.4 × odds_high=20,25,30。ベースライン EV gap のみ（-12.71%）と比較。
- **結果**: 全条件でベースラインを下回り**採用見送り**。最良 odds_high=25 で -20.36%（bets=2,179）。詳細は outputs/ev_gap_experiments/exp0018_ev_gap_odds_band_results.json および experiments/logs/EXP-0018_odds_band_filter.md。
- **ログ**: experiments/logs/EXP-0018_odds_band_filter.md
- **結果 JSON**: outputs/ev_gap_experiments/exp0018_ev_gap_odds_band_results.json

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

詳細は experiments/leaderboard.md 参照。

# Current Findings

- **EXP-0015**: top_n_ev_gap_filter（ev=1.20, ev_gap=0.07）が現行ベスト **-12.71%**（n_w=12）。EXP-0013 ベスト -13.81% を 1.10%pt 上回り採用。
- **EXP-0016**: EXP-0015 ベスト近傍（ev=1.19〜1.21, ev_gap=0.06〜0.08）を探索。最良は同点 -12.71%。ベスト更新なしで採用見送り。
- **EXP-0017**: EV gap + entropy filter（skip if race_entropy > threshold）。ent=1.2〜1.5 で全条件ベースライン -12.71% を下回り採用見送り。bet 数が 1,500〜1,800 に激減し ROI 悪化。
- **EXP-0018**: EV gap + odds band filter（skip if odds_rank1 < odds_low or > odds_high）。odds_low=1.2〜1.4 × odds_high=20,25,30 で全条件ベースライン -12.71% を下回り採用見送り。最良 odds_high=25 で -20.36%（bets=2,179）。
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
- EXP-0018 で EV gap + odds band filter を検証済み（採用見送り）。別軸（top_n 変更・他戦略・calibration 等）の検討を検討。
- ensemble 不具合修正後の再評価。
- 条件別サブ戦略の他軸（entropy 帯・1位オッズ帯・venue/race_class）は必要時に検討（EXP-0014 で pred_prob_gap 帯は見送り）。
- top_n / EV threshold の追加 sweep（必要に応じて）。
- probability calibration の詳細比較（必要に応じて）。
