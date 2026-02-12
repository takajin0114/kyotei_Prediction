#!/usr/bin/env python3
"""
競艇レースデータ取得ツール
"""

import os
import sys
import json
import time
import requests
from datetime import date, datetime
from io import StringIO
from typing import Any
from metaboatrace.models.stadium import StadiumTelCode
from metaboatrace.scrapers.official.website.v1707.pages.race.entry_page import location, scraping as entry_scraping
from metaboatrace.scrapers.official.website.v1707.pages.race.result_page import location as result_location, scraping as result_scraping
from metaboatrace.scrapers.official.website.v1707.pages.race.before_information_page import (
    location as before_info_location,
    scraping as before_info_scraping,
)
from metaboatrace.scrapers.official.website.exceptions import RaceCanceled
from kyotei_predictor.tools.fetch.odds_fetcher import fetch_trifecta_odds
from kyotei_predictor.utils.common import KyoteiUtils


# 文字化け対策: 標準出力のエンコーディングをUTF-8に設定
if sys.platform.startswith('win'):
    import codecs
    # PowerShellでの文字化け対策
    try:
        # 環境変数でUTF-8を強制
        os.environ['PYTHONIOENCODING'] = 'utf-8'
        os.environ['PYTHONLEGACYWINDOWSSTDIO'] = 'utf-8'
        
        # 標準出力をUTF-8に設定（安全な方法）
        if hasattr(sys.stdout, 'detach'):
            sys.stdout = codecs.getwriter('utf-8')(sys.stdout.detach())
            sys.stderr = codecs.getwriter('utf-8')(sys.stderr.detach())
    except Exception:
        # エラーが発生した場合は環境変数のみ設定
        os.environ['PYTHONIOENCODING'] = 'utf-8'
        os.environ['PYTHONLEGACYWINDOWSSTDIO'] = 'utf-8'

def safe_print(message: str) -> None:
    """文字化け対策付きprint関数"""
    utils = KyoteiUtils()
    utils.safe_print(message)

def safe_extract_racers(html_file: StringIO, max_retries: int = 3) -> list[Any]:
    """
    選手データを安全に抽出する関数（エラーハンドリング付き・リトライ機能付き）
    
    Args:
        html_file: HTMLファイルオブジェクト
        max_retries: 最大リトライ回数
    
    Returns:
        list: 選手データのリスト（エラーが発生した場合は空のリスト）
    """
    for attempt in range(max_retries):
        try:
            html_file.seek(0)  # ファイルポインタを先頭に戻す
            racers = entry_scraping.extract_racers(html_file)
            if racers:
                safe_print(f"✅ 選手データ取得成功: {len(racers)}名")
                return racers
            else:
                safe_print(f"⚠️  選手データが空です（試行 {attempt + 1}/{max_retries}）")
                if attempt < max_retries - 1:
                    time.sleep(2)  # 2秒待機してリトライ
                    continue
                else:
                    safe_print("❌ 選手データ取得失敗: 最大リトライ回数に達しました")
                    return []
        except ValueError as e:
            error_msg = str(e)
            if "not enough values to unpack" in error_msg:
                safe_print(f"⚠️  選手名解析エラー（試行 {attempt + 1}/{max_retries}）: 名前の形式が予期しない形式です")
                safe_print(f"⚠️  エラー詳細: {error_msg}")
                if hasattr(e, 'args') and e.args:
                    safe_print(f"⚠️  問題の文字列: {e.args[0]}")
                
                if attempt < max_retries - 1:
                    safe_print(f"🔄 2秒後にリトライします...")
                    time.sleep(2)
                    continue
                else:
                    safe_print("❌ 選手名解析エラー: 最大リトライ回数に達しました - スキップ")
                    return []
            else:
                safe_print(f"⚠️  ValueError（試行 {attempt + 1}/{max_retries}）: {error_msg}")
                if attempt < max_retries - 1:
                    time.sleep(2)
                    continue
                else:
                    raise e
        except Exception as e:
            safe_print(f"⚠️  選手データ抽出エラー（試行 {attempt + 1}/{max_retries}）: {type(e).__name__}: {e}")
            if attempt < max_retries - 1:
                safe_print(f"🔄 2秒後にリトライします...")
                time.sleep(2)
                continue
            else:
                safe_print("❌ 選手データ抽出エラー: 最大リトライ回数に達しました")
                return []
    
    return []

