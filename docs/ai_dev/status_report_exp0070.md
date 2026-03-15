# 現状確認レポート

実ファイル確認に基づく。確認日: 2025-03-15。

---

## 1. 最新状況の整合確認

### 最新 EXP 番号

| 対象 | 記載 | 判定 |
|------|------|------|
| chat_context.md | 最新 EXP: **EXP-0070**（Latest Experiment 節） | ✓ |
| leaderboard.md | EXP-0070 行あり（79行目、Notes 207行目） | ✓ |
| project_status.md | EXP-0070 行あり（最終行 131） | ✓ |
| experiments/logs | `EXP-0070_d_hi475_local_search.md` のみ（EXP-0071 以降なし） | ✓ |

**結論**: **EXP-0070 が最新で一致している。**

### 各ファイル反映状況

- **leaderboard.md**: EXP-0070 が 1 行追加済み。最良 CASE2（4.50≤EV<4.75, prob≥0.05）: ROI 11.12%, profit 5,772, max_dd 8,838、adopt。Notes に tool・log・結果 JSON 記載あり。
- **chat_context.md**: Latest Experiment が EXP-0070、Summary 表に EXP-0070 行、Current Findings に EXP-0070 要約あり。
- **project_status.md**: EXP-0070 の status: completed、purpose、結果、judgment（adopt）、tool・log・結果 JSON が追記済み。
- **experiments/logs/EXP-0070_d_hi475_local_search.md**: 実験目的・共通条件・CASE 定義・結果表・採用判断・考察が記載済み。

### 不整合の有無

- **数値**: 前提報告・ログ・JSON・leaderboard・chat_context・project_status の CASE0〜7 の数値はすべて一致（実 JSON で照合済み）。
- **用語の注意**: EXP-0055 の「CASE2」は Low Payout の CASE2_ev_ge_460、EXP-0070 の「CASE2」は EV 帯 4.50≤EV<4.75 の variant 名。別実験の別定義のため表記上は不整合ではないが、文脈で取り違えないよう注意。
- **chat_context の二重基準**: 「Current Production Strategy」「Best Historical Result」は n_w=12 の EXP-0015（-12.71%）を指しており、厳密評価（n_w=36）の主軸は EXP-0070 CASE2。両方の基準が併存している状態で、どちらを「本番」とするかの明文化はされていない（後述「必要なら修正すべきドキュメント」で対応案を記載）。

---

## 2. EXP-0070 の事実確認

### 実装要約

- **ツール**: `kyotei_predictor/tools/run_exp0070_d_hi475_local_search.py`
- **入力**: 既存 calib_sigmoid 予測（`outputs/ev_cap_experiments/rolling_roi_predictions`）。selection のみ `_filter_bets_by_selection(ev_lo, ev_hi, prob_min)` で変更。
- **共通**: calibration=sigmoid、risk_control=switch_dd4000、n_windows=36、skip_top20pct（`SKIP_TOP_PCT`）。switch_dd4000 の stake スケジュールは **CASE0 の ref_profit で 1 本だけ算出**し、全 CASE で同一スケジュールを適用。
- **CASE 定義**: コード 57–66 行目の `CASES` とログ・前提報告の表が一致（CASE0: 4.30–4.75, 0.05 ～ CASE7: 4.50–4.70, 0.06）。

### ログ / JSON / ドキュメント整合

- **結果 JSON**（`outputs/d_hi475_local_search/exp0070_d_hi475_local_search.json`）を実読済み。summary および results_by_case の ROI / total_profit / max_drawdown / profit_per_1000_bets / bet_count / longest_losing_streak は、ログ表・前提報告・leaderboard の記載と一致。
- **CASE3 の longest_losing_streak**: JSON では 4。ログ・前提報告の「CASE3: longest_lose 4」と一致。**正しい。**

### 数値確認（JSON ベース）

