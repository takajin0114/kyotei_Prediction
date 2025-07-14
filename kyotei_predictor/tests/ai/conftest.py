import pytest

def pytest_addoption(parser):
    parser.addoption('--race-date', action='store', default='2025-07-07', help='テスト用レース日付 (YYYY-MM-DD)')
    parser.addoption('--venue', action='store', default='KIRYU', help='テスト用会場名')
    parser.addoption('--race-no', action='store', default='1', help='テスト用レース番号')
    parser.addoption('--data-dir', action='store', default='kyotei_predictor/data/raw', help='データディレクトリ')

@pytest.fixture
def race_date(request):
    return request.config.getoption('--race-date')

@pytest.fixture
def venue(request):
    return request.config.getoption('--venue')

@pytest.fixture
def race_no(request):
    return request.config.getoption('--race-no')

@pytest.fixture
def data_dir(request):
    return request.config.getoption('--data-dir') 