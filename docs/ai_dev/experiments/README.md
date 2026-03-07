# Experiment Tracker

このディレクトリは、競艇AIプロジェクトの実験履歴を管理する。

## 目的

- モデル比較を残す
- ROI 改善の流れを追跡する
- AI が次の改善候補を判断しやすくする
- 失敗した実験を再実行しないようにする

AI は新しいモデル実験を始める前に、必ず以下を読むこと。

- [docs/ai_dev/project_status.md](../project_status.md)
- [docs/ai_dev/next_tasks.md](../next_tasks.md)
- [docs/ai_dev/experiments/leaderboard.md](leaderboard.md)
- [docs/ai_dev/experiments/open_questions.md](open_questions.md)

## 構成

| ファイル / フォルダ | 説明 |
|---------------------|------|
| experiment_index.md | 実験一覧 |
| experiment_template.md | 実験記録テンプレート（簡易版） |
| experiment_template_yaml.md | 実験記録テンプレート（YAML standard・推奨） |
| field_definitions.md | YAML 項目定義 |
| status_rules.md | status / decision の運用ルール |
| leaderboard.md | 成績上位実験一覧 |
| open_questions.md | 未解決課題 |
| logs/ | 個別実験ログ |

標準の実験記録は **experiment_template_yaml.md** を推奨する。YAML front matter は AI が読む主要情報、Markdown 本文は解釈・考察を記載する。新規実験ログは可能な限り YAML standard を使う。AI は新規実験提案前に leaderboard.md、open_questions.md、status_rules.md を確認すること。

## 運用ルール

1. 新しい実験を開始する前に leaderboard を確認する
2. 実験完了後は experiment_index と leaderboard を更新する
3. ROI が悪かった実験でも rejected として残す
4. AI は過去実験と重複する提案を避ける
5. 新しいチャットでは experiments/leaderboard.md を先に読む

## For AI Assistants

Before proposing a new experiment, review:

- [leaderboard.md](leaderboard.md)
- [open_questions.md](open_questions.md)
- [status_rules.md](status_rules.md)
- the latest logs in [logs/](logs/)

When creating a new log, prefer the YAML standard ([experiment_template_yaml.md](experiment_template_yaml.md)). Avoid proposing the same experiment unless the difference is explicit.
