import requests
from bs4 import BeautifulSoup
import pandas as pd
import re

# ✅ URL (2025年5月31日 戸田1R)
jcd = "02"  # 場所コード (02 = 戸田)
rno = "1"    # レース番号
hd = "20250531"  # 開催日
url = f"https://www.boatrace.jp/owpc/pc/race/raceresult?rno={rno}&jcd={jcd}&hd={hd}"
headers = {"User-Agent": "Mozilla/5.0"}

# ページ取得
response = requests.get(url, headers=headers)
soup = BeautifulSoup(response.content, "html.parser")

# 情報の表示
race_info = {
    "開催日": f"{hd[:4]}/{hd[4:6]}/{hd[6:]}",
    "場コード": jcd,
    "レース番号": f"{rno}R"
}
print("\n【レース情報】")
for key, value in race_info.items():
    print(f"{key}: {value}")

# Table 1 着順情報
table = soup.find_all("table")[1]  # Table 1
rows = table.find_all("tr")[1:]  # ヘッダーは除く

# データ抽出
data = []
for row in rows:
    cols = row.find_all("td")
    if len(cols) >= 4:
        rank = cols[0].get_text(strip=True)
        lane = cols[1].get_text(strip=True)
        raw_name = cols[2].get_text(strip=True)
        time = cols[3].get_text(strip=True)

        # 選手番号と名前を分割
        match = re.match(r'(\d{4})(.+)', raw_name)
        if match:
            reg_num = match.group(1)
            name = match.group(2)
        else:
            reg_num = ''
            name = raw_name

        data.append([rank, lane, reg_num, name, time])

# 着順情報 DataFrame
df_result = pd.DataFrame(data, columns=["着順", "枠", "選手番号", "選手名", "レースタイム"])
print("\n【レース結果】")
print(df_result)

# Table 3 3連単 の抽出
payout_table = soup.find_all("table")[3]  # Table 3
rows = payout_table.find_all("tr")
trifecta_result = None
for row in rows:
    cols = row.find_all("td")
    if len(cols) >= 4 and cols[0].get_text(strip=True) == "3連単":
        combo = cols[1].get_text(strip=True)
        amount = cols[2].get_text(strip=True)
        popularity = cols[3].get_text(strip=True)
        trifecta_result = {
            "組番": combo,
            "払戻金": amount,
            "人気": popularity
        }
        break

if trifecta_result:
    print("\n【3連単結果】")
    for key, value in trifecta_result.items():
        print(f"{key}: {value}")
else:
    print("\n3連単情報が見つかりませんでした。")
