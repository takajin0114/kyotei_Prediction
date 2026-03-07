# 暫定ベスト戦略（ROI 改善フェーズ）

比較結果に基づく現時点の選定。評価は DB 経路・rolling validation・selected_bets 集計に統一済み。

## 1. 暫定ベスト戦略（n_windows=12 細分化評価後の更新）

- **model**: baseline B  
- **calibration**: sigmoid  
- **strategy**: top_n_ev  
- **top_n**: 6  
- **ev_threshold**: 1.20  

（EV 1.16〜1.24 と top_n 4,5,6,8 の細分化 sweep の結果、overall_roi / mean_roi が最も良く bet 数も十分な **top_n=6 + ev=1.20** を採用。詳細は `docs/ROI_EVALUATION_N12_SUMMARY.md` を参照。）

## 2. 選定理由

- **EV threshold sweep**: 同一条件で ev_threshold=1.20 が mean_roi_selected / overall_roi_selected とも最も悪化が小さい（-28.71% / -28.5%）。1.25 は bet 数が減りすぎるリスクがあるため、bet 数と ROI のバランスで 1.20 を採用。
- **top_n sweep**: top_n=3 は mean ROI が最も良いが、bet 数が少なく std も大きい。top_n=10 は bet 数は多いが ROI は 1.20 案より劣る。運用可能性（bet 数・分散）を考えると top_n=5 + ev=1.20 を優先。
- 過度に尖った条件（top_n=3 のみや ev=1.25 のみ）は避け、**ある程度の bet 数を確保しつつ、ROI がややマシな条件**を選んだ。

※ 上記は window 数が少ない（例: 2）実行での傾向。**本番では --n-windows 12 以上で再実行し、mean / std / total_selected_bets を再確認すること。**

## 3. 次に追加で比較すべき条件

- **window 数を増やした再実行**: 例: `--n-windows 12` で rolling validation / EV sweep / top_n sweep を再実行し、暫定ベストが安定するか確認。
- **ev_threshold 1.18, 1.22 など細かく**: 1.15 と 1.20 の間でさらに比較。
- **train_days / test_days の変更**: 30/7 以外（例: 45/7, 30/14）での感度確認。
- **calibration**: sigmoid 固定の前提で、isotonic や none との比較（別フェーズ）。

## 4. 運用候補にする前に確認すべきこと

- 上記「次に比較すべき条件」のうち、少なくとも **n_windows=12 以上の rolling で再評価**すること。
- **overall_roi_selected がプラスになる条件が存在するか**を確認（現状は全条件でマイナスなら、モデル刷新や特徴量の見直しが次のステップ）。
- 本番運用時は **data_source=db, db_path 固定**で再現性を確保すること。
- 運用後は **実ベット数・実払戻と summary の total_bet_selected / total_payout_selected の一致**をサンプル確認すること。

## 5. 実行コマンド例（再現用）

```bash
# 単一戦略の rolling validation（12 window）
python3 -m kyotei_predictor.tools.rolling_validation_roi \
  --db-path kyotei_predictor/data/kyotei_races.sqlite \
  --output-dir outputs --n-windows 12 --ev-threshold 1.20

# EV threshold sweep（同一 train で 5 水準比較）
python3 -m kyotei_predictor.tools.ev_threshold_sweep \
  --db-path kyotei_predictor/data/kyotei_races.sqlite \
  --output-dir outputs --n-windows 12

# top_n sweep
python3 -m kyotei_predictor.tools.topn_sweep \
  --db-path kyotei_predictor/data/kyotei_races.sqlite \
  --output-dir outputs --n-windows 12

# 比較表の出力（CSV / MD）
python3 -m kyotei_predictor.tools.strategy_comparison_export --output-dir outputs --docs-dir docs

# sweep 結果の表表示
python3 -m kyotei_predictor.cli.compare_sweep_summaries --output-dir outputs
```
