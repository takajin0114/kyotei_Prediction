# Next Tasks

新しいモデル比較を始める前に、[leaderboard](../../experiments/leaderboard.md) と [open_questions](../../experiments/open_questions.md) を確認すること。

## Priority 1

- Strategy B pipeline stabilization

## Priority 2

- rolling validation automation

## Priority 3

- LightGBM model sweep

## Priority 4

- XGBoost model sweep

## Priority 5

- ranking probability model
  - P(1st)
  - P(2nd | 1st)
  - P(3rd | 1st, 2nd)

## Priority 6

- feature engineering
  - extended_features_v2 を n_windows=12 で再評価（EXP-0002 は n_windows=2）
  - DB 由来の venue/course 成績・直近N走（recent form）を v2 に組み込む
  - course × venue performance / recent form / motor trend / relative race strength の実データ化