| variant | ROI   | total_profit | max_drawdown | profit_per_1000_bets | bet_count | longest_losing_streak |
|---------|-------|--------------|--------------|----------------------|-----------|------------------------|
| CASE0   | 0.53  | 484          | 15,886       | 469.45               | 1,031     | 4                      |
| CASE1   | 2.32  | 1,654        | 14,394       | 2,039.46             | 811       | 14                     |
| CASE2   | 11.12 | 5,772        | 8,838        | 9,783.05             | 590       | 9                      |
| CASE3   | 5.45  | 4,410        | 12,866       | 4,819.67             | 915       | 4                      |
| CASE4   | -27.98| -17,108      | 17,108       | -24,866.28           | 688       | 4                      |
| CASE5   | -13.58| -11,666      | 13,266       | -12,002.06           | 972       | 4                      |
| CASE6   | -13.99| -8,050       | 11,802       | -12,327.72           | 653       | 8                      |
| CASE7   | -12.18| -4,732       | 11,482       | -10,730.16           | 441       | 10                     |

### 採用判断の妥当性

- **CASE2 adopt**: ROI・total_profit・max_drawdown・profit_per_1000_bets はいずれも CASE0 を上回る。bet_count は 590 に減り、longest_losing_streak は 9（CASE0 は 4）。「利益・効率・DD 改善」を主軸にするなら adopt は妥当。連敗長だけは CASE0/CASE3 より長いため、リスク許容度に応じた運用注意は必要。
- **CASE3 hold**: ROI 5.45%、profit 4,410、longest_lose 4 でバランス型としての hold は妥当。
- **CASE4 / CASE5〜7 reject**: 数値どおり。EV 上限の絞りすぎ・prob_min 0.06 は全ケースで悪化。

---

## 3. 戦略全体の俯瞰

### 現在の主軸

- **正式 reference（n_w=12）**: EXP-0015。top_n_ev_gap_filter, top_n=3, ev=1.20, ev_gap=0.07。ROI -12.71%。chat_context の「Current Production Strategy」「Best Historical Result」はここを指す。
- **厳密評価（n_w=36）の主軸候補**: **EXP-0070 CASE2**。4.50≤EV<4.75, prob≥0.05、sigmoid + switch_dd4000。ROI 11.12%、profit 5,772、max_dd 8,838、bet 590、longest_lose 9。adopt 済み。

### adopt / hold / reject の整理（厳密評価・n_w=36 周辺）

| 扱い | 実験・条件 | 備考 |
|------|------------|------|
| **adopt** | EXP-0070 CASE2（4.50≤EV<4.75） | 主軸候補。ROI・profit・max_dd・profit/1k で最良。 |
| **adopt** | EXP-0065 sigmoid | calibration は sigmoid 維持。 |
| **adopt** | EXP-0063 race_selected_ev≥1.05 | n_w=12 時。n_w=36 では EXP-0064 で不採用。 |
| **hold** | EXP-0070 CASE3（4.30≤EV<4.70） | バランス型、longest_lose 4。 |
| **hold** | EXP-0070 CASE1（4.40≤EV<4.75） | 攻め用。longest_lose 14 に注意。 |
| **hold** | EXP-0055 CASE6（実運用版） | top1_prob_le_035。CASE2 攻め・CASE6 実運用の 2 本立て。 |
| **reject** | EXP-0070 CASE4, CASE5〜7 | EV 上限 4.60 / prob_min 0.06 は悪化。 |

### 改善の流れ

- **n_w=12**: top_n_ev → EV gap → 高EV skip → EV cap → EV 帯フィルタ … と進み、EXP-0015 で -12.71% が公式ベスト。
- **厳密評価（stake=100 固定）**: EXP-0042〜0046 で selection 厳密化・d_hi475 採用 → EXP-0047〜0051 で switch_dd4000 標準化 → EXP-0054〜0056 で Low Payout・CASE6 実運用版 → EXP-0065 で sigmoid 確定 → EXP-0070 で d_hi475 の EV 帯・prob 下限の局所探索 → CASE2 が adopt。
- **指標の推移（厳密評価）**: CASE0（baseline d_hi475）から CASE2 へ、ROI 0.53%→11.12%、profit 484→5,772、max_dd 15,886→8,838、profit_per_1000_bets 469→9,783。bet_count 1,031→590、longest_lose 4→9。

