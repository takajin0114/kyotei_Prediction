# 学習のインプットとアウトプット

**目的**: 学習（最適化・訓練）の入力データと出力結果を整理する。  
**最終更新**: 2025-02-12

---

## 1. 全体像

```
[インプット] データ・設定・ハイパーパラメータ
      ↓
KyoteiEnvManager → 1レースごとに KyoteiEnv
  - 状態: vectorize_race_state(race_data, odds_data) → 192次元
  - 報酬: calc_trifecta_reward(action, 着順, odds, 賭け金)
      ↓
PPO.learn()（Optuna でハイパーパラメータ探索）
      ↓
[アウトプット] モデル・最適化結果・ログ
```

---

## 2. インプット（学習に必要なもの）

### 2.1 データ

| 種別 | 形式・場所 | 必須項目 | 用途 |
|------|------------|----------|------|
| **レースデータ** | JSON ファイル `race_data_YYYY-MM-DD_会場名_RN.json` | 下記参照 | 状態ベクトル・正解着順 |
| **オッズデータ** | JSON ファイル `odds_data_YYYY-MM-DD_会場名_RN.json` | 下記参照 | 状態ベクトル・報酬計算 |

- **配置**: `data_dir` 配下（デフォルト `kyotei_predictor/data/raw`）。サブディレクトリ（例: `YYYY-MM/`）も検索される。
- **ペア**: 同じ日付・会場・レース番号の `race_data_*` と `odds_data_*` が**両方ある**レースだけがエピソードに使われる。片方だけだとスキップされる。
- **フィルタ**: `--year-month 2024-05` でファイル名の日付が `2024-05` のものだけに絞れる。

**race_data_*.json で参照している項目**

| 大項目 | キー | 用途 |
|--------|------|------|
| **race_info** | stadium, race_number, number_of_laps, is_course_fixed | レース全体特徴（会場 one-hot・レース番号・周回・進入固定） |
| **race_entries** | 各艇: pit_number, racer.current_rating, performance.rate_in_all_stadium / rate_in_event_going_stadium, boat.quinella_rate / trio_rate, motor.quinella_rate / trio_rate | 艇ごと特徴（48次元: 6艇×8） |
| **race_records** | pit_number, arrival | **正解着順**（1〜3着の艇番）。報酬計算で使用。arrival が無効なレースはスキップ |

**odds_data_*.json で参照している項目**

| キー | 用途 |
|------|------|
| odds_data | 3連単 120 通りの betting_numbers と ratio。状態ベクトルのオッズ特徴（120次元）と報酬計算（払戻）に使用 |

### 2.2 状態ベクトル（観測空間）

- **次元**: 192（`gym.spaces.Box(low=0, high=1, shape=(192,))`）
- **構成**（`pipelines/kyotei_env.py` の `vectorize_race_state`）:
  - **艇特徴**: 6艇 × 8 = 48次元（艇番正規化・級別 one-hot 4・全国勝率・当地勝率・艇連対率・艇3連対率・モーター連対率・モーター3連対率）
  - **レース特徴**: 会場 one-hot（コード上は 3 会場例）+ レース番号正規化 + 周回 + 進入固定。実装によって 6〜12 次元程度
  - **オッズ特徴**: 3連単 120 通りを log(odds+1) で Min-Max 正規化 → 120次元
- 合計が 192 に満たない場合は **0 パディング** で 192 次元に揃える（予測側 `vectorize_race_state_from_data` では 48+12+120=180 → 12 次元パディング）。

### 2.3 アクション・報酬

| 項目 | 内容 |
|------|------|
| **アクション空間** | `Discrete(120)`。0〜119 が 3連単 120 通り（1-2-3, 1-2-4, …）に対応。 |
| **報酬** | `calc_trifecta_reward(action, 着順タプル, odds_data, bet_amount)`。設定は `config/improvement_config.json` の `reward_design.phase1`。 |
| **報酬ルール** | 的中: (払戻−賭け金)×win_multiplier。2着的中: partial_second_hit_reward。1着のみ的中: partial_first_hit_penalty。不的中: no_hit_penalty。 |

### 2.4 設定ファイル

| ファイル | 内容 |
|----------|------|
| **optimization_config.ini** | MODE（fast/medium/normal）, TRIALS, YEAR_MONTH。バッチ `run_optimization_config.bat` が参照。 |
| **config/improvement_config.json** | 報酬パラメータ（phase1）、ハイパーパラメータ探索範囲（phase2）、学習ステップ数・評価エピソード数。 |

### 2.5 コマンドライン引数（optimize_graduated_reward）

| 引数 | 意味 |
|------|------|
| --data-dir | データディレクトリ（デフォルト: kyotei_predictor/data/raw） |
| --year-month | 年月フィルタ（例: 2024-05） |
| --n-trials | Optuna 試行回数 |
| --test-mode, --minimal, --fast-mode, --medium-mode | 学習ステップ数・評価エピソード数の短縮 |
| --resume-existing | 既存 Optuna スタディを継続 |

---

## 3. アウトプット（学習の結果）

### 3.1 モデル

