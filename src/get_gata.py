import requests
from bs4 import BeautifulSoup
import pandas as pd

# ✅ URLを設定（例：2024年5月1日、住之江競艇場、12R）
url = "https://www.boatrace.jp/owpc/pc/race/racelist?rno=2&jcd=02&hd=20250530"
headers = {
    "User-Agent": "Mozilla/5.0"
}

# ✅ ページ取得
response = requests.get(url, headers=headers)
soup = BeautifulSoup(response.content, "html.parser")

# ✅ 全てのtableタグを取得
tables = soup.find_all("table")

# ✅ 各テーブルを1つずつ表示
for i, table in enumerate(tables):
    print(f"\n--- Table {i} ---")
    rows = table.find_all("tr")
    for row in rows:
        cols = row.find_all(["th", "td"])
        texts = [col.get_text(strip=True) for col in cols]
        print(texts)
