# Experiment Field Definitions

実験ログの YAML front matter で使う項目の定義。集計・比較の入力項目を統一する。

| Field | Type | Required | Description | Allowed / Notes |
|-------|------|----------|-------------|-----------------|
| experiment_id | string | yes | 実験の一意識別子 | EXP-XXXX 形式の連番 |
| date | string | yes | 実験日または記録日 | YYYY-MM-DD |
| status | string | yes | 実験の進行状態 | planned, running, completed, rejected |
| objective | string | no | 実験の目的（短文） | 自由文 |
| hypothesis | string | no | 何を改善すると ROI が良くなると考えたか | 自由文 |
| model | string | no | モデル名 | 例: sklearn baseline, LightGBM, XGBoost |
| calibration | string | no | 確率キャリブレーション | none, sigmoid, isotonic |
| features | array of string | no | 特徴量セット名のリスト | 例: extended_features, venue_course_features |
| strategy | string | no | ベッティング戦略 | 例: top_n_ev |
| parameters.top_n | number or null | no | 上位何件を候補にするか | 整数。未確定時は null |
| parameters.ev_threshold | number or null | no | EV 閾値 | 例: 1.20。未確定時は null |
| validation.method | string | no | 検証方法 | 例: rolling_validation |
| validation.n_windows | number or null | no | ロールング検証の window 数 | 整数。未確定時は null |
| metrics.overall_roi_selected | number or null | no | 全体 ROI（選択ベットのみ） | 小数で -0.28 など。% ではない |
| metrics.mean_roi_selected | number or null | no | window 別 ROI の平均 | 同上 |
| metrics.median_roi_selected | number or null | no | window 別 ROI の中央値 | 同上 |
| metrics.std_roi_selected | number or null | no | window 別 ROI の標準偏差 | 同上 |
| metrics.mean_log_loss | number or null | no | 平均 log loss | 未確定時は null |
| metrics.mean_brier_score | number or null | no | 平均 Brier score | 未確定時は null |
| decision | string | no | 採用判断 | adopt, hold, reject, pending |
| priority | string | no | 優先度（メモ用） | high, medium, low |
| tags | array of string | no | 検索用タグ | 例: baseline, reference |
| related_experiments | array of string | no | 関連する実験 ID | 例: ["EXP-0002"] |

## Allowed values（抜粋）

- **status**: `planned` | `running` | `completed` | `rejected`
- **decision**: `adopt` | `hold` | `reject` | `pending`
- **priority**: `high` | `medium` | `low`

- **features**: 配列。1つ以上指定可。
- **related_experiments**: 配列。空でも可。
- 数値が未確定のときは `null` を指定してよい。
