import unittest
from kyotei_predictor.pipelines.kyotei_env import KyoteiEnv, vectorize_race_state, action_to_trifecta, trifecta_to_action, calc_trifecta_reward, KyoteiEnvManager
from kyotei_predictor.pipelines.state_vector import get_state_dim
import os
import pytest
import gymnasium as gym



class TestKyoteiEnv(unittest.TestCase):
    def test_reset_and_step(self):
        """KyoteiEnv は race_data_path/odds_data_path 必須のため、パスなしでは reset しない"""
        env = KyoteiEnv()
        self.assertIsNone(env.race_data_path)
        self.assertIsNone(env.odds_data_path)
        with self.assertRaises(AssertionError):
            env.reset()
        env.close()

    def test_vectorize_race_state(self):
        # test_raw のサンプルデータで状態ベクトル生成（オッズは状態に含めない）
        base = os.path.join(os.path.dirname(__file__), "..", "data", "test_raw")
        race_path = os.path.join(base, "race_data_2024-05-01_TODA_R1.json")
        odds_path = os.path.join(base, "odds_data_2024-05-01_TODA_R1.json")
        if not os.path.exists(race_path) or not os.path.exists(odds_path):
            self.skipTest("test_raw data not found")
        vec = vectorize_race_state(race_path, odds_path)
        self.assertEqual(vec.shape, (get_state_dim(),))
        self.assertTrue((vec >= 0).all() and (vec <= 1).all())

    def test_action_trifecta_conversion(self):
        # 全actionで可逆性を検証
        for action in range(120):
            trifecta = action_to_trifecta(action)
            action2 = trifecta_to_action(trifecta)
            self.assertEqual(action, action2)
        # 逆方向も一部検証
        self.assertEqual(action_to_trifecta(trifecta_to_action((1,2,3))), (1,2,3))
        self.assertEqual(action_to_trifecta(trifecta_to_action((6,5,4))), (6,5,4))

    def test_calc_trifecta_reward(self):
        # サンプルoddsデータ
        odds_data = [
            {'betting_numbers': [1,2,3], 'ratio': 20.0},
            {'betting_numbers': [2,1,3], 'ratio': 50.0},
        ]
        # 的中パターン: reward = (payout - bet) * win_multiplier（設定で変動するため正であることのみ検証）
        action = trifecta_to_action((1,2,3))
        reward = calc_trifecta_reward(action, (1,2,3), odds_data, bet_amount=100)
        self.assertGreater(reward, 0)
        # 不的中パターン（ペナルティは負）
        action = trifecta_to_action((2,1,3))
        reward_miss = calc_trifecta_reward(action, (1,2,3), odds_data, bet_amount=100)
        self.assertLess(reward_miss, 0)

def test_env_step_reward(race_date, venue, race_no, data_dir):
    race_path = os.path.join(data_dir, f'race_data_{race_date}_{venue}_R{race_no}.json')
    odds_path = os.path.join(data_dir, f'odds_data_{race_date}_{venue}_R{race_no}.json')
    env = KyoteiEnv(race_data_path=race_path, odds_data_path=odds_path, bet_amount=100)
    state, info = env.reset()
    # 正解action（的中）
    correct_action = trifecta_to_action(env.arrival_tuple)
    _, reward, terminated, truncated, info = env.step(correct_action)
    assert reward >= 0
    assert terminated
    # 不的中action
    wrong_action = trifecta_to_action((6,5,4)) if env.arrival_tuple != (6,5,4) else trifecta_to_action((1,2,3))
    env.reset()
    _, reward, terminated, truncated, info = env.step(wrong_action)
    assert reward == -100
    assert terminated

def test_env_manager_multi_race(data_dir):
    from kyotei_predictor.pipelines.state_vector import get_state_dim
    state_dim = get_state_dim()
    manager = KyoteiEnvManager(data_dir=data_dir, bet_amount=100)
    seen_arrivals = set()
    for _ in range(3):
        state, info = manager.reset()
        assert state is not None
        assert state.shape == (state_dim,), f"expected {state_dim}, got {state.shape}"
        assert (state >= 0).all() and (state <= 1).all()
        # action_space.nはDiscrete型のみ
        if isinstance(manager.action_space, gym.spaces.Discrete):
            assert manager.action_space.n == 120
        assert manager.observation_space.shape == (state_dim,)
        # stepでrewardが返る
        action = manager.action_space.sample()
        _, reward, terminated, truncated, info = manager.step(action)
        assert isinstance(reward, float)
        assert terminated
        seen_arrivals.add(info['arrival'])
    # 複数レースでarrival（着順）が異なることを期待
    assert len(seen_arrivals) >= 1

if __name__ == "__main__":
    unittest.main() 