def safe_extract_race_entries(html_file: StringIO, max_retries: int = 3) -> list[Any]:
    """
    レース出走データを安全に抽出する関数（エラーハンドリング付き・リトライ機能付き）
    
    Args:
        html_file: HTMLファイルオブジェクト
        max_retries: 最大リトライ回数
    
    Returns:
        list: レース出走データのリスト（エラーが発生した場合は空のリスト）
    """
    for attempt in range(max_retries):
        try:
            html_file.seek(0)  # ファイルポインタを先頭に戻す
            entries = entry_scraping.extract_race_entries(html_file)
            if entries:
                safe_print(f"✅ レース出走データ取得成功: {len(entries)}艇")
                return entries
            else:
                safe_print(f"⚠️  レース出走データが空です（試行 {attempt + 1}/{max_retries}）")
                if attempt < max_retries - 1:
                    time.sleep(2)
                    continue
                else:
                    safe_print("❌ レース出走データ取得失敗: 最大リトライ回数に達しました")
                    return []
        except Exception as e:
            safe_print(f"⚠️  レース出走データ抽出エラー（試行 {attempt + 1}/{max_retries}）: {type(e).__name__}: {e}")
            if attempt < max_retries - 1:
                safe_print(f"🔄 2秒後にリトライします...")
                time.sleep(2)
                continue
            else:
                safe_print("❌ レース出走データ抽出エラー: 最大リトライ回数に達しました")
                return []
    
    return []

def safe_extract_racer_performances(html_file: StringIO, max_retries: int = 3) -> list[Any]:
    """
    選手成績データを安全に抽出する関数（エラーハンドリング付き・リトライ機能付き）
    
    Args:
        html_file: HTMLファイルオブジェクト
        max_retries: 最大リトライ回数
    
    Returns:
        list: 選手成績データのリスト（エラーが発生した場合は空のリスト）
    """
    for attempt in range(max_retries):
        try:
            html_file.seek(0)  # ファイルポインタを先頭に戻す
            performances = entry_scraping.extract_racer_performances(html_file)
            if performances:
                safe_print(f"✅ 選手成績データ取得成功: {len(performances)}件")
                return performances
            else:
                safe_print(f"⚠️  選手成績データが空です（試行 {attempt + 1}/{max_retries}）")
                if attempt < max_retries - 1:
                    time.sleep(2)
                    continue
                else:
                    safe_print("❌ 選手成績データ取得失敗: 最大リトライ回数に達しました")
                    return []
        except Exception as e:
            safe_print(f"⚠️  選手成績データ抽出エラー（試行 {attempt + 1}/{max_retries}）: {type(e).__name__}: {e}")
            if attempt < max_retries - 1:
                safe_print(f"🔄 2秒後にリトライします...")
                time.sleep(2)
                continue
            else:
                safe_print("❌ 選手成績データ抽出エラー: 最大リトライ回数に達しました")
                return []
    
    return []

def safe_extract_boat_performances(html_file: StringIO, max_retries: int = 3) -> list[Any]:
    """
    ボート成績データを安全に抽出する関数（エラーハンドリング付き・リトライ機能付き）
    
    Args:
        html_file: HTMLファイルオブジェクト
        max_retries: 最大リトライ回数
    
    Returns:
        list: ボート成績データのリスト（エラーが発生した場合は空のリスト）
    """
    for attempt in range(max_retries):
        try:
            html_file.seek(0)  # ファイルポインタを先頭に戻す
            performances = entry_scraping.extract_boat_performances(html_file)
            if performances:
                safe_print(f"✅ ボート成績データ取得成功: {len(performances)}件")
                return performances
            else:
                safe_print(f"⚠️  ボート成績データが空です（試行 {attempt + 1}/{max_retries}）")
                if attempt < max_retries - 1:
                    time.sleep(2)
                    continue
                else:
                    safe_print("❌ ボート成績データ取得失敗: 最大リトライ回数に達しました")
                    return []
        except Exception as e:
            safe_print(f"⚠️  ボート成績データ抽出エラー（試行 {attempt + 1}/{max_retries}）: {type(e).__name__}: {e}")
            if attempt < max_retries - 1:
                safe_print(f"🔄 2秒後にリトライします...")
                time.sleep(2)
                continue
            else:
                safe_print("❌ ボート成績データ抽出エラー: 最大リトライ回数に達しました")
                return []
    
    return []

