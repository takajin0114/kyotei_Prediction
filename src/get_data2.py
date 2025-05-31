from bs4 import BeautifulSoup
import requests
import re
import pandas as pd

# URL（例：戸田 2025/05/31 1R）
jcd = "02"
rno = "1"
hd = "20250531"
url = f"https://www.boatrace.jp/owpc/pc/race/racedata?rno={rno}&jcd={jcd}&hd={hd}"
headers = {"User-Agent": "Mozilla/5.0"}

res = requests.get(url, headers=headers)
soup = BeautifulSoup(res.content, "html.parser")

# デバッグ: 取得したHTMLの先頭500文字を表示
print("--- 取得HTMLプレビュー ---")
print(soup.prettify()[:500])
print("--- /取得HTMLプレビュー ---")

# Table 1 取得
# 取得したテーブル数を確認
print(f"取得したtable数: {len(tables := soup.find_all('table'))}")
if len(tables) < 2:
    print("エラー: テーブルが2つ未満です。ページ構造やURL、日付・レース番号を確認してください。")
    exit(1)
table = tables[1]  # 選手情報があるテーブル
rows = table.find_all("tr")

# 枠ごとのブロックを抽出
def extract_blocks(rows):
    blocks = []
    block = []
    for row in rows:
        cols = row.find_all("td")
        texts = [col.get_text(strip=True) for col in cols if col.get_text(strip=True)]
        if texts and texts[0] in ['１', '２', '３', '４', '５', '６']:
            if block:
                blocks.append(block)
                block = []
            block.append(texts)
        elif block and texts:
            block.append(texts)
        elif block and not texts:
            blocks.append(block)
            block = []
    if block:
        blocks.append(block)
    return blocks

# データ抽出関数
def parse_racer_block(block, lane):
    try:
        raw_profile = block[0][1]
        reg_match = re.match(r"(\d{4})/(.)(.)?(.+?)(\D{2})/(\D+)(\d+)歳/(\d+\.?\d*)kg", raw_profile)
        if reg_match:
            reg_num = reg_match.group(1)
            grade = reg_match.group(2) + (reg_match.group(3) or '')
            name = reg_match.group(4).strip()
            branch = reg_match.group(6).strip()
            age = int(reg_match.group(7))
        else:
            return None

        national = [float(x) for x in re.findall(r"\d+\.\d+", block[2][0])]
        local = [float(x) for x in re.findall(r"\d+\.\d+", block[3][0])]
        motor = re.findall(r"(\d{2,3})", block[4][0])[0]
        motor_rates = [float(x) for x in re.findall(r"\d+\.\d+", block[4][0])]
        boat = re.findall(r"(\d{2,3})", block[5][0])[0]
        boat_rates = [float(x) for x in re.findall(r"\d+\.\d+", block[5][0])]

        return {
            f"枠{lane}_登録番号": reg_num,
            f"枠{lane}_級別": grade,
            f"枠{lane}_氏名": name,
            f"枠{lane}_支部": branch,
            f"枠{lane}_年齢": age,
            f"枠{lane}_全国_勝率": national[0],
            f"枠{lane}_全国_2連率": national[1],
            f"枠{lane}_全国_3連率": national[2],
            f"枠{lane}_当地_勝率": local[0],
            f"枠{lane}_当地_2連率": local[1],
            f"枠{lane}_当地_3連率": local[2],
            f"枠{lane}_モーター番号": motor,
            f"枠{lane}_モーター_2連率": motor_rates[0],
            f"枠{lane}_モーター_3連率": motor_rates[1],
            f"枠{lane}_ボート番号": boat,
            f"枠{lane}_ボート_2連率": boat_rates[0],
            f"枠{lane}_ボート_3連率": boat_rates[1],
        }
    except Exception as e:
        print(f"解析エラー（枠{lane}）:", e)
        return None

# 全枠処理
data = {
    "開催日": f"{hd[:4]}/{hd[4:6]}/{hd[6:]}",
    "場コード": jcd,
    "レース番号": f"{rno}R"
}
blocks = extract_blocks(rows)

for i, block in enumerate(blocks[:6]):  # 枠1〜6
    info = parse_racer_block(block, i + 1)
    if info:
        data.update(info)

# 出力
print("\n【レース全体情報（1行）】")
df = pd.DataFrame([data])
print(df.T)
