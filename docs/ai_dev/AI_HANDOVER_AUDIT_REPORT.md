# AI 引き継ぎドキュメント監査レポート

**実施日**: 2026-03（想定）  
**対象**: 新チャット移行前の AI 引き継ぎ用ドキュメント  
**コード変更**: なし（監査のみ）

---

## 1. bootstrap prompt 整合性

### 指定された読み順と実在

| Step | 指定パス | 実在 |
|------|----------|------|
| 1 | docs/ai_dev/project_status.md | ✓ |
| 2 | docs/ai_dev/architecture.md | ✓ |
| 3 | docs/ai_dev/next_tasks.md | ✓ |
| 4 | experiments/leaderboard.md, experiments/open_questions.md | ✓ ファイルは存在 |
| 5 | experiments/logs/ | ✓ ディレクトリ存在（EXP-0001 等） |
| 6 | docs/ai_dev/prompt_history/ | ✓ |

### 問題点

- **リンク切れ**: `chat_bootstrap_prompt.md` は `docs/ai_dev/` に配置されているため、相対パス `../experiments/...` は **docs/experiments/** を指す。experiments はリポジトリ**ルート**にあるため、`../experiments/` では存在しないパスになる。
  - 正しい相対パス: **`../../experiments/leaderboard.md`**（同様に open_questions, logs, templates）
- 読み順（Overview → Architecture → Next Tasks → Experiment Tracker → Recent Experiments → Prompt History）は合理的。

---

## 2. ai_dev ドキュメント整合性

### 古い構造の有無

- **docs/ai_dev/experiments** への言及は、README と refactor_memo では「experiments/ はリポジトリルート」「docs/ai_dev/experiments は廃止」と明記されており、古いパスでの誘導はなし。

### リファクタメモの鮮度

- **refactor_memo_2026.md**: 第1段（テスト・契約・prediction_tool 分割）と第2段（argparse 分離・重複削除）を実施済みとして記載。最新状態を反映。
- **prediction_tool_refactor_memo.md**: 第1段の責務・契約・実施内容を記載。実施後セクションあり。
- **prediction_tool_refactor_phase2_memo.md**: 第2段の重複・argparse・実施内容を記載。実施後セクションあり。

### 次の AI が理解できるか

- **current architecture**: project_status.md（Strategy B, DB, 評価方法）、architecture.md（pipeline, Strategy B）で把握可能。
- **current development phase**: project_status の「メイン戦略」「モデル比較」、next_tasks の Priority 1–6 で把握可能。
- **next tasks**: next_tasks.md で Priority 1（Strategy B pipeline stabilization）から順に記載あり。
- **不足しがちな点**: 現在の ROI の**数値**は project_status には書かれておらず、experiments/leaderboard.md（EXP-0001 の -28% 等）を見ないと分からない。bootstrap で leaderboard を読む順にしているので、読めば把握可能。

---

## 3. experiments tracker 整合性

### ディレクトリ構成

- **experiments/leaderboard.md** ✓
- **experiments/experiment_index.md** ✓
- **experiments/open_questions.md** ✓
- **experiments/templates/** ✓（experiment_template.md, experiment_template_yaml.md）
- **experiments/logs/** ✓（EXP-0001_baseline_sigmoid_extended_topn6_ev120.md）
- **experiments/README.md**, field_definitions.md, status_rules.md ✓

### bootstrap からの参照

- bootstrap では Step 4・5 および Experiment Logging で experiments を参照しているが、**相対パスが `../experiments/` のため、docs/ai_dev からは解決すると docs/experiments/ になりリンク切れ**。内容・読み順の指定は正しい。

---

## 4. docs 入口の評価

### docs/README.md

- **ドキュメント入口（カテゴリ別）** で architecture / strategy / development / ai_dev / guides を表で整理している。
- 新しい AI が「architecture＝PROJECT_LAYOUT, architecture/README 等」「strategy＝strategy/README, EV_BETTING_STRATEGY 等」「development＝LEARNING_AND_PREDICTION_STATUS 等」「ai_dev＝ai_dev/README, chat_bootstrap」と理解できる構成。
- ai_dev の行で「実験トラッカーは ../experiments/」とあり、**docs/README.md は docs/ 直下にあるため、../experiments/ はリポジトリルートの experiments/ を正しく指す** ✓。

### 問題点

- docs/README 自体に問題はなし。**docs/ai_dev/** 配下の experiments へのリンクのみ相対パス誤り。

---

## 5. リンク切れ

| ファイル | リンク | 解釈されるパス | 結果 |
|----------|--------|----------------|------|
| docs/ai_dev/chat_bootstrap_prompt.md | (../experiments/leaderboard.md) 等 | docs/experiments/... | **切れ** |
| docs/ai_dev/README.md | (../experiments/), (../experiments/field_definitions.md) 等 | docs/experiments/... | **切れ** |
| docs/ai_dev/next_tasks.md | (../experiments/leaderboard.md) 等 | docs/experiments/... | **切れ** |
| docs/ai_dev/experiment_log.md | (../experiments/logs/) | docs/experiments/logs/ | **切れ** |
| README.md（ルート） | (experiments/), (docs/...) | ルート基準で正しい | ✓ |
| docs/README.md | (../experiments/) | ルートの experiments/ | ✓ |
| docs/PROJECT_LAYOUT.md | (../kyotei_predictor/...) 等 | docs から見た相対で妥当 | ✓ |

**結論**: **docs/ai_dev/ 内の experiments へのリンクはすべて `../` を `../../` に修正すると正しく解決する**（experiments がリポジトリルートにあるため）。

---

## 6. 新AI理解テスト結果

chat_bootstrap_prompt.md の読み順に従い、指定ドキュメントを読んだ前提でまとめた結果。

| 項目 | 理解できたか | 根拠 |
|------|--------------|------|
| 1. プロジェクト目的 | ✓ | project_status / README：3連単 EV 予測、Strategy B、ROI 改善 |
| 2. データ構造 | ✓ | project_status（DB 唯一正）、architecture（SQLite, races/odds）、experiments の YAML 項目 |
| 3. 現在のモデル | ✓ | project_status（sklearn / LightGBM / XGBoost）、architecture（baseline B, sigmoid）、leaderboard（EXP-0001） |
| 4. 現在のROI | △ | leaderboard を読めば EXP-0001 の -28% 等は分かる。project_status には数値がなく「現在の ROI」だけでは不足しがち |
| 5. 開発フェーズ | ✓ | project_status（評価方法・成果物）、next_tasks（Priority 1–6） |
| 6. 次の優先タスク | ✓ | next_tasks（Strategy B pipeline stabilization, rolling validation automation 等） |
| 7. 最近のリファクタ | ✓ | refactor_memo_2026 + prediction_tool 第1・第2段メモで実施内容を把握可能 |

**理解を妨げる要因**

- **リンク切れ**: docs/ai_dev から experiments へ遷移しようとすると、`../experiments/` が docs/experiments になり失敗する。修正しないと「Step 4・5 のファイルが開けない」と誤認しうる。
- **現在ROI**: 「現在の ROI」を一言で知りたい場合、project_status に「参照: experiments/leaderboard.md」や「現時点の reference は EXP-0001（overall_roi_selected 約 -28%）」の一文があると親切。

---

## 7. 改善提案

### 必須（リンク修正）

- **docs/ai_dev/** 内の experiments 参照を **`../experiments/` → `../../experiments/`** に変更する。
  - 対象: chat_bootstrap_prompt.md, README.md, next_tasks.md, experiment_log.md
  - これにより「bootstrap の読み順で experiments に到達できる」状態になる。

### 推奨（引き継ぎ品質）

- **project_status.md**: 「現在の reference ROI」を一文で記載するか、「詳細は experiments/leaderboard.md」と明記する。
- **chat_bootstrap_prompt.md**: Step 4 の直前に「experiments はリポジトリルートにあります（docs の外）」と一文入れると、パス解釈の混乱を防げる。
- **重複の整理**: NEXT_TASKS_OVERVIEW.md と docs/ai_dev/next_tasks.md の役割（全体 vs AI 向け優先タスク）を README か bootstrap で一言説明すると、次の AI が迷いにくい。
- **読み順**: 現状の Step 1–6 で十分合理的。変更は不要。

### 任意

- experiments/README.md に「AI は新規実験前に leaderboard.md, open_questions.md, status_rules.md を読む」を再度明記してもよい（bootstrap と重なるが、experiments 単体で開いたときにも有効）。
- 新規 AI 向けに「初回だけ読む一覧」を 1 ファイルにまとめた **ONBOARDING.md** を docs/ai_dev に置く場合は、上記リンク修正後にそこから bootstrap と project_status へ誘導する形にするとよい。

---

**監査結論**: 構成・読み順・リファクタメモの内容は引き継ぎに使える状態。**docs/ai_dev 配下の experiments への相対パス（`../` → `../../`）を修正すれば、bootstrap に従う新 AI がドキュメントを読むだけでプロジェクトを理解できる。**