def safe_extract_motor_performances(html_file: StringIO, max_retries: int = 3) -> list[Any]:
    """
    モーター成績データを安全に抽出する関数（エラーハンドリング付き・リトライ機能付き）
    
    Args:
        html_file: HTMLファイルオブジェクト
        max_retries: 最大リトライ回数
    
    Returns:
        list: モーター成績データのリスト（エラーが発生した場合は空のリスト）
    """
    for attempt in range(max_retries):
        try:
            html_file.seek(0)  # ファイルポインタを先頭に戻す
            performances = entry_scraping.extract_motor_performances(html_file)
            if performances:
                safe_print(f"✅ モーター成績データ取得成功: {len(performances)}件")
                return performances
            else:
                safe_print(f"⚠️  モーター成績データが空です（試行 {attempt + 1}/{max_retries}）")
                if attempt < max_retries - 1:
                    time.sleep(2)
                    continue
                else:
                    safe_print("❌ モーター成績データ取得失敗: 最大リトライ回数に達しました")
                    return []
        except Exception as e:
            safe_print(f"⚠️  モーター成績データ抽出エラー（試行 {attempt + 1}/{max_retries}）: {type(e).__name__}: {e}")
            if attempt < max_retries - 1:
                safe_print(f"🔄 2秒後にリトライします...")
                time.sleep(2)
                continue
            else:
                safe_print("❌ モーター成績データ抽出エラー: 最大リトライ回数に達しました")
                return []
    
    return []

