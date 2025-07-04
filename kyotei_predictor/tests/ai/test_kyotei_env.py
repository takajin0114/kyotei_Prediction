import unittest
from kyotei_predictor.pipelines.kyotei_env import KyoteiEnv, vectorize_race_state, action_to_trifecta, trifecta_to_action, calc_trifecta_reward, KyoteiEnvManager
import os

class TestKyoteiEnv(unittest.TestCase):
    def test_reset_and_step(self):
        env = KyoteiEnv()
        obs, info = env.reset()
        self.assertEqual(obs.shape, (6,))
        self.assertIsInstance(info, dict)
        for _ in range(5):
            action = env.action_space.sample()
            obs, reward, terminated, truncated, info = env.step(action)
            self.assertEqual(obs.shape, (6,))
            self.assertIsInstance(reward, float)
            self.assertIsInstance(terminated, bool)
            self.assertIsInstance(truncated, bool)
            self.assertIsInstance(info, dict)
        env.close()

    def test_vectorize_race_state(self):
        # サンプルデータパス
        race_path = os.path.join(os.path.dirname(__file__), '../data/race_data_2024-06-16_KIRYU_R1.json')
        odds_path = os.path.join(os.path.dirname(__file__), '../data/odds_data_2024-06-15_KIRYU_R1.json')
        vec = vectorize_race_state(race_path, odds_path)
        # shape: (6*9 + 3+1+1 + 120) = 54+5+120=179
        self.assertEqual(vec.shape, (179,))
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
        # 的中パターン
        action = trifecta_to_action((1,2,3))
        reward = calc_trifecta_reward(action, (1,2,3), odds_data, bet_amount=100)
        self.assertEqual(reward, 2000-100)
        # 不的中パターン
        action = trifecta_to_action((2,1,3))
        reward = calc_trifecta_reward(action, (1,2,3), odds_data, bet_amount=100)
        self.assertEqual(reward, -100)

    def test_env_step_reward(self):
        # サンプルデータパス
        race_path = os.path.join(os.path.dirname(__file__), '../data/race_data_2024-06-16_KIRYU_R1.json')
        odds_path = os.path.join(os.path.dirname(__file__), '../data/odds_data_2024-06-15_KIRYU_R1.json')
        env = KyoteiEnv(race_data_path=race_path, odds_data_path=odds_path, bet_amount=100)
        state, info = env.reset()
        # 正解action（的中）
        correct_action = trifecta_to_action(env.arrival_tuple)
        _, reward, terminated, truncated, info = env.step(correct_action)
        self.assertTrue(reward >= 0)
        self.assertTrue(terminated)
        # 不的中action
        wrong_action = trifecta_to_action((6,5,4)) if env.arrival_tuple != (6,5,4) else trifecta_to_action((1,2,3))
        env.reset()
        _, reward, terminated, truncated, info = env.step(wrong_action)
        self.assertEqual(reward, -100)
        self.assertTrue(terminated)

    def test_env_manager_multi_race(self):
        manager = KyoteiEnvManager(data_dir=os.path.join(os.path.dirname(__file__), '../data'), bet_amount=100)
        seen_arrivals = set()
        for _ in range(3):
            state, info = manager.reset()
            self.assertEqual(state.shape, (179,))
            self.assertTrue((state >= 0).all() and (state <= 1).all())
            self.assertEqual(manager.action_space.n, 120)
            self.assertEqual(manager.observation_space.shape, (179,))
            # stepでrewardが返る
            action = manager.action_space.sample()
            _, reward, terminated, truncated, info = manager.step(action)
            self.assertTrue(isinstance(reward, float))
            self.assertTrue(terminated)
            seen_arrivals.add(info['arrival'])
        # 複数レースでarrival（着順）が異なることを期待
        self.assertTrue(len(seen_arrivals) >= 1)

if __name__ == "__main__":
    unittest.main() 