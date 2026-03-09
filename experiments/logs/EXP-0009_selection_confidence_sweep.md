# Experiment: EXP-0009 Selection Strategy (top_n_ev vs top_n_ev_confidence)

## experiment id

EXP-0009

## purpose

ROI 最大化のため、買い目選抜ロジックを改善する。予測モデルは変更せず、**selection strategy** を拡張し、EV 単独ではなく **EV × 信頼度** で選抜する `top_n_ev_confidence` を追加。現行 `top_n_ev` と比較する。

## configuration

- model: xgboost, calibration: sigmoid, features: extended_features
- n_windows: 12, seed: 42
- script: scripts/exp0009_selection_confidence_sweep.py
- output: outputs/exp0009_selection_confidence_sweep.json

比較条件:
- **現行**: top_n_ev（top_n=3, ev_threshold=1.15 / 1.18 / 1.20）
- **新規**: top_n_ev_confidence（同 ev × confidence_type: pred_prob / prob_gap / entropy_adjusted）

評価指標: mean_roi_selected, median_roi_selected, overall_roi_selected, total_selected_bets, hit_rate_rank1_pct, mean_log_loss, mean_brier_score

## results

| strategy_name | ev_threshold | confidence_type | overall_roi_selected | mean_roi_selected | median_roi_selected | total_selected_bets | hit_rate_rank1_pct | mean_log_loss | mean_brier_score |
|---------------|--------------|-----------------|---------------------|-------------------|---------------------|---------------------|-------------------|---------------|------------------|
| top_n_ev_ev114 | 1.15 | — | -16.8% | -16.03 | -19.21 | 18105 | 5.38 | 5.049 | 0.9534 |
| top_n_ev_ev118 | 1.18 | — | **-14.54%** | -15.0 | -18.23 | 15407 | 4.78 | 5.013 | 0.9558 |
| top_n_ev_ev120 | 1.20 | — | -14.88% | -15.36 | -17.55 | 15249 | 4.72 | 5.013 | 0.9558 |
| top_n_ev_conf_pred_prob_ev114 | 1.15 | pred_prob | -38.79% | -38.73 | -72.91 | 35417 | 4.39 | 5.009 | 0.9551 |
| top_n_ev_conf_prob_gap_ev114 | 1.15 | prob_gap | -26.23% | -24.54 | -28.22 | 35417 | 1.8 | 5.009 | 0.9551 |
| top_n_ev_conf_entropy_adjusted_ev114 | 1.15 | entropy_adjusted | -26.23% | -24.54 | -28.22 | 35417 | 1.8 | 5.009 | 0.9551 |
| top_n_ev_conf_pred_prob_ev118 | 1.18 | pred_prob | -38.9% | -38.8 | -72.89 | 35367 | 4.36 | 5.010 | 0.9553 |
| top_n_ev_conf_prob_gap_ev118 | 1.18 | prob_gap | -26.4% | -24.68 | -28.07 | 35367 | 1.75 | 5.010 | 0.9553 |
| top_n_ev_conf_entropy_adjusted_ev118 | 1.18 | entropy_adjusted | -26.4% | -24.68 | -28.07 | 35367 | 1.75 | 5.010 | 0.9553 |
| top_n_ev_conf_pred_prob_ev120 | 1.20 | pred_prob | -38.72% | -38.63 | -73.01 | 35337 | 4.33 | 5.010 | 0.9553 |
| top_n_ev_conf_prob_gap_ev120 | 1.20 | prob_gap | -26.34% | -24.63 | -27.96 | 35337 | 1.75 | 5.010 | 0.9553 |
| top_n_ev_conf_entropy_adjusted_ev120 | 1.20 | entropy_adjusted | -26.34% | -24.63 | -27.96 | 35337 | 1.75 | 5.010 | 0.9553 |

## summary

- **現行 top_n_ev が最良**: ev=1.18 で overall_roi_selected **-14.54%**（1位）、ev=1.20 で -14.88%。bet 数は 15k 前後。
- **top_n_ev_confidence は ROI 悪化**: 全条件で overall_roi -26%〜-39%。bet 数は約 35k（ev≥閾値の**全候補**から top_n を選ぶため、対象レース数が増えている）。
- **結論**: 現状の「EV×信頼度」選抜では、閾値以上の候補を広く取るほど bet 数が増え ROI が悪化。**採用は見送り**。今後は「確率上位 K に限定したうえで EV×信頼度」など候補プールを絞る拡張を検討する。

## notes

- 実行: `PYTHONPATH=. python3 scripts/exp0009_selection_confidence_sweep.py --db-path kyotei_predictor/data/kyotei_races.sqlite --n-windows 12 --seed 42`
- confidence_type: pred_prob（予測確率）, prob_gap（1位-2位確率差）, entropy_adjusted（1/(1+race_entropy)）
- selection_score = ev × confidence の降順で top_n を選ぶ。ev_threshold 以上の候補のみ対象。
