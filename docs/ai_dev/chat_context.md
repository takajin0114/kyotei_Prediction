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

- **最新 EXP**: EXP-0055
- **概要**: Low Payout Filter 頑健性。baseline/CASE2/CASE4/CASE5/CASE6 を n_w=24/30/36 で比較。
- **結果**: CASE2 が全期間で profit 1 位（尖りあり）。CASE6 が安定 2 位。CASE2 攻め版・CASE6 実運用版の 2 本立て採用。
- **ログ**: experiments/logs/EXP-0055_low_payout_filter_robustness.md
- **結果 JSON**: outputs/selection_verified/exp0055_low_payout_filter_robustness_results.json

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
| — | EXP-0025 | confidence_weighted_sizing rollout (EXP-0015/0013/0007) | 同一 run 最良 -13.61%（exp0013+weighted）, bets=14,994 | 14,705〜15,407 | 3戦略とも weighted で改善。hold・実運用で全戦略に weighted 推奨。 |
| — | EXP-0026 | Kelly sizing (EXP-0015/0013/0007) | 最良 ROI confidence_weighted -13.61%。Kelly は -22.6%〜-23% | 14,705〜15,407 | profit・drawdown は Kelly が小さい。ROI 採用 reject、リスク目的 hold。 |
| — | EXP-0027 | EV percentile ROI analysis (EXP-0015/0013/0007) | 全帯赤字。高EV帯が損失源、full が相対最良 | 132〜15,407 | EV percentile 分析で有望 cutoff 候補を特定。hold。 |
| — | EXP-0028 | odds cap (EXP-0015/0013/0007) | 最良 none。cap で ROI 悪化 | 6,307〜15,407 | 高オッズ除外では改善せず。reject。 |
| — | EXP-0029 | probability calibration (EXP-0015/0013/0007) | baseline（sigmoid）が有利。isotonic で約5%pt悪化 | 14,705〜32,883 | isotonic は選別数約2倍で損失拡大。reject。 |
| — | EXP-0030 | confidence_weighted formal baseline (EXP-0015) | 同一 run fixed -14.68%, weighted -14.20%, bets=14,705 | 14,705 | EXP-0015 条件で正式比較。weighted で全指標改善。hold・実運用で weighted 推奨。 |
| — | EXP-0031 | EV high skip (EXP-0015 + confidence_weighted) | 同一 run 最良 -8.85%（skip_top20pct）, bets=11,871 | 11,871〜14,705 | 高EV帯除外で ROI・profit・drawdown 改善。adopt。 |
| — | EXP-0032 | EV high skip longer horizon (n_w=18) | 同一 run 最良 -2.85%（skip_top20pct）, bets=18,195 | 18,195〜22,580 | longer horizon で skip_top20pct 優位再現。adopt。 |
| — | EXP-0033 | EV high skip + EV cap (race-level) | skip_top10/20pct × ev_cap=none/3/4/5, n_w=18 | 5,999〜20,411 | 最良 skip_top20pct+ev_cap_5.0（ROI -2.27%、bets=10,564）。cap 3/4 は ROI 悪化。adopt。 |
| — | EXP-0034 | EV cap 局所探索 (skip_top20pct 固定) | ev_cap=no_cap/4.5/5.0/5.5/6.0/6.5, n_w=18 | 9,588〜18,195 | ev_cap_5.0 が最良のまま。4.5 切りすぎ・5.5 以上悪化。reject。 |
| — | EXP-0035 | high EV skip 率局所探索 (ev_cap_5.0 固定) | skip_top10/15/20/25/30pct, n_w=18 | 10,564（全条件同一） | 全条件同一。ev_cap が支配的。reject。 |
| — | EXP-0036 | EV帯ごとの成績分析 | EV帯別 bet_count/hit_rate/ROI/profit, n_w=18 | 帯別 | 黒字: 3–4, 4–5, 6–8。ev_cap=5.0 支持。hold。 |
| — | EXP-0037 | EV帯フィルタ戦略 | 3<=EV<5 / 4<=EV<5 等, n_w=18 | 2,079〜10,564 | 最良 ev_band_3_5: ROI +18.71%, profit +83,955。ev_band_4_5: ROI +33.78%。adopt。 |
| — | EXP-0038 | EV band + probability フィルタ | 3<=EV<5 + prob>=0.05/0.08/0.10/0.12, n_w=18 | 2,162〜4,565 | 最良 ev3_5_prob005: ROI +24.67%, profit +70,965, max_dd 18,940。adopt。 |
| — | EXP-0039 | EV band + prob + race内EV順位 | 3<=EV<5 + prob>=0.05 + rank 条件, n_w=18 | 59〜2,465 | baseline と rank_le_3/5 同一。rank_2_5/2_7 は bet 59 で -81.42%。reject。 |
| — | EXP-0040 | ベットサイジング最適化 | 条件固定、unit=EV×prob cap 等, n_w=18 | 2,097 | 参考値（後段 stake 再計算で過大評価）。最良 +155.8%。 |
| — | EXP-0041 | ベットサイジング厳密検証 | 条件固定、bet 単位 stake/payout 整合, n_w=18 | 2,097 | 厳密再検証。全 variant 赤字、最良 baseline_fixed ROI -4.39%。 |
| — | EXP-0042 | selection 条件厳密再検証 | stake=100 固定、selection のみ比較, n_w=18 | 1,628〜6,942 | 最良 baseline_c（4≤EV<5）ROI -5.17%。次点 baseline_b。 |
| — | EXP-0043 | selection 局所探索（厳密評価） | baseline_c/b 周辺の EV・prob 微調整, n_w=18 | 656〜2,465 | 最良 variant_j ROI +12.34%。variant_l +5.82%、max_dd 15,040。 |
| — | EXP-0044 | EV帯超微調整（厳密評価） | 4.3≤EV<4.9 周辺の EV 帯・prob 微調整, n_w=18 | 495〜1,112 | 最良 variant_g ROI +30.46%。variant_d（prob≥0.05）: +18.34%, max_dd 11,820。 |
| — | EXP-0045 | EV帯頑健性確認（厳密評価） | ref1/ref2/variant_g/variant_d, n_w=24 | 772〜1,292 | variant_g +9.52%だが不安定。variant_d 主軸格上げ、max_dd 11,820。 |
| — | EXP-0046 | variant_d 近傍安定化探索（厳密評価） | d_base/d_hi475/d_mid 等, n_w=24 | 612〜900 | d_hi475 主軸更新、ROI +13.65%, max_dd 9,420, longest_lose=4。 |
| — | EXP-0047 | d_hi475 運用制御（厳密評価） | base/cap1/dd_guard/sizing_80 等, n_w=24 | 291〜704 | base 維持、保守版 sizing_80 で max_dd・worst_w 改善。2本立て採用。 |
| — | EXP-0048 | 通常/保守モード切替ルール（厳密評価） | normal_only/switch_dd5000 等, n_w=24 | 704 | 主軸通常版維持。switch_dd5000 をオプション化。 |
| — | EXP-0049 | switch_dd 閾値感度（厳密評価） | switch_dd3000〜7000, n_w=24 | 704 | 推奨閾値を switch_dd4000 に更新。profit 最大・max_dd 同水準。 |
| — | EXP-0050 | switch_dd4000 長期頑健性（厳密評価） | normal_only/switch_dd4000/5000, n_w=24/30/36 | 704〜1031 | 30/36 でも優位維持。実運用標準候補へ格上げ。 |
| — | EXP-0051 | switch_dd4000 期間安定性・regime（厳密評価） | normal_only/switch_dd4000/conservative, n_w=36, 6block | 1031 | 後半で悪化傾向。注意条件付き標準採用。 |
| — | EXP-0052 | Seasonality/Regime 分析（厳密評価） | 月別・block・累積・switch・regime特徴, n_w=36 | 1031 | 月別・block強弱・負けはhit_rate高め・bet少なめ。hold。 |
| — | EXP-0053 | Payout/Odds Regime 分析（厳密評価） | 的中時オッズ・払戻・profit_per_hit, n_w=36 | 1031 | 負けblockはhit_odds低・payout約半額。利益悪化は高配当不足で説明。hold。 |
| — | EXP-0054 | Low Payout Regime Filter（厳密評価） | EV/odds/top1_prob フィルタ, n_w=36 | 343〜1031 | 低配当回避で profit/DD 改善。CASE2 最良・CASE6 バランス。hold。 |
| — | EXP-0055 | Low Payout Filter 頑健性（厳密評価） | n_w=24/30/36 比較 | 343〜1031 | CASE2 攻め版・CASE6 実運用版 2本立て採用。 |

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
- **EXP-0025**: confidence-weighted sizing を EXP-0015/0013/0007 に横展開。3 戦略とも fixed より weighted で ROI・profit・drawdown・profit/1000bets が改善。同一 run 最良 exp0013+weighted -13.61%。ROI 1 位は EXP-0015 のまま。**hold**・実運用で全戦略に weighted 推奨。
- **EXP-0026**: Kelly sizing（fraction 0.25/0.5/0.75）を fixed・confidence_weighted と比較。ROI は Kelly が悪化（-22.6%〜-23%）。profit・max_drawdown は Kelly が小さい（リスク抑制）。ROI 採用 **reject**、リスク重視時 **hold**。
- **EXP-0027**: EV percentile 別 ROI 分析。高 EV 帯（top 1〜20%）が損失源、full が相対最良。利益源となる帯はなし。有望 cutoff 候補として「高 EV 帯除外」を次の実験で検証可能。
- **EXP-0028**: オッズキャップ実験。odds_cap 30/50/80 は none より ROI 悪化。高 EV 帯の損失原因として高オッズ単純除外は有効でなかった。reject。
- **EXP-0029**: 確率キャリブレーション実験。isotonic は sigmoid baseline より ROI 約 5%pt 悪化・選別数約 2 倍。sigmoid 維持。reject。
- **EXP-0030**: EXP-0015 条件で fixed vs confidence_weighted を正式比較。同一 run で weighted が ROI・total_profit・max_drawdown・profit_per_1000_bets で改善。EXP-0024/0025 の知見を EXP-0015 ベスト条件で再現。**hold**・実運用で fixed より confidence_weighted 推奨。
- **EXP-0031**: EXP-0015 + confidence_weighted を前提に高EV帯除外（no_skip / skip_top10pct / skip_top20pct）を比較。同一 run で skip_top20pct が最良（ROI -8.85%）。EXP-0027 の示唆どおり高EV帯除外が有効。**adopt**。
- **EXP-0032**: EXP-0031 の正式評価。longer horizon（n_w=18）で no_skip / skip_top10pct / skip_top20pct を比較。skip_top20pct が最良（ROI -2.85%）。期間延長でも高EV帯除外の優位性が再現。**adopt**。
- **EXP-0033**: EV high skip 戦略に race-level EV cap を追加し、ev_cap=none/3/4/5 を比較（n_w=18）。skip_top20pct+ev_cap_5.0 が最良（ROI -2.27%、profit -23,625、max_drawdown 117,910、profit_per_1000bets -2,236.37、bet_count 10,564）。EV cap 3/4 は ROI 悪化。EV cap 5.0 を採用。**adopt**。
- **EXP-0034**: EV cap 局所探索（skip_top20pct 固定、ev_cap=no_cap/4.5/5.0/5.5/6.0/6.5、n_w=18）。ev_cap_5.0 が最良のまま。4.5 は切りすぎ、5.5 以上は ROI・profit 悪化。**reject**。実運用は skip_top20pct + ev_cap_5.0 維持。
- **EXP-0035**: high EV skip 率局所探索（ev_cap_5.0 固定、skip_top10/15/20/25/30pct、n_w=18）。全条件で同一結果（ROI -2.27%、bets=10,564）。ev_cap が支配的で skip 率差なし。**reject**。実運用は skip_top20pct + ev_cap_5.0 維持。
- **EXP-0036**: EV帯ごとの成績分析（n_w=18）。黒字帯: 3–4（+6.07%）, 4–5（+33.78%）, 6–8（+4.05%）。赤字: 5–6, 8–10, >=10。ev_cap=5.0 の妥当性を支持。**hold**。
- **EXP-0037**: EV帯フィルタ戦略（n_w=18）。黒字帯のみ購入でベースラインを大きく上回る。ev_band_3_5: ROI +18.71%、profit +83,955、max_dd 36,525。ev_band_4_5: ROI +33.78%。**adopt**。実運用候補を skip_top20pct + 3<=EV<5 に更新。
- **EXP-0038**: EV band + probability フィルタ（n_w=18）。3<=EV<5 に prob>=0.05 を追加した ev3_5_prob005 が最良（ROI +24.67%、profit +70,965、max_dd 18,940）。**adopt**。実運用候補を skip_top20pct + 3<=EV<5 + prob>=0.05 に更新。
- **EXP-0039**: EV band + prob に race 内 EV 順位フィルタを追加（n_w=18）。rank≤3/≤5 は baseline と同一、rank 2-5/2-7（rank 1 除外）は bet 激減・大幅赤字。**reject**。実運用は EXP-0038 維持。
- **EXP-0040**: 採用条件固定でベットサイジングのみ変更（n_w=18）。verify を 1 回だけ実行し payout を固定、stake を後段で再計算したため **参考値**。size_by_ev_prob_capped で ROI +155.8%、profit +226,307 と出たが過大評価。
- **EXP-0041**: ベットサイジングの**厳密再検証**（各 bet で stake と payout を対応させて計算）。全 variant で赤字。最良は baseline_fixed（ROI -4.39%、total_profit -9,210）。EXP-0040 の数値は過大評価であり、**評価系の厳密化は EXP-0041** で実施した。
- **EXP-0042**: **selection 条件の厳密再採点**（stake=100 固定）。baseline_c（4≤EV<5）と baseline_b（3≤EV<5+prob≥0.05）が候補となり、いずれも赤字だったが最もマシな条件として整理した。
- **EXP-0043**: **selection の局所探索**（EXP-0042 の baseline_c / baseline_b 周辺で EV 帯・prob 閾値を微調整、同一厳密評価）。複数条件で黒字。最良 variant_j（4.3≤EV<4.9）: ROI +12.34%。バランス重視は variant_l（4.3≤EV<4.9, prob≥0.05）: +5.82%、max_dd 15,040。実運用候補を **skip_top20pct + 4.3≤EV<4.9**（必要なら prob≥0.05）に更新。
- **EXP-0044**: **EV帯の超微調整**（4.3≤EV<4.9 周辺を 0.05〜0.10 刻みで探索、同一厳密評価）。reference_1/2 を上回る条件が複数。最良 variant_g（4.40≤EV<4.85）: ROI +30.46%、profit +21,660。variant_d（4.30≤EV<4.80, prob≥0.05）: +18.34%、max_dd 11,820。実運用候補を **skip_top20pct + 4.40≤EV<4.85**（リスク重視時は 4.30≤EV<4.80 + prob≥0.05）に更新。
- **EXP-0045**: **EV帯の頑健性確認**（n_w=24 で長期・前半後半を評価）。variant_g は黒字維持だが longest_losing_streak=10 で不安定。variant_d は安定（longest_lose=4、max_dd 11,820）。**実運用主軸を variant_d に格上げ**。主軸: skip_top20pct + 4.30≤EV<4.80 + prob≥0.05。サブ: 4.40≤EV<4.85（リスク許容時）。
- **EXP-0046**: **variant_d 近傍安定化探索**（n_w=24）。d_hi475（4.30≤EV<4.75, prob≥0.05）が d_base より ROI 13.65%、max_dd 9,420、longest_lose=4、worst_w -2,810 とすべて維持または改善。**主軸を安定版 d_hi475 に更新**。攻め版 d_mid（4.35≤EV<4.75, prob≥0.05）は ROI 18.21% だが longest_lose=6 のためサブ扱い。
- **EXP-0047**: **d_hi475 運用制御**（n_w=24）。base/cap1/cap2/top1_prob/top1_ev/dd_guard_light/sizing_80 を比較。d_hi475 はもともと avg_bets_per_race≈1 のため cap 効果は微小。**sizing_80** で ROI 維持・max_dd 7,536・worst_w -2,248 と改善。**通常版 base / 保守版 sizing_80 の 2 本立て採用**。dd_guard_light は max_dd・longest_lose 抑制に有効だが bet 激減のためオプション。
- **EXP-0048**: **通常/保守モード切替ルール**（n_w=24）。normal_only / conservative_only / switch_after_2_loss / switch_after_3_loss / switch_dd5000 / recover_after_1win を比較。**switch_dd5000**（累積DD≥5000で当該 window を stake=80）が profit 10,814・max_dd 7,766 で最良。**結論: 通常版主軸維持＋切替版をオプション化**。推奨オプション: switch_dd5000。補助: switch_after_2_loss。
- **EXP-0049**: **switch_dd 閾値感度**（n_w=24）。閾値 3000/4000/5000/6000/7000 を比較。**switch_dd4000** が total_profit 11,744 で最大、max_dd 7,766 は 5000 と同水準。**推奨閾値を 5000 から 4000 に更新**（別閾値へ更新）。
- **EXP-0050**: **switch_dd4000 長期頑健性**（n_w=24/30/36）。normal_only / conservative_only / switch_dd4000 / switch_dd5000 を比較。24→30→36 で switch_dd4000 が常に profit・ROI 1位。30/36 でも normal より profit 高・max_dd 低（または唯一黒字）を維持。**switch_dd4000 を「推奨オプション」から「実運用標準候補」へ格上げ**（adopt）。
- **EXP-0051**: **switch_dd4000 期間安定性・regime**（n_w=36、6ブロック）。全ブロックで switch が normal 以上。後半（7月後半〜10月）で成績悪化傾向。switch 発動 22/36 窓。**注意条件付き標準採用**（adopt with caveats）：後半期間の損失を前提とした資金配分・モニタリングを推奨。
- **EXP-0052**: **Seasonality/Regime 分析**（月別・block・累積曲線・switch 発動・regime 特徴）。月別で 08・09 が悪化。負けブロックは bet 数少なめ・hit_rate 高め・EV 同程度。オッズ分布の regime 差の可能性。**hold**（分析知見の整理）。
- **EXP-0053**: **Payout/Odds Regime 分析**（的中時オッズ・払戻・profit_per_hit の block/月別）。勝ち block は avg_hit_odds 18.44・payout_per_hit 1,810、負け block は 8.52・734。hit_rate は負け block の方が高いため、「当たっても低配当に寄っている」ことで利益悪化が説明できる。**hold**（分析知見の反映、即時運用変更なし）。
- **EXP-0054**: **Low Payout Regime Filter**（d_hi475+switch_dd4000 に EV≥4.50/4.60、odds≥10/12/15、top1_prob≤0.35 を追加）。全 CASE で baseline より profit・max_dd 改善。CASE2 最良（profit 17,592）、CASE6 バランス型（profit 8,764、longest_lose 5）。**hold**。
- **EXP-0055**: **Low Payout Filter 頑健性**（n_w=24/30/36 で baseline/CASE2/CASE4/CASE5/CASE6 を比較）。CASE2 は全期間で profit 1 位だが bet 343・longest_lose 9・block 2 依存大。CASE6 は 30/36 で 2 位・longest_lose 5 で安定。**結論**: CASE2 を攻め版、CASE6 を実運用版として **2 本立て採用**。
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
- **実運用候補（厳密評価）**: EXP-0051 で switch_dd4000 の期間安定性を確認済み。**主軸**: 通常版固定（d_hi475 + stake=100）。**実運用標準候補**: **switch_dd4000**（累積DD≥4000で当該 window を stake=80）。**注意条件**（EXP-0051）: 後半（7月後半〜10月相当）で成績悪化傾向のため、後半期間の資金配分・ブロック単位モニタリングを推奨。補助: switch_after_2_loss、参考: switch_dd5000。
- 次の実験候補: 別軸（venue 別 × weighted sizing、他 EV 帯の微調整等）は必要時に実施。
- 会場別パラメータ拡張・別軸（モデル・特徴量・calibration）の検討を継続。
- ensemble 不具合修正後の再評価。
- 条件別サブ戦略の他軸（entropy 帯・1位オッズ帯・venue/race_class）は必要時に検討（EXP-0014 で pred_prob_gap 帯は見送り）。
- top_n / EV threshold の追加 sweep（必要に応じて）。
- probability calibration の詳細比較（必要に応じて）。