def fetch_race_entry_data(
    race_date: date,
    stadium_code: StadiumTelCode,
    race_number: int
) -> dict[str, Any] | None:
    """
    レース前情報（出走表）を取得する関数
    
    Args:
        race_date (date): レース開催日
        stadium_code (StadiumTelCode): 競艇場コード
        race_number (int): レース番号
    
    Returns:
        dict: 取得した出走表データ
    """
    safe_print(f"出走表データ取得開始: {race_date} {stadium_code.name} 第{race_number}レース")
    
    # URLを生成
    url = location.create_race_entry_page_url(
        race_holding_date=race_date,
        stadium_tel_code=stadium_code,
        race_number=race_number
    )
    
    safe_print(f"URL: {url}")
    
    # レート制限
    time.sleep(5)
    
    try:
        # データ取得
        response = requests.get(url)
        response.raise_for_status()
        
        # スクレイピング実行
        html_file = StringIO(response.text)
        
        race_information = entry_scraping.extract_race_information(html_file)
        html_file.seek(0)
        race_entries = safe_extract_race_entries(html_file)
        html_file.seek(0)
        racers = safe_extract_racers(html_file)
        html_file.seek(0)
        racer_performances = safe_extract_racer_performances(html_file)
        html_file.seek(0)
        boat_performances = safe_extract_boat_performances(html_file)
        html_file.seek(0)
        motor_performances = safe_extract_motor_performances(html_file)
        
        # データの整合性チェック
        if not race_entries:
            safe_print("レース出走データが取得できませんでした")
            return None
        
        # 各データの長さを揃える（不足している場合は空のデータで補完）
        max_length = len(race_entries)
        
        if len(racers) < max_length:
            safe_print(f"選手データが不足しています（{len(racers)}/{max_length}）")
            racers.extend([None] * (max_length - len(racers)))
        
        if len(racer_performances) < max_length:
            safe_print(f"選手成績データが不足しています（{len(racer_performances)}/{max_length}）")
            racer_performances.extend([None] * (max_length - len(racer_performances)))
        
        if len(boat_performances) < max_length:
            safe_print(f"ボート成績データが不足しています（{len(boat_performances)}/{max_length}）")
            boat_performances.extend([None] * (max_length - len(boat_performances)))
        
        if len(motor_performances) < max_length:
            safe_print(f"モーター成績データが不足しています（{len(motor_performances)}/{max_length}）")
            motor_performances.extend([None] * (max_length - len(motor_performances)))
        
        # データを辞書形式に変換
        result = {
            "race_info": {
                "date": race_date.isoformat(),
                "stadium": stadium_code.name,
                "race_number": race_number,
                "url": url,
                "title": race_information.title,
                "deadline_at": race_information.deadline_at.isoformat() if race_information.deadline_at else None,
                "number_of_laps": race_information.number_of_laps,
                "is_course_fixed": race_information.is_course_fixed
            },
            "race_entries": []
        }
        
        # 各艇のデータを安全に処理
        for i, entry in enumerate(race_entries):
            racer = racers[i] if i < len(racers) else None
            racer_perf = racer_performances[i] if i < len(racer_performances) else None
            boat_perf = boat_performances[i] if i < len(boat_performances) else None
            motor_perf = motor_performances[i] if i < len(motor_performances) else None
            
            # 選手名の安全な取得（選手名が取得できない場合は"不明"として処理を継続）
            racer_name = "不明"
            if racer:
                try:
                    racer_name = f"{racer.last_name} {racer.first_name}"
                except (AttributeError, ValueError) as e:
                    safe_print(f"⚠️  艇番{entry.pit_number}の選手名解析エラー: {e}")
                    racer_name = "不明"
            
            entry_data = {
                "pit_number": entry.pit_number,
                "racer": {
                    "name": racer_name,
                    "registration_number": racer.registration_number if racer else None,
                    "current_rating": racer.current_rating.name if racer and racer.current_rating else None,
                    "branch": racer.branch if racer else None,
                    "born_prefecture": racer.born_prefecture if racer else None,
                    "birth_date": racer.birth_date.isoformat() if racer and racer.birth_date else None,
                    "height": racer.height if racer else None,
                    "gender": racer.gender.name if racer and racer.gender else None
                },
                "performance": {
                    "rate_in_all_stadium": racer_perf.rate_in_all_stadium if racer_perf else None,
                    "rate_in_event_going_stadium": racer_perf.rate_in_event_going_stadium if racer_perf else None
                },
                "boat": {
                    "number": boat_perf.number if boat_perf else None,
                    "quinella_rate": boat_perf.quinella_rate if boat_perf else None,
                    "trio_rate": boat_perf.trio_rate if boat_perf else None
                },
                "motor": {
                    "number": motor_perf.number if motor_perf else None,
                    "quinella_rate": motor_perf.quinella_rate if motor_perf else None,
                    "trio_rate": motor_perf.trio_rate if motor_perf else None
                }
            }
            result["race_entries"].append(entry_data)
        
        safe_print(f"出走表データ取得成功: {len(race_entries)}艇")
        return result
        
    except requests.exceptions.RequestException as e:
        safe_print(f"[HTTPエラー] {e}")
        if hasattr(e, 'response') and e.response is not None:
            safe_print(f"[HTTPステータス] {e.response.status_code}")
            safe_print(f"[レスポンス先頭500文字]\n{e.response.text[:500]}")
        return None
    except Exception as e:
        import traceback
        # レース中止の場合は特別処理
        if "RaceCanceled" in str(type(e)):
            safe_print(f"レース中止: {race_date} {stadium_code.name} 第{race_number}レース")
            return None
        safe_print(f"エラー: {type(e).__name__}: {e}")
        safe_print(f"詳細: {traceback.format_exc()}")
        return None

