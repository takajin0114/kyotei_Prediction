import os
import glob
import json
from itertools import permutations

def parse_key(path, prefix):
    fname = os.path.basename(path)
    parts = fname.replace(prefix, "").replace(".json", "").split("_")
    if len(parts) >= 3:
        date_parts = parts[0:3]
        date = "".join(date_parts).replace("-", "")
        if len(parts) >= 5:
            stadium = parts[3]
            rno = parts[4]
        elif len(parts) >= 4:
            stadium = parts[3]
            rno = "1"
        else:
            stadium = "UNKNOWN"
            rno = "1"
    else:
        date = parts[0] if parts else "UNKNOWN"
        stadium = parts[1] if len(parts) > 1 else "UNKNOWN"
        rno = parts[2] if len(parts) > 2 else "1"
    rno = rno.replace('R', '')
    try:
        rno_int = int(rno)
    except ValueError:
        rno_int = 1
    return (date, stadium, rno_int)

def main(data_dir):
    race_files = glob.glob(os.path.join(data_dir, 'race_data_*.json'))
    odds_files = glob.glob(os.path.join(data_dir, 'odds_data_*.json'))
    race_map = {parse_key(f, "race_data_"): f for f in race_files}
    odds_map = {parse_key(f, "odds_data_"): f for f in odds_files}
    keys = set(race_map.keys()) & set(odds_map.keys())
    pairs = [(race_map[k], odds_map[k]) for k in sorted(keys)]
    total = 0
    hit = 0
    trifecta_list = list(permutations(range(1,7), 3))
    for race_path, odds_path in pairs:
        with open(race_path, encoding='utf-8') as f:
            race = json.load(f)
        arrival_tuple = None
        valid_records = [r for r in race['race_records'] if r.get('arrival') is not None]
        if len(valid_records) >= 3:
            sorted_records = sorted(valid_records, key=lambda x: x['arrival'])
            arrival_tuple = tuple(r['pit_number'] for r in sorted_records[:3])
        if arrival_tuple is None:
            continue
        total += 1
        if arrival_tuple in trifecta_list:
            hit += 1
    print(f"全レース数: {total}")
    print(f"的中actionが存在するレース数: {hit}")
    if total > 0:
        print(f"的中率: {hit/total:.2%}")
    else:
        print("有効なレースデータがありません")

if __name__ == "__main__":
    import sys
    data_dir = sys.argv[1] if len(sys.argv) > 1 else "kyotei_predictor/data/raw"
    main(data_dir) 