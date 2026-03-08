---
experiment_id: EXP-0003
date: "2026-03-07"
status: completed
objective: feature_set の明示引数化と extended_features_v2 への DB 由来 recent_form / venue_course 実装。v2 を本当に使える形にする。
model: sklearn baseline
calibration: sigmoid
features:
  - extended_features
  - extended_features_v2
strategy: top_n_ev
validation:
  method: rolling_validation
  n_windows: 12
decision: pending_n12_comparison
priority: high
tags:
  - feature_engineering
  - feature_set
  - recent_form
  - venue_course
related_experiments:
  - EXP-0001
  - EXP-0002
---

# EXP-0003 feature_set 明示化と v2 DB 由来特徴の実装

## Purpose

1. **feature_set の明示引数化**: train / predict / rolling validation / feature_sweep で feature_set を引数として扱い、優先順位を「明示引数 > 環境変数 > デフォルト」に統一。学習時の feature_set を meta.json に保存し、予測時に不一致なら warning を出す。
2. **extended_features_v2 の実データ化**: プレースホルダーだった recent_form / venue_course を、DB から取得した選手履歴で計算。リーク防止（対象レース以前の履歴のみ使用）と欠損時の防御的埋めを実施。
3. **n_windows=12 での正式比較の準備**: 上記実装のうえ、feature_sweep で extended_features と extended_features_v2 を n_windows=12 で比較可能にした。

## Implementation Summary

### feature_set 明示化

- `run_baseline_train(..., feature_set=None)` / `run_baseline_predict(..., feature_set=None)` を追加。未指定時は ENV またはデフォルト。
- `save_baseline_model` / `save_baseline_model_metadata` で feature_set を meta.json に保存。`load_baseline_model_metadata` で feature_set を返す。
- rolling_validation_windows.run_one_window に feature_set を渡し、train/predict にそのまま渡す。rolling_validation_roi は feature_set を summary に含める。
- feature_sweep は各 feature set で run_rolling_validation_roi(..., feature_set=...) を呼ぶ。
- CLI: baseline_train / baseline_predict に `--feature-set` を追加。

### DB 由来特徴（recent_form / venue_course）

- **racer_history.py**: `get_racer_history_from_db` で (reg_no, race_date, stadium, arrival) のリストを取得。`date_to` を指定した場合は対象日より前のみ（予測時リーク防止）。`compute_recent_form`（直近N走の平均着順正規化・1着率・3着内率・sample_size）、`compute_venue_form`（当該場の平均着順正規化・1着率・sample_size）を実装。
- **state_vector.py**: extended_features_v2 時、`_build_extended_v2_extras(..., racer_history_cache, race_date, stadium)` で 6艇×5（recent×3 + venue×2）+ motor_trend 8 + relative_race_strength 7 = 45 次元を追加。cache が無い場合は 0.5/0 で防御的に埋める。
- **train**: feature_set==extended_features_v2 かつ db_path があるとき、`get_racer_history_from_db(db_path, date_from=train_start, date_to=train_end)` でキャッシュを組み、`_collect_training_data_from_repository` および `collect_training_data` に `racer_history_cache` を渡す。
- **predict**: feature_set==extended_features_v2 かつ db_path があるとき、`get_racer_history_from_db(db_path, date_to=prediction_date)` でキャッシュを組み、`build_race_state_vector(..., racer_history_cache=cache)` に渡す。

### Tests

- meta に feature_set を保存・読込するテスト。予測時 feature_set mismatch で warning がログに出すことを検証。
- racer_history: 履歴あり/なし、as_of_date より前のみ使用（リークなし）、履歴不足時の防御的戻り値を検証。
- rolling_validation summary の標準キー維持（feature_set を明示渡して実行）。

## Next Step（完了）

- **n_windows=12 正式比較**: EXP-0004 で実施済み。v2 は ROI 悪化のため hold 判断。experiments/logs/EXP-0004_n12_extended_features_v2_formal_comparison.md を参照。

## Configuration (for n_windows=12 comparison)

- Model: sklearn baseline (Strategy B)
- Calibration: sigmoid
- Strategy: top_n_ev（top_n / ev_threshold は現行基準）
- Seed: 42
- n_windows: 12
- Compare: extended_features vs extended_features_v2
