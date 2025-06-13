# 競艇公式サイト構造分析結果

## 調査日時
2025-06-13

## 調査対象
- ボートレース公式サイト: https://www.boatrace.jp/
- 既存スクレイピングライブラリ: metaboatrace/scrapers
- 実装事例: Qiita記事等

## 主要な発見

### 1. 既存ライブラリの存在
**metaboatrace/scrapers** という高品質なスクレイピングライブラリが存在
- PyPIで公開済み: `pip install metaboatrace.scrapers`
- バージョン管理: v1707 (2017年7月のサイト改修に対応)
- 構造化されたアーキテクチャ
- テストカバレッジ完備

### 2. サイト構造の特徴
- **URL構造**: 日付・競艇場コードベースの体系的なURL
- **データ形式**: HTML + 一部JavaScript
- **アクセス制限**: robots.txt存在、適切なレート制限が必要
- **データ範囲**: 過去のレース結果から最新情報まで網羅

### 3. 取得可能なデータ
#### レース基本情報
- 開催場（24競艇場）
- 開催日・レース番号
- 出走表（選手、モーター、ボート）
- レース条件（天候、風速、水温等）

#### 選手データ
- 選手登録番号、氏名、所属支部
- 級別、出身地、生年月日
- 通算成績（勝率、連対率、3連対率）
- 最近の成績動向

#### レース結果
- 着順、決まり手、タイム
- スタートタイミング
- オッズ情報（3連単、3連複、2連単等）
- 払戻金情報

### 4. 技術的な実装パターン
#### URL生成パターン
```python
# 月間スケジュール例
base_url = "https://boatrace.jp/owpc/pc/race/monthlyschedule"
params = {"ym": "202209"}  # 年月指定

# 日別レース結果例
race_url = f"https://boatrace.jp/owpc/pc/race/raceresult"
params = {
    "rno": race_number,
    "jcd": venue_code,
    "hd": date_string
}
```

#### スクレイピング実装例
```python
import requests
from bs4 import BeautifulSoup
from time import sleep

# 基本的なパターン
res = requests.get(url)
res.encoding = res.apparent_encoding
soup = BeautifulSoup(res.text, 'html.parser')

# 必須: レート制限
sleep(5)  # 5秒間隔推奨
```

### 5. 法的・倫理的考慮事項
- **robots.txt**: 存在確認済み、遵守必須
- **アクセス頻度**: 5秒間隔が推奨される
- **利用規約**: 商用利用制限の可能性
- **データ利用**: 個人利用範囲での使用推奨

## 実装戦略の提案

### Option 1: 既存ライブラリ活用
**推奨度: ★★★★★**
```bash
pip install metaboatrace.scrapers
```
- **メリット**: 
  - 即座に利用可能
  - 高品質・テスト済み
  - メンテナンス済み
- **デメリット**: 
  - カスタマイズ制限
  - 依存関係追加

### Option 2: 独自実装
**推奨度: ★★☆☆☆**
- **メリット**: 
  - 完全なカスタマイズ可能
  - 学習効果高い
- **デメリット**: 
  - 開発工数大
  - メンテナンス負荷

### Option 3: ハイブリッド実装
**推奨度: ★★★★☆**
- 既存ライブラリをベースに必要部分のみカスタマイズ
- 段階的な独自実装への移行

## 次のアクションプラン

### Phase 1-A: 既存ライブラリ検証 (Week 1)
1. **metaboatrace.scrapers の動作確認**
   ```bash
   pip install metaboatrace.scrapers
   # 基本的な動作テスト
   ```

2. **データ取得テスト**
   - 選手データ取得
   - レース結果取得
   - エラーハンドリング確認

3. **既存アプリとの統合検討**
   - データ形式の互換性確認
   - パフォーマンス評価

### Phase 1-B: 独自実装準備 (Week 1-2)
1. **詳細サイト構造分析**
   - 具体的なURL構造の解析
   - HTMLパース方法の検討
   - JavaScript動的コンテンツの確認

2. **プロトタイプ実装**
   - 基本的なスクレイピング機能
   - レート制限機能
   - エラーハンドリング

## 推奨実装方針

**最終推奨**: Option 1 (既存ライブラリ活用) → Option 3 (段階的カスタマイズ)

1. **短期**: metaboatrace.scrapersで迅速にデータ取得機能を実装
2. **中期**: 必要に応じて独自機能を追加実装
3. **長期**: 完全独自実装への移行を検討

この方針により、開発リスクを最小化しながら、確実にPhase 1の目標を達成できます。