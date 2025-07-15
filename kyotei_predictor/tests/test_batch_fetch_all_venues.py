import pytest
from datetime import date
from kyotei_predictor.tools.batch import batch_fetch_all_venues as bfa
from metaboatrace.models.stadium import StadiumTelCode

# --- テスト雛形 ---
def test_make_race_file_paths():
    d = date(2024, 7, 15)
    stadium = StadiumTelCode.KIRYU
    race_no = 1
    paths = bfa.make_race_file_paths(d, stadium, race_no)
    assert 'race' in paths and 'odds' in paths and 'canceled' in paths
    assert paths['race'].endswith('race_data_2024-07-15_KIRYU_R1.json')
    assert paths['odds'].endswith('odds_data_2024-07-15_KIRYU_R1.json')
    assert paths['canceled'].endswith('race_canceled_2024-07-15_KIRYU_R1.json')

def test_log_info(capsys):
    bfa.log_info("test message")
    captured = capsys.readouterr()
    assert "test message" in captured.out

# fetch_race_data_parallel, fetch_day_races_parallelは外部APIやファイルI/Oが多いため、
# pytest-mockやtmp_pathを使ったモック・一時ディレクトリテストを推奨

def test_fetch_race_data_parallel_mock(mocker, tmp_path):
    # fetch_complete_race_data, fetch_trifecta_oddsをモック
    mocker.patch.object(bfa, 'fetch_complete_race_data', return_value={'dummy': 1})
    mocker.patch.object(bfa, 'fetch_trifecta_odds', return_value={'dummy': 2})
    d = date(2024, 7, 15)
    stadium = StadiumTelCode.KIRYU
    race_no = 1
    # データ保存先をtmp_pathに差し替え
    mocker.patch('os.path.join', side_effect=lambda *args: str(tmp_path / '_'.join(args[-3:])))
    result = bfa.fetch_race_data_parallel(d, stadium, race_no, rate_limit_seconds=0, max_retries=1)
    assert result['race_success'] is True
    assert result['odds_success'] is True

# fetch_day_races_parallelも同様にモック前提のテスト雛形

def test_fetch_day_races_parallel_mock(mocker, tmp_path):
    mocker.patch.object(bfa, 'fetch_race_data_parallel', return_value={'race_success': True, 'odds_success': True, 'canceled': False, 'race_no': 1})
    d = date(2024, 7, 15)
    stadium = StadiumTelCode.KIRYU
    race_numbers = range(1, 3)
    results = bfa.fetch_day_races_parallel(d, stadium, race_numbers, rate_limit_seconds=0, max_retries=1, max_workers=2)
    assert isinstance(results, list)
    assert all(r['race_success'] for r in results) 