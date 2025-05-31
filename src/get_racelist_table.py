from bs4 import BeautifulSoup
import requests
import pandas as pd

# racelistページからtableデータを取得し、全テーブルの内容を表示
url = "https://www.boatrace.jp/owpc/pc/race/racelist?rno=1&jcd=02&hd=20250531"
headers = {"User-Agent": "Mozilla/5.0"}

response = requests.get(url, headers=headers)
soup = BeautifulSoup(response.content, "html.parser")

tables = soup.find_all("table")
print(f"取得したtable数: {len(tables)}")

# 各テーブルを1つずつ表示
for i, table in enumerate(tables):
    print(f"\n--- Table {i} ---")
    rows = table.find_all("tr")
    for row in rows:
        cols = row.find_all(["th", "td"])
        texts = [col.get_text(strip=True) for col in cols]
        print(texts)

# Table 1のデータをDataFrameに格納
if len(tables) > 0:
    table1 = tables[0]
    rows = table1.find_all("tr")
    data = []
    for row in rows:
        cols = row.find_all(["th", "td"])
        texts = [col.get_text(strip=True) for col in cols]
        if texts:
            data.append(texts)
    # DataFrame化
    if data:
        df = pd.DataFrame(data)
        print("\n[Table 1 DataFrame]")
        print(df)
    else:
        print("Table 1にデータがありません")
else:
    print("tableが見つかりません")
