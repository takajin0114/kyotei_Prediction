# System Architecture

## Data Source

**SQLite**

- `kyotei_predictor/data/kyotei_races.sqlite`

**tables**

- races
- odds
- race_canceled

---

## Prediction Problem

- 6艇レース
- 3連単
- 120 classes

---

## Pipeline

```
data
  ↓
feature engineering
  ↓
model training
  ↓
probability prediction
  ↓
EV calculation
  ↓
bet selection
  ↓
ROI evaluation
```

---

## Strategy B

current main strategy

| 項目 | 内容 |
|------|------|
| model | baseline B |
| calibration | sigmoid |
| betting strategy | top_n_ev |
| parameters | top_n = 6, ev_threshold = 1.20 |

---

## Evaluation

- **rolling validation**: n_windows = 12
- **metrics**: ROI, log_loss, brier_score
