import unittest
from pipelines.kyotei_env import KyoteiEnv, vectorize_race_state, action_to_trifecta, trifecta_to_action
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

if __name__ == "__main__":
    unittest.main() 