def fetch_race_result_data(
    race_date: date,
    stadium_code: StadiumTelCode,
    race_number: int
) -> dict[str, Any] | None:
    """
    レース結果を取得する関数
    
    Args:
        race_date (date): レース開催日
        stadium_code (StadiumTelCode): 競艇場コード
        race_number (int): レース番号
    
    Returns:
        dict: 取得したレース結果データ
    """
    safe_print(f"レース結果データ取得開始: {race_date} {stadium_code.name} 第{race_number}レース")
    
    # URLを生成
    url = result_location.create_race_result_page_url(
        race_holding_date=race_date,
        stadium_tel_code=stadium_code,
        race_number=race_number
    )
    
    safe_print(f"URL: {url}")
    
    # レート制限
    time.sleep(5)
    
    try:
        # データ取得
        response = requests.get(url)
        response.raise_for_status()
        
        # スクレイピング実行
        html_file = StringIO(response.text)
        
        race_records = result_scraping.extract_race_records(html_file)
        html_file.seek(0)
        weather_condition = result_scraping.extract_weather_condition(html_file)
        html_file.seek(0)
        payoffs = result_scraping.extract_race_payoffs(html_file)
        
        # データを辞書形式に変換
        result = {
            "race_records": [
                {
                    "pit_number": record.pit_number,
                    "start_course": record.start_course,
                    "start_time": record.start_time,
                    "total_time": record.total_time,
                    "arrival": record.arrival,
                    "winning_trick": record.winning_trick.name if record.winning_trick else None
                }
                for record in race_records
            ],
            "weather_condition": {
                "weather": weather_condition.weather.name,
                "wind_velocity": weather_condition.wind_velocity,
                "wind_angle": weather_condition.wind_angle,
                "air_temperature": weather_condition.air_temperature,
                "water_temperature": weather_condition.water_temperature,
                "wavelength": weather_condition.wavelength
            },
            "payoffs": [
                {
                    "betting_method": payoff.betting_method.name,
                    "betting_numbers": payoff.betting_numbers,
                    "amount": payoff.amount
                }
                for payoff in payoffs
            ]
        }
        
        safe_print(f"レース結果データ取得成功: {len(result['race_records'])}艇, 払戻{len(result['payoffs'])}件")
        return result
        
    except requests.exceptions.RequestException as e:
        safe_print(f"[HTTPエラー] {e}")
        if hasattr(e, 'response') and e.response is not None:
            safe_print(f"[HTTPステータス] {e.response.status_code}")
            safe_print(f"[レスポンス先頭500文字]\n{e.response.text[:500]}")
        return None
    except Exception as e:
        import traceback
        # レース中止の場合は特別処理
        if "RaceCanceled" in str(type(e)):
            safe_print(f"レース中止: {race_date} {stadium_code.name} 第{race_number}レース")
            return None
        safe_print(f"エラー: {type(e).__name__}: {e}")
        safe_print(f"詳細: {traceback.format_exc()}")
        return None


def _serialize_for_json(obj: Any) -> Any:
    """metaboatrace のモデルを JSON 用に変換（date, Enum, リスト等）"""
    if obj is None:
        return None
    if hasattr(obj, "isoformat"):  # date/datetime
        return obj.isoformat()
    if hasattr(obj, "name"):  # Enum
        return obj.name
    if isinstance(obj, (list, tuple)):
        return [_serialize_for_json(x) for x in obj]
    if isinstance(obj, dict):
        return {k: _serialize_for_json(v) for k, v in obj.items()}
    return obj


