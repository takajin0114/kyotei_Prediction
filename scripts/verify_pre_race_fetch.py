#!/usr/bin/env python3
"""
レース前情報取得の確認スクリプト
- 指定日（デフォルト: 明日）の開催会場を取得し、1レース分の出走表・直前情報を取得
- 取得元URLと取得結果の要約を表示
"""
import sys
import os
from datetime import date, timedelta, datetime

# プロジェクトルートを path に追加
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from metaboatrace.models.stadium import StadiumTelCode
from metaboatrace.scrapers.official.website.v1707.pages.monthly_schedule_page.location import create_monthly_schedule_page_url
from metaboatrace.scrapers.official.website.v1707.pages.monthly_schedule_page.scraping import extract_events
from metaboatrace.scrapers.official.website.v1707.pages.race.entry_page import location as entry_location
from metaboatrace.scrapers.official.website.v1707.pages.race.before_information_page import location as before_info_location
from metaboatrace.scrapers.official.website.v1707.pages.race.odds.trifecta_page import location as odds_location
import requests
from io import StringIO

from kyotei_predictor.tools.fetch.race_data_fetcher import fetch_race_entry_data, fetch_before_information
from kyotei_predictor.tools.fetch.odds_fetcher import fetch_trifecta_odds


def get_schedule_for_date(target_date: date) -> dict:
    """指定日の開催会場とレース番号リストを返す"""
    url = create_monthly_schedule_page_url(target_date.year, target_date.month)
    resp = requests.get(url)
    resp.raise_for_status()
    events = extract_events(StringIO(resp.text))
    schedule = {}
    for event in events:
        for d in range(event.days):
            day = event.starts_on + timedelta(days=d)
            if day == target_date:
                schedule[event.stadium_tel_code.name] = list(range(1, 13))
                break
    return schedule


def main():
    # 明日の日付
    tomorrow = date.today() + timedelta(days=1)
    print("=" * 60)
    print(f"レース前情報取得 確認（対象日: {tomorrow}）")
    print("=" * 60)

    # スケジュール取得
    print("\n[1] スケジュール取得")
    schedule_url = create_monthly_schedule_page_url(tomorrow.year, tomorrow.month)
    print(f"  取得元URL: {schedule_url}")
    schedule = get_schedule_for_date(tomorrow)
    if not schedule:
        print("  開催がありません。別の日で再試行します（今日）。")
        tomorrow = date.today()
        schedule = get_schedule_for_date(tomorrow)
        if not schedule:
            print("  今日も開催がありません。過去の開催日で確認する場合は日付を指定してください。")
            return
    print(f"  開催会場: {list(schedule.keys())}")

    # 先頭会場・第1レースで取得
    stadium_name = list(schedule.keys())[0]
    stadium = getattr(StadiumTelCode, stadium_name, None)
    if not stadium:
        stadium = next((s for s in StadiumTelCode if s.name == stadium_name), list(StadiumTelCode)[0])
    race_no = 1

    # 取得元URLを事前に表示
    entry_url = entry_location.create_race_entry_page_url(
        race_holding_date=tomorrow,
        stadium_tel_code=stadium,
        race_number=race_no,
    )
    before_info_url = before_info_location.create_race_before_information_page_url(
        race_holding_date=tomorrow,
        stadium_tel_code=stadium,
        race_number=race_no,
    )
    odds_url = odds_location.create_odds_page_url(
        race_holding_date=tomorrow,
        stadium_tel_code=stadium,
        race_number=race_no,
    )

    print("\n[2] レース前情報の取得元URL")
    print("  ■ 出走表（選手・艇・モーター・成績）")
    print(f"    {entry_url}")
    print("  ■ 直前情報（展示走・スタート展示・選手コンディション・艇設定・天候）")
    print(f"    {before_info_url}")
    print("  ■ 3連単オッズ（締切後）")
    print(f"    {odds_url}")

    # 出走表取得
    print("\n[3] 出走表の取得")
    entry_data = fetch_race_entry_data(tomorrow, stadium, race_no)
    if entry_data:
        info = entry_data.get("race_info", {})
        entries = entry_data.get("race_entries", [])
        print(f"  タイトル: {info.get('title', '')}")
        print(f"  周回: {info.get('number_of_laps')}周 進入固定: {info.get('is_course_fixed')}")
        print("  艇別:")
        for e in entries:
            r = e.get("racer", {})
            p = e.get("performance", {})
            print(f"    {e['pit_number']}号艇: {r.get('name')} ({r.get('current_rating')}) "
                  f"全国勝率{p.get('rate_in_all_stadium')} 当地{p.get('rate_in_event_going_stadium')}")
    else:
        print("  取得失敗（未公開またはエラー）")

    # 直前情報取得
    print("\n[4] 直前情報の取得")
    before_data = fetch_before_information(tomorrow, stadium, race_no)
    if before_data:
        n_start = len(before_data.get("start_exhibition", []))
        n_circum = len(before_data.get("circumference_exhibition", []))
        weather = before_data.get("weather_condition") or {}
        print(f"  スタート展示: {n_start}件, 周回展示: {n_circum}件")
        if weather.get("air_temperature") is not None:
            print(f"  天候: {weather.get('weather')} 気温{weather.get('air_temperature')}℃ 風速{weather.get('wind_velocity')}m")
        if n_start or n_circum:
            for s in before_data.get("start_exhibition", [])[:6]:
                print(f"    艇{s.get('pit_number')} 進入{s.get('start_course')} ST {s.get('start_time')}")
    else:
        print("  取得失敗または未公開（展示走実施後のみ公開）")

    # 3連単オッズ（締切後でないと取れない場合あり）
    print("\n[5] 3連単オッズの取得")
    odds_data = fetch_trifecta_odds(tomorrow, stadium, race_no)
    if odds_data and odds_data.get("odds_data"):
        print(f"  取得件数: {len(odds_data['odds_data'])} 通り")
    else:
        print("  未公開または締切前のため取得できませんでした")

    print("\n" + "=" * 60)
    print("以上でレース前情報取得の確認を完了しました。")
    print("=" * 60)


if __name__ == "__main__":
    main()
