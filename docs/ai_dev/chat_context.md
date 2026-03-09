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
- strategy: top_n_ev
- top_n: 3
- ev_threshold: 1.18
- seed: 42
- features: extended_features
- validation windows: 12

---

# Best Historical Result (Leaderboard #1)

leaderboard の 1 位。

- strategy: top_n=3, ev=1.18
- ROI: **-14.54%** (n_w=12)
- selected_bets: —（experiments/leaderboard.md の Bet Sizing 表参照）
- validation windows: 12

---

# Latest Experiment

**EXP-0009**

実験内容
ROI 最大化のため、買い目選抜ロジックを改善する。予測モデルは変更せず、**selection strategy** を拡張し、EV 単独ではなく **EV × 信頼度** で選抜する `top_n_ev_confidence` を追加。現行 `top_n_ev` と比較する。

結果
- **現行 top_n_ev が最良**: ev=1.18 で overall_roi_selected **-14.54%**（1位）、ev=1.20 で -14.88%。bet 数は 15k 前後。 - **top_n_ev_confidence は ROI 悪化**: 全条件で overall_roi -26%〜-39%。bet 数は約 35k（ev≥閾値の**全候補**から top_n を選ぶため、対象レース数が増えている）。 - **結論**: 現状の「EV×信頼度」選抜では、閾値以上の候補を広く取るほど bet 数が増え ROI が悪化。**採用は見送り**。今後は「確率上位 K に限定したうえで EV×信頼度」など候補プールを絞る拡張を検討する。

結論
現状の「EV×信頼度」選抜では、閾値以上の候補を広く取るほど bet 数が増え ROI が悪化。**採用は見送り**。今後は「確率上位 K に限定したうえで EV×信頼度」など候補プールを絞る拡張を検討する。

ログ: experiments/logs/EXP-0009_selection_confidence_sweep.md


---

# Leaderboard Summary

| EXP | strategy | ROI | bets |
|-----|----------|-----|------|
| EXP-0007 | top_n=3, ev=1.18 | **-14.54%** (n_w=12) | — |
| EXP-0006 | top_n=3, ev=1.20 | **-14.88%** (n_w=12) | — |
| EXP-0007 | top_n=4, ev=1.05 | **-17.85%** (n_w=12) | — |
| EXP-0006 | top_n=6, ev=1.00 | **-18.78%** (n_w=12) | — |
| EXP-0006 | top_n=3, ev=1.20 (grid) | -10.94% (n_w=6) | — |

詳細は experiments/leaderboard.md 参照。

---

# Current Findings

- EV threshold を下げると bet 数が増える。ev=1.18 が 1 位（-14.54%）、ev=1.20 が 2 位（-14.88%）。
- top_n が大きいと ROI が悪化する傾向（top_n=3 が最良、top_n=6 で -18.78%）。
- bet sizing は fixed が最良。Kelly 系は資金制約で破綻リスクあり。
- calibration は sigmoid が none より有利（-14.88% vs -15.80%）。
- xgboost が lightgbm より ROI 良好（-14.88% vs -20.90%）。

---

# Open Questions

- EXP-0008 Task3: ensemble（確率平均）で bet_count=0 となる不具合。予測マージ／パス参照の修正が必要。
- 暫定 best（n_w=4）top_n=3, ev=1.25 は n_w=12 再評価が未実施。

---

# Next Experiments

- ensemble 不具合修正後の再評価。
- top_n / EV threshold の追加 sweep（必要に応じて）。
- probability calibration の詳細比較（必要に応じて）。
