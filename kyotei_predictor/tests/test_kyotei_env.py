import pytest
import numpy as np
from kyotei_predictor.pipelines.kyotei_env import KyoteiEnv, vectorize_race_state, calc_trifecta_reward

# --- vectorize_race_stateのモックテスト雛形 ---
def test_vectorize_race_state_mock(mocker):
    mocker.patch("builtins.open", mocker.mock_open(read_data='{"race_info": {"stadium": "KIRYU", "race_number": 1, "number_of_laps": 3, "is_course_fixed": true}, "race_entries": [{"pit_number": 1, "racer": {"current_rating": "A1"}, "performance": {"rate_in_all_stadium": 6.0, "rate_in_event_going_stadium": 5.0}, "boat": {"quinella_rate": 30.0, "trio_rate": 40.0}, "motor": {"quinella_rate": 20.0, "trio_rate": 30.0}}], "race_records": [{"arrival": 1, "pit_number": 1}]}'))
    mocker.patch("json.load", side_effect=[{
        "race_info": {"stadium": "KIRYU", "race_number": 1, "number_of_laps": 3, "is_course_fixed": True},
        "race_entries": [{"pit_number": 1, "racer": {"current_rating": "A1"}, "performance": {"rate_in_all_stadium": 6.0, "rate_in_event_going_stadium": 5.0}, "boat": {"quinella_rate": 30.0, "trio_rate": 40.0}, "motor": {"quinella_rate": 20.0, "trio_rate": 30.0}}],
        "race_records": [{"arrival": 1, "pit_number": 1}]
    }, {"odds_data": [{"betting_numbers": [1,2,3], "ratio": 10.0}]}])
    vec = vectorize_race_state("dummy_race.json", "dummy_odds.json")
    assert isinstance(vec, np.ndarray)

# --- calc_trifecta_rewardのテスト雛形 ---
def test_calc_trifecta_reward_hit():
    action = 0
    arrival_tuple = (1,2,3)
    odds_data = [{"betting_numbers": [1,2,3], "ratio": 10.0}]
    reward = calc_trifecta_reward(action, arrival_tuple, odds_data, bet_amount=100)
    assert reward == 900.0

def test_calc_trifecta_reward_miss():
    action = 1
    arrival_tuple = (1,2,3)
    odds_data = [{"betting_numbers": [1,2,3], "ratio": 10.0}]
    reward = calc_trifecta_reward(action, arrival_tuple, odds_data, bet_amount=100)
    assert reward < 0

# --- KyoteiEnvのreset/stepのモックテスト雛形 ---
def test_kyotei_env_reset_step_mock(mocker):
    dummy_race_info = {"stadium": "KIRYU", "race_number": 1, "number_of_laps": 3, "is_course_fixed": True}
    dummy_odds = {"odds_data": []}
    mocker.patch("builtins.open", mocker.mock_open(read_data='{"race_records": [{"arrival": 1, "pit_number": 1}, {"arrival": 2, "pit_number": 2}, {"arrival": 3, "pit_number": 3}], "race_info": {"stadium": "KIRYU", "race_number": 1, "number_of_laps": 3, "is_course_fixed": true}, "race_entries": [{"pit_number": 1, "racer": {"current_rating": "A1"}, "performance": {"rate_in_all_stadium": 6.0, "rate_in_event_going_stadium": 5.0}, "boat": {"quinella_rate": 30.0, "trio_rate": 40.0}, "motor": {"quinella_rate": 20.0, "trio_rate": 30.0}}]}'))
    mocker.patch("json.load", side_effect=[{
        "race_records": [{"arrival": 1, "pit_number": 1}, {"arrival": 2, "pit_number": 2}, {"arrival": 3, "pit_number": 3}],
        "race_info": dummy_race_info,
        "race_entries": [{"pit_number": 1, "racer": {"current_rating": "A1"}, "performance": {"rate_in_all_stadium": 6.0, "rate_in_event_going_stadium": 5.0}, "boat": {"quinella_rate": 30.0, "trio_rate": 40.0}, "motor": {"quinella_rate": 20.0, "trio_rate": 30.0}}],
        "odds_data": []
    }, {"odds_data": [{"betting_numbers": [1,2,3], "ratio": 10.0}]},
      {"race_records": [], "race_entries": [], "race_info": dummy_race_info, "odds_data": []},
      {"race_records": [], "race_entries": [], "race_info": dummy_race_info, "odds_data": []},
      {"race_records": [], "race_entries": [], "race_info": dummy_race_info, "odds_data": []},
      {"race_records": [], "race_entries": [], "race_info": dummy_race_info, "odds_data": []}])
    env = KyoteiEnv(race_data_path="dummy_race.json", odds_data_path="dummy_odds.json")
    state, info = env.reset()
    assert state is not None
    next_state, reward, terminated, truncated, info = env.step(0)
    assert terminated is True
    assert isinstance(reward, float) 