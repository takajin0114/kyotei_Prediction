import pytest
from datetime import date
from kyotei_predictor.tools.fetch import odds_fetcher as of
from metaboatrace.models.stadium import StadiumTelCode

# --- fetch_trifecta_oddsのモックテスト雛形 ---
def test_fetch_trifecta_odds_mock(mocker):
    mocker.patch("kyotei_predictor.tools.fetch.odds_fetcher.requests.get", return_value=mocker.Mock(status_code=200, text="<html></html>", raise_for_status=lambda: None))
    mocker.patch("kyotei_predictor.tools.fetch.odds_fetcher.scraping.extract_odds", return_value=[mocker.Mock(betting_numbers=[1,2,3], ratio=10.5, betting_method="TRIFECTA")])
    d = date(2024, 7, 15)
    stadium = StadiumTelCode.KIRYU
    race_no = 1
    result = of.fetch_trifecta_odds(d, stadium, race_no)
    assert isinstance(result, dict)
    assert result['odds_count'] == 1

# --- fetch_odds_for_raceのモックテスト雛形 ---
def test_fetch_odds_for_race_mock(mocker):
    mocker.patch.object(of, "fetch_trifecta_odds", return_value={
        'race_date': '2024-07-15',
        'stadium': 'KIRYU',
        'race_number': 1,
        'odds_count': 1,
        'odds_data': [{'betting_numbers': [1,2,3], 'ratio': 10.5, 'betting_method': 'TRIFECTA', 'combination': '1-2-3'}],
        'url': 'http://example.com'
    })
    result = of.fetch_odds_for_race('2024-07-15', 'KIRYU', 1)
    assert isinstance(result, dict)
    assert result['odds_count'] == 1

# --- analyze_odds_dataのテスト雛形 ---
def test_analyze_odds_data(capsys):
    odds_data = {
        'odds_count': 2,
        'odds_data': [
            {'betting_numbers': [1,2,3], 'ratio': 10.5, 'betting_method': 'TRIFECTA', 'combination': '1-2-3'},
            {'betting_numbers': [2,1,3], 'ratio': 5.0, 'betting_method': 'TRIFECTA', 'combination': '2-1-3'}
        ]
    }
    of.analyze_odds_data(odds_data)
    captured = capsys.readouterr()
    assert "オッズデータ分析" in captured.out
    assert "人気順" in captured.out 