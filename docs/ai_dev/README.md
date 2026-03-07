# AI Development System

このプロジェクトは AI（Cursor / ChatGPT）と共同開発している。

AIが新しい作業を開始する前に
必ず以下を読む

- [docs/ai_dev/project_status.md](project_status.md)
- [docs/ai_dev/next_tasks.md](next_tasks.md)
- [docs/ai_dev/architecture.md](architecture.md)

実験管理は [docs/ai_dev/experiments/](experiments/) を参照すること。項目定義・ステータスルールは [field_definitions.md](experiments/field_definitions.md)、[status_rules.md](experiments/status_rules.md)。

## Chat Bootstrap

When starting a new AI coding session, read [docs/ai_dev/chat_bootstrap_prompt.md](chat_bootstrap_prompt.md).

---

## 構造

| ファイル / フォルダ | 説明 |
|---------------------|------|
| project_status.md | 現在のプロジェクト状態 |
| next_tasks.md | 次にやるタスク |
| architecture.md | システム設計 |
| chat_bootstrap_prompt.md | 新規 AI セッション用の標準引き継ぎプロンプト |
| experiment_log.md | モデル実験ログ（概要） |
| experiments/ | 実験トラッカー（一覧・leaderboard・個別ログ） |
| prompt_history/ | AIプロンプト履歴 |
| models/ | モデル比較 |
| analysis/ | ROI分析 |
