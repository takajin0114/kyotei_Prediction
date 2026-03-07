# Experiment Leaderboard

このファイルは主要実験の比較表を管理する。

## ROI Leaderboard

| Rank | Experiment ID | Model | Calibration | Features | Strategy | overall_roi_selected | Notes |
|---|---|---|---|---|---|---|---|
| 1 | EXP-0001 | sklearn baseline | sigmoid | extended_features | top_n_ev | -28% | current reference |
| - | EXP-0002 | sklearn baseline | sigmoid | extended_features_v2 | top_n_ev | -35% (n_w=2) | v2 比較・hold |

## Notes

- この表は主に overall_roi_selected で比較する
- 同程度なら安定性（std_roi_selected）も考慮する
- AI は新しい提案をする前に leaderboard を確認すること
