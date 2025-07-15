import pytest
from kyotei_predictor.utils.common import KyoteiUtils

# --- load_json_file, save_json_fileのモックテスト雛形 ---
def test_load_json_file_mock(mocker):
    mocker.patch("builtins.open", mocker.mock_open(read_data='{"a": 1}'))
    mocker.patch("json.load", return_value={"a": 1})
    result = KyoteiUtils.load_json_file("dummy.json")
    assert result == {"a": 1}

def test_save_json_file_mock(mocker):
    mocker.patch("os.makedirs", return_value=None)
    m = mocker.mock_open()
    mocker.patch("builtins.open", m)
    result = KyoteiUtils.save_json_file({"a": 1}, "dummy.json")
    assert result is True

# --- normalize_probabilities, softmaxのテスト ---
def test_normalize_probabilities():
    probs = [2, 3, 5]
    norm = KyoteiUtils.normalize_probabilities(probs)
    assert abs(sum(norm) - 1.0) < 1e-8

def test_softmax():
    x = [1.0, 2.0, 3.0]
    sm = KyoteiUtils.softmax(x)
    assert abs(sum(sm) - 1.0) < 1e-8
    assert all(0 <= v <= 1 for v in sm)

# --- validate_race_dataのテスト ---
def test_validate_race_data_valid():
    race_data = {
        'race_id': 'R1',
        'boats': [
            {'boat_number': 1, 'arrival': 1},
            {'boat_number': 2, 'arrival': 2},
            {'boat_number': 3, 'arrival': 3},
            {'boat_number': 4, 'arrival': 4},
            {'boat_number': 5, 'arrival': 5},
            {'boat_number': 6, 'arrival': 6}
        ]
    }
    assert KyoteiUtils.validate_race_data(race_data) is True

def test_validate_race_data_invalid():
    race_data = {'race_id': 'R1', 'boats': [{'boat_number': 1}]}
    assert KyoteiUtils.validate_race_data(race_data) is False 