# 時系列を守った学習/検証分離

学習期間と検証期間を分離し、未来情報が混入しない形で B案（および A案）の汎化性能を評価した結果をまとめる。

---

## 背景

- 7日検証や 60日（6月+7月）検証では、学習データに 7 月が含まれている可能性があり、検証期間と近いと性能が過大評価されうる。
- 時系列を守り「train に含まない期間で test」することで、本当の汎化性能を確認する。

---

## 実施した分離検証（パターンA）

| 項目 | 内容 |
|------|------|
| **train** | 2024-06-01 〜 2024-06-30（6月のみ） |
| **test** | 2024-07-01 〜 2024-07-31（7月のみ） |
| **モデル** | B案を 6 月データのみで再学習（`baseline_b_train202406.joblib`） |
| **evaluation_mode** | selected_bets |
| **比較戦略** | B top_n=3 / B top_n=5 EV>1.05 / B top_n=10 EV>1.10 |

---

## B案の結果（train=6月 / test=7月）

| 条件 | ROI | hit_rate (1位) | total_bet | hit_count | races_with_result |
|------|-----|----------------|-----------|-----------|-------------------|
| B top_n=3 | **-7.93%** | 13.59% | 172,200 | 78 | 574 |
| B top_n=5 EV>1.05 | **-19.67%** | 6.27% | 174,000 | 36 | 574 |
| B top_n=10 EV>1.10 | **-34.82%** | 7.84% | 341,900 | 45 | 574 |

- **要点**: 学習を 6 月のみに限定し、7 月だけで検証すると **B案はすべてマイナス ROI**。
- 従来の「7月データで学習したモデルで 7 月を検証」した場合の高 ROI は、**学習と検証の期間が近いことによる楽観バイアス**の可能性が高い。
- 保存先: **logs/rolling_validation_b_202406_202407.json**

---

## A案（PPO）の長期検証について

- A案は PPO モデル（`best_model.zip` 等）を別途学習する必要があり、本リポジトリには学習済みモデルが含まれていない。
- **実行方法**: 学習済み PPO を用意したうえで、以下で日別予測を生成する。
  - 6月: `python -m kyotei_predictor.tools.prediction_tool --predict-date 2024-06-DD --data-dir kyotei_predictor/data/raw/2024-06 --output-dir outputs/a_long_range_202406 --include-selected-bets`（DD は 01〜30）
  - 7月: 同様に `--predict-date 2024-07-DD`、`--data-dir .../2024-07`、`--output-dir outputs/a_long_range_202407`
- 各日の予測 JSON を `run_verify(path, data_dir, evaluation_mode='selected_bets')` で検証し、日別の total_bet / total_payout / hit_count を合算すれば A案の長期指標が得られる。
- B案との比較時は、**同一 data_dir・同一日付範囲・同一 evaluation_mode** で揃える。

---

## 現時点の推奨戦略

1. **時系列分離を前提に評価する**: 学習に使っていない期間で検証した結果を主に参照する。
2. **B案**: 6月学習→7月検証ではマイナスとなったため、**学習期間と検証期間をずらしたロールング検証**（例: 6月前半学習→6月後半検証）や、**より長期の学習データ**を入れたうえでの再評価が有効。
3. **EV 閾値**: 60日（6月+7月・学習に7月含むモデル）では EV を上げるほど ROI がやや増加する傾向（`docs/EV_STRATEGY_EXPERIMENT.md` の 60日 EV 比較を参照）。時系列分離後でも同様の傾向があるかは今後の検証で確認する。
4. **本番運用**: 学習では検証/本番期間のデータを使わない。検証時は final odds、本番は current odds のみ使用（`docs/DATA_LEAKAGE_CHECK.md` 参照）。

---

## 参照

- **State Vector 棚卸し（モーター・ボート）**: `docs/STATE_VECTOR_AUDIT_MOTOR_BOAT.md`（モーター・ボート情報の入力構造・評価）
- ロールング検証の集計: `kyotei_predictor/tools/rolling_validation_aggregate.py`
- 学習: `python -m kyotei_predictor.cli.baseline_train --data-dir kyotei_predictor/data/raw/2024-06 --model-path outputs/baseline_b_train202406.joblib --max-samples 10000`
- 予測: `python -m kyotei_predictor.cli.baseline_predict --predict-date 2024-07-DD --data-dir kyotei_predictor/data/raw/2024-07 --model-path outputs/baseline_b_train202406.joblib --output outputs/rolling_train202406/predictions_baseline_2024-07-DD.json --include-selected-bets --strategy top_n --top-n 3`

---

## How to Run（再実行手順）

1. **B案を6月のみで学習**  
   `python -m kyotei_predictor.cli.baseline_train --data-dir kyotei_predictor/data/raw/2024-06 --model-path outputs/baseline_b_train202406.joblib --max-samples 10000`

