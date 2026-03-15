# EXP-0064: Selected Race EV Threshold Search

## 実験目的

EXP-0063 で有効だった Selected Race EV Filter の閾値最適化。race_selected_ev = Σ(selected_prob×odds) でレースをフィルタし、閾値 1.02〜1.08 を探索する。

## 実装内容

- 閾値: CASE0 なし、CASE1≥1.02、CASE2≥1.03、CASE3≥1.04、CASE4≥1.05、CASE5≥1.06、CASE6≥1.08。
- 戦略: d_hi475 + switch_dd4000。n_windows=36。

## 実験条件

| 項目 | 値 |
|------|-----|
| n_windows | 36 |
| 戦略 | d_hi475 + switch_dd4000 |
| 予測 | outputs/ev_cap_experiments/rolling_roi_predictions |
| DB | kyotei_races.sqlite |

## 結果表（n_windows=36）

| variant | ROI | total_profit | max_drawdown | profit_per_1000_bets | bet_count | longest_losing_streak |
|---------|-----|--------------|--------------|----------------------|-----------|------------------------|
| CASE0_baseline | 0.53% | 484 | 15,886 | 469.45 | 1,031 | 4 |
| CASE1_race_selected_ev_ge_102 | -1.05% | -894 | 14,998 | -947.03 | 944 | 4 |
| CASE2_race_selected_ev_ge_103 | -1.05% | -894 | 14,998 | -947.03 | 944 | 4 |
| CASE3_race_selected_ev_ge_104 | -1.05% | -894 | 14,998 | -947.03 | 944 | 4 |
| CASE4_race_selected_ev_ge_105 | -1.05% | -894 | 14,998 | -947.03 | 944 | 4 |
| CASE5_race_selected_ev_ge_106 | -1.05% | -894 | 14,998 | -947.03 | 944 | 4 |
| CASE6_race_selected_ev_ge_108 | -1.05% | -894 | 14,998 | -947.03 | 944 | 4 |

## 考察

- **n_w=36 では baseline（フィルタなし）が最良**: 唯一黒字（ROI 0.53%、profit 484）。race_selected_ev≥1.02〜1.08 のいずれも赤字（ROI -1.05%、profit -894）。
- EXP-0063（n_w=12）では race_selected_ev フィルタが有効だったが、**長期（n_w=36）ではフィルタが利益を損なう**。期間依存性あり。
- **採用判断**: n_w=36 に合わせる場合は **Selected Race EV フィルタは使わない**（CASE0 維持）。n_w=12 に合わせる場合は EXP-0063 どおり race_selected_ev≥1.05 を採用可能。horizon に応じた使い分けを推奨。

---

- 実行コマンド: `python3 -m kyotei_predictor.tools.run_exp0064_selected_race_ev_threshold --n-windows 36`
- 結果 JSON: `outputs/selected_race_ev_threshold/exp0064_selected_race_ev_threshold.json`
