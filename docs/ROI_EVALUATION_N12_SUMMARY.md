# 暫定ベスト戦略の再評価（n_windows=12・細分化 sweep）

baseline B + sigmoid のまま、ev_threshold と top_n を細かく比較した結果の要約。

## 1. 実行コマンド一覧

```bash
# 1) EV threshold 細分化（1.16, 1.18, 1.20, 1.22, 1.24）・12 window
python3 -m kyotei_predictor.tools.ev_threshold_sweep \
  --db-path kyotei_predictor/data/kyotei_races.sqlite \
  --n-windows 12 \
  --thresholds "1.16,1.18,1.2,1.22,1.24" \
  --output-dir outputs

# 2) top_n 細分化（4, 5, 6, 8）・ev=1.20 固定・12 window
python3 -m kyotei_predictor.tools.topn_sweep \
  --db-path kyotei_predictor/data/kyotei_races.sqlite \
  --n-windows 12 \
  --top-n-values "4,5,6,8" \
  --ev-threshold 1.20 \
  --output-dir outputs

# 3) 比較表の出力（CSV / MD）
python3 -m kyotei_predictor.tools.strategy_comparison_export \
  --output-dir outputs --docs-dir docs

# 4) sweep 結果の表表示
python3 -m kyotei_predictor.cli.compare_sweep_summaries --output-dir outputs
```

単一戦略の rolling validation（暫定ベスト再評価用）:

```bash
python3 -m kyotei_predictor.tools.rolling_validation_roi \
  --db-path kyotei_predictor/data/kyotei_races.sqlite \
  --n-windows 12 --ev-threshold 1.20 --top-n 5 --output-dir outputs
```

## 2. 比較結果の表

| strategy | top_n | ev_threshold | mean_roi_selected | median_roi_selected | std_roi_selected | overall_roi_selected | total_selected_bets | mean_selected_bets_per_window | mean_log_loss | mean_brier_score |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| top_n_ev | 5 | 1.16 | -29.19 | -30.4 | 9.36 | -29.37 | 42979 | 3581.58 | 5.371767 | 0.936668 |
| top_n_ev | 5 | 1.18 | -29.35 | -30.34 | 9.33 | -29.53 | 42748 | 3562.33 | 5.371767 | 0.936668 |
| top_n_ev | 5 | 1.2 | -29.24 | -30.66 | 9.51 | -29.43 | 42505 | 3542.08 | 5.371767 | 0.936668 |
| top_n_ev | 5 | 1.22 | -29.18 | -30.91 | 9.38 | -29.36 | 42308 | 3525.67 | 5.371767 | 0.936668 |
| top_n_ev | 5 | 1.24 | -29.3 | -31.04 | 9.27 | -29.47 | 42050 | 3504.17 | 5.371767 | 0.936668 |
| top_n_ev | 4 | 1.2 | -30.49 | -29.75 | 9.47 | -30.57 | 37041 | 3086.75 | 5.371767 | 0.936668 |
| top_n_ev | 6 | 1.2 | -27.99 | -30.01 | 9.68 | -28.17 | 47157 | 3929.75 | 5.371767 | 0.936668 |
| top_n_ev | 8 | 1.2 | -31.11 | -29.87 | 8.85 | -31.23 | 54544 | 4545.33 | 5.371767 | 0.936668 |

- 確率校正: log_loss / Brier は全条件で同一（同一モデル・同一予測のため戦略で変わらない）。

## 3. ベスト条件

**現時点のベスト条件（今回のグリッド内）**

- **top_n**: 6  
- **ev_threshold**: 1.20  
- **model**: baseline B  
- **calibration**: sigmoid  
- **strategy**: top_n_ev  

**選定理由**

- **overall_roi_selected** が最良: -28.17（他は -29% 台〜-31% 台）。
- **mean_roi_selected** も最良: -27.99。
- **total_selected_bets** は 47,157（極端に少くなく、運用に使える水準）。
- std_roi_selected は 9.68 でやや大きいが、他条件と同程度で許容範囲。
- EV のみの比較では ev=1.22 がわずかに良いが、top_n=6 の効果の方が大きく、組み合わせでは **top_n=6 + ev=1.20** を採用。

## 4. A / B の判断

**判断: B. モデル改善（特徴量追加・モデル見直し）に進む**

**理由**

- 戦略パラメータ（ev_threshold / top_n）を細かく振っても、全条件で **overall ROI は約 -28% 〜 -31%** のまま。
- ベスト条件（top_n=6, ev=1.20）でも **約 -28%** であり、閾値や top_n の微調整だけではプラス転換は期待しにくい。
- log_loss・Brier はモデル共通のため戦略で変わらず、**確率の質の改善にはモデル側の変更が必要**。
- したがって「戦略条件の最適化を続ける」より「モデル改善に進む」方が合理的。

## 5. 次にやるべきこと

1. **運用する場合**  
   - 上記ベスト条件（top_n=6, ev_threshold=1.20）で DB 経路を固定して再現性を確保する。  
   - 必要なら top_n=6 + ev=1.22 の組み合わせを 1 回だけ rolling で確認する。

2. **モデル改善に進む場合**  
   - 特徴量の追加・見直し、モデル構造の変更、学習データ期間・サンプル数の検討を行う。  
   - 改善後のモデルで、同じ rolling validation / EV sweep / top_n sweep を再実行し、ROI と log_loss・Brier の変化を比較する。

3. **確率校正の追加検証（任意）**  
   - isotonic や別の calibration を試す場合は、モデル更新と分けて「同じモデル・別 calibration」で比較するとよい。

---

- 比較表の詳細: `outputs/strategy_comparison.csv` / `docs/ROI_STRATEGY_COMPARISON.md`  
- EV sweep 生データ: `outputs/ev_threshold_sweep_summary.json`  
- top_n sweep 生データ: `outputs/topn_sweep_summary.json`