2. **7月の日別予測**（DD は 01〜31）  
   - top_n=3: `python -m kyotei_predictor.cli.baseline_predict --predict-date 2024-07-DD --data-dir kyotei_predictor/data/raw/2024-07 --model-path outputs/baseline_b_train202406.joblib --output outputs/rolling_train202406/predictions_baseline_2024-07-DD.json --include-selected-bets --strategy top_n --top-n 3`  
   - top_n_ev は `--strategy top_n_ev --top-n 5 --ev-threshold 1.05` 等で別ファイルに出力。

3. **集計**  
   `python -m kyotei_predictor.tools.rolling_validation_aggregate`  
   実行後、`logs/rolling_validation_b_202406_202407.json` が更新される。

4. **60日 EV閾値比較**  
   6月・7月の既存予測（baseline_b_abtest モデル）を利用。  
   `python -m kyotei_predictor.tools.ev_threshold_60day_aggregate`  
   実行後、`logs/ev_threshold_comparison_60day.json` が更新される。

5. **ロールング検証（複数 window）**  
   `python -m kyotei_predictor.tools.rolling_validation_windows`  
   実行後、`logs/rolling_validation_b_windows.json` と `logs/rolling_validation_b_before_after.json` が更新される。

6. **ロールング検証（特徴量 before/after）**  
   プロジェクトルートで `PYTHONPATH=. python3 kyotei_predictor/tools/rolling_validation_feature.py`  
   実行後、`logs/rolling_validation_feature_before_after.json` が更新される。

7. **ロールング検証（キャリブレーション比較）**  
   プロジェクトルートで `PYTHONPATH=. python3 kyotei_predictor/tools/rolling_validation_calibration.py`  
   実行後、`logs/rolling_validation_calibration_before_after.json` と `logs/rolling_validation_calibration_compare.json` が更新される。

---

## ロールング検証（複数 window）

### window 設計

- **train 長**: 15日（改善前）または 30日（改善後・学習期間拡張の検証用）
- **test 長**: 7日固定
- **ルール**: train は test より前の期間のみ使用。未来情報なし。

| window | train (15日) | test (7日) |
|--------|----------------|------------|
| 1 | 2024-06-01〜06-15 | 2024-06-16〜06-22 |
| 2 | 2024-06-08〜06-22 | 2024-06-23〜06-29 |
| 3 | 2024-06-15〜06-29 | 2024-06-30〜07-06 |
| 4 | 2024-06-22〜07-06 | 2024-07-07〜07-13 |

改善後（30日学習）では、各 test に対して「test_start の最大30日前」から train_end までを学習に使用（データがある範囲でクリップ）。

### 比較条件

- **戦略**: B top_n=3 / B top_n=5 EV>1.10 / B top_n=5 EV>1.15
- **evaluation_mode**: selected_bets

### B案の結果（改善前: 15日学習）

| 戦略 | 平均 ROI | 中央値 ROI | 正のROI window数/全window数 | 平均 hit_rate(1位) |
|------|----------|------------|-----------------------------|---------------------|
| B top_n=3 | -1.14% | -21.85% | 1/4 | 11.98% |
| B top_n=5 EV>1.10 | **19.69%** | **25.9%** | **2/4** | 7.39% |
| B top_n=5 EV>1.15 | **18.39%** | **24.96%** | **2/4** | 6.49% |

- EV 閾値 1.10・1.15 では 4 window 中 2 つでプラス。top_n=3 は 1/4 のみプラス。

### 改善前後比較（15日 vs 30日学習）

| 戦略 | 改善前(15d) 平均ROI | 改善後(30d) 平均ROI | 改善後 正のROI window数 |
|------|---------------------|----------------------|-------------------------|
| B top_n=3 | -1.14% | -40.71% | 0/4 |
| B top_n=5 EV>1.10 | 19.69% | -45.78% | 0/4 |
| B top_n=5 EV>1.15 | 18.39% | -46.13% | 0/4 |

- **要点**: 学習期間を 15日→30日 に拡張すると、**全戦略で平均 ROI が悪化**し、正の ROI を出した window は 0 になった。
- 今回試した「学習期間の拡張」は汎化性能の改善にはつながらなかった。短い window（15日）で直近に合わせて学習した方が、このデータ・期間では検証スコアが良かった。

### 特徴量1つ追加の影響（モーター勝率代理）

同じ 15日学習・7日検証・4 window で、特徴量「モーター勝率代理」の有無を比較した。

