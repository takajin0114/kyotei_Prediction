"""
共通状態ベクトル（state_vector）のテスト。
オッズを状態に含めない設計で、学習・予測で同一の次元・並びになることを確認する。
"""
import json
import os
import unittest
import numpy as np

from kyotei_predictor.pipelines.state_vector import (
    build_race_state_vector,
    get_state_dim,
    get_stadium_names_order,
    EXTENDED_V2_EXTRA_DIM,
)


class TestStateVector(unittest.TestCase):
    """build_race_state_vector の単体テスト"""

    def test_state_dim_constant(self):
        """get_state_dim() が 48 + 会場数 + 3 または +4（モーター勝率代理あり）であること"""
        stadiums = get_stadium_names_order()
        dim = get_state_dim()
        self.assertIn(dim, [48 + len(stadiums) + 3, 48 + len(stadiums) + 4], msg="state dim should be 48+stadiums+3 or +4")

    def test_build_race_state_vector_shape(self):
        """race_data のみで状態を生成すると get_state_dim() 次元になること"""
        race = {
            "race_info": {
                "date": "2024-05-01",
                "stadium": "TODA",
                "race_number": 1,
                "number_of_laps": 3,
                "is_course_fixed": False,
            },
            "race_entries": [
                {
                    "pit_number": i,
                    "racer": {"current_rating": "B1"},
                    "performance": {"rate_in_all_stadium": 5.0, "rate_in_event_going_stadium": 5.0},
                    "boat": {"quinella_rate": 50.0, "trio_rate": 50.0},
                    "motor": {"quinella_rate": 50.0, "trio_rate": 50.0},
                }
                for i in range(1, 7)
            ],
        }
        state = build_race_state_vector(race, None)
        self.assertEqual(state.shape, (get_state_dim(),))
        self.assertEqual(state.dtype, np.float32)
        self.assertTrue(np.all((state >= 0) | (np.isclose(state, 0))))
        self.assertTrue(np.all((state <= 1) | (np.isclose(state, 1))))

    def test_build_race_state_vector_ignores_odds(self):
        """odds_data を渡しても状態の次元・値が変わらないこと（オッズは状態に含めない）"""
        race = {
            "race_info": {"stadium": "KIRYU", "race_number": 1, "number_of_laps": 3, "is_course_fixed": False},
            "race_entries": [
                {
                    "pit_number": i,
                    "racer": {"current_rating": "A1"},
                    "performance": {"rate_in_all_stadium": 6.0, "rate_in_event_going_stadium": 6.0},
                    "boat": {"quinella_rate": 60.0, "trio_rate": 70.0},
                    "motor": {"quinella_rate": 55.0, "trio_rate": 65.0},
                }
                for i in range(1, 7)
            ],
        }
        odds = {"odds_data": [{"betting_numbers": [1, 2, 3], "ratio": 10.0}]}
        state_no_odds = build_race_state_vector(race, None)
        state_with_odds = build_race_state_vector(race, odds)
        self.assertEqual(state_no_odds.shape, state_with_odds.shape)
        np.testing.assert_array_almost_equal(state_no_odds, state_with_odds)

    def test_same_race_same_vector(self):
        """同じ race_data からは常に同じベクトルが得られること"""
        race = {
            "race_info": {"stadium": "GAMAGORI", "race_number": 5, "number_of_laps": 3, "is_course_fixed": True},
            "race_entries": [
                {
                    "pit_number": i,
                    "racer": {"current_rating": "A2"},
                    "performance": {"rate_in_all_stadium": 4.5, "rate_in_event_going_stadium": 4.0},
                    "boat": {"quinella_rate": 45.0, "trio_rate": 55.0},
                    "motor": {"quinella_rate": 40.0, "trio_rate": 50.0},
                }
                for i in range(1, 7)
            ],
        }
        a = build_race_state_vector(race, None)
        b = build_race_state_vector(race, None)
        np.testing.assert_array_almost_equal(a, b)

    def test_from_real_json(self):
        """test_raw の実データで状態が生成できること"""
        data_dir = os.path.join(os.path.dirname(__file__), "..", "data", "test_raw")
        race_file = os.path.join(data_dir, "race_data_2024-05-01_TODA_R1.json")
        if not os.path.exists(race_file):
            self.skipTest(f"test data not found: {race_file}")
        with open(race_file, encoding="utf-8") as f:
            race = json.load(f)
        state = build_race_state_vector(race, None)
        self.assertEqual(state.shape, (get_state_dim(),))
        self.assertFalse(np.any(np.isnan(state)))

    def test_build_from_race_records_fallback(self):
        """race_entries が無く race_records のみの場合にエントリが構築されること"""
        race = {
            "race_info": {"stadium": "KIRYU", "race_number": 1, "is_course_fixed": False},
            "race_records": [{"pit_number": i} for i in range(1, 7)],
        }
        state = build_race_state_vector(race, None)
        self.assertEqual(state.shape, (get_state_dim(),))
        self.assertFalse(np.any(np.isnan(state)))

    def test_build_with_number_of_laps_none(self):
        """number_of_laps が無い場合 laps=0 で計算されること"""
        race = {
            "race_info": {"stadium": "EDOGAWA", "race_number": 2, "is_course_fixed": False},
            "race_entries": [
                {
                    "pit_number": i,
                    "racer": {"current_rating": "B1"},
                    "performance": {},
                    "boat": {},
                    "motor": {},
                }
                for i in range(1, 7)
            ],
        }
        state = build_race_state_vector(race, None)
        self.assertEqual(state.shape, (get_state_dim(),))

    def test_extended_features_v2_dim_and_build(self):
        """feature_set=extended_features_v2 のとき次元が base+EXTENDED_V2_EXTRA_DIM になり落ちずにビルドできること"""
        prev = os.environ.get("KYOTEI_FEATURE_SET"), os.environ.get("KYOTEI_USE_MOTOR_WIN_PROXY")
        try:
            os.environ["KYOTEI_FEATURE_SET"] = "extended_features_v2"
            if "KYOTEI_USE_MOTOR_WIN_PROXY" in os.environ:
                del os.environ["KYOTEI_USE_MOTOR_WIN_PROXY"]
            stadiums = get_stadium_names_order()
            base_extended = 48 + len(stadiums) + 4
            expected_dim = base_extended + EXTENDED_V2_EXTRA_DIM
            self.assertEqual(get_state_dim(), expected_dim)
            race = {
                "race_info": {"stadium": "TODA", "race_number": 1, "number_of_laps": 3, "is_course_fixed": False},
                "race_entries": [
                    {
                        "pit_number": i,
                        "racer": {"current_rating": "B1"},
                        "performance": {"rate_in_all_stadium": 5.0, "rate_in_event_going_stadium": 5.0},
                        "boat": {"quinella_rate": 50.0, "trio_rate": 50.0},
                        "motor": {"quinella_rate": 50.0, "trio_rate": 50.0},
                    }
                    for i in range(1, 7)
                ],
            }
            state = build_race_state_vector(race, None)
            self.assertEqual(state.shape, (expected_dim,))
            self.assertFalse(np.any(np.isnan(state)))
        finally:
            if prev[0] is not None:
                os.environ["KYOTEI_FEATURE_SET"] = prev[0]
            elif "KYOTEI_FEATURE_SET" in os.environ:
                os.environ.pop("KYOTEI_FEATURE_SET")
            if prev[1] is not None:
                os.environ["KYOTEI_USE_MOTOR_WIN_PROXY"] = prev[1]


if __name__ == "__main__":
    unittest.main()
