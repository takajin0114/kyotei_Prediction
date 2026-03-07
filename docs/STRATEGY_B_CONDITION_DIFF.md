# 主戦略 B の条件差分メモ

過去の「sigmoid でプラス結果」と、直近の「EV 戦略比較でマイナス」の差分を追跡するための整理。

---

## 1. 比較対象の実行

| 実行 | 結果の傾向 | 保存先 |
|------|------------|--------|
| キャリブレーション比較（rolling_validation_calibration） | sigmoid で EV>1.10 平均 ROI **53.54%**、EV>1.15 **55.40%**（プラス） | logs/rolling_validation_calibration_before_after.json |
| EV 閾値スイープ（ev_threshold_sweep） | 1 window で全閾値マイナス。1.15 が -15.91% で相対的に最良 | logs/ev_threshold_sweep.json |
| Rolling EV 比較（rolling_ev_strategy_compare） | 4 window で EV>1.15 平均 ROI **-21.94%**（マイナス） | logs/rolling_ev_strategy_compare.json |

---

## 2. 条件の対応関係

### 2.1 train / test window

| 項目 | キャリブレーション比較 | EV スイープ | Rolling EV 比較 |
|------|------------------------|-------------|------------------|
| window 数 | 4 | 1 | 4 |
| train 長 | 15日 | 15日 | 15日 |
| test 長 | 7日 | 7日 | 7日 |
| window 定義 | 06-01~06-15→06-16~06-22 他 4 本 | 06-01~06-15→06-16~06-22 | 上記と同じ 4 本 |

→ **window 定義は同一**。EV スイープのみ 1 window。

### 2.2 モデル・キャリブレーション

| 項目 | キャリブレーション比較 | Rolling EV 比較 |
|------|------------------------|------------------|
| calibration | none / sigmoid / isotonic を別々に学習 | sigmoid のみ |
| モデル保存先 | rolling_b_calib_{none,sigmoid,isotonic}.joblib | rolling_b_ev_compare.joblib |
| 予測保存先 | rolling_windows_15d_calib_{calib}/ | rolling_windows_15d_ev_compare/ |

→ **sigmoid 時はどちらも calibration=sigmoid で 15 日学習。ロジックは同じ。**

### 2.3 買い目・検証

| 項目 | キャリブレーション比較 | Rolling EV 比較 |
|------|------------------------|------------------|
| 戦略 | top_n=3, top_n_ev 5 with 1.10, 1.15 | 同上 |
| evaluation_mode | selected_bets | selected_bets |
| verify | run_verify(path, data_dir, evaluation_mode="selected_bets") | 同上 |
| 集計 | aggregate_by_strategy（ROI, hit_rate, total_bet 等） | 同上 + fixed/kelly_half の bankroll シミュレーション |

→ **選定・検証・ROI 集計の流れは同じ。** Rolling EV 比較は bankroll 指標を追加しているだけ。

### 2.4 データ・実行環境

| 項目 | 備考 |
|------|------|
| データディレクトリ | いずれも raw_dir（例: kyotei_predictor/data/raw）を参照。実行時点のファイル内容に依存。 |
| 実行日時 | キャリブレーション比較と Rolling EV 比較で異なる可能性。 |
| 乱数 | 学習に乱数を含むため、実行ごとにモデルが変わりうる。 |

---

## 3. 差分から考えられる原因

1. **実行タイミング・データ**  
   キャリブレーション比較と Rolling EV 比較で、raw データの範囲や中身が違う可能性（追加・修正された race_data / odds_data 等）。

2. **学習の非決定性**  
   RandomForest 等の乱数で、同じ window でも学習結果が run ごとに変わる。再実行でプラスになったりマイナスになったりしうる。

3. **モデル保存先の違い**  
   別々のディレクトリを使っているため、過去の「プラスだった run」のモデルは残っていない。再現するには **同じスクリプトを再実行**し、そのときの結果を見る必要がある。

4. **集計方法の違い**  
   ROI そのものの算出は同じ（total_payout / total_bet - 1）。bankroll シミュレーションは ROI の前後で行っているだけなので、マイナス/プラスの逆転理由にはならない。

---

## 4. 再現・追跡のしかた

- **キャリブレーション比較の再現**  
  `PYTHONPATH=. python3 kyotei_predictor/tools/rolling_validation_calibration.py`  
  → 同じ 4 window で none / sigmoid / isotonic を再計算。sigmoid の平均 ROI が再実行でどうなるか確認する。

- **主戦略のみの再検証**  
  `PYTHONPATH=. python3 kyotei_predictor/tools/strategy_b_validation_windows.py`  
  → 主戦略（EV>=1.15 + fixed）だけで 4 window を回し、logs/strategy_b_validation_windows.json で ROI を確認する。

- **1 本化フローの確認**  
  `python -m kyotei_predictor.cli.run_strategy_b --train-start 2024-06-01 --train-end 2024-06-15 --predict-date 2024-06-16 --data-dir kyotei_predictor/data/raw`  
  → 1 window だけ学習・予測・検証し、summary で ROI を確認する。

---

## 5. 結論（現時点）

- **条件の違い**: window 定義・戦略・verify・ROI 集計は揃えられる。違うのは「実行ごとのデータ・乱数・モデル保存先」。
- **なぜ以前プラスで今回マイナスか**: 上記の「データ or 乱数 or 実行タイミング」の差が最も疑わしい。コード上のロジック差では説明しにくい。
- **今後の判断**: 主戦略 1.15 + fixed は「相対的に最良」として採用しつつ、**定期的に strategy_b_validation_windows や rolling_validation_calibration を再実行**し、平均 ROI や正の ROI window 数を追う。再現性が悪い場合はデータ固定・シード固定の検討を検討する。