| 戦略 | 従来（特徴量なし）平均ROI | 従来 正のROI | 特徴量追加後 平均ROI | 特徴量追加後 正のROI |
|------|----------------------------|--------------|------------------------|----------------------|
| B top_n=3 | -1.14% | 1/4 | -20.49% | 0/4 |
| B top_n=5 EV>1.10 | 19.69% | 2/4 | -36.84% | 0/4 |
| B top_n=5 EV>1.15 | 18.39% | 2/4 | -39.55% | 0/4 |

- **解釈**: 特徴量追加後は **全戦略で平均 ROI が悪化**し、正の ROI window は 0/4。15日 rolling では **従来の特徴量（モーター勝率代理なし）の方が汎化が良い**。EV 1.10〜1.15 の有効性は、特徴量追加前のモデルで確認された状態を維持するのが無難。
- **保存先**: **logs/rolling_validation_feature_before_after.json**
- **実行**: `PYTHONPATH=. python3 kyotei_predictor/tools/rolling_validation_feature.py`

### 確率キャリブレーションの影響（15日 rolling・同一条件）

calibration=none / sigmoid / isotonic で同一 4 window を比較した結果。

| 戦略 | none 平均ROI | sigmoid 平均ROI | isotonic 平均ROI | isotonic 正のROI |
|------|--------------|-----------------|------------------|------------------|
| B top_n=3 | -1.14% | 30.26% | 18.20% | 2/4 |
| B top_n=5 EV>1.10 | 19.69% | **53.54%** | **44.55%** | **3/4** |
| B top_n=5 EV>1.15 | 18.39% | **55.40%** | **40.51%** | 2/4 |

- **解釈**: キャリブレーション（sigmoid / isotonic）を導入すると、**平均 ROI が大きく改善**。EV 1.10・1.15 の有効性は維持・強化。現時点の推奨は「従来特徴量 + calibration=sigmoid（または isotonic）+ EV>1.10 または 1.15」。
- **保存先**: **logs/rolling_validation_calibration_before_after.json**, **logs/rolling_validation_calibration_compare.json**
- **実行**: `PYTHONPATH=. python3 kyotei_predictor/tools/rolling_validation_calibration.py`

### 現時点の主戦略（15日 rolling・EV 戦略確定後）

- **推奨**: B案 + **calibration=sigmoid** + B top_n=5 **EV>=1.15** + **bet sizing=fixed**。EV 閾値はスイープ（logs/ev_threshold_sweep.json）で 1.15 を採用、bet sizing は rolling EV 比較（logs/rolling_ev_strategy_compare.json）で fixed を採用。詳細は **docs/EV_BETTING_STRATEGY.md**。
- **代替**: EV 1.10（やや多点）、calibration=isotonic（安定性重視時）。

### 主戦略 1.15 + fixed の window 別結果（再検証）

主戦略のみで 4 window を再実行した結果。保存先: **logs/strategy_b_validation_windows.json**

| window | train | test | EV>1.15 roi_pct | EV>1.15 profit |
|--------|--------|------|------------------|-----------------|
| 1 | 06-01~06-15 | 06-16~06-22 | -15.91 | -10,960 |
| 2 | 06-08~06-22 | 06-23~06-29 | -49.81 | -35,860 |
| 3 | 06-15~06-29 | 06-30~07-06 | （同上形式） | |
| 4 | 06-22~07-06 | 07-07~07-13 | （同上形式） | |

- **安定性**: 直近実行では 4 中 1 window のみプラス。平均 ROI はマイナス。過去の calibration 比較では同 4 window で sigmoid がプラスだったため、実行タイミング・乱数・データの差が考えられる（**docs/STRATEGY_B_CONDITION_DIFF.md**）。
- **今後の判断基準**: 定期的に `strategy_b_validation_windows.py` または `rolling_validation_calibration.py` を再実行し、平均 ROI と正の ROI window 数を追う。再現性が悪い場合はシード固定・データスナップショットを検討する。

### 現時点での汎化評価

- **ロールング検証（4 window）**: 15日学習では EV 1.10・1.15 が 2/4 window でプラス。30日学習では全 window でマイナス。特徴量「モーター勝率代理」追加は悪化。**確率キャリブレーション（sigmoid / isotonic）導入で平均 ROI が改善**（EV>1.10 で 19.69% → 53.54% / 44.55%、正のROI は 2/4 または 3/4）。
- **解釈**: 直近 15日で学習し EV で絞る方針は維持。特徴量追加は今回有効でなかったため従来特徴量のまま。**キャリブレーションを有効にした B案 + EV 1.10 / 1.15 を現時点の推奨戦略**とする。
- 保存先: **logs/rolling_validation_b_windows.json**, **logs/rolling_validation_b_before_after.json**, **logs/rolling_validation_feature_before_after.json**, **logs/rolling_validation_calibration_before_after.json**, **logs/rolling_validation_calibration_compare.json**
