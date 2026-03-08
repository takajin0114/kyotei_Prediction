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

## ChatGPT Review Workflow

1. Cursor で作業する
2. `bash scripts/ai_dev_cycle.sh` を実行する
3. `docs/ai_dev/chat_context.md` が生成される
4. GitHub に push する
5. ChatGPT には `chat_context.md` の raw URL を渡す

`chat_context.md` に含まれる内容:

- **run_report** … 実装結果レポート（変更ファイル・実行コマンド・結果・懸念・次アクション）
- **leaderboard** … 実験 ROI 一覧
- **project_status** … プロジェクト状態
- **latest experiment** … experiments/logs/ の最新実験ログ 1 件

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
| **chat_context.md** | **ChatGPT レビュー用: run_report / leaderboard / project_status / 最新実験の統合** |
| **templates/** | **current_task / run_report のテンプレート** |
| experiment_log.md | モデル実験ログ（概要） |
| experiments/（リポジトリルート） | 実験トラッカー（一覧・leaderboard・個別ログ） |
| prompt_history/ | AIプロンプト履歴 |
| models/ | モデル比較 |
| analysis/ | ROI分析 |
