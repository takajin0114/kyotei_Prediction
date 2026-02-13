# 大量変更が見える時の安全なステージング運用

## 背景

このリポジトリでは JSON などを Git LFS で管理しています。  
環境によっては `git lfs pull` 後に、内容が変わっていなくても大量の `M` が表示される場合があります。

この状態で `git add .` を実行すると、意図しないファイルまでコミットに入るリスクがあります。

## 推奨運用

1. まず現状を確認

```bash
git status -sb
```

2. 変更対象ファイルだけを明示してステージ

```bash
git add path/to/file1 path/to/file2
```

3. ステージ内容を確認

```bash
git diff --cached --name-only
git diff --cached
```

4. 問題なければコミット

```bash
git commit -m "your message"
```

## 誤ってステージした場合

ステージだけ外す（作業ファイルはそのまま）:

```bash
git restore --staged path/to/file
```

全ステージを外す:

```bash
git restore --staged .
```

## 避けるべき操作

- `git add .`
- `git commit -a`

どちらも大量の無関係変更を巻き込みやすいため、このリポジトリでは非推奨です。
