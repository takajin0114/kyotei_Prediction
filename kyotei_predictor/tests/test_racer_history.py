"""
DB 由来 recent_form / venue_course 計算のユニットテスト。
リークなし（as_of_date より前のみ使用）と履歴不足時の防御を検証する。
"""
import unittest

from kyotei_predictor.pipelines.racer_history import (
    compute_recent_form,
    compute_venue_form,
)

# (reg_no, race_date, stadium, arrival)
History = list


class TestComputeRecentForm(unittest.TestCase):
    def test_no_history_returns_defensive(self):
        """履歴が無い場合は (0.5, 0.0, 0.0, 0) で落ちないこと"""
        out = compute_recent_form([], "12345", "2024-06-15", n=5)
        self.assertEqual(out, (0.5, 0.0, 0.0, 0))

    def test_only_future_races_returns_defensive(self):
        """as_of_date 以降のレースだけある場合は使わず (0.5, 0.0, 0.0, 0)"""
        history: History = [
            ("12345", "2024-06-20", "TODA", 1),
            ("12345", "2024-06-25", "TODA", 2),
        ]
        out = compute_recent_form(history, "12345", "2024-06-15", n=5)
        self.assertEqual(out, (0.5, 0.0, 0.0, 0))

    def test_uses_only_past_races_no_leak(self):
        """as_of_date より前の履歴のみ使用し、当日以降は使わないこと"""
        history: History = [
            ("12345", "2024-06-01", "TODA", 1),
            ("12345", "2024-06-08", "TODA", 2),
            ("12345", "2024-06-15", "TODA", 3),  # as_of 同日は含めない
            ("12345", "2024-06-22", "TODA", 1),
        ]
        out = compute_recent_form(history, "12345", "2024-06-15", n=5)
        # 使うのは 2024-06-01, 2024-06-08 の2走のみ
        self.assertEqual(out[3], 2)
        self.assertAlmostEqual(out[0], 1.0 - (1.5 - 1) / 5.0)  # avg_rank 1.5 -> norm
        self.assertAlmostEqual(out[1], 0.5)   # 1着率 1/2
        self.assertAlmostEqual(out[2], 1.0)   # 3着内 2/2

    def test_enough_history_returns_rates(self):
        """直近 n 走が揃っている場合に 1着率・3着内率が計算されること"""
        history: History = [
            ("R1", "2024-05-01", "A", 1),
            ("R1", "2024-05-08", "A", 2),
            ("R1", "2024-05-15", "A", 1),
            ("R1", "2024-05-22", "A", 3),
            ("R1", "2024-05-29", "A", 2),
        ]
        out = compute_recent_form(history, "R1", "2024-06-01", n=5)
        self.assertEqual(out[3], 5)
        self.assertGreater(out[0], 0)
        self.assertLessEqual(out[0], 1)
        self.assertAlmostEqual(out[1], 2 / 5)  # 1着2回
        self.assertAlmostEqual(out[2], 5 / 5)   # 3着内5回

    def test_different_reg_no_ignored(self):
        """別の選手の履歴は含めないこと"""
        history: History = [
            ("OTHER", "2024-05-01", "A", 1),
            ("OTHER", "2024-05-08", "A", 6),
        ]
        out = compute_recent_form(history, "R1", "2024-06-01", n=5)
        self.assertEqual(out, (0.5, 0.0, 0.0, 0))


class TestComputeVenueForm(unittest.TestCase):
    def test_no_history_returns_defensive(self):
        """履歴が無い場合は (0.5, 0.0, 0) で落ちないこと"""
        out = compute_venue_form([], "12345", "2024-06-15", "TODA", n=10)
        self.assertEqual(out, (0.5, 0.0, 0))

    def test_uses_only_past_and_same_stadium(self):
        """as_of_date より前かつ当該場のみ使用すること"""
        history: History = [
            ("R1", "2024-05-01", "TODA", 1),
            ("R1", "2024-05-08", "TODA", 2),
            ("R1", "2024-05-15", "EDOGAWA", 3),
            ("R1", "2024-05-22", "TODA", 1),
        ]
        out = compute_venue_form(history, "R1", "2024-05-25", "TODA", n=10)
        # TODA かつ 2024-05-25 より前: 5/1, 5/8, 5/22 の3走 → 1着2回
        self.assertEqual(out[2], 3)
        self.assertAlmostEqual(out[1], 2 / 3, places=4)

    def test_different_stadium_ignored(self):
        """他場の成績は含めないこと"""
        history: History = [
            ("R1", "2024-05-01", "EDOGAWA", 1),
            ("R1", "2024-05-08", "EDOGAWA", 1),
        ]
        out = compute_venue_form(history, "R1", "2024-06-01", "TODA", n=10)
        self.assertEqual(out, (0.5, 0.0, 0))


if __name__ == "__main__":
    unittest.main()
