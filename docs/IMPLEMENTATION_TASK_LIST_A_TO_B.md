# A案→B案移行前 実装タスク一覧

**目的**: B案（予測と買い目選定の分離・ROI 重視）へ進む前段として、A案で整備すべきことを実装可能なタスクに落とし込む。  
**前提**: [ROADMAP_A_TO_B_BACKGROUND.md](ROADMAP_A_TO_B_BACKGROUND.md) の背景と「A案で今やること／やらないこと」に沿う。  
**既に実施済み**: 評価指標の分離（metrics.py）、betting モジュール（single/top_n/threshold）、optimize_for 設定、selected_bets オプション — これらは「共通基盤」として位置づけ、本タスク一覧では検証・補完・次の一歩のみを記載する。

---

## タスクの3分類

| 分類 | 意味 | B案との関係 |
|------|------|-------------|
| **1. 直近やること** | B案に進まなくても共通資産として有効。A案の品質・再現性・比較可能性を高める。 | そのまま B案の評価・比較の土台になる。 |
| **2. B案に行く前の準備** | B案試作や移行判断のために、比較・差し替えをしやすくする整備。 | 予測形式・ログ・config を揃えておくと B案実装時の変更範囲が小さくなる。 |
| **3. B案で新規に作ること** | 将来の新規開発。A案の延長ではなく B案として実装する項目。 | 本リストでは「何を作るか」と完了条件だけ記載し、着手時期は別判断。 |

---

# 1. 直近やること

B案に進む前でも共通資産として有効なタスク。

---

## 1.1 評価指標分離の検証と不足分の補完

| 項目 | 内容 |
|------|------|
| **タスク名** | 評価指標分離の検証と不足分の補完 |
| **目的** | 既存の metrics / evaluate_model / evaluate_graduated_reward_model が hit_rate / mean_reward / ROI / 投資額・払戻額を正しく出力し、optimize_for の切り替えが効くことを確認し、不足があれば補う。 |
| **なぜ必要か** | 指標分離は実装済みだが、評価・最適化の全経路で一貫して使われているか、検証ツールと比較可能な形式かが明文化されていない。B案でも同じ指標を使う前提で揃えておく必要がある。 |
| **変更対象ファイル候補** | `kyotei_predictor/tools/evaluation/metrics.py`, `evaluate_graduated_reward_model.py`, `optimize_graduated_reward.py`（evaluate_model）, `kyotei_predictor/tools/verify_predictions.py`, `docs/CHANGELOG_ROI_RESPONSIBILITY.md` |
| **優先度** | 高 |
| **依存関係** | なし（既存実装の上で検証） |
| **完了条件** | (1) evaluate_graduated_reward_model 実行時に ROI・投資額・払戻額が JSON に含まれることを確認。(2) optimize_for=roi で Optuna を 1 トライアルだけ回し、objective が ROI になっていることを確認。(3) 必要なら verify_predictions の出力キーと評価 JSON のキー対応を 1 行ドキュメントに書く。 |
| **B案への接続** | B案でも同じ metrics を「予測＋買い目選定」の結果に適用する。 |

---

## 1.2 ROI 指標の明確化（検証結果の標準出力形式）

| 項目 | 内容 |
|------|------|
| **タスク名** | ROI 指標の明確化（検証結果の標準出力形式） |
| **目的** | 検証（verify_predictions）と評価（evaluate_graduated_reward_model）の両方で、ROI・投資額・払戻額・的中件数を同じ用語・同じ単位で出し、ログや JSON に残しやすい形式にする。 |
| **なぜ必要か** | 現状は検証が「1位に100円賭けた場合の ROI」、評価が「環境の step ごとの払戻合計」と定義が異なる。比較可能にするには「何にいくら賭けて、いくら払い戻ったか」を共通フォーマットで書く必要がある。 |
| **変更対象ファイル候補** | `kyotei_predictor/tools/verify_predictions.py`（出力キー・説明）, `kyotei_predictor/tools/evaluation/evaluate_graduated_reward_model.py`（statistics のキー説明）, `docs/ROI_AND_RESPONSIBILITY_SEPARATION.md` または本ドキュメントに「指標定義」サブセクション追加 |
| **優先度** | 高 |
| **依存関係** | 1.1 の確認後が望ましい（指標が揃っている前提で形式を決める） |
| **完了条件** | (1) ROI / total_bet / total_payout / hit_count の定義を 1 か所（docs または docstring）に明記。(2) verify_predictions の要約と evaluate の metrics が同じ名前で比較できることをドキュメントに 1 行追記。 |
| **B案への接続** | B案では selected_bets に基づく ROI を同じ形式で出力する。 |

