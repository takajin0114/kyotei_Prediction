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

## Notes

- EXP-0005 で sklearn / LightGBM / XGBoost を n_windows=12 で比較。XGBoost が最良 ROI（-20.7%）で adopt。
- この表は主に overall_roi_selected で比較する
- 同程度なら安定性（std_roi_selected）も考慮する
- extended_features_v2 は n_windows=12 でも extended_features より ROI 悪化 → hold
- AI は新しい提案をする前に leaderboard を確認すること
