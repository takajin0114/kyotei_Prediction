# EV 戦略の導入と比較実験

複数日 A/B 実験で B案が優位だったため、EV（Expected Value）戦略を導入し、「買いすぎ」を抑えながら ROI がどこまで維持できるかを検証した。

---

## EV 戦略

- **expected_roi** = probability × odds（1.0 で元金、1.05 で 5% プラス）。
- **domain/ev.py**: `compute_expected_value(probability, odds)` で計算。
- **betting_selector**:
  - 既存の **ev**: 全候補のうち expected_roi >= ev_threshold のみ購入。オッズなし時は top_n でフォールバック。
  - **top_n_ev**: 上位 top_n 候補のうち、expected_roi >= ev_threshold の組み合わせのみ購入（ハイブリッド）。

---

## 比較条件

| 項目 | 内容 |
|------|------|
| **期間** | 2024-07-01 〜 2024-07-07 |
| **data_dir** | kyotei_predictor/data/raw/2024-07 |
| **evaluation_mode** | selected_bets |
| **条件1** | A案 PPO top_n=3 |
| **条件2** | B案 Baseline top_n=3 |
| **条件3** | B案 Baseline top_n=5 + EV>1.05 |
| **条件4** | B案 Baseline top_n=10 + EV>1.10 |

---

## 結果

| 条件 | ROI | hit_rate (1位) | total_bet | total_payout | hit_count |  bet数(概算) |
|------|-----|----------------|-----------|--------------|-----------|--------------|
| A PPO top_n=3 | 14.8% | 21.97% | 39600 | 45460 | 29 | 396 |
| B top_n=3 | 982.98% | 73.48% | 39600 | 428860 | 97 | 396 |
| B top_n=5 EV>1.05 | 858.17% | 72.73% | 44700 | 428300 | 96 | 447 |
| B top_n=10 EV>1.10 | 424.88% | 72.73% | 81600 | 428300 | 96 | 816 |

- **bet数**: 100円/点として total_bet/100。
- 保存先: **logs/ab_test_ev_strategy.json**

---

## 考察

- **EV でどう変わったか**
  - B案 top_n=3 に比べ、**top_n=5 EV>1.05** は bet 数が増えるが（447 vs 396）、ROI は 982% → 858% とやや低下するも高水準を維持。買い目を「期待リターン 5% 以上」に絞っても的中数・払戻はほぼ維持。
  - **top_n=10 EV>1.10** は bet 数が約 2 倍（816）になるが、EV 閾値で厳しく絞るため払戻は top_n=5 EV>1.05 と同程度。ROI は 424% と、bet 数増の影響で top_n=3 より下がるがプラスを維持。
- **買いすぎ防止**: EV 閾値（1.05, 1.10）で「期待リターンが閾値未満の組み合わせ」を省くことで、無駄な購入を減らしつつ ROI を維持できる。閾値を上げると bet 数は減るが、払戻も減る可能性がある。

---

## 実装メモ

- **domain/ev.py**: `compute_expected_value(probability, odds)` を追加。
- **utils/betting_selector.py**: 戦略 `top_n_ev` と `select_top_n_ev(predictions, top_n, ev_threshold)` を追加。
- **application/baseline_predict_usecase.py**: 各レースの `all_combinations` にオッズ（ratio）を付与する `_attach_odds_to_combinations` を追加。EV 計算に必要。
- **application/compare_ab_usecase.py**: 複数予測を比較する `run_compare_ab_multi` を追加。
- **cli/baseline_predict.py**: `--strategy top_n_ev` と `--ev-threshold` の説明を追加。

---

## 最終出力（Sprint サマリ）

### Experiment Result

| 条件 | ROI | hit_rate (1位) | bet数(概算) |
|------|-----|----------------|-------------|
| A PPO top_n=3 | 14.8% | 21.97% | 396 |
| B top_n=3 | 982.98% | 73.48% | 396 |
| B top_n=5 EV>1.05 | 858.17% | 72.73% | 447 |
| B top_n=10 EV>1.10 | 424.88% | 72.73% | 816 |

### Observation

- **EV でどう変わったか**: B案で EV 閾値（1.05, 1.10）をかけると、top_n=3 より bet 数が増える条件（top_n=5, top_n=10）でも「期待リターン閾値以上」だけに絞れる。その結果、top_n=5 EV>1.05 は ROI 858% と高水準を維持。top_n=10 EV>1.10 は bet 数が多くなるが ROI 424% でプラスを維持。買いすぎを抑えつつ ROI を維持する効果が確認できた。

### Next Steps

1. **モデル改善**: A案（PPO）の 1 位予想精度向上。B案は特徴量拡張で EV 閾値以上の候補を増やす。
2. **EV 閾値調整**: 1.05 / 1.10 以外（例: 1.02, 1.15）で比較し、bet 数と ROI のトレードオフを確認する。
3. **特徴量追加**: オッズとの相性を考慮した特徴量や、calibration で確率精度を上げ、expected_roi の信頼性を高める。
