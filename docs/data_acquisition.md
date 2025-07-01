
# データ取得技術ドキュメント

## 📌 使用ライブラリ
```python
metaboatrace.scrapers==3.3.1  # 競艇データスクレイピング
requests==2.31.0             # HTTP通信
beautifulsoup4==4.12.2       # HTML解析
```

## 🛠️ 主要クラス/機能
### 1. RaceListScraper
```python
from metaboatrace.scrapers import RaceListScraper
scraper = RaceListScraper()
races = scraper.scrape(date="2024-06-15", stadium="桐生")
```
**取得データ**:
- レース番号
- 出走選手
- 締切時刻

### 2. RaceResultScraper
```python
from metaboatrace.scrapers import RaceResultScraper
scraper = RaceResultScraper()
results = scraper.scrape(date="2024-06-15", stadium="桐生", race_number=1)
```
**取得データ**:
- 着順
- スタートタイム
- 払戻金

## ⚠️ 注意事項
1. アクセス間隔は5秒以上空ける
2. 取得データは24時間以内に削除（規約準拠）
3. エラー時は10分間リトライ待機

## 🔗 関連ファイル
- `kyotei_predictor/race_data_fetcher.py`
- `config/access_settings.yaml`