---

## 1.3 Betting strategy の責務分離の確認とテスト拡充

| 項目 | 内容 |
|------|------|
| **タスク名** | Betting strategy の責務分離の確認とテスト拡充 |
| **目的** | 予測ツールが「候補とスコア」を出し、買い目選定が tools/betting で行われることをコードとテストで確認し、不足テストを足す。 |
| **なぜ必要か** | betting モジュールは実装済みだが、prediction_tool のデフォルトは selected_bets を出さない。責務が「設定で切り替え可能」になっていることをテストで保証すると、B案で買い目だけ差し替えやすくなる。 |
| **変更対象ファイル候補** | `kyotei_predictor/tests/test_betting_strategy.py`, `kyotei_predictor/tests/test_evaluation_metrics.py`, `kyotei_predictor/tools/prediction_tool.py`（コメント・docstring のみ可）, `kyotei_predictor/tools/verify_predictions.py`（selected_bets を読む経路は将来タスク） |
| **優先度** | 中 |
| **依存関係** | なし |
| **完了条件** | (1) test_betting_strategy / test_evaluation_metrics が pytest で通る。(2) prediction_tool で --include-selected-bets を付けたときに selected_bets が設定の strategy に従って出ることを 1 回手動または簡単な統合テストで確認。(3) 「予測は all_combinations まで、買い目は select_bets の責務」を README_TESTS または本ドキュメントに 1 行追記。 |
| **B案への接続** | B案では常に betting 経由で買い目を決め、予測ツールは all_combinations のみ返す形に寄せる。 |

---

## 1.4 検証ログの標準化（出力先・ファイル名・1回分の要約形式）

| 項目 | 内容 |
|------|------|
| **タスク名** | 検証ログの標準化（出力先・ファイル名・1回分の要約形式） |
| **目的** | 検証（verify_predictions）の結果を毎回同じ場所・同じ形式で残し、時系列や設定別の比較がしやすいようにする。 |
| **なぜ必要か** | 現状は --output で任意パスに JSON を出せるが、デフォルトの出力先や「1回の検証で必ず出す要約」がプロジェクト全体で決まっていない。ベースライン比較や B案比較のためには「検証1回＝1ファイル」の習慣が必要。 |
| **変更対象ファイル候補** | `kyotei_predictor/tools/verify_predictions.py`（デフォルト出力先・ファイル名規則）, `docs/guides/batch_usage.md` または `docs/PROJECT_LAYOUT.md`, `scripts/run_learning_prediction_cycle.*`（検証結果の保存先を合わせる） |
| **優先度** | 中 |
| **依存関係** | なし（既存 --output を壊さず拡張） |
| **完了条件** | (1) 検証結果の推奨出力先（例: outputs/verification_YYYYMMDD_HHMMSS.json または logs/verification_*.json）を 1 つ決め、docs に記載。(2) 1回分の要約に含めるキー（hit_rate_rank1_pct, roi_pct_our_1st, total_bet 等）を一覧にし、verify_predictions の --output がその形式で出すことを確認。(3) 既存の --output オプションはそのまま残す。 |
| **B案への接続** | B案では「selected_bets に基づく ROI」を同じ要約形式に追加する。 |

---

## 1.5 Train / Valid / Test 分割の固定とドキュメント化

