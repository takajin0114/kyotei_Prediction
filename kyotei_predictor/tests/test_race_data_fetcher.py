import pytest
from datetime import date
from io import StringIO
from kyotei_predictor.tools.fetch import race_data_fetcher as rdf
from metaboatrace.models.stadium import StadiumTelCode

# --- safe_extract_racers系のテスト雛形 ---
def test_safe_extract_racers_empty():
    html = StringIO("")
    result = rdf.safe_extract_racers(html)
    assert isinstance(result, list)

def test_safe_extract_race_entries_empty():
    html = StringIO("")
    result = rdf.safe_extract_race_entries(html)
    assert isinstance(result, list)

# --- fetch_race_entry_data, fetch_race_result_data, fetch_complete_race_dataのモックテスト雛形 ---
def test_fetch_race_entry_data_mock(mocker):
    mocker.patch("kyotei_predictor.tools.fetch.race_data_fetcher.requests.get", return_value=mocker.Mock(status_code=200, text="<html></html>", raise_for_status=lambda: None))
    mocker.patch.object(rdf, "safe_extract_race_entries", return_value=[mocker.Mock(pit_number=1)])
    mocker.patch.object(rdf, "safe_extract_racers", return_value=[mocker.Mock(last_name="A", first_name="B", registration_number=1, current_rating=mocker.Mock(name="A"), branch="X", born_prefecture="Y", birth_date=None, height=170, gender=mocker.Mock(name="M"))])
    mocker.patch.object(rdf, "safe_extract_racer_performances", return_value=[mocker.Mock(rate_in_all_stadium=6.0, rate_in_event_going_stadium=5.0)])
    mocker.patch.object(rdf, "safe_extract_boat_performances", return_value=[mocker.Mock(number=1, quinella_rate=30.0, trio_rate=50.0)])
    mocker.patch.object(rdf, "safe_extract_motor_performances", return_value=[mocker.Mock(number=1, quinella_rate=20.0, trio_rate=40.0)])
    mocker.patch("kyotei_predictor.tools.fetch.race_data_fetcher.entry_scraping.extract_race_information", return_value=mocker.Mock(title="title", deadline_at=None, number_of_laps=3, is_course_fixed=False))
    d = date(2024, 7, 15)
    stadium = StadiumTelCode.KIRYU
    race_no = 1
    result = rdf.fetch_race_entry_data(d, stadium, race_no)
    assert isinstance(result, dict)

def test_fetch_race_result_data_mock(mocker):
    mocker.patch("kyotei_predictor.tools.fetch.race_data_fetcher.requests.get", return_value=mocker.Mock(status_code=200, text="<html></html>", raise_for_status=lambda: None))
    mocker.patch("kyotei_predictor.tools.fetch.race_data_fetcher.result_scraping.extract_race_records", return_value=[mocker.Mock(pit_number=1, start_course=1, start_time="0.15", total_time="1:50.0", arrival=1, winning_trick=mocker.Mock(name="TRICK"))])
    mocker.patch("kyotei_predictor.tools.fetch.race_data_fetcher.result_scraping.extract_weather_condition", return_value=mocker.Mock(weather=mocker.Mock(name="晴"), wind_velocity=3, wind_angle=90, air_temperature=25, water_temperature=22, wavelength=5))
    mocker.patch("kyotei_predictor.tools.fetch.race_data_fetcher.result_scraping.extract_race_payoffs", return_value=[mocker.Mock(betting_method=mocker.Mock(name="TRIFECTA"), betting_numbers=[1,2,3], amount=1000)])
    d = date(2024, 7, 15)
    stadium = StadiumTelCode.KIRYU
    race_no = 1
    result = rdf.fetch_race_result_data(d, stadium, race_no)
    assert isinstance(result, dict)

def test_fetch_complete_race_data_mock(mocker):
    mocker.patch.object(rdf, "fetch_race_entry_data", return_value={"race_info": {"date": "2024-07-15", "stadium": "KIRYU", "race_number": 1, "url": "", "title": "title", "deadline_at": None, "number_of_laps": 3, "is_course_fixed": False}, "race_entries": []})
    mocker.patch.object(rdf, "fetch_race_result_data", return_value={"race_records": [], "weather_condition": {}, "payoffs": []})
    d = date(2024, 7, 15)
    stadium = StadiumTelCode.KIRYU
    race_no = 1
    result = rdf.fetch_complete_race_data(d, stadium, race_no)
    assert isinstance(result, dict) 