def fetch_before_information(
    race_date: date,
    stadium_code: StadiumTelCode,
    race_number: int,
) -> dict[str, Any] | None:
    """
    レース前の直前情報（展示走・スタート展示・選手体重・艇設定・天候）を取得する。
    展示走実施後にのみ公開されるため、取得できない場合は None を返す。

    Args:
        race_date: レース開催日
        stadium_code: 競艇場コード
        race_number: レース番号

    Returns:
        直前情報の辞書。キー: start_exhibition, circumference_exhibition,
        racer_conditions, boat_settings, weather_condition。一部のみ取得可能な場合あり。
    """
    safe_print(f"直前情報取得開始: {race_date} {stadium_code.name} 第{race_number}レース")
    url = before_info_location.create_race_before_information_page_url(
        race_holding_date=race_date,
        stadium_tel_code=stadium_code,
        race_number=race_number,
    )
    safe_print(f"URL: {url}")
    time.sleep(5)
    try:
        response = requests.get(url)
        response.raise_for_status()
        html_file = StringIO(response.text)
        result: dict[str, Any] = {
            "race_info": {
                "date": race_date.isoformat(),
                "stadium": stadium_code.name,
                "race_number": race_number,
                "url": url,
            },
            "start_exhibition": [],
            "circumference_exhibition": [],
            "racer_conditions": [],
            "boat_settings": [],
            "weather_condition": None,
        }
        # スタート展示（ST 等）
        try:
            html_file.seek(0)
            start_records = before_info_scraping.extract_start_exhibition_records(html_file)
            result["start_exhibition"] = [
                {k: _serialize_for_json(getattr(r, k)) for k in ("pit_number", "start_course", "start_time")}
                for r in start_records
            ]
        except Exception as e:
            safe_print(f"スタート展示取得スキップ: {e}")
        # 周回展示（展示タイム）
        try:
            html_file.seek(0)
            circum_records = before_info_scraping.extract_circumference_exhibition_records(html_file)
            result["circumference_exhibition"] = [
                {k: _serialize_for_json(getattr(r, k)) for k in ("pit_number", "exhibition_time")}
                for r in circum_records
            ]
        except Exception as e:
            safe_print(f"周回展示取得スキップ: {e}")
        # 選手コンディション（体重・調整）
        try:
            html_file.seek(0)
            conditions = before_info_scraping.extract_racer_conditions(html_file)
            result["racer_conditions"] = [
                {k: _serialize_for_json(getattr(c, k)) for k in ("racer_registration_number", "weight", "adjust")}
                for c in conditions
            ]
        except Exception as e:
            safe_print(f"選手コンディション取得スキップ: {e}")
        # 艇設定（チルト・新ペラ・部品交換）
        try:
            html_file.seek(0)
            boat_settings = before_info_scraping.extract_boat_settings(html_file)
            if not isinstance(boat_settings, list):
                boat_settings = [boat_settings] if boat_settings else []
            serialized = []
            for b in boat_settings:
                d = {
                    "pit_number": getattr(b, "pit_number", None),
                    "tilt": getattr(b, "tilt", None),
                    "is_new_propeller": getattr(b, "is_new_propeller", None),
                }
                if hasattr(b, "motor_parts_exchanges") and b.motor_parts_exchanges:
                    d["motor_parts_exchanges"] = _serialize_for_json(b.motor_parts_exchanges)
                serialized.append(d)
            result["boat_settings"] = serialized
        except Exception as e:
            safe_print(f"艇設定取得スキップ: {e}")
        # 天候（レース前時点）
        try:
            html_file.seek(0)
            w = before_info_scraping.extract_weather_condition(html_file)
            result["weather_condition"] = {
                "weather": getattr(w.weather, "name", str(w.weather)) if w else None,
                "wind_velocity": getattr(w, "wind_velocity", None) if w else None,
                "wind_angle": getattr(w, "wind_angle", None) if w else None,
                "air_temperature": getattr(w, "air_temperature", None) if w else None,
                "water_temperature": getattr(w, "water_temperature", None) if w else None,
                "wavelength": getattr(w, "wavelength", None) if w else None,
            }
        except Exception as e:
            safe_print(f"天候取得スキップ: {e}")
        if any(result["start_exhibition"]) or any(result["circumference_exhibition"]):
            safe_print(f"直前情報取得成功: スタート展示{len(result['start_exhibition'])}件, 周回展示{len(result['circumference_exhibition'])}件")
        else:
            safe_print("直前情報は未公開または取得できませんでした（展示走前は空になります）")
        return result
    except requests.exceptions.RequestException as e:
        safe_print(f"[HTTPエラー] {e}")
        return None
    except Exception as e:
        import traceback
        safe_print(f"直前情報エラー: {type(e).__name__}: {e}")
        safe_print(traceback.format_exc())
        return None


def fetch_pre_race_data(
    race_date: date,
    stadium_code: StadiumTelCode,
    race_number: int,
) -> dict[str, Any] | None:
    """
    レース前に取得できる情報を統合して返す。
    出走表は必須。直前情報は展示走実施後のみ取得可能で、取得できた場合にマージする。

    Args:
        race_date: レース開催日
        stadium_code: 競艇場コード
        race_number: レース番号

    Returns:
        出走表 + 直前情報（取得時のみ）をマージした辞書。
        出走表が取得できない場合は None。
    """
    safe_print(f"レース前データ取得: {race_date} {stadium_code.name} 第{race_number}レース")
    entry_data = fetch_race_entry_data(race_date, stadium_code, race_number)
    if not entry_data:
        return None
    before_info = fetch_before_information(race_date, stadium_code, race_number)
    if before_info:
        # 直前情報の項目のみマージ（race_info は出走表のものを維持）
        entry_data = dict(entry_data)
        entry_data["start_exhibition"] = before_info.get("start_exhibition", [])
        entry_data["circumference_exhibition"] = before_info.get("circumference_exhibition", [])
        entry_data["racer_conditions"] = before_info.get("racer_conditions", [])
        entry_data["boat_settings"] = before_info.get("boat_settings", [])
        if before_info.get("weather_condition") is not None:
            entry_data["weather_condition"] = before_info["weather_condition"]
        safe_print("レース前データ取得完了（出走表＋直前情報）")
    else:
        entry_data = dict(entry_data)
        entry_data.setdefault("start_exhibition", [])
        entry_data.setdefault("circumference_exhibition", [])
        entry_data.setdefault("racer_conditions", [])
        entry_data.setdefault("boat_settings", [])
        safe_print("レース前データ取得完了（出走表のみ。直前情報は未公開）")
    return entry_data


