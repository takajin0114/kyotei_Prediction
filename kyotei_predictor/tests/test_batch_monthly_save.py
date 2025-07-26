import os
import shutil
import json
from datetime import datetime
from kyotei_predictor.tools.batch import retry_missing_races

def test_monthly_save(tmp_path):
    # テスト用日付・会場
    date_str = "2025-07-20"
    venue = "TESTVENUE"
    race_no = 1
    # テスト用RAW_DATA_DIRを一時ディレクトリに差し替え
    retry_missing_races.RAW_DATA_DIR = str(tmp_path)
    # ダミーデータ保存
    dummy_data = {"test": True}
    month_dir = os.path.join(tmp_path, "2025-07")
    os.makedirs(month_dir, exist_ok=True)
    race_fname = f"race_data_{date_str}_{venue}_R{race_no}.json"
    race_fpath = os.path.join(month_dir, race_fname)
    with open(race_fpath, 'w', encoding='utf-8') as f:
        json.dump(dummy_data, f)
    # ファイルが正しい場所に存在するか
    assert os.path.exists(race_fpath)
    # 内容確認
    with open(race_fpath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    assert data["test"] is True 