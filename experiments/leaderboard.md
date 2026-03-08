# Experiment Leaderboard

このファイルは主要実験の比較表を管理する。

## ROI Leaderboard

| Rank | Experiment ID | Model | Calibration | Features | Strategy | overall_roi_selected | Notes |
|---|---|---|---|---|---|---|---|
| 1 | EXP-0005 | xgboost | sigmoid | extended_features | top_n_ev | **-20.7%** (n_w=12) | 新 reference 候補 |
| 2 | EXP-0005 | lightgbm | sigmoid | extended_features | top_n_ev | -29.9% (n_w=12) | 安定性良好 |
| 3 | EXP-0004 | sklearn baseline | sigmoid | extended_features | top_n_ev | -27.7% (n_w=12) | 現行 reference |
| 4 | EXP-0001 | sklearn baseline | sigmoid | extended_features | top_n_ev | -28% | 旧 reference |
| - | EXP-0002 | sklearn baseline | sigmoid | extended_features_v2 | top_n_ev | -35% (n_w=2) | v2 比較・hold |
| - | EXP-0004 | sklearn baseline | sigmoid | extended_features_v2 | top_n_ev | -33.76% (n_w=12) | v2 正式比較・hold |

## EV Threshold Sweep (ev_threshold_only, EXP-0005)

| ev_threshold | overall_roi | mean_roi | median_roi | bet_count | profit | max_drawdown |
|---|---|---|---|---|---|---|
| 1.05 | -48.95% | -49.05 | -50.38 | 212614 | -10,406,510 | 10,406,510 |
| 1.10 | -49.56% | -49.65 | -49.48 | 204223 | -10,121,210 | 10,121,210 |
| 1.15 | -50.83% | -50.95 | -49.52 | 196230 | -9,974,130 | 9,974,130 |
| 1.20 | -51.23% | -51.49 | -51.53 | 188699 | -9,667,800 | 9,667,800 |
| 1.25 | -51.35% | -51.61 | -51.55 | 181616 | -9,325,560 | 9,325,560 |

## Notes

- EXP-0005 で sklearn / LightGBM / XGBoost を n_windows=12 で比較。XGBoost が最良 ROI（-20.7%）で adopt。
- EXP-0005 ev_threshold_sweep: ev_threshold_only 戦略で threshold 1.05〜1.25 を比較（n_w=6）。最良 ROI は ev=1.05 で -48.95%。
- この表は主に overall_roi_selected で比較する
- 同程度なら安定性（std_roi_selected）も考慮する
- extended_features_v2 は n_windows=12 でも extended_features より ROI 悪化 → hold
- AI は新しい提案をする前に leaderboard を確認すること