| 出力先 | 内容 |
|--------|------|
| **optuna_models/graduated_reward_best/best_model.zip** | 最良試行の PPO モデル。**予測ツールがデフォルトで読み込む**。 |
| **optuna_models/trial_N/** | 各 Optuna 試行の best_model.zip とチェックポイント。最良が上記にコピーされる。 |
| **optuna_models/graduated_reward_checkpoints/** | チェックポイント（設定により使用）。 |

### 3.2 最適化結果

| 出力先 | 内容 |
|--------|------|
| **optuna_results/graduated_reward_optimization_YYYYMMDD_HHMMSS.json** | 全試行の番号・スコア・ハイパーパラメータ・状態。最良試行の情報を含む。 |

### 3.3 評価・ログ

| 出力先 | 内容 |
|--------|------|
| **optuna_logs/trial_N/evaluations.npz** | 最良モデルの詳細評価（hit_rate, mean_reward, std_reward 等）。 |
| **kyotei_predictor/logs/optimize_graduated_reward_YYYYMMDD.log** | 最適化スクリプトのログ（UTF-8）。 |
| **outputs/logs/optimize_objective_error_*.log** | 目的関数内で例外が発生したときのトレースバック。 |

### 3.4 評価指標（Optuna の目的関数）

- **スコア** = `hit_rate * 100 + mean_reward / 1000`
- 評価時: `evaluate_model()` で `n_eval_episodes` 回エピソードを回し、的中率（3連単完全一致）と平均報酬を算出。

---

## 4. 一覧表（インプット・アウトプット）

| 分類 | 項目 | 説明 |
|------|------|------|
| **インプット** | データディレクトリ | race_data_* と odds_data_* のペアが存在するディレクトリ |
| | 年月フィルタ | 対象ファイルの絞り込み（任意） |
| | race_data 中身 | race_info, race_entries, race_records（着順） |
| | odds_data 中身 | odds_data（120通り） |
| | 報酬パラメータ | improvement_config.json の phase1 |
| | ハイパーパラメータ範囲 | improvement_config.json の phase2（または fast/medium の固定範囲） |
| | 試行回数・モード | optimization_config.ini または CLI |
| **アウトプット** | best_model.zip | 予測で使用する PPO モデル |
| | 試行別モデル | optuna_models/trial_N/best_model.zip |
| | 最適化結果 JSON | 全試行のスコア・パラメータ |
| | 評価 npz | 最良モデルの hit_rate, mean_reward 等 |
| | ログ | 最適化・エラー時のログファイル |

---

## 5. 方向性の評価（所感）

### 5.1 良い点

- **学習と予測の入力が一致している**  
  学習時の「状態」は「出走表＋オッズ」から作っており、予測時も同じく出走表＋オッズで状態を組む。**レース前に手に入る情報だけを状態に使う**という方向で一貫している（結果の race_records は報酬計算専用で、状態には入れていない）。

- **出力がそのまま運用に使える**  
  3連単 120 通りへの確率分布 → 上位20組・購入提案という流れになっており、「何を買うか」に直結する形でアウトプットが出ている。

- **報酬設計が目的と噛み合っている**  
  的中時の払戻を強めつつ、2着的中をプラス・1着のみをマイナスにする段階的報酬になっており、「当たりやすさ」と「回収」のバランスを取る方向になっている。

- **データの入り口がはっきりしている**  
  race_data / odds_data のペア・ファイル命名・data_dir が決まっており、取得バッチ→学習→予測のデータの流れが追いやすい。

### 5.2 気にするとよい点・改善の余地

- **オッズのタイミング**  
  状態にオッズを含めているため、「締切後オッズが確定してから予測する」運用になる。締切前のみで予測したい場合は、オッズなし or 仮オッズで状態を組む設計への変更が必要。

- **直前情報がまだ状態に入っていない**  
  出走表＋オッズは使っているが、スタート展示・周回展示・天候（直前情報）は取得だけして状態ベクトルには未使用。**レース前に使える情報を増やす**という意味では、これらを状態に組み込むと方向性がさらに揃う（次元拡張・再学習が必要）。

- **学習データは「過去の結果付き」が前提**  
  教師信号は「実際の着順」なので、学習には必ず race_records が要る。そのため「未来のレース」は結果がないので予測専用。インとアウトの役割分担（学習＝結果あり／予測＝結果なし）ははっきりしている。

- **状態次元の揃え方**  
  環境側と予測側で会場数などが微妙に違うと 192 次元へのパディングに依存しがち。会場リストや特徴量の定義を**学習・予測で共通化**しておくと、インの解釈がぶれにくい。

### 5.3 まとめ

- **方向性**: 「レース前に得られる情報（出走表＋オッズ）を入力に、3連単の確率分布を出力する」というインとアウトの関係は筋が通っている。  
- **強化するなら**: 直前情報を状態に含める、オッズの有無・タイミングを運用に合わせて設計する、学習と予測で状態の定義を完全に揃える、の3点を意識するとよい。  
  → オッズを回収率計算専用にする設計と、状態定義の共通化の詳細は **[ODDS_AND_STATE_DESIGN.md](ODDS_AND_STATE_DESIGN.md)** を参照。

---

## 6. 参照

- [LEARNING_AND_PREDICTION_STATUS.md](LEARNING_AND_PREDICTION_STATUS.md) — 学習・予想の手順と前提
- [optimization/OPTIMIZATION_GUIDE.md](optimization/OPTIMIZATION_GUIDE.md) — 最適化の詳細
- `kyotei_predictor/tools/optimization/optimize_graduated_reward.py` — 学習エントリポイント
- `kyotei_predictor/pipelines/kyotei_env.py` — 環境・状態ベクトル・報酬
- `kyotei_predictor/config/improvement_config.json` — 報酬・ハイパーパラメータ

（上記「5. 方向性の評価」は現状の設計に対する所感であり、今後の拡張の参考用です。）