| 項目 | 内容 |
|------|------|
| **タスク名** | Train / Valid / Test 分割の固定とドキュメント化 |
| **目的** | 学習に使うデータ範囲と、評価・検証に使うデータ範囲をプロジェクトで 1 通りの方針にし、再現可能にする。 |
| **なぜ必要か** | 現状は KyoteiEnvManager の date_from / date_to や year_month で範囲を指定するが、「学習用」「評価用」「検証用（予測結果の検証）」の切り分けが設定やドキュメントで明文化されていない。比較や B案移行時に「同じ test セットで比較した」と言えるようにする。 |
| **変更対象ファイル候補** | `kyotei_predictor/config/improvement_config.json` または新規 config セクション, `kyotei_predictor/pipelines/kyotei_env.py`（KyoteiEnvManager の利用方法）, `docs/DATA_STORAGE_AND_DB.md` または本ドキュメント, `scripts/run_optimization_config.bat` / 学習バッチ（日付範囲の渡し方） |
| **優先度** | 中 |
| **依存関係** | データの存在範囲に依存（date_from/date_to を決める前に利用可能なデータを確認する） |
| **完了条件** | (1) 「学習用」「評価用（Optuna 内の evaluate_model）」「検証用（verify_predictions に渡す予測と race_data）」のデータ範囲の決め方を 1 ページにまとめる（例: 学習＝2025-01〜10、検証＝2025-11 など）。(2) 設定またはドキュメントで「推奨 date_from/date_to」を記載。(3) コードの破壊的変更は不要。既存の引数で範囲を指定できることを確認すればよい。 |
| **B案への接続** | B案でも同じ test セットで「A案モデル vs B案フロー」を比較する。 |

---

## 1.6 特徴量・状態ベクトル基盤の整理（ドキュメントと定義の一意化）

| 項目 | 内容 |
|------|------|
| **タスク名** | 特徴量・状態ベクトル基盤の整理（ドキュメントと定義の一意化） |
| **目的** | build_race_state_vector で何が入っているか、次元数・各次元の意味を 1 か所にまとめ、将来の特徴量追加や B案での再利用をしやすくする。 |
| **なぜ必要か** | 状態ベクトルは学習・予測の共通入力。ここが不明瞭だと、B案で別モデルを足すときやオッズを別扱いするときに混乱する。 |
| **変更対象ファイル候補** | `kyotei_predictor/pipelines/state_vector.py`, `docs/STATE_VECTOR_REVIEW.md` または新規 `docs/STATE_VECTOR_SPEC.md` |
| **優先度** | 低〜中 |
| **依存関係** | なし |
| **完了条件** | (1) get_state_dim() の値と、各次元が何を表すか（または「何番目が何」の一覧）をドキュメントに書く。(2) オッズが状態に含まれないことと、報酬計算で別途使うことを明記。既存の STATE_VECTOR_REVIEW があればそこに追記でも可。 |
| **B案への接続** | B案で確率モデルや EV 計算を足すとき、同じ状態定義を参照する。 |

---

# 2. B案に行く前の準備としてやること

B案試作や移行比較のために整えておくタスク。

---

## 2.1 予測出力形式の標準化（スキーマの明文化）