### 局所探索か構造改善か

- EXP-0070 は **局所探索**（EV 帯・prob_min のグリッド）。モデル・特徴量・calibration・risk 制御は変更していない。
- 構造的な変更は、過去の EV 帯フィルタ採用（EXP-0037〜0046）や switch_dd4000 採用（EXP-0048〜0051）で既に取り込まれている。現状は「既存パイプライン内の selection パラメータ最適化」に相当。

---

## 4. 方針再評価

### 現方針への評価

- **強み**: 厳密評価で ROI・profit・max_dd・profit/1k が baseline より明確に改善。sigmoid + switch_dd4000 は一貫して採用され、EV 帯の絞り（4.50≤EV<4.75）が有効と数値で確認された。
- **弱み**: CASE2 は bet 590・longest_lose 9 と、CASE0 より bet 減・連敗長増。n_w=24/30 での頑健性は未検証。EXP-0055 で言及された「CASE2 の特定期間依存」は別定義の CASE2 だが、EXP-0070 CASE2 も window 数・期間に依存する可能性はある。

### 継続 / 修正 / 転換 の判断

- **結論: 現方針は「継続しつつ、頑健性確認を追加」が妥当。**
- **理由**:
  1. CASE2 は CASE0 を ROI・profit・max_dd・profit/1k で一貫して上回り、adopt の根拠は十分。
  2. ただし「主軸格上げ」の前に、n_w=24/30 や block 別で優位が再現するかの確認が望ましい（収穫逓減には入っているが、最後の一手の検証として価値がある）。
  3. EV 帯・prob の微調整（4.45〜4.55 など）は効果が限定的になる可能性が高く、優先度は下げてよい。
  4. 本質改善（モデル・特徴量・calibration・新フィルタ）は EXP-0066 のボトルネック（EV 1.2–1.5）など別軸の検討と並行でよい。

### 収穫逓減と次に掘る論点

- **収穫逓減**: d_hi475 周りの EV 帯・prob の局所探索は、EXP-0070 で一通り実施済み。さらに 0.05 刻みの細かい EV 探索は、bet 数減少・longest_lose リスク増の割にリターンが小さい可能性が高い。
- **次に掘る論点**: (1) CASE2 の n_w=24/30 での優位性・block 安定性。(2) CASE2 と CASE6（Low Payout 実運用版）の役割分担（攻め・安定の 2 本立て）の整理。(3) EXP-0066 に基づく EV 1.2–1.5 帯の改善（予測品質・selection の見直し）。

### CASE2 を主軸にしてよいか / 頑健性確認が先か

- **推奨**: **頑健性確認を先に 1 本実施したうえで、CASE2 を厳密評価の主軸として格上げする**のがよい。
- CASE2 は 1 実験・n_w=36 のみの結果。n_w=24/30 で profit・ROI が CASE0 や CASE6 を上回るか、block で極端な依存がないかを確認してから「実運用標準」にすると、リスクが抑えられる。

---

## 5. 次の実験提案

### 案1: EXP-0070 CASE2 の頑健性確認（n_w=24/30 および block 比較）

- **目的**: CASE2（4.50≤EV<4.75, prob≥0.05）が n_w=24/30 でも CASE0 や CASE6 を上回るか、block 単位で偏りがないかを確認する。
- **仮説**: CASE2 の優位は n_w=36 に依存せず、n_w=24/30 でも再現する（または少なくとも CASE0 より良い）。
- **具体的な変更点**: 既存 EXP-0070 ツールを流用し、n_windows=24, 30 でも実行。同一条件で CASE0 / CASE2 /（可能なら CASE6 相当）を並べ、profit・ROI・max_dd・longest_lose を比較。n_w=36 の既存結果とあわせて block 別（例: 6 block）の profit を集計し、CASE2 の block 依存度を確認。
- **期待する改善指標**: 主に「判断の確度」の向上。CASE2 の採用を n_w ・期間に依存しない形で裏付け、または反例があれば hold 条件を明文化。
- **リスク**: n_w=24/30 で CASE2 が CASE0 より悪化する場合、horizon 依存の採用条件（例: n_w=36 のみ CASE2）が必要になる。
- **優先度**: **高**（主軸格上げの前提として推奨）。

