from datetime import datetime
from metaboatrace.models.stadium import StadiumTelCode
from kyotei_predictor.tools.batch.batch_fetch_all_venues import fetch_race_data_parallel

if __name__ == "__main__":
    print("[DEBUG] スクリプト開始")
    day = datetime.strptime("2024-01-04", "%Y-%m-%d").date()
    stadium = StadiumTelCode.KIRYU
    race_list = [3, 4, 7, 9, 11]
    for race_no in race_list:
        print(f"[TEST] {day} {stadium.name} R{race_no}")
        try:
            result = fetch_race_data_parallel(day, stadium, race_no, rate_limit_seconds=1, max_retries=3)
            print("[RESULT]", result)
        except Exception as e:
            print(f"[EXCEPTION] R{race_no}", type(e).__name__, e) 