| 項目 | 内容 |
|------|------|
| **タスク名** | 予測出力形式の標準化（スキーマの明文化） |
| **目的** | 予測 JSON（all_combinations, selected_bets 等）のキーと型を 1 か所に定義し、検証ツールや B案の買い目選定が同じ前提で読めるようにする。 |
| **なぜ必要か** | 現状は prediction_tool の出力を verify_predictions が読んでいるが、公式なスキーマがない。B案で「予測だけ別サービス」にしたときに、契約（インターフェース）が明確である必要がある。 |
| **変更対象ファイル候補** | `docs/` に新規 `PREDICTION_OUTPUT_SCHEMA.md` または既存の LEARNING_INPUT_OUTPUT.md に追記, `kyotei_predictor/tools/prediction_tool.py`（docstring でスキーマ参照を書く）, `kyotei_predictor/tools/verify_predictions.py`（期待キーのコメント） |
| **優先度** | 中 |
| **依存関係** | 1.2 で ROI まわりの用語を揃えた後がよい |
| **完了条件** | (1) 予測 JSON のトップキー（prediction_date, predictions, execution_summary 等）と、1 レース分のオブジェクトに含めるキー（venue, race_number, all_combinations, selected_bets の有無）を一覧化。(2) all_combinations の 1 要素のキー（combination, probability, rank, expected_value 等）を記載。(3) 破壊的変更はしない。既存出力を説明するだけ。 |
| **B案への接続** | B案では「予測サービスはこのスキーマで返す。買い目選定は all_combinations を受け取る」とできる。 |

---

## 2.2 ベースライン比較用ログ形式の固定

| 項目 | 内容 |
|------|------|
| **タスク名** | ベースライン比較用ログ形式の固定 |
| **目的** | 学習 1 回・評価 1 回・検証 1 回ごとに「何をしたか・どの指標が出たか」を同じフォーマットで残し、A案ベースラインと B案を同じ土俵で比較できるようにする。 |
| **なぜ必要か** | B案にしたあと「A案より良くなったか」を判断するには、A案のときの数値を同じ形式で蓄積している必要がある。 |
| **変更対象ファイル候補** | `docs/IMPLEMENTATION_TASK_LIST_A_TO_B.md`（本ドキュメントに「推奨ログフォーマット」サブセクション）, 学習スクリプト・評価スクリプトの出力（JSON 1 行 or 固定キーの JSON ファイル）, `logs/` の命名規則 |
| **優先度** | 中 |
| **依存関係** | 1.4（検証ログ標準化）と 1.2（ROI 指標明確化）の後がよい |
| **完了条件** | (1) 「学習 1 回分」「評価 1 回分」「検証 1 回分」に含める推奨キーをドキュメントに書く。(2) 既存の評価 JSON（evaluate_graduated_reward_model の出力）と検証の --output がその推奨に沿っていることを確認。(3) 新規にログを吐くスクリプトを増やさなくても、既存出力を「ベースライン比較用」として使う運用でよい。 |
| **B案への接続** | B案の評価・検証結果を同じキーで出力し、A案と並べて比較する。 |

---

## 2.3 モデル比較インターフェースの整理（評価・予測の入口の統一）

| 項目 | 内容 |
|------|------|
| **タスク名** | モデル比較インターフェースの整理（評価・予測の入口の統一） |
| **目的** | 「モデルパスを渡すと評価結果（metrics）を返す」「モデルパスとデータを渡すと予測 JSON を返す」という入口を、既存スクリプトの上に薄く揃え、将来 B案モデルを差し替えたときに同じ入口で比較できるようにする。 |
| **なぜ必要か** | 現状は optimize_graduated_reward / evaluate_graduated_reward_model / prediction_tool がそれぞれ別の入口。B案で別モデルを試すときに「同じ評価関数に通す」ために、評価・予測の呼び出し方を 1 通りにそろえておくと便利。 |
| **変更対象ファイル候補** | `kyotei_predictor/tools/evaluation/evaluate_graduated_reward_model.py`（関数の引数・戻り値の型を明示）, `kyotei_predictor/tools/prediction_tool.py`（load_model + predict のインターフェース）, 新規 `kyotei_predictor/tools/evaluation/run_evaluation.py` は作らない（既存をラップする doc だけでも可） |
| **優先度** | 低 |
| **依存関係** | 1.1 の検証後 |
| **完了条件** | (1) 「評価を回すにはこの関数／コマンドにこの引数を渡す」「予測を回すにはこのクラス／コマンドにこの引数」を 1 ページにまとめる。(2) コードの大規模リファクタはしない。既存の使い方をドキュメント化し、必要なら小さなラッパー関数を 1 つ足す程度。 |
| **B案への接続** | B案の「予測モデル」を同じ引数で呼び出し、同じ評価関数に通す。 |