---

### 案2: CASE2 と CASE6（Low Payout 実運用版）の役割分担の整理

- **目的**: EXP-0070 CASE2（攻め・高 ROI）と EXP-0055 CASE6（実運用・安定）を、同一 n_w で比較し、資金・リスク許容に応じた使い分けを明文化する。
- **仮説**: CASE2 は profit・ROI 優先、CASE6 は longest_lose・max_dd 優先。用途別に「攻め用」「安定用」の 2 本立てが成立する。
- **具体的な変更点**: 同一 n_w（24/30/36）・同一予測で、EXP-0070 の CASE0/CASE2 と、EXP-0055 の CASE6（top1_prob_le_035）を同じ集計枠で評価。profit・ROI・max_dd・bet_count・longest_lose を表にし、さらに「利益優先」「安定優先」のシナリオ別に推奨を 1 文で書く。
- **期待する改善指標**: 運用指針の明確化。どちらを標準にするか／併用する場合の配分の目安。
- **リスク**: CASE2 と CASE6 の定義・データソースが異なるため、比較の前提（予測・日付範囲）を揃える必要がある。
- **優先度**: **中**（運用設計の整理用）。

---

### 案3: EV 1.2–1.5 帯のボトルネック対策（EXP-0066 フォロー）

- **目的**: EXP-0066 で特定された「EV 1.2–1.5 が損失源」を、selection または閾値で避ける・軽減する。
- **仮説**: EV 帯フィルタや race 単位の EV 下限を入れることで、その帯の bet を減らし、全体 ROI が改善する（n_w=36 の厳密評価で検証）。
- **具体的な変更点**: 既存 d_hi475 / CASE2 の前に「レース内 max_ev や race_ev が一定以上」などの条件を追加する、または EV 1.2–1.5 に該当する bet を除外する variant を 1〜2 個用意し、CASE0/CASE2 と比較。
- **期待する改善指標**: ROI・profit の微増、または EV 帯別 ROI の改善。
- **リスク**: 厳密評価の selection はすでに 4.30≤EV<4.75 付近に絞っており、EV 1.2–1.5 は別レイヤ（モデル出力の別解釈）のため、効果が小さい可能性がある。
- **優先度**: **低**（本質改善の入り口として、余裕があれば実施）。

---

## 6. 必要なら修正すべきドキュメント

### 修正対象と内容

1. **chat_context.md**
   - **現状**: 「Current Production Strategy」は n_w=12 の top_n_ev_gap_filter のみ。「Next Experiments」の実運用候補も d_hi475 + switch_dd4000 の説明が中心で、EXP-0070 CASE2 を主軸候補として明記していない。
   - **修正案**: 「厳密評価（n_w=36）の主軸候補」として EXP-0070 CASE2（4.50≤EV<4.75, prob≥0.05）を 1 行追加。Next Experiments に「CASE2 の n_w=24/30 頑健性確認後に主軸格上げ」と追記。
   - **任意**: Project Goal に「厳密評価は n_w=36 で別枠管理」と 1 行あると、n_w=12 と n_w=36 の二重基準が読み手に伝わりやすい。

2. **不整合・記載漏れ**
   - 上記以外に、数値のズレや EXP 番号の不一致は確認していない。前提報告に挙がった変更ファイルの反映は、実ファイル確認の範囲で問題なし。

---

## 経営判断としての一言要約

- **EXP-0070 は最新で、ドキュメント・JSON・コードは一致している。CASE2（4.50≤EV<4.75）の adopt は数値的にも妥当。**
- **現方針は継続でよく、そのうえで「CASE2 の n_w=24/30 での頑健性確認」を 1 本やってから、厳密評価の主軸を CASE2 に格上げするのがおすすめ。**
- **EV 帯・prob のさらに細かい局所探索は収穫逓減に入っているため優先度は下げ、代わりに CASE2 と CASE6 の役割分担の整理や、EXP-0066 に基づく EV 1.2–1.5 帯の検討を中〜低優先で持っておくとよい。**
