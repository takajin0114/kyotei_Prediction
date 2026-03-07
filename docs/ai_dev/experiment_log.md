# Experiment Log

ここではモデル実験結果の概要を記録する。詳細な個別実験は [experiments/logs/](../../experiments/logs/) に保存する。

---

## Experiment 001

| 項目 | 内容 |
|------|------|
| Model | baseline B |
| Calibration | sigmoid |
| Features | extended_features |
| Strategy | top_n_ev |
| Parameters | top_n = 6, ev_threshold = 1.20 |

**Result**

- overall_roi_selected: -28%

**Notes**

- EV strategy tuning alone has limited improvement

**Next step**

- model improvement