---

## 2.4 Config 項目の整理（evaluation / betting の一覧と非推奨の明示）

| 項目 | 内容 |
|------|------|
| **タスク名** | Config 項目の整理（evaluation / betting の一覧と非推奨の明示） |
| **目的** | improvement_config.json の evaluation / betting を一覧し、各項目の意味・推奨値・将来変更する場合の影響をドキュメントに書く。未使用や非推奨があれば明示する。 |
| **なぜ必要か** | 設定が増えると「何を変えると何が変わるか」が分かりにくくなる。B案で config を拡張する前に、現状分を整理しておく。 |
| **変更対象ファイル候補** | `docs/config_usage_guide.md`, `kyotei_predictor/config/improvement_config.json`（コメントは JSON では書けないので docs に）, `kyotei_predictor/config/improvement_config_manager.py`（get_* の docstring） |
| **優先度** | 低 |
| **依存関係** | なし |
| **完了条件** | (1) evaluation（optimize_for, roi_evaluation_enabled）と betting（strategy, top_n, score_threshold, ev_threshold）の一覧と説明を config_usage_guide に追加。(2) 既存の reward_design / learning_parameters との関係を 1 行ずつ書く。(3) コード変更は不要でよい。docs のみ。 |
| **B案への接続** | B案で EV や新戦略を追加するとき、同じ config セクションに項目を足す。 |

---

# 3. B案で新規に作ること

将来の新規開発項目。着手時期は別判断。ここでは「何を作るか」と完了条件のみ記載。

---

## 3.1 検証ツールで selected_bets に基づく ROI 計算オプション

| 項目 | 内容 |
|------|------|
| **タスク名** | 検証ツールで selected_bets に基づく ROI 計算オプション |
| **目的** | 予測 JSON に selected_bets が含まれる場合、「1位に100円」ではなく「selected_bets の各組み合わせに 100 円」として投資額・払戻額・ROI を算出するオプションを verify_predictions に追加する。 |
| **なぜ必要か** | B案では買い目選定が複数点になるため、1位のみの ROI ではなく「選定結果全体の ROI」で評価したい。 |
| **変更対象ファイル候補** | `kyotei_predictor/tools/verify_predictions.py` |
| **優先度** | B案試作時 |
| **依存関係** | 2.1（予測出力形式の標準化）, 1.4（検証ログ標準化） |
| **完了条件** | (1) --betting-summary 等のフラグで、selected_bets があるレースについて selected_bets ベースの ROI を算出し、要約に roi_pct_selected_bets 等を追加。(2) selected_bets が無い場合は従来どおり 1 位のみの ROI。(3) 既存の --output 形式を拡張する形にし、破壊しない。 |
| **B案への接続** | B案の買い目選定結果を検証で評価するための必須機能。 |

---

## 3.2 EV（期待値）ベースの買い目選定の本実装

| 項目 | 内容 |
|------|------|
| **タスク名** | EV（期待値）ベースの買い目選定の本実装 |
| **目的** | 確率（予測スコア）とオッズから期待値 EV を計算し、ev_threshold 以上の組み合わせのみ購入する戦略を、betting モジュールで本実装する。現状の EV 戦略は top_n フォールバックのみ。 |
| **なぜ必要か** | ROI 改善には「EV > 0 または閾値以上の買い目だけ買う」が有効な場合がある。B案の中心的な買い目選定ロジックになる。 |
| **変更対象ファイル候補** | `kyotei_predictor/tools/betting/strategy.py`（EVBettingStrategy）, 予測候補に expected_value を載せる処理（prediction_tool または別モジュール）, `improvement_config.json` の ev_threshold |
| **優先度** | B案試作時 |
| **依存関係** | 2.1（予測出力に expected_value または確率が含まれること）, オッズデータの取得方法の確定 |
| **完了条件** | (1) 候補ごとに EV = 確率×オッズ - 1（または同様の定義）を計算し、閾値以上のみ select_bets の結果に含める。(2) オッズが無い場合は既存どおり top_n フォールバック。(3) 単体テストで EV 計算と閾値フィルタを検証。 |
| **B案への接続** | B案のデフォルト買い目選定の 1 つとして使う。 |