def fetch_complete_race_data(
    race_date: date,
    stadium_code: StadiumTelCode,
    race_number: int
) -> dict[str, Any]:
    """
    1レースの完全なデータ（出走表 + 結果）を取得する関数
    
    Args:
        race_date (date): レース開催日
        stadium_code (StadiumTelCode): 競艇場コード
        race_number (int): レース番号
    
    Returns:
        dict: 完全なレースデータ
    """
    safe_print(f"完全レースデータ取得: {race_date} {stadium_code.name} 第{race_number}レース")
    safe_print("=" * 60)
    
    # 出走表データ取得
    entry_data = fetch_race_entry_data(race_date, stadium_code, race_number)
    if not entry_data:
        # レース中止の場合は例外を再発生
        raise RaceCanceled(f"レース中止: {race_date} {stadium_code.name} 第{race_number}レース")
    
    # レース結果データ取得
    result_data = fetch_race_result_data(race_date, stadium_code, race_number)
    if not result_data:
        # レース中止の場合は例外を再発生
        raise RaceCanceled(f"レース中止: {race_date} {stadium_code.name} 第{race_number}レース")
    
    # データを統合
    complete_data = {
        **entry_data,
        **result_data
    }
    
    return complete_data

def main() -> None:
    """メイン実行関数"""
    safe_print("競艇完全データ取得テスト")
    safe_print("=" * 50)
    
    # テスト条件
    test_date = date(2024, 6, 15)
    stadium = StadiumTelCode.KIRYU
    race_num = 1
    
    # 完全データ取得
    complete_data = fetch_complete_race_data(test_date, stadium, race_num)
    
    if complete_data:
        # 結果表示
        safe_print(f"\n取得結果サマリー:")
        safe_print(f"  日付: {complete_data['race_info']['date']}")
        safe_print(f"  競艇場: {complete_data['race_info']['stadium']}")
        safe_print(f"  レース: {complete_data['race_info']['title']}")
        safe_print(f"  締切時刻: {complete_data['race_info']['deadline_at']}")
        
        safe_print(f"\n出走表:")
        for entry in complete_data['race_entries']:
            safe_print(f"  {entry['pit_number']}号艇: {entry['racer']['name']} ({entry['racer']['current_rating']})")
            safe_print(f"    全国勝率: {entry['performance']['rate_in_all_stadium']}")
        
        safe_print(f"\nレース結果:")
        sorted_records = sorted(complete_data['race_records'], key=lambda x: x['arrival'])
        for record in sorted_records:
            safe_print(f"  {record['arrival']}着: {record['pit_number']}号艇 (ST:{record['start_time']})")
        
        safe_print(f"\n天候:")
        weather = complete_data['weather_condition']
        safe_print(f"  {weather['weather']}, 風速{weather['wind_velocity']}m/s, 気温{weather['air_temperature']}℃")
        
        safe_print(f"\n払戻:")
        for payoff in complete_data['payoffs']:
            method_name = {
                'TRIFECTA': '3連単',
                'TRIO': '3連複',
                'EXACTA': '2連単',
                'QUINELLA': '2連複'
            }.get(payoff['betting_method'], payoff['betting_method'])
            numbers = '-'.join(map(str, payoff['betting_numbers']))
            safe_print(f"  {method_name} {numbers}: {payoff['amount']:,}円")
        
        # JSONファイルに保存
        output_file = os.path.join("kyotei_predictor", "data", "raw", f"complete_race_data_{test_date.strftime('%Y%m%d')}_{stadium.name}_R{race_num}.json")
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(complete_data, f, ensure_ascii=False, indent=2)
        
        safe_print(f"\n完全データを保存しました: {output_file}")
        safe_print("\n出走表 + レース結果の完全データ取得に成功しました！")
    
    else:
        safe_print("\nデータ取得に失敗しました。")

if __name__ == "__main__":
    # テスト: 2024-01-04 KIRYU 第9レースのみ取得
    from datetime import date
    from metaboatrace.models.stadium import StadiumTelCode
    test_date = date(2024, 1, 4)
    stadium = StadiumTelCode.KIRYU
    race_num = 9
    safe_print("[テスト実行] 2024-01-04 KIRYU 第9レース 完全データ取得")
    complete_data = fetch_complete_race_data(test_date, stadium, race_num)
    if complete_data:
        safe_print("[テスト結果] データ取得成功")
    else:
        safe_print("[テスト結果] データ取得失敗")