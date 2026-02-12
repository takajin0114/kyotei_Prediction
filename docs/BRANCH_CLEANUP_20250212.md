# ブランチ整理（2025-02-12）

## 実施した内容

### マージ・プッシュ
- **feature/repository-cleanup** を **main** にマージ（Fast-forward）
- **main** を `origin/main` にプッシュ
- **main** の上流を `origin/main` に設定

### 削除したローカルブランチ
| ブランチ | 理由 |
|----------|------|
| feature/repository-cleanup | main にマージ済み |
| feature/fast-mode-implementation | feature/data-acquisition-stabilization-20250811 と同一コミット・main に含まれる |
| feature/data-acquisition-stabilization-20250811 | main の履歴に含まれる |

### 削除したリモートブランチ
| ブランチ | 理由 |
|----------|------|
| origin/feature/repository-cleanup | main にマージ済み |
| origin/feature/data-acquisition-stabilization-20250811 | 未マージ確認ののち `--merged main` でマージ済みと判定し削除 |
| origin/feature/fast-mode-implementation | 同上 |

---

## 未マージ確認の結果（第二回整理）

`git branch -r --merged main` で main に完全にマージされているリモートブランチを確認し、上記 2 本のみ削除しました。

**残しているリモートブランチ**（いずれも `main..origin/<branch>` にコミットあり＝未マージ）  
docs-cleanup, docs/api-tasks-update-20240625, docs/update-20250703, docs/update-repo-md-20250626, feature/add-data-acquisition-docs, feature/algorithm-docs-b123, feature/api-caching, feature/api-endpoints-refactor, feature/api-error-handling-refactor, feature/b1-trifecta-extensions, feature/batch-data-fetcher-docs, feature/batch-system-improvements, feature/docs-update-20250627, feature/investment-value-trifecta, feature/next-steps-update, feature/optimization-batch-fix-and-docs-cleanup, feature/phase3-complete, feature/prediction-tool-e2e-test-and-doc-update, feature/refactoring-phase1-4, feature/refactoring-phase1-4-clean, feature/repository-cleanup-and-optimization, feature/repository-cleanup-and-optimization-new, feature/repository-refactoring, feature/rl-ppo-sample, feature/rl-roadmap-update, feature/rl-state-action-vectorization, feature/statistics-b5, feature/update-roadmap-v2, fix/conditional-learn-dir-support, refactor/dir-structure-20250704, web-display-implementation

これらは main に未マージのコミットを含むため、意図的に削除していません。不要と判断したブランチは、マージ or 破棄を決めたうえで `git push origin --delete <branch>` で削除してください。
