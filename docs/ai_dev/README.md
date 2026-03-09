# AI Development System

このプロジェクトは AI（Cursor / ChatGPT）と共同開発している。

AIが新しい作業を開始する前に
必ず以下を読む

- [docs/ai_dev/project_status.md](project_status.md)
- [docs/ai_dev/next_tasks.md](next_tasks.md)
- [docs/ai_dev/architecture.md](architecture.md)

実験管理は [experiments/](../../experiments/) を参照すること。項目定義・ステータスルールは [field_definitions.md](../../experiments/field_definitions.md)、[status_rules.md](../../experiments/status_rules.md)。

## Chat Bootstrap

When starting a new AI coding session, read [docs/ai_dev/chat_bootstrap_prompt.md](chat_bootstrap_prompt.md).

---

## AI開発フロー（ChatGPT ↔ Cursor 連携）

ChatGPT と Cursor の間のコピペを減らすため、リポジトリ内の Markdown でやり取りする。

1. **ChatGPT** が [docs/ai_dev/current_task.md](current_task.md) に指示を書く
2. **Cursor** がそれを読んで実装する
3. 実装後、リポジトリルートで次を実行する  
   `bash scripts/ai_dev_cycle.sh`
4. [docs/ai_dev/run_report.md](run_report.md) が生成される
5. そのレポートを ChatGPT に貼り付けて引き継ぐ

テンプレートは [docs/ai_dev/templates/](templates/) を参照。

---

## Experiment Automation

開発者は

```bash
bash scripts/run_experiment_cycle.sh
```

を実行するだけで、以下が更新される。

- **validation**（rolling_validation_roi）
- **experiment log**（experiments/logs/EXP-xxxx.md）
- **leaderboard**（experiments/leaderboard.md の Recent 表）

DB パスは環境変数 `KYOTEI_DB_PATH` で指定（未設定時は `data/races.db`）。リポジトリルートで実行すること。

---

## 実験後の更新手順

実験を実行し leaderboard を更新したら、**chat_context.md** を同期してから commit / push する。

```
実験実行
  ↓
leaderboard 更新（experiments/leaderboard.md）
  ↓
update_chat_context 実行
  ↓
git commit
  ↓
git push
```

**手順**

1. 実験スクリプトを実行し、必要に応じて `experiments/logs/EXP-XXXX_*.md` を追加・更新する。
2. `experiments/leaderboard.md` を更新する。
3. 以下を実行して **Latest Experiment** と **Leaderboard Summary** を自動更新する。
   ```bash
   python3 -m kyotei_predictor.tools.update_chat_context
   ```
   （リポジトリルートで実行。`PYTHONPATH=.` が必要な場合は `PYTHONPATH=. python3 -m kyotei_predictor.tools.update_chat_context`）
4. `git add` → `git commit` → `git push` する。

**新しい EXP ログを作るとき**

- `experiments/logs/EXP-XXXX_*.md` を作成したあと、上記の **update_chat_context** を実行すると、chat_context の「Latest Experiment」がその EXP に更新される。

---

## ChatGPT Review Workflow

1. Cursor で作業する
2. `bash scripts/ai_dev_cycle.sh` を実行するか、実験後は `python3 -m kyotei_predictor.tools.update_chat_context` で chat_context を更新する
3. `docs/ai_dev/chat_context.md` を確認する
4. GitHub に push する
5. ChatGPT には `chat_context.md` の raw URL を渡す

`chat_context.md` に含まれる内容:

- **Project Overview** … 現在の目的（ROI 最大化）
- **Current Strategy** … model / calibration / strategy / top_n / ev_threshold / seed
- **Latest Experiment** … 最新 EXP 番号・概要・結果（update_chat_context で自動更新）
- **Leaderboard Summary** … 上位実験の ROI（update_chat_context で自動更新）
- **Open Questions** … 現在の課題
- **Next Experiments** … 次の実験予定

---

## 構造

| ファイル / フォルダ | 説明 |
|---------------------|------|
| project_status.md | 現在のプロジェクト状態 |
| next_tasks.md | 次にやるタスク |
| architecture.md | システム設計 |
| chat_bootstrap_prompt.md | 新規 AI セッション用の標準引き継ぎプロンプト |
| **current_task.md** | **AI開発フロー: ChatGPT が書く指示** |
| **run_report.md** | **AI開発フロー: Cursor が書く実装結果レポート** |
| **chat_context.md** | **ChatGPT レビュー用: Project Overview / Current Strategy / Latest Experiment / Leaderboard Summary / Open Questions / Next Experiments。実験後は `python3 -m kyotei_predictor.tools.update_chat_context` で Latest と Leaderboard を更新。** |
| **templates/** | **current_task / run_report のテンプレート** |
| experiment_log.md | モデル実験ログ（概要） |
| experiments/（リポジトリルート） | 実験トラッカー（一覧・leaderboard・個別ログ） |
| prompt_history/ | AIプロンプト履歴 |
| models/ | モデル比較 |
| analysis/ | ROI分析 |
