# Experiment: EXP-0039 EV band + probability + race内EV順位フィルタ

## experiment id

EXP-0039

## purpose

EXP-0038 で skip_top20pct + 3≤EV<5 + prob≥0.05（ev3_5_prob005）が adopt。race 内の EV 1位は市場歪み・過大評価の影響を受けやすい可能性があるため、EV band + probability に **race 内 EV 順位**条件を追加し、ROI・利益効率・ドローダウンの改善を検証する。

## ベース条件

- skip_top20pct（日付内でレースを max_ev 降順に並べ、上位20%のレースを除外。EXP-0037/0038 と同一定義）
- 3 ≤ EV < 5
- prob ≥ 0.05

## rank フィルタ定義

- **race内EV順位**: そのレースの selected_bets のうち、「3≤EV<5 かつ prob≥0.05」を満たす組み合わせのみを対象に、**EV 降順**で並べたときの順位。1位＝EV 最大、2位＝2番目に大きい EV、…。
- 順位付け対象は **skip_top20pct 適用後の各レース**について、そのレース内の bet 候補（上記 EV+prob を満たすもの）のみ。日付内の並び順には依存しない。
- 集計では、各レースの stake・payout を「そのレースで条件を満たす bet 数」で按分し、variant ごとに「rank 条件を満たす bet 数」に応じて按分した stake・payout を加算。

## implementation

- ツール: `kyotei_predictor/tools/run_exp0039_ev_prob_rank_strategy.py`
- 既存 rolling predictions: `outputs/ev_cap_experiments/rolling_roi_predictions`（EXP-0037/0038 と同一）
- 処理フロー（各日付）:
  1. 対象レースを読み込み（selected_bets + all_combinations + verify 結果）
  2. レースを max_ev 降順で並べ、skip_top20pct 適用
  3. 各レースで 3≤EV<5 かつ prob≥0.05 を満たす bet を抽出し、EV 降順で順位付与（1-indexed）
  4. variant ごとに rank 条件で bet を抽出し、stake・payout を (通過 bet 数 / 当該レースの ev_prob bet 数) で按分して集計
  5. ROI, total_profit, max_drawdown, profit_per_1000_bets, bet_count, race_count を算出

## command

```bash
cd /path/to/kyotei_Prediction
python3 -m kyotei_predictor.tools.run_exp0039_ev_prob_rank_strategy \
  --db-path kyotei_predictor/data/kyotei_races.sqlite \
  --n-windows 18
```

## results table (n_windows=18)

| variant                      | ROI     | total_profit | max_drawdown | profit_per_1000_bets | bet_count | race_count |
|-----------------------------|---------|--------------|--------------|----------------------|-----------|------------|
| ev3_5_prob005               | 21.30%  | 74,150       | 31,145       | 30,081.14            | 2,465     | 2,406      |
| ev3_5_prob005_rank_le_3     | 21.30%  | 74,150       | 31,145       | 30,081.14            | 2,465     | 2,406      |
| ev3_5_prob005_rank_le_5     | 21.30%  | 74,150       | 31,145       | 30,081.14            | 2,465     | 2,406      |
| ev3_5_prob005_rank_2_5      | -81.42% | -4,885       | 4,885        | -82,796.61           | 59        | 59         |
| ev3_5_prob005_rank_2_7      | -81.42% | -4,885       | 4,885        | -82,796.61           | 59        | 59         |

- 参考: total_race_days = 126、平均 bet 数/日は baseline で約 2,465/126 ≈ 19.6。

## interpretation

1. **baseline と rank_le_3 / rank_le_5**  
   3 variant は完全に同一結果。データ上、3≤EV<5 かつ prob≥0.05 を満たす bet はレースあたり多くとも 3〜5 件程度のため、rank ≤ 3 / ≤ 5 の条件では除外が発生せず、baseline と一致した。

2. **rank_2_5 / rank_2_7（rank 1 を除外）**  
   EV 1位を除外すると、対象 bet 数が 59 に激減し、ROI -81.42%、total_profit -4,885、max_drawdown 4,885。利益の多くが **rank 1（EV 最大の bet）** に集中しており、rank 1 を外すと利益が消失し損失に転じる。

3. **race 内 EV rank フィルタの効果**  
   - rank を「上から」制限（≤3, ≤5）しても、今回のデータでは追加の絞り込みにならず改善なし。
   - rank 1 を除外（2≤rank≤5, 2≤rank≤7）すると、bet 数・利益とも大きく悪化。
   - したがって、**race 内 EV 順位フィルタは ROI・利益効率・ドローダウンの改善に寄与しなかった**。

4. **baseline と EXP-0038 の数値差**  
   EXP-0038 の ev3_5_prob005 は「レース単位で max_ev とその bet の prob が条件を満たす場合にレース全体を採用」、本実験の baseline は「レース内で 3≤EV<5 かつ prob≥0.05 を満たす bet のみを按分で集計」のため、採用レース・stake の定義が異なり、数値は完全には一致しない。

## judgment

- **reject**
- race 内 EV 順位フィルタは、rank ≤ 3 / ≤ 5 では baseline と同一で改善なし、rank 2〜5 / 2〜7（rank 1 除外）では bet 数激減・大幅赤字のため採用しない。実運用候補は **EXP-0038 の ev3_5_prob005（skip_top20pct + 3≤EV<5 + prob≥0.05）** を維持する。

## result JSON

- outputs/ev_prob_rank_strategy/exp0039_ev_prob_rank_strategy_results.json
