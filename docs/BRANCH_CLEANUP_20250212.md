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

---

## リモートブランチの整理（任意）

以下は main にマージ済み、または古いドキュメント/機能用のリモートブランチです。  
必要に応じて `git push origin --delete <branch>` で削除できます。

- docs-cleanup
- docs/api-tasks-update-20240625
- docs/update-20250703
- docs/update-repo-md-20250626
- feature/add-data-acquisition-docs
- feature/docs-update-20250627
- feature/fast-mode-implementation（main に含まれる）
- feature/data-acquisition-stabilization-20250811（main に含まれる）
- feature/optimization-batch-fix-and-docs-cleanup
- feature/repository-cleanup-and-optimization
- feature/repository-cleanup-and-optimization-new
- feature/repository-refactoring
- refactor/dir-structure-20250704
- その他、マージ済みと判断した feature/* / fix/* / docs/*

削除前に `git log main..origin/<branch>` で未マージのコミットがないか確認することを推奨します。