---

## 3.3 予測と購入判断の完全分離（予測ツールのデフォルト挙動）

| 項目 | 内容 |
|------|------|
| **タスク名** | 予測と購入判断の完全分離（予測ツールのデフォルト挙動） |
| **目的** | 予測ツールは常に「all_combinations のみ」返し、購入提案（流し・ボックス等）は別モジュールまたは別コマンドで行う形にし、デフォルトで selected_bets を出さないのではなく「買い目は常に betting 経由」と明示する。 |
| **なぜ必要か** | A案では「上位20を前提にした購入提案」が prediction_tool 内に残っている。B案では予測はスコアまで、買い目はすべて betting に寄せる。 |
| **変更対象ファイル候補** | `kyotei_predictor/tools/prediction_tool.py`（generate_purchase_suggestions の呼び出しをオプション化または別エントリに移す）, Web 表示やバッチが「購入提案」をどこから取るかの変更 |
| **優先度** | B案移行時（後半） |
| **依存関係** | 3.1, 3.2 の利用が前提。Web 表示が selected_bets または新・購入提案 API を参照する必要あり。 |
| **完了条件** | (1) 予測のデフォルト出力が all_combinations（＋必要なら selected_bets）のみで、従来の purchase_suggestions（流し・ボックス等）は別オプションまたは別ツールで生成する。(2) 既存の run_complete_prediction 等は互換レイヤーで従来挙動を残すか、ドキュメントで非推奨と明記。 |
| **B案への接続** | B案の「予測＝候補とスコア」「買い目＝betting のみ」の完成形。 |

---

## 3.4 確率推定系モデル（別モデル）の検討

| 項目 | 内容 |
|------|------|
| **タスク名** | 確率推定系モデル（別モデル）の検討 |
| **目的** | 予測を「確率分布」として出力するモデル（PPO の policy 以外）を検討し、必要なら設計・プロトタイプを立てる。 |
| **なぜ必要か** | B案の先には「予測＝確率、買い目選定＝EV 等」という分離があり、確率を直接出力するモデルがあると EV 計算がしやすい。 |
| **変更対象ファイル候補** | 新規モジュール（例: pipelines/probability_model.py 等）, 既存 state_vector の再利用 |
| **優先度** | 長期（B案安定後） |
| **依存関係** | 2.3（モデル比較インターフェース）, 1.6（状態ベクトル仕様） |
| **完了条件** | (1) 検討結果を docs にまとめる（必要性・選択肢・既存 PPO との役割分担）。(2) プロトタイプをやる場合は「入力＝状態、出力＝120 通りの確率」のインターフェースを既存評価と揃える。 |
| **B案への接続** | B案の「予測」を PPO 以外に差し替えるときの候補。 |

---

## 3.5 A/B 比較の自動化（同一データ・同一指標での比較スクリプト）

| 項目 | 内容 |
|------|------|
| **タスク名** | A/B 比較の自動化（同一データ・同一指標での比較スクリプト） |
| **目的** | 「A案の予測」「B案の買い目選定を適用した予測」を同じ検証データ・同じ指標で比較し、結果を 1 ファイルにまとめるスクリプトまたは手順を作る。 |
| **なぜ必要か** | B案に移行した効果を定量的に示すには、同一条件での比較が欠かせない。 |
| **変更対象ファイル候補** | 新規 `scripts/compare_a_b_baseline.sh` または `kyotei_predictor/tools/analysis/compare_prediction_strategies.py`, `docs/` に実行手順 |
| **優先度** | B案試作〜移行時 |
| **依存関係** | 2.2（ベースライン比較用ログ形式）, 3.1（selected_bets ベース ROI） |
| **完了条件** | (1) 同一予測 JSON に対して「1位のみ」「selected_bets」の両方で ROI を算出し、並べて出力する。(2) または 2 つの予測 JSON（A案出力と B案出力）を同じ検証データで検証し、指標を並べる。(3) 手順を docs に書く。 |
| **B案への接続** | 移行判断の根拠となる数値を出す。 |

