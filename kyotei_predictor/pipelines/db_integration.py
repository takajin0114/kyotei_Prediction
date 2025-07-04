import sqlite3
import os
import json
from typing import List, Dict, Any, Optional
import glob

class KyoteiDB:
    def __init__(self, db_path: str = 'data/kyotei_history.db'):
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self.conn = sqlite3.connect(db_path)
        self._create_tables()

    def _create_tables(self):
        c = self.conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS races (
            race_id TEXT PRIMARY KEY,
            date TEXT,
            stadium TEXT,
            round INTEGER,
            weather TEXT,
            wind_velocity REAL,
            air_temperature REAL
        )''')
        c.execute('''CREATE TABLE IF NOT EXISTS results (
            race_id TEXT,
            pit_number INTEGER,
            arrival INTEGER,
            start_time REAL,
            total_time REAL,
            PRIMARY KEY (race_id, pit_number)
        )''')
        self.conn.commit()

    def insert_race(self, race: Dict[str, Any]):
        c = self.conn.cursor()
        c.execute('''INSERT OR REPLACE INTO races (race_id, date, stadium, round, weather, wind_velocity, air_temperature)
                     VALUES (?, ?, ?, ?, ?, ?, ?)''',
                  (
                      race.get('race_id'),
                      race.get('date'),
                      race.get('stadium'),
                      race.get('round'),
                      race.get('weather'),
                      race.get('wind_velocity'),
                      race.get('air_temperature')
                  ))
        self.conn.commit()

    def insert_results(self, results: List[Dict[str, Any]]):
        c = self.conn.cursor()
        for result in results:
            c.execute('''INSERT OR REPLACE INTO results (race_id, pit_number, arrival, start_time, total_time)
                         VALUES (?, ?, ?, ?, ?)''',
                      (
                          result.get('race_id'),
                          result.get('pit_number'),
                          result.get('arrival'),
                          result.get('start_time'),
                          result.get('total_time')
                      ))
        self.conn.commit()

    def fetch_race(self, race_id: str) -> Optional[Dict[str, Any]]:
        c = self.conn.cursor()
        c.execute('SELECT * FROM races WHERE race_id = ?', (race_id,))
        row = c.fetchone()
        if row:
            keys = ['race_id', 'date', 'stadium', 'round', 'weather', 'wind_velocity', 'air_temperature']
            return dict(zip(keys, row))
        return None

    def fetch_all_races(self) -> list[dict]:
        c = self.conn.cursor()
        c.execute('SELECT * FROM races')
        rows = c.fetchall()
        keys = ['race_id', 'date', 'stadium', 'round', 'weather', 'wind_velocity', 'air_temperature']
        return [dict(zip(keys, row)) for row in rows]

    def fetch_results_by_race(self, race_id: str) -> list[dict]:
        c = self.conn.cursor()
        c.execute('SELECT * FROM results WHERE race_id = ?', (race_id,))
        rows = c.fetchall()
        keys = ['race_id', 'pit_number', 'arrival', 'start_time', 'total_time']
        return [dict(zip(keys, row)) for row in rows]

    def close(self):
        self.conn.close()

# --- サンプル: JSONからDBへインポート ---
def import_race_json(json_path: str, db: KyoteiDB):
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    # レース情報
    race_info = data.get('race_info', {})
    race_id = f"{race_info.get('date')}_{race_info.get('stadium')}_R{race_info.get('race_number')}"
    race_row = {
        'race_id': race_id,
        'date': race_info.get('date'),
        'stadium': race_info.get('stadium'),
        'round': race_info.get('race_number'),
        'weather': race_info.get('weather'),
        'wind_velocity': race_info.get('wind_velocity'),
        'air_temperature': race_info.get('air_temperature')
    }
    db.insert_race(race_row)
    # 結果情報
    results = []
    for rec in data.get('race_records', []):
        results.append({
            'race_id': race_id,
            'pit_number': rec.get('pit_number'),
            'arrival': rec.get('arrival'),
            'start_time': rec.get('start_time'),
            'total_time': rec.get('total_time')
        })
    db.insert_results(results)

def import_race_json_bulk(directory: str, db: KyoteiDB):
    files = glob.glob(f"{directory}/race_data_*.json")
    for fpath in files:
        try:
            import_race_json(fpath, db)
        except Exception as e:
            print(f"[WARN] {fpath} のインポート失敗: {e}")

# --- 利用例 ---
# db = KyoteiDB()
# all_races = db.fetch_all_races()
# for race in all_races:
#     print(race)
# results = db.fetch_results_by_race('2024-06-06_KIRYU_R1')
# for r in results:
#     print(r)
# db.close() 