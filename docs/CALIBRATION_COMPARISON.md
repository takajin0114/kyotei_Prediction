# Calibration 比較

| calibration | mean_roi_selected | median_roi_selected | std_roi_selected | overall_roi_selected | total_selected_bets | mean_selected_bets_per_window | mean_log_loss | mean_brier_score |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| none | -26.9 | -26.9 | 5.01 | -27.17 | 4659 | 2329.5 | 4.197415 | 0.947711 |
| sigmoid | -19.72 | -19.72 | 14.07 | -20.39 | 7585 | 3792.5 | 5.230171 | 0.947853 |
| isotonic | -38.5 | -38.5 | 1.99 | -38.56 | 8190 | 4095 | 23.72651 | 0.944274 |

(n_windows=2)
