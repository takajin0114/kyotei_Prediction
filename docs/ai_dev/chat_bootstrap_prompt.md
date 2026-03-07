# AI Chat Bootstrap Prompt

このプロジェクトは  
BoatRace（競艇）3連単 EV prediction AI を開発している。

新しい AI セッションでは  
**以下の順番でリポジトリを読んでから作業を開始すること。**

---

## Step 1 — Project Overview

**read**  
[docs/ai_dev/project_status.md](project_status.md)

**理解する内容**
- プロジェクトの目的
- データセット
- 現在のモデル
- 現在の ROI
- 開発フェーズ

---

## Step 2 — Architecture

**read**  
[docs/ai_dev/architecture.md](architecture.md)

**理解する内容**
- prediction pipeline
- feature → model → EV → bet selection
- Strategy B

---

## Step 3 — Next Tasks

**read**  
[docs/ai_dev/next_tasks.md](next_tasks.md)

**理解する内容**
- 現在の優先タスク
- モデル改善の方向

---

## Step 4 — Experiment Tracker

**read**  
[docs/ai_dev/experiments/leaderboard.md](experiments/leaderboard.md)  
then  
[docs/ai_dev/experiments/open_questions.md](experiments/open_questions.md)

**理解する内容**
- 現在のベストモデル
- 未解決課題

---

## Step 5 — Recent Experiments

**read**  
[docs/ai_dev/experiments/logs/](experiments/logs/)

最新の実験ログを確認する。  
YAML front matter を優先して読むこと。

---

## Step 6 — Prompt History

**read**  
[docs/ai_dev/prompt_history/](prompt_history/)

直近のプロンプト履歴を確認する。

---

## Development Rules

AI は新しい提案をする前に

1. 過去実験と重複していないか  
2. leaderboard を上回る可能性があるか  
3. open_questions に関連するか  

を確認すること。

---

## Experiment Logging

新しい実験を行う場合  
[docs/ai_dev/experiments/experiment_template_yaml.md](experiments/experiment_template_yaml.md)  
を使用する。

---

## Goal

**最終目標**  
BoatRace 3連単戦略  
long-term **ROI > 100%**