---

# 補足：今やるべきでないこと

- **学習アルゴリズムの入れ替え**: PPO をやめて別手法に全面切り替えるのは行わない（ROADMAP の「A案で今やらないこと」に同じ）。
- **報酬設計の大幅変更**: 段階的報酬を ROI に合わせて設計し直すかは、実験結果を見てから。本タスク一覧では「評価で ROI を出し、optimize_for=roi で回す」までを直近〜準備で扱う。
- **予測出力形式の破壊的変更**: all_combinations のキー名や構造を変えない。拡張（selected_bets 追加）は互換を保つ。
- **既存コマンドの廃止**: 学習・予測・検証の既存入口は残し、デフォルトは従来挙動とする。

---

# 優先度順タスク一覧（実装着手用）

| 順 | タスク ID | タスク名 | 優先度 | 主な変更対象 |
|----|-----------|----------|--------|--------------|
| 1 | 1.1 | 評価指標分離の検証と不足分の補完 | 高 | evaluation/metrics.py, evaluate_graduated_reward_model.py, optimize_graduated_reward.py |
| 2 | 1.2 | ROI 指標の明確化（検証結果の標準出力形式） | 高 | verify_predictions.py, evaluate_graduated_reward_model.py, docs |
| 3 | 1.3 | Betting strategy の責務分離の確認とテスト拡充 | 中 | test_betting_strategy.py, test_evaluation_metrics.py, prediction_tool |
| 4 | 1.4 | 検証ログの標準化 | 中 | verify_predictions.py, docs, scripts |
| 5 | 1.5 | Train/Valid/Test 分割の固定とドキュメント化 | 中 | config, docs, KyoteiEnvManager 利用方法 |
| 6 | 2.1 | 予測出力形式の標準化（スキーマの明文化） | 中 | docs（PREDICTION_OUTPUT_SCHEMA 等） |
| 7 | 2.2 | ベースライン比較用ログ形式の固定 | 中 | docs, 既存評価・検証出力の確認 |
| 8 | 1.6 | 特徴量・状態ベクトル基盤の整理 | 低〜中 | state_vector.py, STATE_VECTOR_REVIEW.md 等 |
| 9 | 2.3 | モデル比較インターフェースの整理 | 低 | docs, 既存評価・予測の使い方 |
| 10 | 2.4 | Config 項目の整理 | 低 | config_usage_guide.md |
| — | 3.x | B案で新規に作ること（3.1〜3.5） | B案時 | 各タスクの「変更対象ファイル候補」参照 |

---

## 関連ドキュメント

- [EVALUATION_METRICS_SPEC.md](EVALUATION_METRICS_SPEC.md) — **評価・検証の指標定義**（hit_rate, roi_pct, total_bet, total_payout, hit_count の共通キーと比較の注意）
- [ROADMAP_A_TO_B_BACKGROUND.md](ROADMAP_A_TO_B_BACKGROUND.md) — 背景と「A案で今やること／やらないこと」
- [ROI_AND_RESPONSIBILITY_SEPARATION.md](ROI_AND_RESPONSIBILITY_SEPARATION.md) — 技術方針と既存実装の調査
- [CHANGELOG_ROI_RESPONSIBILITY.md](CHANGELOG_ROI_RESPONSIBILITY.md) — 評価指標分離・betting の変更差分
- [NEXT_TASKS_OVERVIEW.md](NEXT_TASKS_OVERVIEW.md) — プロジェクト全体の次にやること（即時・短期・中期）

**最終更新**: 2026-03
